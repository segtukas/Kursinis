"""Unit testai: chest apdovanojimų taisyklės ir Factory Method."""

from __future__ import annotations

import random
import unittest

from f1_game.oop_rewards import (
    DEFAULT_CHEST_REWARD_SERVICE,
    DiamondChestRule,
    EmeraldChestRule,
    GoldenChestRule,
    PositionChestRuleFactory,
    SilverChestRule,
)


class TestPositionChestRuleFactory(unittest.TestCase):
    def setUp(self) -> None:
        self.factory = PositionChestRuleFactory()

    def test_creates_silver_for_high_positions(self) -> None:
        for pos in (16, 19, 20):
            with self.subTest(pos=pos):
                rule = self.factory.create_rule(pos)
                self.assertIsInstance(rule, SilverChestRule)

    def test_creates_golden_for_mid_pack(self) -> None:
        for pos in (11, 13, 15):
            with self.subTest(pos=pos):
                rule = self.factory.create_rule(pos)
                self.assertIsInstance(rule, GoldenChestRule)

    def test_creates_emerald(self) -> None:
        for pos in (6, 8, 10):
            with self.subTest(pos=pos):
                rule = self.factory.create_rule(pos)
                self.assertIsInstance(rule, EmeraldChestRule)

    def test_creates_diamond_for_top_positions(self) -> None:
        for pos in (1, 3, 5):
            with self.subTest(pos=pos):
                rule = self.factory.create_rule(pos)
                self.assertIsInstance(rule, DiamondChestRule)


class TestChestRewardService(unittest.TestCase):
    def test_reward_tier_and_counts_match_game_rules(self) -> None:
        pool = [f"Upg{i}" for i in range(10)]
        inv = {k: 0 for k in pool}
        rng = random.Random(12345)

        reward = DEFAULT_CHEST_REWARD_SERVICE.build_reward(
            player_position=3,
            upgrade_pool=pool,
            upgrade_inventory=inv,
            rng=rng,
        )
        self.assertEqual(reward.tier, "DIAMOND")
        self.assertTrue(46 <= reward.cash <= 65, reward.cash)
        self.assertEqual(len(reward.upgrades), 5)
        # Inventory auga lygiai tiek, kiek upgrade'ų
        self.assertEqual(sum(inv.values()), 5)

    def test_silver_uses_pool_slice_length(self) -> None:
        pool = ["a", "b", "c", "d"]
        inv = {k: 0 for k in pool}
        reward = DEFAULT_CHEST_REWARD_SERVICE.build_reward(
            player_position=18,
            upgrade_pool=pool,
            upgrade_inventory=inv,
            rng=random.Random(0),
        )
        self.assertEqual(reward.tier, "SILVER")
        self.assertEqual(len(reward.upgrades), min(2, len(pool)))


if __name__ == "__main__":
    unittest.main()
