"""Provider-neutral usage accounting; no prices or provider capabilities are assumed."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class TokenUsage:
    input_tokens: int
    output_tokens: int
    cached_input_tokens: int = 0

    def __post_init__(self) -> None:
        for count in (self.input_tokens, self.output_tokens, self.cached_input_tokens):
            if type(count) is not int or count < 0:
                raise ValueError("usage counts must be non-negative integers")
        if self.cached_input_tokens > self.input_tokens:
            raise ValueError("cached input must be a subset of total input")


@dataclass(frozen=True, slots=True)
class TokenPrices:
    input_per_million: Decimal
    output_per_million: Decimal
    cached_input_per_million: Decimal | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.input_per_million, Decimal) or not isinstance(
            self.output_per_million, Decimal
        ):
            raise ValueError("input and output prices must be Decimal values")
        for price in (
            self.input_per_million,
            self.output_per_million,
            self.cached_input_per_million,
        ):
            if price is not None and (
                not isinstance(price, Decimal) or not price.is_finite() or price < 0
            ):
                raise ValueError("prices must be finite non-negative Decimal values")

    def estimate(self, usage: TokenUsage) -> Decimal | None:
        if usage.cached_input_tokens and self.cached_input_per_million is None:
            return None  # Do not invent an unknown cache billing rate.
        return (
            Decimal(usage.input_tokens - usage.cached_input_tokens) * self.input_per_million
            + Decimal(usage.output_tokens) * self.output_per_million
            + Decimal(usage.cached_input_tokens) * (self.cached_input_per_million or Decimal(0))
        ) / Decimal(1_000_000)


@dataclass(frozen=True, slots=True)
class TaskAttempt:
    task_id: str
    correct: bool
    usage: TokenUsage | None

    def __post_init__(self) -> None:
        if not isinstance(self.task_id, str) or not self.task_id or type(self.correct) is not bool:
            raise ValueError("attempt requires a task identifier and boolean correctness")
        if self.usage is not None and not isinstance(self.usage, TokenUsage):
            raise ValueError("attempt usage must be TokenUsage or explicitly unknown")


def account_attempts(attempts: Iterable[TaskAttempt], prices: TokenPrices) -> dict[str, object]:
    """Include failed/incorrect/retried attempts; count each successful task once.

    Unknown billable usage or cached pricing makes the total cost unknown, never
    zero. Known totals remain useful as lower bounds and are labelled as such.
    Output counts include provider-billed reasoning once, as reported by clients.
    """
    rows = list(attempts)
    successes = len({row.task_id for row in rows if row.correct})
    usages = [row.usage for row in rows if row.usage is not None]
    token_complete = len(usages) == len(rows)
    estimates = [prices.estimate(usage) for usage in usages]
    cost_complete = token_complete and all(value is not None for value in estimates)
    known_cost = sum((value for value in estimates if value is not None), Decimal(0))
    tokens = sum(usage.input_tokens + usage.output_tokens for usage in usages)
    return {
        "attempts": len(rows),
        "successful_tasks": successes,
        "known_total_tokens": tokens,
        "token_usage_complete": token_complete,
        "known_cost_lower_bound": known_cost,
        "cost_complete": cost_complete,
        "total_cost": known_cost if cost_complete else None,
        "tokens_per_success": Decimal(tokens) / successes if successes and token_complete else None,
        "cost_per_success": known_cost / successes if successes and cost_complete else None,
    }
