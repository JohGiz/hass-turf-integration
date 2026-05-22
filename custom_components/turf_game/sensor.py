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
        
        sensors = [
            TurfZonesSensor(session, turfname),
            TurfPphSensor(session, turfname)
        ]
        
        # Kontrollera om den globala sensorn för nya zoner redan har laddats.
        # Detta säkerställer att den bara skapas en gång, oavsett hur många användare som läggs till.
        domain_data = hass.data.setdefault(config_entry.domain, {})
        if not domain_data.get("latest_zones_sensor_loaded"):
            sensors.append(TurfLatestZonesSensor(session))
            domain_data["latest_zones_sensor_loaded"] = True
            
        async_add_entities(sensors, update_before_add=True)
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
    """Sensor som visar hur många poäng per timme en Turf-spelare får just nu."""

    def __init__(self, session, turfname: str) -> None:
        """Initiera sensorn."""
        self.session = session
        self.turfname = turfname
        self._attr_name = f"Turf Points Per Hour {turfname}"
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
                        self._attr_native_value = user_data.get("pointsPerHour", 0)
                    else:
                        self._attr_native_value = None
                else:
                    _LOGGER.error("Fel vid anrop till Turf API (Poäng per timme). HTTP-status: %s", response.status)
        except Exception as err:
            _LOGGER.error("Kunde inte uppdatera Turf-sensorn för poäng per timme: %r", err)


class TurfLatestZonesSensor(SensorEntity):
    """Sensor som visar de senast skapade zonerna."""

    def __init__(self, session) -> None:
        """Initiera sensorn."""
        self.session = session
        self._attr_name = "Turf Latest Created Zones"
        self._attr_unique_id = "turf_latest_created_zones"
        self._attr_icon = "mdi:map-marker-star"
        self._extra_state_attributes = {}

    @property
    def extra_state_attributes(self):
        """Returnera extra attribut för sensorn (t.ex. listan med zoner)."""
        return self._extra_state_attributes

    async def async_update(self) -> None:
        """Hämta aktuell data asynkront från Turf API (Feed/Zone)."""
        url = "https://api.turfgame.com/v5/feeds/zone"
        headers = {
            "User-Agent": "HomeAssistant-TurfIntegration/0.1.0",
            "Accept": "application/json"
        }
        
        try:
            # Observera: Detta är ett GET-anrop för feeds, inte POST!
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data and isinstance(data, list) and len(data) > 0:
                        newest = data[0]
                        
                        # Hämta namnet på zonen (feed-datan kan se lite annorlunda ut än vanliga zoner)
                        zone_name = newest.get("name")
                        if not zone_name and "zone" in newest:
                            zone_name = newest["zone"].get("name")
                            
                        self._attr_native_value = zone_name if zone_name else "Okänd zon"
                        
                        # Bygg en snygg lista att ha i attributen för Home Assistant
                        new_zones_list = []
                        for item in data:
                            z = item.get("zone", item)
                            new_zones_list.append({
                                "name": z.get("name", "Okänd"),
                                "dateCreated": z.get("dateCreated", ""),
                                "region": z.get("region", {}).get("name", "Okänd region")
                            })

                        self._extra_state_attributes = {
                            "new_zones": new_zones_list,
                            "count": len(new_zones_list)
                        }
                    else:
                        self._attr_native_value = "Inga nya zoner"
                        self._extra_state_attributes = {"new_zones": [], "count": 0}
                else:
                    _LOGGER.error("Fel vid anrop till Turf API (Senaste zonerna). HTTP-status: %s", response.status)
        except Exception as err:
            _LOGGER.error("Kunde inte uppdatera Turf-sensorn för senaste zoner: %r", err)