from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple


@dataclass(frozen=True)
class ChestReward:
    tier: str
    cash: int
    upgrades: List[str]


class ChestTierRule(ABC):
    """
    Abstract reward rule for a single chest tier.
    - Abstraction: abstract matches() contract.
    - Encapsulation: tier/money range/upgrade count are hidden internals.
    """

    def __init__(
        self, tier: str, money_range: Tuple[int, int], upgrade_count: int
    ) -> None:
        self._tier = tier
        self._money_range = money_range
        self._upgrade_count = upgrade_count

    @abstractmethod
    def matches(self, player_position: int) -> bool:
        """Return True if this rule should be used for position."""

    def roll_reward(
        self, upgrade_pool: Sequence[str], rng: random.Random = random
    ) -> ChestReward:
        cash = rng.randint(self._money_range[0], self._money_range[1])
        pool = list(upgrade_pool)
        rng.shuffle(pool)
        picks = pool[: min(self._upgrade_count, len(pool))]
        return ChestReward(tier=self._tier, cash=cash, upgrades=picks)


class SilverChestRule(ChestTierRule):
    def __init__(self) -> None:
        super().__init__(tier="SILVER", money_range=(15, 20), upgrade_count=2)

    def matches(self, player_position: int) -> bool:
        return player_position >= 16


class GoldenChestRule(ChestTierRule):
    def __init__(self) -> None:
        super().__init__(tier="GOLDEN", money_range=(21, 30), upgrade_count=3)

    def matches(self, player_position: int) -> bool:
        return 11 <= player_position <= 15


class EmeraldChestRule(ChestTierRule):
    def __init__(self) -> None:
        super().__init__(tier="EMERALD", money_range=(31, 45), upgrade_count=4)

    def matches(self, player_position: int) -> bool:
        return 6 <= player_position <= 10


class DiamondChestRule(ChestTierRule):
    def __init__(self) -> None:
        super().__init__(tier="DIAMOND", money_range=(46, 65), upgrade_count=5)

    def matches(self, player_position: int) -> bool:
        return 1 <= player_position <= 5


class ChestRuleFactory(ABC):
    """Factory Method pattern: chooses which concrete chest rule to create."""

    @abstractmethod
    def create_rule(self, player_position: int) -> ChestTierRule:
        """Return concrete rule object for given final position."""


class PositionChestRuleFactory(ChestRuleFactory):
    def create_rule(self, player_position: int) -> ChestTierRule:
        if player_position >= 16:
            return SilverChestRule()
        if player_position >= 11:
            return GoldenChestRule()
        if player_position >= 6:
            return EmeraldChestRule()
        return DiamondChestRule()


class ChestRewardService:
    """
    Inheritance + polymorphism usage point:
    rules are different subclasses of ChestTierRule, handled uniformly.
    """

    def __init__(
        self, rules: Sequence[ChestTierRule], factory: ChestRuleFactory
    ) -> None:
        self._rules = list(rules)
        self._factory = factory

    def build_reward(
        self,
        player_position: int,
        upgrade_pool: Sequence[str],
        upgrade_inventory: Dict[str, int],
        rng: random.Random = random,
    ) -> ChestReward:
        # Primary path: explicit Factory Method pattern (listed requirement).
        primary_rule = self._factory.create_rule(player_position)
        reward = primary_rule.roll_reward(upgrade_pool, rng=rng)
        for upg in reward.upgrades:
            upgrade_inventory[upg] += 1
        return reward


DEFAULT_CHEST_REWARD_SERVICE = ChestRewardService(
    rules=[
        SilverChestRule(),
        GoldenChestRule(),
        EmeraldChestRule(),
        DiamondChestRule(),
    ],
    factory=PositionChestRuleFactory(),
)
