"""Tests for the PGW config flow."""

from unittest.mock import AsyncMock, patch

import pytest
from pgw_api import PGWAuthError, PGWConnectionError

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.pgw.const import DOMAIN

USER_INPUT = {
    CONF_USERNAME: "test@example.com",
    CONF_PASSWORD: "testpass",
}


@pytest.fixture(autouse=True)
def _enable_custom(enable_custom_integrations):
    """Enable custom integrations for all tests in this module."""


@pytest.fixture
def mock_validate():
    with patch(
        "custom_components.pgw.config_flow.PGWApiClient"
    ) as mock_cls:
        instance = mock_cls.return_value
        instance.async_validate_credentials = AsyncMock()
        yield instance


async def test_user_flow_success(hass: HomeAssistant, mock_validate):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "PGW Gas"
    assert result["data"] == USER_INPUT


async def test_user_flow_invalid_auth(hass: HomeAssistant, mock_validate):
    mock_validate.async_validate_credentials.side_effect = PGWAuthError("bad")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_user_flow_connection_error(hass: HomeAssistant, mock_validate):
    mock_validate.async_validate_credentials.side_effect = PGWConnectionError("down")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_flow_unknown_error(hass: HomeAssistant, mock_validate):
    mock_validate.async_validate_credentials.side_effect = RuntimeError("boom")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "unknown"}


async def test_user_flow_duplicate(hass: HomeAssistant, mock_validate):
    """Second config entry with same username is rejected."""
    # Create first entry
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY

    # Try duplicate
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
