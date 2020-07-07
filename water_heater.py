import asyncio
import json
import logging

import aiohttp
from omnilogic.omnilogic import OmniLogic
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, ATTR_TEMPERATURE, TEMP_CELSIUS, TEMP_FAHRENHEIT
from homeassistant.core import HomeAssistant
from homeassistant.components.water_heater import (
    WaterHeaterEntity, 
    SUPPORT_OPERATION_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({})}, extra=vol.ALLOW_EXTRA)

SUPPORT_FLAGS_HEATER = (SUPPORT_TARGET_TEMPERATURE | SUPPORT_OPERATION_MODE)

conf = entry.data
username = conf[CONF_USERNAME]
password = conf[CONF_PASSWORD]

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the heater device"""

async def async_setup_entry(hass, config_entry, async_add_entities):
    await async_setup_platform(hass, {}, async_add_entities)


class OmniLogicHeater(WaterHeaterEntity):
    """Representation of an OmniLogic Heater Device"""

    def __init__(self, name, min_temp, max_temp, temp_setpoint, unit_of_measurement, current_operation, pool_id, equipment_id):
        """Initialize the Water Heater Device """
        self._name = name
        self._support_flags = SUPPORT_FLAGS_HEATER

        if temp_setpoint is not None:
            self._support_flags = self._support_flags | SUPPORT_TARGET_TEMPERATURE
        if current_operations is not None:
            self._support_flags = self._support_flags | SUPPORT_OPERATION_MODE

        self._target_temperature = temp_setpoint
        self._unit_of_measurement = unit_of_measurement
        self._current_operation = current_operation
        self._pool_id = pool_id
        self._equipmentid = equipment_id
        self._operation_list = [
            "on",
            "off",
        ]

    @property
    def supported_features(self):
        """Returns the list of supported features"""
        return self._support_flags

    @property
    def should_poll(self):
        """Return the polling state"""
        return True

    @property
    def name(self):
        """Return the name of the heater"""
        return self._name

    @property
    def temperature_unit(self):
        """Return the unit of measure"""
        return self._unit_of_measurement

    @property
    def target_temperature(self):
        """Return the temperature we are trying to reach"""
        return self._target_temperature

    @property
    def current_operation(self):
        """Return the current operation (on/off)"""
        return self._current_operation

    @property
    def operation_list(self):
        """Return the list of available operation modes."""
        return self._operation_list

    async def set_temperature(self, **kwargs):
        """Set the Heater Temperature Setpoint"""
        self._target_temperature = kwargs.get(ATTR_TEMPERATURE)

        """Call OmniLogic to update Temp"""
        
        api_client = OmniLogic(username, password)

        success = await api_client.set_heater_temperature(int(self._pool_id), int(self._equipmentid), int(self._target_temperature))

        if success:
            self.schedule_update_ha_state()
    
    async def set_operation_mode(self, operation_mode):
        """Turn the heater on or off"""
        self._current_operation = operation_mode 

        """Call OmniLogic to update On/Off"""
        heaterEnable = True
        if self._current_operation == "off":
            heaterEnable = False

        api_client = OmniLogic(username, password)

        success = await api_client.set_heater_onoff(int(self._pool_id), int(self._equipmentid), heaterEnable)

        if success:
            self.schedule_update_ha_state()

    async def async_update(self):
        """Retrieve latest state."""
        api_client = OmniLogic(username, password)

        BOWS = await api_client.get_BOWS()

        """Find the right heater to report"""
        for i, BOW in enumerate(BOWS):
            bow_systemId = BOW["System-Id"]

            if self._pool_id == bow_systemId:
                """Pools match = validate heater ID"""
                bow_heater = json.loads(json.dumps(BOWS[i]["Heater"]))
                heater_systemId = bow_heater["System-Id"]

                if self._equipmentid == heater_systemId:
                    """This is the right heater - pull the current status"""
                    self._target_temperature = bow_heater["Current-Set-Point"]
                    self._current_operation = (
                        "on"
                        if bow_heater["Enabled"] == "yes"
                        else "off"
                    )


        
    