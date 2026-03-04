"""Canonical column contracts and schema validators."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence
import re


REQUIRED_CORE_COLUMNS = (
    "ship_date",
    "year_month",
    "year_quarter",
    "year",
    "amount_ship",
    "amount_supply",
    "amount_pre_share",
    "amount_post_share",
    "qty",
    "brand",
    "territory_code",
    "pharmacy_uid",
)

REQUIRED_AUDIT_COLUMNS = (
    "share_applied_flag",
    "share_rule_version",
    "share_rule_source",
)

VALID_SHARE_RULE_SOURCES = {"direct", "extended", "none"}

SNAKE_CASE_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    missing: tuple[str, ...] = ()
    invalid: tuple[str, ...] = ()
    message: str = ""


def missing_columns(columns: Iterable[str], required: Sequence[str]) -> tuple[str, ...]:
    cols = set(columns)
    return tuple(c for c in required if c not in cols)


def validate_required_columns(
    columns: Iterable[str], required: Sequence[str]
) -> ValidationResult:
    missing = missing_columns(columns, required)
    if missing:
        return ValidationResult(
            ok=False,
            missing=missing,
            message=f"Missing required columns: {', '.join(missing)}",
        )
    return ValidationResult(ok=True, message="Required columns are present.")


def validate_snake_case_columns(columns: Iterable[str]) -> ValidationResult:
    invalid = tuple(c for c in columns if not SNAKE_CASE_PATTERN.match(c))
    if invalid:
        return ValidationResult(
            ok=False,
            invalid=invalid,
            message=f"Non snake_case columns: {', '.join(invalid)}",
        )
    return ValidationResult(ok=True, message="All columns are snake_case.")


def validate_share_rule_source_values(values: Iterable[str]) -> ValidationResult:
    invalid = tuple(sorted({v for v in values if v not in VALID_SHARE_RULE_SOURCES}))
    if invalid:
        return ValidationResult(
            ok=False,
            invalid=invalid,
            message=f"Invalid share_rule_source values: {', '.join(invalid)}",
        )
    return ValidationResult(ok=True, message="share_rule_source values are valid.")

