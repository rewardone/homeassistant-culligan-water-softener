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
UPDATE_INTERVAL = timedelta(seconds=30)

# Softener property names as they are defined in the class
# these may not be the same names needed to fetch the data from Ayla
ATTR_AVG_DAILY_USAGE = "average_daily_usage"
CAPACITY_REM_GAL = "capacity_remaining_gal"
CURRENT_FLOW_RATE = "current_flow_rate"
DAYS_SALT_REM = "days_salt_remaining"
DAYS_SINCE_LAST_REGEN = "days_since_last_regen"
ERROR_CODE = "error_code"
ERROR_MESSAGE = "error_message"
LAST_REGEN_DATE = "last_regen_date"
MANUAL_SALT_LEVEL_REM = "manual_salt_level_rem_calc"
NEXT_REGEN_ON = "next_regen_on_date"
REGEN_INTERVAL = "regen_interval_days"
REGEN_TONIGHT_PENDING = "regen_tonight_pending"
RSSI = "rssi"
SALT_LEVEL_LOW = "salt_level_low"
TIME_REM_IN_VALVE_POSITION = "time_rem_in_position"
TOTAL_GALLONS_TODAY = "total_gallons_today"
TOTAL_GALLONS_INSTALL = "total_gallons_since_install"
TOTAL_REGENS_INSTALL = "total_regens_since_install"
VALVE_POSITION = "valve_position"
WATER_HARDNESS = "water_hardness"

# More human-readable names for the sensors
ATTRIBUTES: Final[dict[str, str]] = {
    ATTR_AVG_DAILY_USAGE: "average_daily_usage",
    CAPACITY_REM_GAL: "capacity_remaining_gal",
    CURRENT_FLOW_RATE: "current_flow_rate",
    DAYS_SALT_REM: "days_salt_remaining",
    DAYS_SINCE_LAST_REGEN: "days_since_last_regen",
    ERROR_CODE: "error_code",
    ERROR_MESSAGE: "error_message",
    LAST_REGEN_DATE: "last_regen_date",
    MANUAL_SALT_LEVEL_REM: "manual_salt_level_rem_calc",
    NEXT_REGEN_ON: "next_regen_on_date",
    REGEN_INTERVAL: "regen_interval_days",
    REGEN_TONIGHT_PENDING: "regen_tonight_pending",
    RSSI: "rssi",
    SALT_LEVEL_LOW: "salt_level_low",
    TIME_REM_IN_VALVE_POSITION: "time_rem_in_position",
    TOTAL_GALLONS_TODAY: "total_gallons_today",
    TOTAL_GALLONS_INSTALL: "total_gallons_since_install",
    TOTAL_REGENS_INSTALL: "total_regens_since_install",
    VALVE_POSITION: "valve_position",
    WATER_HARDNESS: "water_hardness",
}

# Ayla currently has domains for EU, CN, and everywhere else
AYLA_REGION_ELSEWHERE: Final = "Elsewhere"
AYLA_REGION_EU: Final = "Europe"
AYLA_REGION_DEFAULT: Final = AYLA_REGION_ELSEWHERE
AYLA_REGION_OPTIONS = [AYLA_REGION_ELSEWHERE, AYLA_REGION_EU]

# Configuration and options
CONF_ENABLED = "enabled"

# Culligans App ID
CULLIGAN_APP_ID = "OAhRjZjfBSwKLV8MTCjscAdoyJKzjxQW"

# Icon
ICON = "mdi:water-circle"

# Platforms
SENSOR = "sensor"
PLATFORMS = [SENSOR]  # [Platform.SENSOR]

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
