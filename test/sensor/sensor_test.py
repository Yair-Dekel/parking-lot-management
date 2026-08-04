"""
sensor_test.py

Tests the real SensorServer component (TCP accept loop, per-connection
buffering, message parsing) against multiple concurrently-connected
sensors.

The only thing faked out here is the underlying paho.mqtt.client.Client:
SensorServer.start() normally connects to a live broker, and we don't
want these tests to depend on one being up. The fake just records what
SensorServer tries to publish so we can assert on it. Actual delivery
over a real broker is covered separately in mqtt_test.py.

Run via `make test-sensor` (see Makefile), or directly with:
    python3 -m unittest sensor_test -v
"""

import json
import threading
import time
import unittest
from unittest.mock import patch

from parking_lot.sensor import Sensor
import parking_lot.sensor_server as sensor_server_module
from parking_lot.sensor_server import SensorServer


class FakeMqttClient:
    """Stand-in for paho.mqtt.client.Client. Records every publish() call
    instead of talking to a real broker."""

    def __init__(self, *args, **kwargs):
        self.published = []
        self.on_connect = None
        self.on_disconnect = None

    def connect(self, host, port):
        pass

    def loop_start(self):
        pass

    def loop_stop(self):
        pass

    def disconnect(self):
        pass

    def publish(self, topic, payload, qos=0):
        self.published.append((topic, payload))
        return _FakePublishResult()


class _FakePublishResult:
    def wait_for_publish(self):
        pass


class SensorServerMultiSensorTest(unittest.TestCase):
    LOT_ID = "lot_test"
    SENSOR_SERVER_ID = "ss_test"
    TCP_PORT = 6200

    def setUp(self):
        patcher = patch.object(sensor_server_module.mqtt, "Client", FakeMqttClient)
        self.addCleanup(patcher.stop)
        patcher.start()

        self.sensor_server = SensorServer(
            lot_id=self.LOT_ID,
            sensor_server_id=self.SENSOR_SERVER_ID,
            tcp_port=self.TCP_PORT,
        )
        self.sensor_server.start()
        time.sleep(0.3)  # let the TCP listener come up

    def tearDown(self):
        self.sensor_server.stop()

    def _published_payloads(self):
        raw_publishes = self.sensor_server._mqtt_client.published
        return [json.loads(payload) for _, payload in raw_publishes]

    def test_single_sensor_update_is_processed(self):
        with Sensor("sensor_1", "A1", "localhost", self.TCP_PORT) as sensor:
            sensor.report_occupancy(True)
        time.sleep(0.3)

        payloads = self._published_payloads()

        self.assertEqual(len(payloads), 1)
        self.assertEqual(payloads[0]["sensor_id"], "sensor_1")
        self.assertEqual(payloads[0]["spot_id"], "A1")
        self.assertEqual(payloads[0]["is_occupied"], True)

    def test_multiple_sensors_connect_and_update_concurrently(self):
        sensor_count = 5
        sensors = [
            Sensor(f"sensor_{i}", f"spot_{i}", "localhost", self.TCP_PORT)
            for i in range(sensor_count)
        ]

        for sensor in sensors:
            sensor.connect()

        def report(sensor: Sensor, index: int):
            sensor.report_occupancy(index % 2 == 0)

        threads = [
            threading.Thread(target=report, args=(sensor, index))
            for index, sensor in enumerate(sensors)
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        time.sleep(0.5)

        for sensor in sensors:
            sensor.disconnect()

        payloads = self._published_payloads()
        self.assertEqual(len(payloads), sensor_count)

        payload_by_spot = {payload["spot_id"]: payload for payload in payloads}

        for index in range(sensor_count):
            spot_id = f"spot_{index}"
            self.assertIn(spot_id, payload_by_spot)
            self.assertEqual(payload_by_spot[spot_id]["sensor_id"], f"sensor_{index}")
            self.assertEqual(payload_by_spot[spot_id]["is_occupied"], index % 2 == 0)

    def test_multiple_updates_from_same_sensor_over_persistent_connection(self):
        sensor = Sensor("sensor_x", "spot_x", "localhost", self.TCP_PORT)
        sensor.connect()
        sensor.report_occupancy(True)
        sensor.report_occupancy(False)
        sensor.report_occupancy(True)
        time.sleep(0.3)
        sensor.disconnect()

        payloads = self._published_payloads()

        self.assertEqual(len(payloads), 3)
        self.assertEqual([payload["is_occupied"] for payload in payloads], [True, False, True])

    def test_one_sensor_disconnecting_does_not_affect_others(self):
        sensor_a = Sensor("sensor_a", "spot_a", "localhost", self.TCP_PORT)
        sensor_b = Sensor("sensor_b", "spot_b", "localhost", self.TCP_PORT)

        sensor_a.connect()
        sensor_b.connect()

        sensor_a.report_occupancy(True)
        sensor_a.disconnect()

        time.sleep(0.2)

        sensor_b.report_occupancy(False)
        time.sleep(0.3)
        sensor_b.disconnect()

        payloads = self._published_payloads()
        spot_ids = {payload["spot_id"] for payload in payloads}

        self.assertEqual(spot_ids, {"spot_a", "spot_b"})