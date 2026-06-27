"""Initiering för Turf Game-integrationen."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Lista över vilka plattformar denna integration stöder (just nu bara sensorer)
PLATFORMS: list[Platform] = [Platform.SENSOR]

SCAN_INTERVAL = timedelta(minutes=5)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Sätt upp Turf Game från konfigurationen."""
    turfname = entry.data.get("turfname")
    if not turfname:
        _LOGGER.error("Kunde inte hitta 'turfname' i konfigurationen")
        return False

    # Använd Home Assistants rekommenderade metod för asynkrona HTTP-anrop
    session = async_get_clientsession(hass)
    domain_data = hass.data.setdefault(DOMAIN, {})

    # Skapa ett globalt lås för att förhindra HTTP 429 (Too Many Requests) från Turf API
    if "api_lock" not in domain_data:
        domain_data["api_lock"] = asyncio.Lock()
    api_lock = domain_data["api_lock"]

    async def async_update_user_data():
        async with api_lock:
            await asyncio.sleep(1.5)
            url = "https://api.turfgame.com/v5/users"
            payload = [{"name": turfname}]
            headers = {
                "User-Agent": "HomeAssistant-TurfIntegration/0.4.0",
                "Accept": "application/json",
            }
            try:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data and isinstance(data, list) and len(data) > 0:
                            return data[0]
                        return None
                    error_text = await response.text()
                    raise UpdateFailed(f"HTTP {response.status}: {error_text}")
            except UpdateFailed:
                raise
            except Exception as err:
                raise UpdateFailed(f"Kunde inte uppdatera från Turf API: {err}") from err

    user_coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"turf_user_{turfname}",
        update_method=async_update_user_data,
        update_interval=SCAN_INTERVAL,
    )
    # Hämta data direkt första gången; ConfigEntryNotReady kastas här (i __init__) om det misslyckas
    await user_coordinator.async_config_entry_first_refresh()

    entry_data: dict = {"user_coordinator": user_coordinator}

    if "zone_feed_coordinator" not in domain_data:
        async def async_update_zone_feed():
            async with api_lock:
                await asyncio.sleep(1.5)
                url = "https://api.turfgame.com/v5/feeds/zone"
                headers = {
                    "User-Agent": "HomeAssistant-TurfIntegration/0.4.0",
                    "Accept": "application/json",
                }
                try:
                    # Observera: Detta är ett GET-anrop för feeds, inte POST!
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            return await response.json()
                        error_text = await response.text()
                        raise UpdateFailed(f"HTTP {response.status}: {error_text}")
                except UpdateFailed:
                    raise
                except Exception as err:
                    raise UpdateFailed(f"Kunde inte uppdatera Turf zone feed: {err}") from err

        zone_feed_coordinator = DataUpdateCoordinator(
            hass,
            _LOGGER,
            name="turf_zone_feed",
            update_method=async_update_zone_feed,
            update_interval=SCAN_INTERVAL,
        )
        await zone_feed_coordinator.async_config_entry_first_refresh()
        domain_data["zone_feed_coordinator"] = zone_feed_coordinator

    entry_data["zone_feed_coordinator"] = domain_data["zone_feed_coordinator"]

    watched_zones_str = entry.options.get(
        "watched_zones",
        entry.data.get("watched_zones", ""),
    )
    watched_zones = list(
        dict.fromkeys(z.strip() for z in watched_zones_str.split(",") if z.strip())
    )

    watched_regions_str = entry.options.get(
        "watched_new_zones_in_regions",
        entry.data.get("watched_new_zones_in_regions", ""),
    )
    watched_regions = list(
        dict.fromkeys(r.strip() for r in watched_regions_str.split(",") if r.strip())
    )

    watched_areas_str = entry.options.get(
        "watched_new_zones_in_areas",
        entry.data.get("watched_new_zones_in_areas", ""),
    )
    watched_areas = list(
        dict.fromkeys(a.strip() for a in watched_areas_str.split(",") if a.strip())
    )

    entry_data["watched_regions"] = watched_regions
    entry_data["watched_areas"] = watched_areas

    if watched_zones:
        async def async_update_zone_owners():
            async with api_lock:
                await asyncio.sleep(1.5)
                url = "https://api.turfgame.com/v5/zones"
                payload = [{"name": name} for name in watched_zones]
                headers = {
                    "User-Agent": "HomeAssistant-TurfIntegration/0.4.0",
                    "Accept": "application/json",
                }
                try:
                    async with session.post(url, json=payload, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            return {zone["name"]: zone for zone in data if "name" in zone}
                        error_text = await response.text()
                        raise UpdateFailed(f"HTTP {response.status}: {error_text}")
                except UpdateFailed:
                    raise
                except Exception as err:
                    raise UpdateFailed(f"Kunde inte uppdatera zonägare: {err}") from err

        zone_owner_coordinator = DataUpdateCoordinator(
            hass,
            _LOGGER,
            name="turf_zone_owners",
            update_method=async_update_zone_owners,
            update_interval=SCAN_INTERVAL,
        )
        await zone_owner_coordinator.async_config_entry_first_refresh()
        entry_data["zone_owner_coordinator"] = zone_owner_coordinator
        entry_data["watched_zones"] = watched_zones

    domain_data[entry.entry_id] = entry_data

    # Säg till Home Assistant att skicka vidare uppsättningen till sensor.py
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Hantera vad som händer när användaren tar bort integrationen i Home Assistant."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        domain_data = hass.data.get(DOMAIN, {})
        domain_data.pop(entry.entry_id, None)
        domain_data.pop("zone_feed_coordinator", None)
    return unload_ok


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Ladda om integrationen när options ändras (t.ex. bevakade zoner)."""
    await hass.config_entries.async_reload(entry.entry_id)
