"""Tests for the watched-region/area zone sensors' new-zone deduplication.

Reproduces the reported bug: a zone (Zone A) that already triggered a
notification must not reappear in `new_zones` when a later zone (Zone B)
shows up in the same watched region/area's feed, since the Turf zone feed
is a sliding window that keeps recently created zones around.
"""
from __future__ import annotations

from custom_components.turf_game.sensor import (
    TurfWatchedAreasZonesSensor,
    TurfWatchedRegionsZonesSensor,
)


class FakeCoordinator:
    """Stand-in for DataUpdateCoordinator; only `.data` is read by the sensors."""

    def __init__(self, data=None) -> None:
        self.data = data


def _zone(name: str, region: str, area: str = "") -> dict:
    return {
        "name": name,
        "dateCreated": "2026-06-29T10:00:00Z",
        "region": {"name": region, "area": {"name": area}},
    }


def test_region_sensor_suppresses_zones_already_present_on_first_update():
    coordinator = FakeCoordinator(data=[_zone("Zone A", "Region X")])
    sensor = TurfWatchedRegionsZonesSensor(coordinator, "player", ["Region X"])

    sensor._handle_coordinator_update()

    assert sensor.extra_state_attributes["new_zones"] == []
    assert sensor.native_value == "Inga nya zoner"


def test_region_sensor_only_reports_genuinely_new_zone():
    coordinator = FakeCoordinator(data=[])
    sensor = TurfWatchedRegionsZonesSensor(coordinator, "player", ["Region X"])
    sensor._handle_coordinator_update()  # baseline: no zones yet

    coordinator.data = [_zone("Zone A", "Region X")]
    sensor._handle_coordinator_update()
    assert [z["name"] for z in sensor.extra_state_attributes["new_zones"]] == ["Zone A"]
    assert sensor.native_value == "Zone A"

    # Zone B appears; the feed still contains Zone A (sliding window)
    coordinator.data = [_zone("Zone B", "Region X"), _zone("Zone A", "Region X")]
    sensor._handle_coordinator_update()
    assert [z["name"] for z in sensor.extra_state_attributes["new_zones"]] == ["Zone B"]
    assert sensor.native_value == "Zone B"


def test_region_sensor_keeps_last_new_zone_when_no_further_new_zones():
    coordinator = FakeCoordinator(data=[])
    sensor = TurfWatchedRegionsZonesSensor(coordinator, "player", ["Region X"])
    sensor._handle_coordinator_update()

    coordinator.data = [_zone("Zone A", "Region X")]
    sensor._handle_coordinator_update()

    # Next poll, feed unchanged
    sensor._handle_coordinator_update()
    assert sensor.extra_state_attributes["new_zones"] == []
    assert sensor.native_value == "Zone A"


def test_region_sensor_survives_restart_baseline_without_renotifying():
    coordinator = FakeCoordinator(data=[_zone("Zone A", "Region X")])
    sensor = TurfWatchedRegionsZonesSensor(coordinator, "player", ["Region X"])
    sensor._handle_coordinator_update()  # simulates HA restart with Zone A already in the feed

    # Zone B appears afterwards; only it should be reported
    coordinator.data = [_zone("Zone B", "Region X"), _zone("Zone A", "Region X")]
    sensor._handle_coordinator_update()
    assert [z["name"] for z in sensor.extra_state_attributes["new_zones"]] == ["Zone B"]


def test_area_sensor_only_reports_genuinely_new_zone():
    coordinator = FakeCoordinator(data=[])
    sensor = TurfWatchedAreasZonesSensor(coordinator, "player", ["Area Y"])
    sensor._handle_coordinator_update()  # baseline

    coordinator.data = [_zone("Zone A", "Region X", "Area Y")]
    sensor._handle_coordinator_update()
    assert [z["name"] for z in sensor.extra_state_attributes["new_zones"]] == ["Zone A"]

    coordinator.data = [
        _zone("Zone B", "Region X", "Area Y"),
        _zone("Zone A", "Region X", "Area Y"),
    ]
    sensor._handle_coordinator_update()
    assert [z["name"] for z in sensor.extra_state_attributes["new_zones"]] == ["Zone B"]
