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
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Hantera vad som händer när användaren tar bort integrationen i Home Assistant."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop("zone_feed_coordinator", None)
    return unload_ok


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Ladda om integrationen när options ändras (t.ex. bevakade zoner)."""
    await hass.config_entries.async_reload(entry.entry_id)