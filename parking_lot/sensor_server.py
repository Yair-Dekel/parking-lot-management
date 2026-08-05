"""
sensor_server.py

Responsibilities:
    - Listen for occupancy updates coming from sensors components over a TCP socket,
      as line-delimited JSON.
    - Publish those occupancy changes to the main server over MQTT, so the
      main server can update Redis.

A single parking lot can have more than one sensor server, each one
typically responsible for a specific area of the lot. Each sensor server
publishes on its own MQTT topic (derived from lot_id + sensor_server_id) so the
main server can tell which sensor server (and therefore which area) an
update came from.

start() runs the event loop on an internal background thread and returns
immediately. stop() can then be called from anywhere (main thread, a
signal handler, another component, etc.) to shut the loop down cleanly.

Requires: paho-mqtt (pip install paho-mqtt --break-system-packages)
"""

import argparse
import json
import socket
import select
import threading
import time
from dataclasses import dataclass, asdict
from typing import Optional

import paho.mqtt.client as mqtt


@dataclass
class SpotUpdate:
    lot_id: str
    sensor_server_id: str
    sensor_id: str
    spot_id: str
    is_occupied: bool
    timestamp: float


class SensorServer:
    def __init__(
        self,
        lot_id: str,
        sensor_server_id: str,
        tcp_host: str = "0.0.0.0",
        tcp_port: int = 6000,
        mqtt_host: str = "localhost",
        mqtt_port: int = 1883,
        mqtt_topic_prefix: str = "parking",
    ):
        self.lot_id = lot_id
        self.sensor_server_id = sensor_server_id

        self.tcp_host = tcp_host
        self.tcp_port = tcp_port

        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        self.mqtt_topic = f"{mqtt_topic_prefix}/{self.lot_id}/{self.sensor_server_id}/spot_update"

        self._tcp_socket: Optional[socket.socket] = None
        self._running = threading.Event()
        self._loop_thread: Optional[threading.Thread] = None

        self._epoll: Optional[select.epoll] = None
        self._fd_to_socket = {}
        self._buffers = {}

        self._mqtt_client = mqtt.Client(
            client_id=f"sensor_server_{self.sensor_server_id}",
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        )
        self._mqtt_client.on_connect = self._on_mqtt_connect
        self._mqtt_client.on_disconnect = self._on_mqtt_disconnect

    # ------------------------------------------------------------------
    # API: start / stop
    # ------------------------------------------------------------------
    def start(self):
        self._running.set()

        self._start_mqtt()
        self._start_tcp_server()

        self._loop_thread = threading.Thread(target=self._run, daemon=True)
        self._loop_thread.start()

    def stop(self):
        self._running.clear()

        if self._loop_thread is not None:
            self._loop_thread.join()
            self._loop_thread = None

    #------------------------------------------------------------------
    # TCP: sensor server -> sensors
    #------------------------------------------------------------------
    def _start_mqtt(self):
        self._mqtt_client.connect(self.mqtt_host, self.mqtt_port)
        self._mqtt_client.loop_start()

    def _start_tcp_server(self):
        self._tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._tcp_socket.bind((self.tcp_host, self.tcp_port))
        self._tcp_socket.listen()

        self._tcp_socket.setblocking(False)

        self._epoll = select.epoll()
        self._epoll.register(self._tcp_socket.fileno(), select.EPOLLIN)

        self._fd_to_socket = {self._tcp_socket.fileno(): self._tcp_socket}

    def _run(self):
        while self._running.is_set():
            # Timeout of 1 second so we periodically re-check self._running
            # even when no socket is ready, otherwise stop() would never
            # be able to break us out of a blocking poll().
            events = self._epoll.poll(1)

            for fd, event in events:
                # Handle new connections
                if fd == self._tcp_socket.fileno():
                    self._accept_new_connection()

                # Handle closed / errored connections
                elif event & (select.EPOLLHUP | select.EPOLLERR):
                    self._close_connection(fd)

                # Handle incoming data from existing connections
                elif event & select.EPOLLIN:
                    self._handle_incoming_data(fd)

        self._shutdown()

    def _shutdown(self):
        for fd in list(self._fd_to_socket.keys()):
            self._close_connection(fd)

        if self._epoll is not None:
            self._epoll.close()
            self._epoll = None

        self._mqtt_client.loop_stop()
        self._mqtt_client.disconnect()

    def _accept_new_connection(self):
        try:
            connection, address = self._tcp_socket.accept()
        except OSError:
            return

        connection.setblocking(False)

        fd = connection.fileno()
        self._epoll.register(fd, select.EPOLLIN)
        self._fd_to_socket[fd] = connection
        self._buffers[fd] = ""

    def _handle_incoming_data(self, fd: int):
        connection = self._fd_to_socket[fd]

        try:
            chunk = connection.recv(4096)
        except (ConnectionResetError, OSError):
            self._close_connection(fd)
            return

        if not chunk:
            self._close_connection(fd)
            return

        self._buffers[fd] += chunk.decode("utf-8")

        while "\n" in self._buffers[fd]:
            line, self._buffers[fd] = self._buffers[fd].split("\n", 1)
            line = line.strip()

            if line:
                self._process_sensor_message(line)

    def _close_connection(self, fd: int):
        connection = self._fd_to_socket.pop(fd, None)
        self._buffers.pop(fd, None)

        if connection is None:
            return

        try:
            self._epoll.unregister(fd)
        except (OSError, FileNotFoundError):
            pass

        connection.close()

    def _process_sensor_message(self, raw_message: str):
        try:
            payload = json.loads(raw_message)
        except json.JSONDecodeError:
            return

        try:
            sensor_id = payload["sensor_id"]
            spot_id = payload["spot_id"]
            is_occupied = bool(payload["is_occupied"])
        except KeyError:
            return

        timestamp = payload.get("timestamp", time.time())

        self.publish_spot_update(sensor_id, spot_id, is_occupied, timestamp)

    # ------------------------------------------------------------------
    # MQTT: sensor server -> main server
    # ------------------------------------------------------------------
    def publish_spot_update(
        self,
        sensor_id: str,
        spot_id: str,
        is_occupied: bool,
        timestamp: Optional[float] = None,
    ):
        update = SpotUpdate(
            lot_id=self.lot_id,
            sensor_server_id=self.sensor_server_id,
            sensor_id=sensor_id,
            spot_id=spot_id,
            is_occupied=is_occupied,
            timestamp=timestamp if timestamp is not None else time.time(),
        )

        payload = json.dumps(asdict(update))

        result = self._mqtt_client.publish(self.mqtt_topic, payload, qos=1)
        result.wait_for_publish()

    def _on_mqtt_connect(self, client, userdata, flags, reason_code, properties):
        pass

    def _on_mqtt_disconnect(self, client, userdata, reason_code, properties):
        pass
