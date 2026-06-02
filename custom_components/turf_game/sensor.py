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

TURF_RANKS = {
    0: "Newbie",
    1: "Novice Scout",
    2: "Experienced Scout",
    3: "Advanced Scout",
    4: "Master Scout",
    5: "Scout Elder",
    6: "Novice Traveller",
    7: "Experienced Traveller",
    8: "Advanced Traveller",
    9: "Master Traveller",
    10: "World Traveller",
    11: "Novice Explorer",
    12: "Experienced Explorer",
    13: "Advanced Explorer",
    14: "Master Explorer",
    15: "Great Explorer",
    16: "Novice Adventurer",
    17: "Experienced Adventurer",
    18: "Advanced Adventurer",
    19: "Master Adventurer",
    20: "Super Adventurer",
    21: "Novice Seeker",
    22: "Experienced Seeker",
    23: "Advanced Seeker",
    24: "Master Seeker",
    25: "The Seeker",
    26: "Novice Conquistador",
    27: "Experienced Conquistador",
    28: "Advanced Conquistador",
    29: "Master Conquistador",
    30: "Grand Conquistador",
    31: "Novice Zoner",
    32: "Experienced Zoner",
    33: "Advanced Zoner",
    34: "Master Zoner",
    35: "Delicate Zoner",
    36: "Light Turfer",
    37: "Novice Turfer",
    38: "Experienced Turfer",
    39: "Advanced Turfer",
    40: "Turf Master",
    41: "Turf Grandmaster",
    42: "Turf Guardian",
    43: "Turf Knight",
    44: "Turf Hero",
    45: "Turf Elder",
    46: "Turf Preacher",
    47: "Turf Lord",
    48: "Turf Overlord",
    49: "Turf Count",
    50: "Turf King",
    51: "Turf Tsar",
    52: "Turf Caesar",
    53: "Amazing Turfer",
    54: "Incredible Turfer",
    55: "Holy Turfer",
    56: "Turf Angel",
    57: "Turf Archangel",
    58: "Turf God",
    59: "Turf Titan",
    60: "Turfalicious",
}


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
                    "User-Agent": "HomeAssistant-TurfIntegration/0.4.0",
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
            TurfPphSensor(coordinator, turfname),
            TurfRankSensor(coordinator, turfname),
            TurfPlaceSensor(coordinator, turfname)
        ]

        if "zone_feed_coordinator" not in domain_data:
            async def async_update_zone_feed():
                """Hämta data från Turf API (Feed/Zone) asynkront med lås."""
                async with api_lock:
                    await asyncio.sleep(1.5)  # Turf tillåter bara 1 anrop per sekund
                    url = "https://api.turfgame.com/v5/feeds/zone"
                    headers = {
                        "User-Agent": "HomeAssistant-TurfIntegration/0.4.0",
                        "Accept": "application/json"
                    }
                    try:
                        # Observera: Detta är ett GET-anrop för feeds, inte POST!
                        async with session.get(url, headers=headers) as response:
                            if response.status == 200:
                                return await response.json()
                            else:
                                error_text = await response.text()
                                raise UpdateFailed(f"HTTP {response.status}: {error_text}")
                    except Exception as err:
                        raise UpdateFailed(f"Kunde inte uppdatera Turf zone feed: {err}")

            zone_feed_coordinator = DataUpdateCoordinator(
                hass,
                _LOGGER,
                name="turf_zone_feed",
                update_method=async_update_zone_feed,
                update_interval=SCAN_INTERVAL,
            )
            await zone_feed_coordinator.async_config_entry_first_refresh()
            domain_data["zone_feed_coordinator"] = zone_feed_coordinator
            sensors.append(TurfLatestZonesSensor(zone_feed_coordinator))
            

        watched_zones_str = config_entry.options.get(
            "watched_zones",
            config_entry.data.get("watched_zones", ""),
        )
        watched_zones = list(dict.fromkeys(z.strip() for z in watched_zones_str.split(",") if z.strip()))

        if watched_zones:
            async def async_update_zone_owners():
                """Hämta alla bevakade zoner i ett enda batch-anrop."""
                async with api_lock:
                    await asyncio.sleep(1.5)
                    url = "https://api.turfgame.com/v5/zones"
                    payload = [{"name": name} for name in watched_zones]
                    headers = {
                        "User-Agent": "HomeAssistant-TurfIntegration/0.4.0",
                        "Accept": "application/json"
                    }
                    try:
                        async with session.post(url, json=payload, headers=headers) as response:
                            if response.status == 200:
                                data = await response.json()
                                return {zone["name"]: zone for zone in data if "name" in zone}
                            else:
                                error_text = await response.text()
                                raise UpdateFailed(f"HTTP {response.status}: {error_text}")
                    except Exception as err:
                        raise UpdateFailed(f"Kunde inte uppdatera zonägare: {err}")

            zone_owner_coordinator = DataUpdateCoordinator(
                hass,
                _LOGGER,
                name="turf_zone_owners",
                update_method=async_update_zone_owners,
                update_interval=SCAN_INTERVAL,
            )
            await zone_owner_coordinator.async_config_entry_first_refresh()

            for zone_name in watched_zones:
                sensors.append(TurfZoneOwnerSensor(zone_owner_coordinator, zone_name, turfname))

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


