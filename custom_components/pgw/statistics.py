"""Long-term statistics for the PGW integration.

PGW only publishes monthly billing data, so a live ``total_increasing`` sensor can
never populate the energy dashboard with history: it starts the day the
integration is installed and does not move until the next bill posts.

Instead we push the full billing history into Home Assistant's long-term
statistics as external statistics, one point per billing month with a running
cumulative sum. The energy dashboard then renders one bar per billing month for
the entire account history and stays current as new bills post.

Two statistics are published:

* ``pgw:gas_consumption`` - volume in CCF, the accurate consumption history.
* ``pgw:gas_cost`` - the same history priced at your *current* rate, so total
  spend is comparable across months. It is an estimate, not what you were billed.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, tzinfo
from typing import TYPE_CHECKING

from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.models import StatisticData, StatisticMetaData
from homeassistant.components.recorder.statistics import async_add_external_statistics
from homeassistant.const import UnitOfVolume
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util

from .const import DOMAIN, LOGGER

if TYPE_CHECKING:
    from .coordinator import PGWData

CONSUMPTION_STATISTIC_ID = f"{DOMAIN}:gas_consumption"
COST_STATISTIC_ID = f"{DOMAIN}:gas_cost"


def _tz() -> tzinfo:
    return dt_util.DEFAULT_TIME_ZONE or dt_util.UTC


def _month_start(value: date | datetime) -> datetime:
    """Return midnight on the first of ``value``'s month, in local time."""
    return datetime(value.year, value.month, 1, tzinfo=_tz())


def _previous_month_start(value: date | datetime) -> datetime:
    """Return midnight on the first of the month before ``value``."""
    if value.month == 1:
        return datetime(value.year - 1, 12, 1, tzinfo=_tz())
    return datetime(value.year, value.month - 1, 1, tzinfo=_tz())


@dataclass(frozen=True)
class _Point:
    """A single cumulative statistics point."""

    start: datetime
    ccf: float
    cost: float


def _build_points(data: PGWData) -> list[_Point]:
    """Collapse the billing history into one cumulative point per month."""
    # De-duplicate on (year, month), keeping the last value the API returned.
    by_month: dict[tuple[int, int], float] = {
        (entry.month.year, entry.month.month): entry.ccf for entry in data.usage
    }
    ordered = sorted(by_month.items())
    rate = data.billing.current_rate or 0.0

    # Zero anchor one month before the first bill, so the first month's bar is
    # the delta up from zero rather than an absolute cumulative value.
    first_year, first_month = ordered[0][0]
    points = [
        _Point(
            start=_previous_month_start(date(first_year, first_month, 1)),
            ccf=0.0,
            cost=0.0,
        )
    ]

    running_ccf = 0.0
    running_cost = 0.0
    for (year, month), ccf in ordered:
        running_ccf += ccf
        running_cost += ccf * rate
        points.append(
            _Point(
                start=_month_start(date(year, month, 1)),
                ccf=round(running_ccf, 3),
                cost=round(running_cost, 2),
            )
        )
    return points


@callback
def async_import_history(hass: HomeAssistant, data: PGWData) -> None:
    """Import the full PGW billing history into long-term statistics."""
    if "recorder" not in hass.config.components or not data.usage:
        return

    points = _build_points(data)
    currency = hass.config.currency or "USD"

    consumption_meta = StatisticMetaData(
        has_mean=False,
        has_sum=True,
        name="PGW Gas Consumption",
        source=DOMAIN,
        statistic_id=CONSUMPTION_STATISTIC_ID,
        unit_of_measurement=UnitOfVolume.CENTUM_CUBIC_FEET,
    )
    cost_meta = StatisticMetaData(
        has_mean=False,
        has_sum=True,
        name="PGW Gas Cost (estimated at current rate)",
        source=DOMAIN,
        statistic_id=COST_STATISTIC_ID,
        unit_of_measurement=currency,
    )

    async_add_external_statistics(
        hass,
        consumption_meta,
        [StatisticData(start=p.start, state=p.ccf, sum=p.ccf) for p in points],
    )
    async_add_external_statistics(
        hass,
        cost_meta,
        [StatisticData(start=p.start, state=p.cost, sum=p.cost) for p in points],
    )
    LOGGER.debug(
        "Imported %d months of PGW statistics (through %s)",
        len(points) - 1,
        points[-1].start.date(),
    )


@callback
def async_clear_legacy_statistics(hass: HomeAssistant, entry_id: str) -> None:
    """Drop stale auto-generated stats from the old total_increasing sensor.

    Before this integration owned its statistics, ``sensor.pgw_gas_meter_total_usage``
    was a ``total_increasing`` sensor and the recorder generated its own (flat,
    near-zero) statistics for it. Those would collide with the imported history,
    so clear them once per Home Assistant start.
    """
    if "recorder" not in hass.config.components:
        return
    statistic_id = er.async_get(hass).async_get_entity_id(
        "sensor", DOMAIN, f"{entry_id}_total_usage"
    )
    if statistic_id is not None:
        get_instance(hass).async_clear_statistics([statistic_id])
