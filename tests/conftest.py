"""Shared test fixtures for PGW integration tests."""

from __future__ import annotations

from datetime import date

import pytest
from pgw_api import BillingSummary, GasUsage

from custom_components.pgw.coordinator import PGWData


def make_usage(
    month: date = date(2024, 1, 1),
    ccf: float = 85.0,
    period_start: date | None = date(2023, 12, 15),
    period_end: date | None = date(2024, 1, 16),
) -> GasUsage:
    return GasUsage(
        month=month, ccf=ccf, period_start=period_start, period_end=period_end
    )


def make_billing(
    current_bill: float = 120.50,
    current_usage_ccf: float = 85.0,
    current_period_days: int = 32,
    previous_bill: float = 95.00,
    previous_usage_ccf: float = 60.0,
    previous_period_days: int = 30,
    previous_year_bill: float = 110.00,
    previous_year_usage_ccf: float = 80.0,
    balance_due: float = 120.50,
    period_start: date | None = date(2023, 12, 15),
    period_end: date | None = date(2024, 1, 16),
) -> BillingSummary:
    return BillingSummary(
        current_bill=current_bill,
        current_usage_ccf=current_usage_ccf,
        current_period_days=current_period_days,
        previous_bill=previous_bill,
        previous_usage_ccf=previous_usage_ccf,
        previous_period_days=previous_period_days,
        previous_year_bill=previous_year_bill,
        previous_year_usage_ccf=previous_year_usage_ccf,
        balance_due=balance_due,
        period_start=period_start,
        period_end=period_end,
    )


@pytest.fixture
def sample_data() -> PGWData:
    """PGWData with two months of usage and billing."""
    return PGWData(
        usage=[
            make_usage(date(2024, 1, 1), 85.0, date(2023, 12, 15), date(2024, 1, 16)),
            make_usage(date(2023, 12, 1), 72.0, date(2023, 11, 14), date(2023, 12, 15)),
        ],
        billing=make_billing(),
    )


@pytest.fixture
def empty_data() -> PGWData:
    """PGWData with no usage."""
    return PGWData(usage=[], billing=make_billing())


@pytest.fixture
def single_month_data() -> PGWData:
    """PGWData with only one month of usage."""
    return PGWData(
        usage=[make_usage(date(2024, 1, 1), 85.0)],
        billing=make_billing(),
    )
