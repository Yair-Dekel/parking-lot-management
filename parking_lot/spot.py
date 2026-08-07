"""
spot.py

Represents a single parking spot occupancy reading - what a Sensor
observes and reports.
"""

import json
from typing import Optional


class Spot:
    def __init__(
        self,
        parking_lot_id: int = 0,
        id: int = 0,
        taken: bool = False,
        handicap: bool = False,
        electric: bool = False,
        floor: int = 0,
    ):
        self.parking_lot_id = parking_lot_id
        self.id = id
        self.taken = taken
        self.handicap = handicap
        self.electric = electric
        self.floor = floor

    def toggle_occupancy(self):
        self.taken = not self.taken

    def to_dict(self) -> dict:
        return dict(self.__dict__)

    @classmethod
    def from_dict(cls, data: dict) -> "Spot":
        return cls(**data)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, raw: str) -> "Spot":
        return cls.from_dict(json.loads(raw))
