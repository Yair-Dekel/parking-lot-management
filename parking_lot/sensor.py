"""
sensor.py

Simulated parking spot sensor (lot component).

In a real deployment a sensor would sit physically at one parking spot and
push occupancy changes to its sensor server automatically. Here it's
simulated: the simulation code creates a Sensor tied to one
spot_id and calls report_occupancy() whenever that spot's state changes.

Wire format sent to the sensor server (TCP, one JSON object per line):
    {
        "sensor_id":   str,
        "spot_id":     str,
        "is_occupied": bool,
        "timestamp":   float
    }
"""

import json
import socket
import time
from typing import Optional


class Sensor:
    def __init__(
        self,
        sensor_id: str,
        spot_id: str,
        sensor_server_host: str = "localhost",
        sensor_server_port: int = 6000,
    ):
        self.sensor_id = sensor_id
        self.spot_id = spot_id
        self.sensor_server_host = sensor_server_host
        self.sensor_server_port = sensor_server_port

        self._socket: Optional[socket.socket] = None

    def connect(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect((self.sensor_server_host, self.sensor_server_port))

    def disconnect(self):
        if self._socket is not None:
            self._socket.close()
            self._socket = None

    def is_connected(self) -> bool:
        return self._socket is not None

    def report_occupancy(self, is_occupied: bool, timestamp: Optional[float] = None):
        if self._socket is None:
            raise RuntimeError("Sensor is not connected. Call connect() first.")

        message = {
            "sensor_id": self.sensor_id,
            "spot_id": self.spot_id,
            "is_occupied": is_occupied,
            "timestamp": timestamp if timestamp is not None else time.time(),
        }

        payload = json.dumps(message) + "\n"
        self._socket.sendall(payload.encode("utf-8"))

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.disconnect()

