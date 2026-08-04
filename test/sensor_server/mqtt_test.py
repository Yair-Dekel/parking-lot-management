"""
mqtt_test.py

End-to-end test of the Sensor -> SensorServer -> MQTT path.

This test runs a real SensorServer and a fake MQTT client subscribed to 
the topic it publishes on, so it verifies MQTT delivery actually works, 
not just that the sensor server tries to publish.

Requires a running MQTT broker reachable at MQTT_HOST:MQTT_PORT, e.g.:
    mosquitto -p 1883

Run via `make test-mqtt` (see Makefile), or directly with:
    python3 -m unittest mqtt_test -v
"""

import json
import queue
import time
import unittest

import paho.mqtt.client as mqtt

from parking_lot.sensor import Sensor
from parking_lot.sensor_server import SensorServer

MQTT_HOST = "localhost"
MQTT_PORT = 1883


class MqttSubscriber:
    """Subscribes to a topic and hands received messages back through a
    queue, so tests can assert on what the sensor server actually
    published over MQTT."""

    def __init__(self, topic: str, host: str = MQTT_HOST, port: int = MQTT_PORT):
        self.topic = topic
        self.messages: "queue.Queue" = queue.Queue()

        self._client = mqtt.Client(client_id="mqtt_test_subscriber")
        self._client.on_message = self._on_message
        self._client.connect(host, port)
        self._client.subscribe(self.topic, qos=1)
        self._client.loop_start()

    def _on_message(self, client, userdata, message):
        self.messages.put(json.loads(message.payload.decode("utf-8")))

    def wait_for_message(self, timeout: float = 5):
        return self.messages.get(timeout=timeout)

    def stop(self):
        self._client.loop_stop()
        self._client.disconnect()


class MqttPublishingTest(unittest.TestCase):
    LOT_ID = "lot_test"
    SENSOR_SERVER_ID = "ss_test"
    TCP_PORT = 6100

    def setUp(self):
        self.sensor_server = SensorServer(
            lot_id=self.LOT_ID,
            sensor_server_id=self.SENSOR_SERVER_ID,
            tcp_port=self.TCP_PORT,
            mqtt_host=MQTT_HOST,
            mqtt_port=MQTT_PORT,
        )
        self.sensor_server.start()
        time.sleep(0.5)  # let the TCP listener and MQTT connection come up

        self.subscriber = MqttSubscriber(self.sensor_server.mqtt_topic)
        time.sleep(0.5)  # let the subscription register with the broker

    def tearDown(self):
        self.subscriber.stop()
        self.sensor_server.stop()

    def test_sensor_update_is_published_over_mqtt(self):
        sensor = Sensor("sensor_e2e", "E5", "localhost", self.TCP_PORT)
        sensor.connect()
        sensor.report_occupancy(True)
        sensor.disconnect()

        published = self.subscriber.wait_for_message(timeout=5)

        self.assertEqual(published["lot_id"], self.LOT_ID)
        self.assertEqual(published["sensor_server_id"], self.SENSOR_SERVER_ID)
        self.assertEqual(published["sensor_id"], "sensor_e2e")
        self.assertEqual(published["spot_id"], "E5")
        self.assertEqual(published["is_occupied"], True)
        self.assertIn("timestamp", published)

    def test_occupancy_transition_is_published(self):
        sensor = Sensor("sensor_e2e_2", "E6", "localhost", self.TCP_PORT)
        sensor.connect()

        sensor.report_occupancy(True)
        first = self.subscriber.wait_for_message(timeout=5)

        sensor.report_occupancy(False)
        second = self.subscriber.wait_for_message(timeout=5)

        sensor.disconnect()

        self.assertEqual(first["is_occupied"], True)
        self.assertEqual(second["is_occupied"], False)

    def test_multiple_sensors_publish_independently(self):
        sensor_a = Sensor("sensor_a", "F1", "localhost", self.TCP_PORT)
        sensor_b = Sensor("sensor_b", "F2", "localhost", self.TCP_PORT)

        sensor_a.connect()
        sensor_b.connect()

        sensor_a.report_occupancy(True)
        sensor_b.report_occupancy(False)

        sensor_a.disconnect()
        sensor_b.disconnect()

        received = [self.subscriber.wait_for_message(timeout=5) for _ in range(2)]
        received_spot_ids = {message["spot_id"] for message in received}

        self.assertEqual(received_spot_ids, {"F1", "F2"})