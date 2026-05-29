"""Test the Entia cover platform."""

from unittest.mock import AsyncMock

import pytest

from homeassistant.components.cover import (
    ATTR_CURRENT_POSITION,
    ATTR_POSITION,
    DOMAIN as COVER_DOMAIN,
    SERVICE_CLOSE_COVER,
    SERVICE_OPEN_COVER,
    SERVICE_SET_COVER_POSITION,
    CoverState,
)
from homeassistant.components.dsoklic.const import ATTR_BLIND_POSITION, DOMAIN
from homeassistant.const import ATTR_ENTITY_ID, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from tests.common import MockConfigEntry

MOCK_COVER_ID = 42475
MOCK_COVER_FLAT = {
    "flat": {
        "floors": [
            {
                "rooms": [
                    {
                        "id": 2,
                        "label": "Bedroom",
                        "devices": [{"id": MOCK_COVER_ID, "label": "Bedroom Blind"}],
                    }
                ]
            }
        ]
    }
}
MOCK_DEVICES_COVER_OPEN = [
    {"id": MOCK_COVER_ID, "attributes": [{"id": ATTR_BLIND_POSITION, "value": 0}]}
]
MOCK_DEVICES_COVER_CLOSED = [
    {"id": MOCK_COVER_ID, "attributes": [{"id": ATTR_BLIND_POSITION, "value": 100}]}
]
MOCK_DEVICES_COVER_PARTIAL = [
    {"id": MOCK_COVER_ID, "attributes": [{"id": ATTR_BLIND_POSITION, "value": 30}]}
]


def _entity_id(hass: HomeAssistant) -> str:
    registry = er.async_get(hass)
    entity_id = registry.async_get_entity_id(
        COVER_DOMAIN, DOMAIN, f"{DOMAIN}_{MOCK_COVER_ID}_cover"
    )
    assert entity_id is not None, "Cover entity was not registered"
    return entity_id


@pytest.fixture
async def init_cover_integration(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_api_client: AsyncMock,
) -> MockConfigEntry:
    """Set up the Entia integration with a cover device."""
    mock_api_client.get_flat.return_value = MOCK_COVER_FLAT
    mock_api_client.get_devices.return_value = MOCK_DEVICES_COVER_OPEN
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    return mock_config_entry


@pytest.mark.usefixtures("init_cover_integration")
async def test_cover_open_state(hass: HomeAssistant) -> None:
    """Test that API value 0 (fully open) reports CoverState.OPEN and position 100."""
    state = hass.states.get(_entity_id(hass))
    assert state.state == CoverState.OPEN
    assert state.attributes[ATTR_CURRENT_POSITION] == 100


async def test_cover_closed_state(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_api_client: AsyncMock,
) -> None:
    """Test that API value 100 (fully closed) reports CoverState.CLOSED and position 0."""
    mock_api_client.get_flat.return_value = MOCK_COVER_FLAT
    mock_api_client.get_devices.return_value = MOCK_DEVICES_COVER_CLOSED
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get(_entity_id(hass))
    assert state.state == CoverState.CLOSED
    assert state.attributes[ATTR_CURRENT_POSITION] == 0


async def test_cover_partial_position(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_api_client: AsyncMock,
) -> None:
    """Test that API value 30 maps to HA position 70."""
    mock_api_client.get_flat.return_value = MOCK_COVER_FLAT
    mock_api_client.get_devices.return_value = MOCK_DEVICES_COVER_PARTIAL
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get(_entity_id(hass))
    assert state.state == CoverState.OPEN
    assert state.attributes[ATTR_CURRENT_POSITION] == 70


@pytest.mark.usefixtures("init_cover_integration")
async def test_open_cover(
    hass: HomeAssistant,
    mock_api_client: AsyncMock,
) -> None:
    """Test that open_cover calls set_device_attribute with API value 0."""
    entity_id = _entity_id(hass)
    await hass.services.async_call(
        COVER_DOMAIN, SERVICE_OPEN_COVER, {ATTR_ENTITY_ID: entity_id}, blocking=True
    )
    mock_api_client.set_device_attribute.assert_called_once_with(
        MOCK_COVER_ID, ATTR_BLIND_POSITION, 0
    )


@pytest.mark.usefixtures("init_cover_integration")
async def test_close_cover(
    hass: HomeAssistant,
    mock_api_client: AsyncMock,
) -> None:
    """Test that close_cover calls set_device_attribute with API value 100."""
    entity_id = _entity_id(hass)
    await hass.services.async_call(
        COVER_DOMAIN, SERVICE_CLOSE_COVER, {ATTR_ENTITY_ID: entity_id}, blocking=True
    )
    mock_api_client.set_device_attribute.assert_called_once_with(
        MOCK_COVER_ID, ATTR_BLIND_POSITION, 100
    )


@pytest.mark.usefixtures("init_cover_integration")
async def test_set_cover_position(
    hass: HomeAssistant,
    mock_api_client: AsyncMock,
) -> None:
    """Test that set_cover_position inverts HA position to the API value."""
    entity_id = _entity_id(hass)
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_SET_COVER_POSITION,
        {ATTR_ENTITY_ID: entity_id, ATTR_POSITION: 70},
        blocking=True,
    )
    mock_api_client.set_device_attribute.assert_called_once_with(
        MOCK_COVER_ID, ATTR_BLIND_POSITION, 30
    )


async def test_cover_unavailable_when_missing_from_data(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_api_client: AsyncMock,
) -> None:
    """Test that the entity becomes unavailable when device disappears from coordinator data."""
    mock_api_client.get_flat.return_value = MOCK_COVER_FLAT
    mock_api_client.get_devices.return_value = MOCK_DEVICES_COVER_OPEN
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    entity_id = _entity_id(hass)
    assert hass.states.get(entity_id).state == CoverState.OPEN

    mock_api_client.get_devices.return_value = []
    coordinator = mock_config_entry.runtime_data
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == STATE_UNAVAILABLE
