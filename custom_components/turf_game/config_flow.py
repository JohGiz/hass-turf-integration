"""Config flow for Turf Game integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries, exceptions
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema({vol.Required("turfname"): str})

async def validate_input(hass: HomeAssistant, data: dict) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    if len(data["turfname"]) < 3:
        raise InvalidName

    session = async_get_clientsession(hass)
    url = "https://api.turfgame.com/v5/users"
    payload = [{"name": data["turfname"]}]

    try:
        async with session.post(url, json=payload) as response:
            if response.status != 200:
                raise CannotConnect
            
            result = await response.json()
            # Turf API returnerar en tom lista om spelaren inte hittades
            if not result or not isinstance(result, list) or len(result) == 0:
                raise InvalidName
    except aiohttp.ClientError:
        raise CannotConnect

    return {"title": data["turfname"]}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Turf Game."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                return self.async_create_entry(title=info["title"], data=user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidName:
                errors["turfname"] = "invalid_name"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidName(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid hostname."""