from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from typing import Dict, Optional


@dataclass
class DriverIdentity:
    name: str
    surname: str
    number: str
    country: str


@dataclass
class EconomyState:
    money_balance: int
    upgrade_inventory: Dict[str, int]
    upgrade_levels: Dict[str, int]


@dataclass
class CarDevelopmentState:
    car_part_tiers: Dict[str, int]
    teammate_car_tiers: Dict[str, int]


@dataclass
class CareerMetaState:
    winning_team_name: str
    teammate_result: str
    season_gp_index: int
    championship_points: Dict[str, int]
    career_profile_unlocked: bool
    season_started_once: bool
    signing_bonus_given: bool
    selected_offer_name: str


@dataclass
class CareerSnapshot:
    """
    Composition example:
    CareerSnapshot is composed of multiple domain objects.
    """

    driver: DriverIdentity
    economy: EconomyState
    car_development: CarDevelopmentState
    meta: CareerMetaState


class SnapshotSerializer(ABC):
    @abstractmethod
    def save(self, file_path: str, snapshot: CareerSnapshot) -> None:
        pass

    @abstractmethod
    def load(self, file_path: str) -> Optional[CareerSnapshot]:
        pass


class JsonSnapshotSerializer(SnapshotSerializer):
    def save(self, file_path: str, snapshot: CareerSnapshot) -> None:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as fh:
            json.dump(asdict(snapshot), fh, ensure_ascii=False, indent=2)

    def load(self, file_path: str) -> Optional[CareerSnapshot]:
        if not os.path.exists(file_path):
            return None
        with open(file_path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
        return CareerSnapshot(
            driver=DriverIdentity(**raw.get("driver", {})),
            economy=EconomyState(**raw.get("economy", {})),
            car_development=CarDevelopmentState(**raw.get("car_development", {})),
            meta=CareerMetaState(**raw.get("meta", {})),
        )


class CareerDataManager:
    """
    Aggregation example:
    manager aggregates serializer dependency via constructor injection.
    """

    def __init__(self, serializer: SnapshotSerializer) -> None:
        self._serializer = serializer

    def save_snapshot(self, file_path: str, snapshot: CareerSnapshot) -> None:
        self._serializer.save(file_path, snapshot)

    def load_snapshot(self, file_path: str) -> Optional[CareerSnapshot]:
        return self._serializer.load(file_path)
