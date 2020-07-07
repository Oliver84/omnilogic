"""The Omnilogic integration."""
import asyncio
import json
import logging

import aiohttp
from omnilogic.omnilogic import OmniLogic
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, ATTR_TEMPERATURE, TEMP_CELCIUS, TEMP_FARENHEIT
from homeassistant.core import HomeAssistant

from .water_heater import OmniLogicHeater

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({})}, extra=vol.ALLOW_EXTRA)

# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
PLATFORMS = ["light"]


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Omnilogic component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Omnilogic from a config entry."""
    # TODO Store an API object for your platforms to access
    # hass.data[DOMAIN][entry.entry_id] = MyApi(...)

    # for component in PLATFORMS:
    #     hass.async_create_task(
    #         hass.config_entries.async_forward_entry_setup(entry, component)
    #     )

    conf = entry.data
    username = conf[CONF_USERNAME]
    password = conf[CONF_PASSWORD]

    api_client = OmniLogic(username, password)
    config_data = await api_client.get_msp_config_file()
    telemetry_data = await api_client.get_telemetry_data()
    BOWS = await api_client.get_BOWS()

    for i, BOW in enumerate(BOWS):
        
        _LOGGER.info("BOW")
        _LOGGER.info(BOW["Name"])
        bow_name = BOW["Name"]
        bow_systemId = BOW["System-Id"]

        # Filter Information
        filterPump = json.loads(json.dumps(BOWS[i]["Filter"]))
        fp_name = filterPump["Name"].replace(" ", "_")
        fp_systemId = filterPump["System-Id"]

        filterSpeed = telemetry_data["Backyard"]["BOW%s" % (i + 1)]["Filter"][
            "filterSpeed"
        ]
        filterMaxSpeed = filterPump["Max-Pump-Speed"]
        filterMinSpeed = filterPump["Min-Pump-Speed"]
        filterState = (
            "on"
            if telemetry_data["Backyard"]["BOW%s" % (i + 1)]["Filter"]["filterState"]
            == "1"
            else "off"
        )
        hass.states.async_set(
            f"omnilogic.{bow_name}_{fp_name}", filterState, {"speed": filterSpeed, "icon":"mdi:water-pump", "max_speed": filterMaxSpeed, "min_speed": filterMinSpeed, "filter_id": fp_systemId}
        )

        # Water Temp
        waterTemp = telemetry_data['Backyard']['BOW%s' %(i + 1)]['waterTemp']
        hass.states.async_set('omnilogic.%s_water_temp' %(bow_name), waterTemp, {"unit_of_measurement":"°F", "icon":"mdi:thermometer"})

        # Air Temp
        airTemp = telemetry_data['Backyard']['airTemp']
        hass.states.async_set('omnilogic.%s_air_temp' %(bow_name), airTemp, {"unit_of_measurement": "°F", "icon":"mdi:thermometer"})

        # Heater

        bow_heater = json.loads(json.dumps(BOWS[i]["Heater"]))
        heater_name = bow_heater["Operation"]["Heater-Equipment"]["Name"].replace(" ", "_")
        heater_systemId = bow_heater["System-Id"]
        
        heater_setPoint = bow_heater["Current-Set-Point"]
        heater_maxTemp = bow_heater["Max-Settable-Water-Temp"]
        heater_minTemp = bow_heater["Min-Settable-Water-Temp"]

        heater_state = (
            "on"
            if bow_heater["Enabled"] == "yes"
            else "off"
        )

        #omni_heater = OmniLogicHeater(heater_name, heater_minTemp, heater_maxTemp, heater_setPoint, TEMP_FARENHEIT, heater_state, bow_systemId, heater_systemId)

        #hass.states.async_set(
        #    f"omnilogic.{bow_name}_{heater_name}", heater_state, {"setpoint": heater_setPoint, "icon": "mdi:radiator","max_temp": heater_maxTemp, "min_temp": heater_minTemp, "heater_id": heater_systemId, "virtual_id": heater_virtualID}
        #)

    await api_client.close()

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
