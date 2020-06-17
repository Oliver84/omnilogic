from homeassistant.const import (
    CONF_PASSWORD, CONF_USERNAME)
import logging
import aiohttp
import xml.etree.ElementTree as ET

DOMAIN = 'omnilogic'
OMNILOGIC_API_URL = 'https://app1.haywardomnilogic.com/HAAPI/HomeAutomation/API.ashx'
_LOGGER = logging.getLogger(__name__)

class OmnilogicApiClient:
  def __init__(self, username=None, password=None, token=None, on_new_token=None):
      """Creates client from provided credentials.
      If token is not provided, or is no longer valid, then a new token will
      be fetched if username and password are provided.
      If on_new_token is provided, it will be called with the newly created token.
      This should be used to save the token, both after initial login and after an
      automatic token renewal. The token is returned as a string and can be passed
      directly into this constructor.
      """

      self._username = username
      self._password = password
      self._token = token if token else None
      self._new_token_callback = on_new_token
      self._session = aiohttp.ClientSession()

  async def close(self):
        await self._session.close()

  async def _get_token(self):
    request = ET.Element('Request')
    name = ET.SubElement(request, 'Name')
    name.text = 'Login'
    parameters = ET.SubElement(request, 'Parameters')
    username = ET.SubElement(parameters, 'Parameter')
    username.set('dataType', 'string')
    username.set('name', 'UserName')
    username.text = self._username
    password = ET.SubElement(parameters, 'Parameter')
    password.set('dataType', 'string')
    password.set('name', 'Password')
    password.text = self._password
    xml_data = ET.tostring(request, encoding='UTF-8', method='xml').decode()

    async with self._session.post(OMNILOGIC_API_URL, data=xml_data) as resp:
        response = await resp.text()
        root = ET.fromstring(response)
        token = root[1][3].text
        self.close()
    return token

  async def _get_new_token(self):
      return await self._get_token()

  async def authenticate(self):

        if not self._token:
            self._token = await self._get_new_token()
  async def post(self):
        await self.authenticate()

async def async_setup(hass, base_config):
    config = base_config.get(DOMAIN)

    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    api_client = OmnilogicApiClient(username, password)
    await api_client.post()
    return True