class TurfLatestZonesSensor(CoordinatorEntity, SensorEntity):
    """Sensor som visar de senast skapade zonerna."""

    def __init__(self, coordinator) -> None:
        """Initiera sensorn."""
        super().__init__(coordinator)
        self._attr_name = "Turf Latest Created Zones"
        self._attr_unique_id = "turf_latest_created_zones"
        self._attr_icon = "mdi:map-marker-star"

    @property
    def native_value(self):
        """Hämta värdet från koordinatorn."""
        data = self.coordinator.data
        if not data or not isinstance(data, list) or len(data) == 0:
            return "Inga nya zoner"
        newest = data[0]
        # Hämta namnet på zonen (feed-datan kan se lite annorlunda ut än vanliga zoner)
        zone_name = newest.get("name")
        if not zone_name and "zone" in newest:
            zone_name = newest["zone"].get("name")
        return zone_name if zone_name else "Okänd zon"

    @property
    def extra_state_attributes(self):
        """Returnera extra attribut för sensorn (t.ex. listan med zoner)."""
        data = self.coordinator.data
        if not data or not isinstance(data, list) or len(data) == 0:
            return {"new_zones": [], "count": 0}
        # Bygg en snygg lista att ha i attributen för Home Assistant
        new_zones_list = []
        for item in data:
            z = item.get("zone", item)
            new_zones_list.append({
                "name": z.get("name", "Okänd"),
                "dateCreated": z.get("dateCreated", ""),
                "region": z.get("region", {}).get("name", "Okänd region"),
                "area": z.get("region", {}).get("area", {}).get("name", "")
            })
        return {"new_zones": new_zones_list, "count": len(new_zones_list)}


class TurfZoneOwnerSensor(CoordinatorEntity, SensorEntity):
    """Sensor som visar vem som äger en specifik Turf-zon."""

    def __init__(self, coordinator, zone_name: str, player_name: str) -> None:
        """Initiera sensorn."""
        super().__init__(coordinator)
        self.zone_name = zone_name
        self.player_name = player_name
        self._attr_name = f"Turf Zone {zone_name}"
        safe_name = zone_name.lower().replace(" ", "_")
        self._attr_unique_id = f"turf_zone_owner_{safe_name}"
        self._attr_icon = "mdi:map-marker-account"

    @property
    def native_value(self):
        """Hämta värdet från koordinatorn."""
        data = self.coordinator.data
        if not data or self.zone_name not in data:
            return "Zon ej hittad"
        owner = data[self.zone_name].get("currentOwner")
        return owner.get("name") if owner else "Ingen ägare"

    @property
    def extra_state_attributes(self):
        """Returnera extra attribut för sensorn."""
        data = self.coordinator.data
        if not data or self.zone_name not in data:
            return {}
        zone = data[self.zone_name]
        owner = zone.get("currentOwner")
        owner_name = owner.get("name") if owner else None
        return {
            "latitude": zone.get("latitude"),
            "longitude": zone.get("longitude"),
            "zone_name": zone.get("name"),
            "owned_by_player": owner_name == self.player_name,
        }


class TurfRankSensor(CoordinatorEntity, SensorEntity):
    """Sensor som visar spelarens aktuella rank (titel) i Turf."""

    def __init__(self, coordinator, turfname: str) -> None:
        """Initiera sensorn."""
        super().__init__(coordinator)
        self.turfname = turfname
        self._attr_name = f"Turf Rank {turfname}"
        self._attr_unique_id = f"turf_rank_{turfname.lower()}"
        self._attr_icon = "mdi:shield-star"

    @property
    def native_value(self):
        """Hämta värdet (ranknamn) från koordinatorn."""
        if self.coordinator.data:
            rank_num = self.coordinator.data.get("rank")
            if rank_num is not None:
                return TURF_RANKS.get(rank_num, f"Rank {rank_num}")
        return None

    @property
    def extra_state_attributes(self):
        """Returnera extra attribut för sensorn."""
        if self.coordinator.data:
            return {
                "rank_level": self.coordinator.data.get("rank"),
                "total_points": self.coordinator.data.get("totalPoints"),
            }
        return {}


class TurfPlaceSensor(CoordinatorEntity, SensorEntity):
    """Sensor som visar spelarens aktuella placering i pågående omgång."""

    def __init__(self, coordinator, turfname: str) -> None:
        """Initiera sensorn."""
        super().__init__(coordinator)
        self.turfname = turfname
        self._attr_name = f"Turf Place {turfname}"
        self._attr_unique_id = f"turf_place_{turfname.lower()}"
        self._attr_icon = "mdi:trophy"
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        """Hämta värdet (global placering) från koordinatorn."""
        if self.coordinator.data:
            return self.coordinator.data.get("place")
        return None
