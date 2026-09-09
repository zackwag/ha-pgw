"""Tests for statistics point building and date helpers."""

from datetime import date, datetime, timezone

from custom_components.pgw.statistics import (
    _build_points,
    _month_start,
    _previous_month_start,
)
from tests.conftest import make_billing, make_usage

from custom_components.pgw.coordinator import PGWData


class TestMonthStart:
    def test_basic(self):
        result = _month_start(date(2024, 3, 15))
        assert result.year == 2024
        assert result.month == 3
        assert result.day == 1
        assert result.hour == 0

    def test_from_datetime(self):
        result = _month_start(datetime(2024, 7, 20, 14, 30))
        assert result.month == 7
        assert result.day == 1


class TestPreviousMonthStart:
    def test_mid_year(self):
        result = _previous_month_start(date(2024, 6, 15))
        assert result.year == 2024
        assert result.month == 5
        assert result.day == 1

    def test_january_wraps_to_december(self):
        result = _previous_month_start(date(2024, 1, 10))
        assert result.year == 2023
        assert result.month == 12
        assert result.day == 1


class TestBuildPoints:
    def test_two_months(self):
        data = PGWData(
            usage=[
                make_usage(date(2024, 2, 1), 50.0),
                make_usage(date(2024, 1, 1), 80.0),
            ],
            billing=make_billing(
                current_bill=120.50,
                current_usage_ccf=85.0,
            ),
        )
        points = _build_points(data)

        # Zero anchor + 2 months = 3 points
        assert len(points) == 3

        # Anchor is one month before the earliest data
        assert points[0].ccf == 0.0
        assert points[0].cost == 0.0
        assert points[0].start.month == 12
        assert points[0].start.year == 2023

        # First real month
        assert points[1].ccf == 80.0
        assert points[1].start.month == 1

        # Second month is cumulative
        assert points[2].ccf == 130.0
        assert points[2].start.month == 2

    def test_cumulative_cost_uses_current_rate(self):
        data = PGWData(
            usage=[
                make_usage(date(2024, 1, 1), 100.0),
            ],
            billing=make_billing(current_bill=200.0, current_usage_ccf=100.0),
        )
        points = _build_points(data)
        rate = 200.0 / 100.0  # $2/CCF

        assert points[1].cost == round(100.0 * rate, 2)

    def test_deduplicates_same_month(self):
        data = PGWData(
            usage=[
                make_usage(date(2024, 1, 1), 80.0),
                make_usage(date(2024, 1, 1), 85.0),
            ],
            billing=make_billing(),
        )
        points = _build_points(data)
        # Anchor + 1 deduplicated month
        assert len(points) == 2
        # Last value wins
        assert points[1].ccf == 85.0

    def test_zero_rate_when_no_usage(self):
        data = PGWData(
            usage=[make_usage(date(2024, 1, 1), 50.0)],
            billing=make_billing(current_bill=0.0, current_usage_ccf=0.0),
        )
        points = _build_points(data)
        assert points[1].cost == 0.0

    def test_single_month(self):
        data = PGWData(
            usage=[make_usage(date(2024, 6, 1), 40.0)],
            billing=make_billing(current_bill=60.0, current_usage_ccf=40.0),
        )
        points = _build_points(data)
        assert len(points) == 2
        assert points[0].start.month == 5
        assert points[1].start.month == 6
        assert points[1].ccf == 40.0
