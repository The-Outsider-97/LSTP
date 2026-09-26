from __future__ import annotations

from pathlib import Path

GRAMMAR = Path("spec/grammar.ebnf")


def _grammar() -> str:
    return GRAMMAR.read_text(encoding="utf-8")


def test_expression_numbers_are_unsigned_so_minus_has_one_owner() -> None:
    text = _grammar()
    primary = text.split("primary_expression =", 1)[1].split(";", 1)[0]
    assert "unsigned_number" in primary
    assert "signed_number" not in primary
    assert "signed_period" not in primary
    assert 'unary_expression = [ "-", horizontal_space_opt ], postfix_expression' in text


def test_scope_retains_signed_literals() -> None:
    text = _grammar()
    scope = text.split("scope_item =", 1)[1].split(";", 1)[0]
    assert "signed_number" in scope
    assert "signed_period" in scope


def test_confidence_has_no_term_or_claim_specific_attachment() -> None:
    text = _grammar()
    postfix = text.split("postfix_expression =", 1)[1].split(";", 1)[0]
    claim = text.split("claim_clause =", 1)[1].split(";", 1)[0]
    weighted = text.split("weighted_alternative =", 1)[1].split(";", 1)[0]
    assert "confidence_clause" not in postfix
    assert "confidence_clause" not in claim
    assert "confidence_clause" not in weighted
    assert 'confidence_clause = "%", confidence_number' in text
