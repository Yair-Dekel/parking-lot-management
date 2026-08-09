"""
run_sensor_server.py

Standalone MQTT listener test for test/mqtt/.

Starts a real SensorServer and blocks until Ctrl+C. Meant to be run by
hand, alongside run_main_server (C++) and run_sensors.py, so you can
watch the whole chain work end to end:

    run_sensors.py --(TCP)--> run_sensor_server.py --(MQTT)--> run_main_server

Run:
    python3 run_sensor_server.py
    python3 run_sensor_server.py --tcp-port 6300 --mqtt-port 1883
"""

import argparse
import os
import sys
import time

# Let this script be run directly (`python3 run_sensor_server.py`) without
# having to set PYTHONPATH by hand: parking_lot/ lives two levels up from
# test/mqtt/, at the project root.
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from parking_lot.sensor_server import SensorServer  # noqa: E402


def parse_args():
    parser = argparse.ArgumentParser(description="Run a standalone sensor server for manual MQTT testing")

    parser.add_argument("--lot-id", default="lot_mqtt_test", help="ID of the parking lot")
    parser.add_argument("--server-id", default="ss_mqtt_test", help="ID of this sensor server")
    parser.add_argument("--tcp-host", default="0.0.0.0", help="Host to listen for sensors on")
    parser.add_argument("--tcp-port", type=int, default=6300, help="Port to listen for sensors on")
    parser.add_argument("--mqtt-host", default="localhost", help="MQTT broker host")
    parser.add_argument("--mqtt-port", type=int, default=1883, help="MQTT broker port")

    return parser.parse_args()


def main():
    args = parse_args()

    server = SensorServer(
        lot_id=args.lot_id,
        sensor_server_id=args.server_id,
        tcp_host=args.tcp_host,
        tcp_port=args.tcp_port,
        mqtt_host=args.mqtt_host,
        mqtt_port=args.mqtt_port,
    )

    server.start()

    print(f"Sensor server '{args.server_id}' (lot '{args.lot_id}') listening on "
          f"{args.tcp_host}:{args.tcp_port}, publishing to MQTT topic '{server.mqtt_topic}' "
          f"at {args.mqtt_host}:{args.mqtt_port}.")
    print("Ctrl+C to stop.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping sensor server...")
        server.stop()


if __name__ == "__main__":
    main()
