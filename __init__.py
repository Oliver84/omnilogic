from homeassistant.const import (
    CONF_PASSWORD, CONF_USERNAME)
import logging
import aiohttp
import json
import xml.etree.ElementTree as ET
from omnilogic.omnilogic import OmniLogic

DOMAIN = 'omnilogic'
_LOGGER = logging.getLogger(__name__)

async def async_setup(hass, base_config):
    config = base_config.get(DOMAIN)

    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    api_client = OmniLogic(username, password)
    config_data = await api_client.get_msp_config_file()
    telemetry_data = await api_client.get_telemetry_data()
    BOWS = await api_client.get_BOWS()
    
    for i, BOW in enumerate(BOWS):
        _LOGGER.info('BOW')
        _LOGGER.info(BOW['Name'])
        bow_name = BOW['Name']
        bow_systemId = BOW['System-Id']
        
        # Filter Pump
        filterPump = json.loads(json.dumps(BOWS[i]['Filter']))
        fp_name = filterPump['Name'].replace(' ', '_')
        fp_systemId = filterPump['System-Id']
        filterSpeed = telemetry_data['Backyard']['BOW%s' %(i + 1)]['Filter']['filterSpeed']
        filterState = 'on' if telemetry_data['Backyard']['BOW%s' %(i + 1)]['Filter']['filterState'] == '1' else 'off'
        hass.states.async_set('omnilogic.%s_%s' %(bow_name, fp_name), filterState, {'speed': filterSpeed})

        # Water Temp
        waterTemp = telemetry_data['Backyard']['BOW%s' %(i + 1)]['waterTemp']
        hass.states.async_set('omnilogic.%s_water_temp' %(bow_name), waterTemp)
    await api_client.close()
    return True
