"""Initiering för Turf Game-integrationen."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN

# Lista över vilka plattformar denna integration stöder (just nu bara sensorer)
PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Sätt upp Turf Game från konfigurationen."""
    hass.data.setdefault(DOMAIN, {})

    # Säg till Home Assistant att skicka vidare uppsättningen till sensor.py
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Hantera vad som händer när användaren tar bort integrationen i Home Assistant."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    return unload_ok