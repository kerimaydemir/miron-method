import math
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class ThreeWayProbability:
    home: Decimal
    draw: Decimal
    away: Decimal

    def __post_init__(self) -> None:
        if any(value < 0 or value > 1 for value in (self.home, self.draw, self.away)):
            raise ValueError("probabilities must be within [0, 1]")
        if abs(self.home + self.draw + self.away - Decimal("1")) > Decimal(".000001"):
            raise ValueError("probabilities must sum to one")


def elo_expected_score(
    home_rating: Decimal, away_rating: Decimal, home_advantage: Decimal = Decimal("65")
) -> Decimal:
    exponent = float((away_rating - (home_rating + home_advantage)) / Decimal("400"))
    return Decimal(str(1 / (1 + math.pow(10, exponent))))


def poisson_mass(goals: int, intensity: Decimal) -> Decimal:
    if goals < 0 or intensity <= 0:
        raise ValueError("goals must be non-negative and intensity positive")
    return Decimal(
        str(math.exp(-float(intensity)) * math.pow(float(intensity), goals) / math.factorial(goals))
    )


def poisson_three_way(
    home_intensity: Decimal, away_intensity: Decimal, max_goals: int = 12
) -> ThreeWayProbability:
    if max_goals < 6:
        raise ValueError("max_goals must cover a meaningful tail")
    home, draw, away = Decimal("0"), Decimal("0"), Decimal("0")
    for home_goals in range(max_goals + 1):
        home_mass = poisson_mass(home_goals, home_intensity)
        for away_goals in range(max_goals + 1):
            joint = home_mass * poisson_mass(away_goals, away_intensity)
            if home_goals > away_goals:
                home += joint
            elif home_goals == away_goals:
                draw += joint
            else:
                away += joint
    total = home + draw + away
    return ThreeWayProbability(home=home / total, draw=draw / total, away=away / total)


def multiplicative_fair_probabilities(decimal_prices: tuple[Decimal, ...]) -> tuple[Decimal, ...]:
    if len(decimal_prices) < 2 or any(price <= 1 for price in decimal_prices):
        raise ValueError("at least two decimal prices greater than one are required")
    raw = tuple(Decimal("1") / price for price in decimal_prices)
    overround = sum(raw, start=Decimal("0"))
    return tuple(probability / overround for probability in raw)


def brier_score(predictions: tuple[Decimal, Decimal, Decimal], realized_index: int) -> Decimal:
    if realized_index not in (0, 1, 2):
        raise ValueError("realized_index must be 0, 1, or 2")
    targets = tuple(Decimal("1") if index == realized_index else Decimal("0") for index in range(3))
    return sum(
        (
            (probability - target) ** 2
            for probability, target in zip(predictions, targets, strict=True)
        ),
        start=Decimal("0"),
    )
