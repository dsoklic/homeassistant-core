"""Entia cover entities."""

from typing import Any

from homeassistant.components.cover import (
    ATTR_POSITION,
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTR_BLIND_POSITION, DOMAIN
from .coordinator import EntiaConfigEntry, EntiaCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EntiaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Entia cover entities from a config entry."""
    coordinator: EntiaCoordinator = entry.runtime_data
    async_add_entities(
        EntiaCover(coordinator, device_id)
        for device_id, device in coordinator.data.items()
        if ATTR_BLIND_POSITION in device["attributes"]
    )


class EntiaCover(CoordinatorEntity[EntiaCoordinator], CoverEntity):
    """Representation of an Entia window blind."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_device_class = CoverDeviceClass.BLIND
    _attr_supported_features = (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.SET_POSITION
    )

    def __init__(self, coordinator: EntiaCoordinator, device_id: int) -> None:
        """Initialize the cover."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_cover"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(device_id))},
            name=coordinator.data[device_id]["name"],
            manufacturer="Entia",
        )

    @property
    def available(self) -> bool:
        """Return True if the device is present in the latest coordinator data."""
        return super().available and self._device_id in self.coordinator.data

    @property
    def current_cover_position(self) -> int | None:
        """Return current position (0=closed, 100=fully open)."""
        device = self.coordinator.data.get(self._device_id)
        if device is None:
            return None
        raw = device["attributes"].get(ATTR_BLIND_POSITION)
        if raw is None:
            return None
        return 100 - raw  # API is inverted: 0=open, 100=closed

    @property
    def is_closed(self) -> bool | None:
        """Return True if the cover is fully closed."""
        pos = self.current_cover_position
        if pos is None:
            return None
        return pos == 0

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        await self.coordinator.client.set_device_attribute(
            self._device_id, ATTR_BLIND_POSITION, 0
        )
        await self.coordinator.async_refresh()

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        await self.coordinator.client.set_device_attribute(
            self._device_id, ATTR_BLIND_POSITION, 100
        )
        await self.coordinator.async_refresh()

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move the cover to a specific position."""
        await self.coordinator.client.set_device_attribute(
            self._device_id, ATTR_BLIND_POSITION, 100 - kwargs[ATTR_POSITION]
        )
        await self.coordinator.async_refresh()
