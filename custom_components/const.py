from typing import Final
from logging import getLogger
from datetime import timedelta
from homeassistant.const import Platform

LOGGER = getLogger(__package__)

DOMAIN: Final = "culligan_water_softener"
UPDATE_INTERVAL = timedelta(seconds=5)
API_TIMEOUT = 20
PLATFORMS = [Platform.SENSOR]

# Ayla currently has domains for EU, CN, and everywhere else
AYLA_REGION_ELSEWHERE: Final = "Elsewhere"
AYLA_REGION_EU: Final = "Europe"
AYLA_REGION_DEFAULT: Final = AYLA_REGION_ELSEWHERE
AYLA_REGION_OPTIONS = [AYLA_REGION_ELSEWHERE, AYLA_REGION_EU]

VOLUME_FLOW_RATE_LITERS_PER_MINUTE: Final = "L/m"
VOLUME_FLOW_RATE_GALLONS_PER_MINUTE: Final = "gal/m"