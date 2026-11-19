from decimal import Decimal

import pytest

from lstp.costs import TaskAttempt, TokenPrices, TokenUsage, account_attempts


def test_cache_counts_are_subsets_and_reasoning_is_not_added_twice() -> None:
    prices = TokenPrices(Decimal("2"), Decimal("10"), Decimal("0.2"))
    assert prices.estimate(TokenUsage(1000, 100, 800)) == Decimal("0.00156")
    with pytest.raises(ValueError):
        TokenUsage(10, 1, 11)
    with pytest.raises(ValueError):
        TokenUsage(True, 1)


def test_failed_and_repeated_attempts_cost_money_but_do_not_duplicate_successes() -> None:
    prices = TokenPrices(Decimal("1"), Decimal("2"))
    result = account_attempts(
        [
            TaskAttempt("a", False, TokenUsage(100, 10)),
            TaskAttempt("a", True, TokenUsage(100, 10)),
            TaskAttempt("a", True, TokenUsage(100, 10)),
            TaskAttempt("b", False, TokenUsage(100, 10)),
        ],
        prices,
    )
    assert result["successful_tasks"] == 1
    assert result["known_total_tokens"] == 440
    assert result["cost_per_success"] == Decimal("0.00048")


def test_missing_usage_or_cache_rate_never_becomes_free_usage() -> None:
    prices = TokenPrices(Decimal("1"), Decimal("2"))
    assert prices.estimate(TokenUsage(100, 10, 50)) is None
    result = account_attempts(
        [
            TaskAttempt("a", True, TokenUsage(100, 10)),
            TaskAttempt("b", False, None),
        ],
        prices,
    )
    assert result["cost_per_success"] is None
    assert result["tokens_per_success"] is None
    assert result["known_cost_lower_bound"] == Decimal("0.00012")
    assert result["cost_complete"] is False


@pytest.mark.parametrize("price", [Decimal("NaN"), Decimal("Infinity"), Decimal("-1"), 0.1])
def test_invalid_prices_fail_closed(price: Decimal) -> None:
    with pytest.raises(ValueError):
        TokenPrices(price, Decimal("1"))
