"""Tests for sensor value and attribute extraction functions."""

from datetime import date

from custom_components.pgw.sensor import (
    _balance_attrs,
    _balance_due,
    _current_bill,
    _current_bill_attrs,
    _current_month,
    _current_month_attrs,
    _gas_rate,
    _previous_month,
    _previous_month_attrs,
    _total_usage,
    _total_usage_attrs,
)


class TestTotalUsage:
    def test_sums_all_months(self, sample_data):
        assert _total_usage(sample_data) == 85.0 + 72.0

    def test_empty_usage(self, empty_data):
        assert _total_usage(empty_data) is None

    def test_attrs(self, sample_data):
        attrs = _total_usage_attrs(sample_data)
        assert attrs["months_tracked"] == 2
        assert attrs["newest_month"] == "January 2024"
        assert attrs["oldest_month"] == "December 2023"

    def test_attrs_empty(self, empty_data):
        assert _total_usage_attrs(empty_data) == {}


class TestCurrentMonth:
    def test_returns_first_entry(self, sample_data):
        assert _current_month(sample_data) == 85.0

    def test_empty(self, empty_data):
        assert _current_month(empty_data) is None

    def test_attrs(self, sample_data):
        attrs = _current_month_attrs(sample_data)
        assert attrs["billing_month"] == "January 2024"
        assert attrs["period_start"] == "2023-12-15"
        assert attrs["period_end"] == "2024-01-16"

    def test_attrs_no_period(self):
        from tests.conftest import make_billing, make_usage
        from custom_components.pgw.coordinator import PGWData

        data = PGWData(
            usage=[make_usage(period_start=None, period_end=None)],
            billing=make_billing(),
        )
        attrs = _current_month_attrs(data)
        assert "period_start" not in attrs
        assert "period_end" not in attrs


class TestPreviousMonth:
    def test_returns_second_entry(self, sample_data):
        assert _previous_month(sample_data) == 72.0

    def test_single_month(self, single_month_data):
        assert _previous_month(single_month_data) is None

    def test_empty(self, empty_data):
        assert _previous_month(empty_data) is None

    def test_attrs(self, sample_data):
        attrs = _previous_month_attrs(sample_data)
        assert attrs["billing_month"] == "December 2023"

    def test_attrs_single_month(self, single_month_data):
        assert _previous_month_attrs(single_month_data) == {}


class TestBilling:
    def test_current_bill(self, sample_data):
        assert _current_bill(sample_data) == 120.50

    def test_current_bill_attrs(self, sample_data):
        attrs = _current_bill_attrs(sample_data)
        assert attrs["usage_ccf"] == 85.0
        assert attrs["period_days"] == 32
        assert attrs["period_start"] == "2023-12-15"
        assert attrs["period_end"] == "2024-01-16"

    def test_balance_due(self, sample_data):
        assert _balance_due(sample_data) == 120.50

    def test_balance_attrs(self, sample_data):
        attrs = _balance_attrs(sample_data)
        assert attrs["previous_bill"] == 95.00
        assert attrs["previous_year_bill"] == 110.00

    def test_gas_rate(self, sample_data):
        assert _gas_rate(sample_data) == 120.50 / 85.0

    def test_gas_rate_zero_usage(self):
        from tests.conftest import make_billing, make_usage
        from custom_components.pgw.coordinator import PGWData

        data = PGWData(
            usage=[make_usage()],
            billing=make_billing(current_usage_ccf=0.0),
        )
        assert _gas_rate(data) is None
