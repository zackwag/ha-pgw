"""Constants for the PGW integration."""

import logging

from homeassistant.const import Platform

DOMAIN = "pgw"
LOGGER = logging.getLogger(__package__)

PLATFORMS = [Platform.SENSOR]

SCAN_INTERVAL_HOURS = 6
