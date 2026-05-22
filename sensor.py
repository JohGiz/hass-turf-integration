"""Platform for sensor integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)

# Hur ofta Home Assistant ska hämta ny data från Turf (vi sätter den på var 5:e minut
# för att inte spamma deras API i onödan)
SCAN_INTERVAL = timedelta(minutes=5)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Sätt upp Turf-sensorn utifrån data från konfigurationsflödet."""
    # Hämta namnet som användaren skrev in vid installationen i Home Assistant
    turfname = config_entry.data.get("turfname")
    
    if turfname:
        # Använd Home Assistants rekommenderade metod för asynkrona HTTP-anrop
        session = async_get_clientsession(hass)
        async_add_entities([
            TurfZonesSensor(session, turfname),
            TurfPphSensor(session, turfname)
        ], update_before_add=True)
    else:
        _LOGGER.error("Kunde inte hitta 'turfname' i konfigurationen")


class TurfZonesSensor(SensorEntity):
    """Sensor som visar hur många zoner en Turf-spelare äger just nu."""

    def __init__(self, session, turfname: str) -> None:
        """Initiera sensorn."""
        self.session = session
        self.turfname = turfname
        self._attr_name = f"Turf Zones {turfname}"
        self._attr_unique_id = f"turf_zones_{turfname.lower()}"
        self._attr_native_unit_of_measurement = "zones"
        self._attr_icon = "mdi:map-marker-multiple"
        self._attr_state_class = SensorStateClass.MEASUREMENT

    async def async_update(self) -> None:
        """Hämta aktuell data asynkront från Turf API."""
        url = "https://api.turfgame.com/v5/users"
        payload = [{"name": self.turfname}]
        headers = {
            "User-Agent": "HomeAssistant-TurfIntegration/0.1.0",
            "Accept": "application/json"
        }
        
        try:
            async with self.session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    _LOGGER.debug("Data från Turf: %s", data)
                    
                    # Kontrollera att API:et returnerade en fylld lista
                    if data and isinstance(data, list) and len(data) > 0:
                        user_data = data[0]
                        # 'zones'-nyckeln innehåller en array med ID:n för tagna zoner.
                        # Antalet objekt i arrayen = antalet zoner användaren håller just nu.
                        zones = user_data.get("zones", [])
                        self._attr_native_value = len(zones)
                    else:
                        _LOGGER.warning("Hittade ingen data för Turf-användaren: %s", self.turfname)
                        self._attr_native_value = None
                else:
                    error_text = await response.text()
                    _LOGGER.error("Fel vid anrop till Turf API. HTTP-status: %s, Svar: %s", response.status, error_text)
        except Exception as err:
            _LOGGER.error("Kunde inte uppdatera Turf-sensorn: %r", err)


class TurfPphSensor(SensorEntity):
    """Sensor som visar hur många poäng per timme (PPH) en Turf-spelare får just nu."""

    def __init__(self, session, turfname: str) -> None:
        """Initiera sensorn."""
        self.session = session
        self.turfname = turfname
        self._attr_name = f"Turf PPH {turfname}"
        self._attr_unique_id = f"turf_pph_{turfname.lower()}"
        self._attr_native_unit_of_measurement = "pph"
        self._attr_icon = "mdi:speedometer"
        self._attr_state_class = SensorStateClass.MEASUREMENT

    async def async_update(self) -> None:
        """Hämta aktuell data asynkront från Turf API."""
        url = "https://api.turfgame.com/v5/users"
        payload = [{"name": self.turfname}]
        headers = {
            "User-Agent": "HomeAssistant-TurfIntegration/0.1.0",
            "Accept": "application/json"
        }
        
        try:
            async with self.session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data and isinstance(data, list) and len(data) > 0:
                        user_data = data[0]
                        self._attr_native_value = user_data.get("pph", 0)
                    else:
                        self._attr_native_value = None
                else:
                    _LOGGER.error("Fel vid anrop till Turf API (PPH). HTTP-status: %s", response.status)
        except Exception as err:
            _LOGGER.error("Kunde inte uppdatera Turf PPH-sensorn: %r", err)
