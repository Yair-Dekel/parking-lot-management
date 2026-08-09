"""
run_sensors.py

Standalone MQTT listener test for test/mqtt/.

Creates several simulated Sensors, connects them to a running
SensorServer (run_sensor_server.py), and sends occupied/free switches so
you can visually confirm each message shows up:

  1. printed here, when a sensor sends it
  2. printed by run_main_server, once it travels through
     SensorServer -> MQTT -> MainServer

Run (after run_main_server and run_sensor_server are already running):
    python3 run_sensors.py
    python3 run_sensors.py --count 10 --rounds 5 --interval 0.5
"""

import argparse
import time

from parking_lot.sensor import Sensor
from parking_lot.spot import Spot


def parse_args():
    parser = argparse.ArgumentParser(description="Send simulated sensor occupancy switches for manual MQTT testing")

    parser.add_argument("--host", default="localhost", help="Sensor server host")
    parser.add_argument("--port", type=int, default=6300, help="Sensor server port")
    parser.add_argument("--count", type=int, default=5, help="Number of sensors to simulate")
    parser.add_argument("--rounds", type=int, default=3, help="Number of occupied/free switches per sensor")
    parser.add_argument("--interval", type=float, default=1.0, help="Seconds to wait between switches")

    return parser.parse_args()


def main():
    args = parse_args()

    sensors = [
        Sensor(Spot(parking_lot_id=0, id=i), args.host, args.port)
        for i in range(args.count)
    ]

    print(f"Connecting {args.count} sensors to {args.host}:{args.port}...")
    for sensor in sensors:
        sensor.connect()
    print("All sensors connected.\n")

    for round_number in range(1, args.rounds + 1):
        print(f"--- Round {round_number} ---")

        for sensor in sensors:
            sensor.spot.toggle_occupancy()
            sensor.report_occupancy()
            print(f"Sent: spot_id={sensor.spot.id}, taken={sensor.spot.taken}")

        time.sleep(args.interval)

    print("\nDisconnecting sensors...")
    for sensor in sensors:
        sensor.disconnect()
    print("Done.")


if __name__ == "__main__":
    main()