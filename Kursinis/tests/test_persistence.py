"""Unit testai: JSON karjeros failo import/export (composition objektas)."""

from __future__ import annotations

import os
import tempfile
import unittest

from f1_game.persistence import (
    CarDevelopmentState,
    CareerDataManager,
    CareerMetaState,
    CareerSnapshot,
    DriverIdentity,
    EconomyState,
    JsonSnapshotSerializer,
)


def _sample_snapshot() -> CareerSnapshot:
    return CareerSnapshot(
        driver=DriverIdentity(
            name="Test",
            surname="Racer",
            number="17",
            country="LT",
        ),
        economy=EconomyState(
            money_balance=1200,
            upgrade_inventory={"Overtaking Upgrade": 1},
            upgrade_levels={"Overtaking Upgrade": 2},
        ),
        car_development=CarDevelopmentState(
            car_part_tiers={"Engine": 1},
            teammate_car_tiers={"Engine": 2},
        ),
        meta=CareerMetaState(
            winning_team_name="McLaren",
            teammate_result="Lando Norris",
            season_gp_index=2,
            championship_points={"drv::Lando Norris": 25},
            career_profile_unlocked=True,
            season_started_once=True,
            signing_bonus_given=True,
            selected_offer_name="A",
        ),
    )


class TestJsonSnapshotRoundTrip(unittest.TestCase):
    def test_save_load_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "s", "career.json")
            manager = CareerDataManager(serializer=JsonSnapshotSerializer())
            original = _sample_snapshot()
            manager.save_snapshot(path, original)
            loaded = manager.load_snapshot(path)
            self.assertIsNotNone(loaded)
            assert loaded is not None
            self.assertEqual(loaded.driver, original.driver)
            self.assertEqual(loaded.economy, original.economy)
            self.assertEqual(loaded.car_development, original.car_development)
            self.assertEqual(loaded.meta, original.meta)

    def test_load_missing_returns_none(self) -> None:
        manager = CareerDataManager(serializer=JsonSnapshotSerializer())
        self.assertIsNone(
            manager.load_snapshot(os.path.join("no", "such", "file.json"))
        )


if __name__ == "__main__":
    unittest.main()
