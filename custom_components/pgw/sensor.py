"""Sensor platform for PGW integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, override

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PGWConfigEntry, PGWCoordinator, PGWData


@dataclass(frozen=True, kw_only=True)
class PGWSensorEntityDescription(SensorEntityDescription):
    """Description for PGW sensor."""

    value_fn: Callable[[PGWData], float | None]
    attributes_fn: Callable[[PGWData], dict[str, Any]]


def _total_usage(data: PGWData) -> float | None:
    if not data.usage:
        return None
    return sum(entry.ccf for entry in data.usage)


def _total_usage_attrs(data: PGWData) -> dict[str, Any]:
    if not data.usage:
        return {}
    return {
        "months_tracked": len(data.usage),
        "oldest_month": data.usage[-1].month.strftime("%B %Y"),
        "newest_month": data.usage[0].month.strftime("%B %Y"),
    }


def _current_month(data: PGWData) -> float | None:
    if not data.usage:
        return None
    return data.usage[0].ccf


def _previous_month(data: PGWData) -> float | None:
    if len(data.usage) < 2:
        return None
    return data.usage[1].ccf


def _current_month_attrs(data: PGWData) -> dict[str, Any]:
    if not data.usage:
        return {}
    entry = data.usage[0]
    attrs: dict[str, Any] = {"billing_month": entry.month.strftime("%B %Y")}
    if entry.period_start:
        attrs["period_start"] = entry.period_start.isoformat()
    if entry.period_end:
        attrs["period_end"] = entry.period_end.isoformat()
    return attrs


def _previous_month_attrs(data: PGWData) -> dict[str, Any]:
    if len(data.usage) < 2:
        return {}
    entry = data.usage[1]
    attrs: dict[str, Any] = {"billing_month": entry.month.strftime("%B %Y")}
    if entry.period_start:
        attrs["period_start"] = entry.period_start.isoformat()
    if entry.period_end:
        attrs["period_end"] = entry.period_end.isoformat()
    return attrs


def _current_bill(data: PGWData) -> float | None:
    return data.billing.current_bill


def _current_bill_attrs(data: PGWData) -> dict[str, Any]:
    b = data.billing
    attrs: dict[str, Any] = {
        "usage_ccf": b.current_usage_ccf,
        "period_days": b.current_period_days,
    }
    if b.period_start:
        attrs["period_start"] = b.period_start.isoformat()
    if b.period_end:
        attrs["period_end"] = b.period_end.isoformat()
    return attrs


def _balance_due(data: PGWData) -> float | None:
    return data.billing.balance_due


def _balance_attrs(data: PGWData) -> dict[str, Any]:
    b = data.billing
    return {
        "previous_bill": b.previous_bill,
        "previous_year_bill": b.previous_year_bill,
    }


def _gas_rate(data: PGWData) -> float | None:
    """Effective rate in $/CCF for energy dashboard cost tracking."""
    return data.billing.current_rate


def _gas_rate_attrs(data: PGWData) -> dict[str, Any]:
    return {}


SENSORS: tuple[PGWSensorEntityDescription, ...] = (
    PGWSensorEntityDescription(
        key="total_usage",
        translation_key="total_usage",
        native_unit_of_measurement=UnitOfVolume.CENTUM_CUBIC_FEET,
        # No state_class: the energy dashboard is fed from imported monthly
        # statistics (see statistics.py), not from this live sensor. Letting the
        # recorder also track this sensor would collide with that history.
        device_class=SensorDeviceClass.GAS,
        value_fn=_total_usage,
        attributes_fn=_total_usage_attrs,
    ),
    PGWSensorEntityDescription(
        key="current_month_usage",
        translation_key="current_month_usage",
        native_unit_of_measurement=UnitOfVolume.CENTUM_CUBIC_FEET,
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.GAS,
        value_fn=_current_month,
        attributes_fn=_current_month_attrs,
    ),
    PGWSensorEntityDescription(
        key="previous_month_usage",
        translation_key="previous_month_usage",
        native_unit_of_measurement=UnitOfVolume.CENTUM_CUBIC_FEET,
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.GAS,
        value_fn=_previous_month,
        attributes_fn=_previous_month_attrs,
    ),
    PGWSensorEntityDescription(
        key="current_bill",
        translation_key="current_bill",
        native_unit_of_measurement="$",
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.MONETARY,
        value_fn=_current_bill,
        attributes_fn=_current_bill_attrs,
    ),
    PGWSensorEntityDescription(
        key="balance_due",
        translation_key="balance_due",
        native_unit_of_measurement="$",
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.MONETARY,
        value_fn=_balance_due,
        attributes_fn=_balance_attrs,
    ),
    PGWSensorEntityDescription(
        key="gas_rate",
        translation_key="gas_rate",
        native_unit_of_measurement="$/CCF",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_gas_rate,
        attributes_fn=_gas_rate_attrs,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PGWConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up PGW sensors."""
    coordinator = entry.runtime_data
    async_add_entities(
        PGWSensor(coordinator, description) for description in SENSORS
    )


class PGWSensor(CoordinatorEntity[PGWCoordinator], SensorEntity):
    """PGW gas usage sensor."""

    entity_description: PGWSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PGWCoordinator,
        description: PGWSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            name="PGW Gas Meter",
            manufacturer="Philadelphia Gas Works",
        )

    @property
    @override
    def native_value(self) -> float | None:
        """Return the sensor value."""
        if not self.coordinator.data:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    @override
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        if not self.coordinator.data:
            return {}
        return self.entity_description.attributes_fn(self.coordinator.data)
