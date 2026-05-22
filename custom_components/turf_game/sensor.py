"""Platform for sensor integration."""
from __future__ import annotations

import asyncio
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
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

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
        domain_data = hass.data.setdefault(config_entry.domain, {})

        # Skapa ett globalt lås för att förhindra HTTP 429 (Too Many Requests) från Turf API
        if "api_lock" not in domain_data:
            domain_data["api_lock"] = asyncio.Lock()
        api_lock = domain_data["api_lock"]

        async def async_update_user_data():
            """Hämta data från Turf API asynkront med lås."""
            async with api_lock:
                await asyncio.sleep(1.5)  # Turf tillåter bara 1 anrop per sekund
                url = "https://api.turfgame.com/v5/users"
                payload = [{"name": turfname}]
                headers = {
                    "User-Agent": "HomeAssistant-TurfIntegration/0.2.0",
                    "Accept": "application/json"
                }
                try:
                    async with session.post(url, json=payload, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data and isinstance(data, list) and len(data) > 0:
                                return data[0]
                            return None
                        else:
                            error_text = await response.text()
                            raise UpdateFailed(f"HTTP {response.status}: {error_text}")
                except Exception as err:
                    raise UpdateFailed(f"Kunde inte uppdatera från Turf API: {err}")

        coordinator = DataUpdateCoordinator(
            hass,
            _LOGGER,
            name=f"turf_user_{turfname}",
            update_method=async_update_user_data,
            update_interval=SCAN_INTERVAL,
        )

        # Hämta data direkt första gången för att undvika "Unknown"
        await coordinator.async_config_entry_first_refresh()

        sensors = [
            TurfZonesSensor(coordinator, turfname),
            TurfPphSensor(coordinator, turfname)
        ]

        if not domain_data.get("latest_zones_sensor_loaded"):
            sensors.append(TurfLatestZonesSensor(session, api_lock))
            domain_data["latest_zones_sensor_loaded"] = True
            
        async_add_entities(sensors)
    else:
        _LOGGER.error("Kunde inte hitta 'turfname' i konfigurationen")


class TurfZonesSensor(CoordinatorEntity, SensorEntity):
    """Sensor som visar hur många zoner en Turf-spelare äger just nu."""

    def __init__(self, coordinator, turfname: str) -> None:
        """Initiera sensorn."""
        super().__init__(coordinator)
        self.turfname = turfname
        self._attr_name = f"Turf Zones {turfname}"
        self._attr_unique_id = f"turf_zones_{turfname.lower()}"
        self._attr_native_unit_of_measurement = "zones"
        self._attr_icon = "mdi:map-marker-multiple"
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        """Hämta värdet från koordinatorn."""
        if self.coordinator.data:
            zones = self.coordinator.data.get("zones", [])
            return len(zones)
        return None


class TurfPphSensor(CoordinatorEntity, SensorEntity):
    """Sensor som visar hur många poäng per timme en Turf-spelare får just nu."""

    def __init__(self, coordinator, turfname: str) -> None:
        """Initiera sensorn."""
        super().__init__(coordinator)
        self.turfname = turfname
        self._attr_name = f"Turf Points Per Hour {turfname}"
        self._attr_unique_id = f"turf_pph_{turfname.lower()}"
        self._attr_native_unit_of_measurement = "pph"
        self._attr_icon = "mdi:speedometer"
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        """Hämta värdet från koordinatorn."""
        if self.coordinator.data:
            return self.coordinator.data.get("pointsPerHour", 0)
        return None


class TurfLatestZonesSensor(SensorEntity):
    """Sensor som visar de senast skapade zonerna."""

    def __init__(self, session, api_lock) -> None:
        """Initiera sensorn."""
        self.session = session
        self.api_lock = api_lock
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
        async with self.api_lock:
            await asyncio.sleep(1.5)  # Turf tillåter bara 1 anrop per sekund
            url = "https://api.turfgame.com/v5/feeds/zone"
            headers = {
                "User-Agent": "HomeAssistant-TurfIntegration/0.2.0",
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