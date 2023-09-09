"""Constants for Culligan Custom Component"""

from typing import Final
from logging import getLogger
from datetime import timedelta
from homeassistant.const import Platform

LOGGER = getLogger(__package__)

# Basic information
DOMAIN: Final = "culligan"
DEFAULT_NAME = DOMAIN
NAME = "Culligan"
ISSUE_URL = "https://github.com/rewardone/homeassistant-culligan-water-softener/issues"
VERSION = "1.0.0"

# Polling
API_TIMEOUT = 20
UPDATE_INTERVAL = timedelta(seconds=5)

# Ayla currently has domains for EU, CN, and everywhere else
AYLA_REGION_ELSEWHERE: Final = "Elsewhere"
AYLA_REGION_EU: Final = "Europe"
AYLA_REGION_DEFAULT: Final = AYLA_REGION_ELSEWHERE
AYLA_REGION_OPTIONS = [AYLA_REGION_ELSEWHERE, AYLA_REGION_EU]

# Configuration and options
CONF_ENABLED = "enabled"

# Culligans App ID
CULLIGAN_APP_ID = "OAhRjZjfBSwKLV8MTCjscAdoyJKzjxQW"

# Platforms
PLATFORMS = [Platform.SENSOR]

STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""

VOLUME_FLOW_RATE_LITERS_PER_MINUTE: Final = "L/m"
VOLUME_FLOW_RATE_GALLONS_PER_MINUTE: Final = "gal/m"
