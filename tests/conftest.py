"""Test fixtures for the turf_game custom component.

Home Assistant core is not a project dependency, so importing
``custom_components.turf_game.sensor`` directly would fail. We install
minimal stand-ins for the handful of homeassistant symbols sensor.py
imports, just enough to exercise the sensor logic in isolation.
"""
from __future__ import annotations

import os
import sys
import types

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


def _install_stub_homeassistant() -> None:
    if "homeassistant" in sys.modules:
        return

    homeassistant = types.ModuleType("homeassistant")
    const = types.ModuleType("homeassistant.const")
    components = types.ModuleType("homeassistant.components")
    components_sensor = types.ModuleType("homeassistant.components.sensor")
    config_entries = types.ModuleType("homeassistant.config_entries")
    core = types.ModuleType("homeassistant.core")
    helpers = types.ModuleType("homeassistant.helpers")
    helpers_aiohttp_client = types.ModuleType("homeassistant.helpers.aiohttp_client")
    helpers_entity_platform = types.ModuleType("homeassistant.helpers.entity_platform")
    helpers_update_coordinator = types.ModuleType("homeassistant.helpers.update_coordinator")

    class SensorEntity:
        """Stand-in for homeassistant.components.sensor.SensorEntity."""

    class SensorStateClass:
        MEASUREMENT = "measurement"

    class Platform:
        SENSOR = "sensor"

    class ConfigEntry:
        """Stand-in for homeassistant.config_entries.ConfigEntry."""

    class HomeAssistant:
        """Stand-in for homeassistant.core.HomeAssistant."""

    class AddEntitiesCallback:
        """Stand-in for homeassistant.helpers.entity_platform.AddEntitiesCallback."""

    def async_get_clientsession(hass):
        """Stand-in for homeassistant.helpers.aiohttp_client.async_get_clientsession."""
        raise NotImplementedError("not needed for sensor unit tests")

    class UpdateFailed(Exception):
        """Stand-in for homeassistant.helpers.update_coordinator.UpdateFailed."""

    class DataUpdateCoordinator:
        """Stand-in for homeassistant.helpers.update_coordinator.DataUpdateCoordinator."""

        def __init__(self, *args, **kwargs) -> None:
            self.data = None

    class CoordinatorEntity:
        """Stand-in for homeassistant.helpers.update_coordinator.CoordinatorEntity.

        Mirrors the two behaviors sensor.py relies on: storing the
        coordinator, and `_handle_coordinator_update` writing state.
        """

        def __init__(self, coordinator) -> None:
            self.coordinator = coordinator

        def _handle_coordinator_update(self) -> None:
            self.async_write_ha_state()

        def async_write_ha_state(self) -> None:
            """No-op: the real version requires an attached hass instance."""

    const.Platform = Platform
    components_sensor.SensorEntity = SensorEntity
    components_sensor.SensorStateClass = SensorStateClass
    config_entries.ConfigEntry = ConfigEntry
    core.HomeAssistant = HomeAssistant
    helpers_aiohttp_client.async_get_clientsession = async_get_clientsession
    helpers_entity_platform.AddEntitiesCallback = AddEntitiesCallback
    helpers_update_coordinator.CoordinatorEntity = CoordinatorEntity
    helpers_update_coordinator.DataUpdateCoordinator = DataUpdateCoordinator
    helpers_update_coordinator.UpdateFailed = UpdateFailed

    sys.modules["homeassistant"] = homeassistant
    sys.modules["homeassistant.const"] = const
    sys.modules["homeassistant.components"] = components
    sys.modules["homeassistant.components.sensor"] = components_sensor
    sys.modules["homeassistant.config_entries"] = config_entries
    sys.modules["homeassistant.core"] = core
    sys.modules["homeassistant.helpers"] = helpers
    sys.modules["homeassistant.helpers.aiohttp_client"] = helpers_aiohttp_client
    sys.modules["homeassistant.helpers.entity_platform"] = helpers_entity_platform
    sys.modules["homeassistant.helpers.update_coordinator"] = helpers_update_coordinator


_install_stub_homeassistant()
