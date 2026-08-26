"""Sensor platform for PGW integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, override

from pgw_api import GasUsage

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
from .coordinator import PGWConfigEntry, PGWCoordinator


@dataclass(frozen=True, kw_only=True)
class PGWSensorEntityDescription(SensorEntityDescription):
    """Description for PGW sensor."""

    value_fn: Callable[[list[GasUsage]], float | None]
    attributes_fn: Callable[[list[GasUsage]], dict[str, Any]]


def _total_usage_ft3(data: list[GasUsage]) -> float | None:
    """Cumulative total of all usage in ft³ (for energy dashboard)."""
    if not data:
        return None
    return sum(entry.cf for entry in data)


def _total_usage_attrs(data: list[GasUsage]) -> dict[str, Any]:
    if not data:
        return {}
    return {
        "months_tracked": len(data),
        "oldest_month": data[-1].month.strftime("%B %Y"),
        "newest_month": data[0].month.strftime("%B %Y"),
    }


def _current_month_ft3(data: list[GasUsage]) -> float | None:
    if not data:
        return None
    return data[0].cf


def _previous_month_ft3(data: list[GasUsage]) -> float | None:
    if len(data) < 2:
        return None
    return data[1].cf


def _current_month_attrs(data: list[GasUsage]) -> dict[str, Any]:
    if not data:
        return {}
    entry = data[0]
    attrs: dict[str, Any] = {
        "billing_month": entry.month.strftime("%B %Y"),
        "ccf": entry.ccf,
    }
    if entry.period_start:
        attrs["period_start"] = entry.period_start.isoformat()
    if entry.period_end:
        attrs["period_end"] = entry.period_end.isoformat()
    return attrs


def _previous_month_attrs(data: list[GasUsage]) -> dict[str, Any]:
    if len(data) < 2:
        return {}
    entry = data[1]
    attrs: dict[str, Any] = {
        "billing_month": entry.month.strftime("%B %Y"),
        "ccf": entry.ccf,
    }
    if entry.period_start:
        attrs["period_start"] = entry.period_start.isoformat()
    if entry.period_end:
        attrs["period_end"] = entry.period_end.isoformat()
    return attrs


SENSORS: tuple[PGWSensorEntityDescription, ...] = (
    PGWSensorEntityDescription(
        key="total_usage",
        translation_key="total_usage",
        native_unit_of_measurement=UnitOfVolume.CUBIC_FEET,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.GAS,
        value_fn=_total_usage_ft3,
        attributes_fn=_total_usage_attrs,
    ),
    PGWSensorEntityDescription(
        key="current_month_usage",
        translation_key="current_month_usage",
        native_unit_of_measurement=UnitOfVolume.CUBIC_FEET,
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.GAS,
        value_fn=_current_month_ft3,
        attributes_fn=_current_month_attrs,
    ),
    PGWSensorEntityDescription(
        key="previous_month_usage",
        translation_key="previous_month_usage",
        native_unit_of_measurement=UnitOfVolume.CUBIC_FEET,
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.GAS,
        value_fn=_previous_month_ft3,
        attributes_fn=_previous_month_attrs,
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
