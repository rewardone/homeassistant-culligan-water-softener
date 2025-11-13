"""Constants for Culligan Custom Component"""

from typing import Final
from logging import getLogger
from homeassistant.const import Platform

LOGGER = getLogger(__package__)

# Basic information
CLIENT: Final = "client"
DOMAIN: Final = "culligan"
DEFAULT_NAME = DOMAIN
NAME = "Culligan"
ISSUE_URL = "https://github.com/rewardone/homeassistant-culligan-water-softener/issues"
VERSION = "1.3.7.2"

# Polling
API_TIMEOUT = 20

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
PLATFORMS = [Platform.BINARY_SENSOR, Platform.BUTTON, Platform.SENSOR, Platform.SWITCH]

STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""

# key is Ayla property, value is culliganIoT property
PROPERTY_VALUE_MAP = {
    "actual_state_dealer_bypass": "actual_state_dealer_bypass",        # no sensor created
    "standard_bypass"           : "actual_state_dealer_bypass",        # unknown if correct mapping, but ayla uses this for bypass and CulIoT doesn't have it
    "aqua_sensor_Zmin"          : "aquasensor_z_min_tank_1",
    "aqua_sensor_Zratio_current": "aquasensor_z_ratio_current_tank_1",
    "away_mode_water_use"       : "away_mode_water_use",
    "avg_no_of_days_btwn_reg"   : "avg_no_of_days_btwn_reg",
    "avg_sun"                   : "avg_sun",
    "avg_mon"                   : "avg_mon",
    "avg_tue"                   : "avg_tue",
    "avg_wed"                   : "avg_wed",
    "avg_thr"                   : "avg_thr",
    "avg_fri"                   : "avg_fri",
    "avg_sat"                   : "avg_sat",
    "average_daily_usage"       : "average_daily_use",
    "BD_rinse"                  : "bd_rinse",                           # no sensor created
    "bw_time"                   : "bw_time",                            # no sensor created
    "capacity_remaining_gallons": "capacity_remaining_tank_1",
    "current_flow_rate"         : "current_flow_rate",
    "days_salt_remaining"       : "days_salt_remaining",
    "days_since_last_regen"     : "days_since_last_regen_tank_1",
    "daily_usage_day_1"         : "daily_usage_day_01",
    "daily_usage_day_2"         : "daily_usage_day_02",
    "daily_usage_day_3"         : "daily_usage_day_03",
    "daily_usage_day_4"         : "daily_usage_day_04",
    "daily_usage_day_5"         : "daily_usage_day_05",
    "daily_usage_day_6"         : "daily_usage_day_06",
    "daily_usage_day_7"         : "daily_usage_day_07",
    "error_flags"               : "errors",
    "flow_profiles_max_flow"    : "flow_meter_high_flow_limit",
    "flow_profiles_min_flow"    : "flow_meter_low_flow_limit",
    "flow_profile_R1_minutes"   : "",
    "flow_profile_R2_minutes"   : "flow_profile_r2_minutes",
    "flow_profile_R3_minutes"   : "flow_profile_r3_minutes",
    "flow_profile_R4_minutes"   : "flow_profile_r4_minutes",
    "flow_profile_R5_minutes"   : "flow_profile_r5_minutes",
    "gbe_fw_version"            : "gbx_firmware_version",
    "gbe_serial_number"         : "",
    "hardness_in_grains_per_gal": "hardness_value",
    "hourly_usage_hour_1"       : "hourly_usage_hour_01",
    "hourly_usage_hour_2"       : "hourly_usage_hour_02",
    "hourly_usage_hour_3"       : "hourly_usage_hour_03",
    "hourly_usage_hour_4"       : "hourly_usage_hour_04",
    "hourly_usage_hour_5"       : "hourly_usage_hour_05",
    "hourly_usage_hour_6"       : "hourly_usage_hour_06",
    "hourly_usage_hour_7"       : "hourly_usage_hour_07",
    "hourly_usage_hour_8"       : "hourly_usage_hour_08",
    "hourly_usage_hour_9"       : "hourly_usage_hour_09",
    "hourly_usage_hour_10"      : "hourly_usage_hour_10",
    "hourly_usage_hour_11"      : "hourly_usage_hour_11",
    "hourly_usage_hour_12"      : "hourly_usage_hour_12",
    "hourly_usage_hour_13"      : "hourly_usage_hour_13",
    "hourly_usage_hour_14"      : "hourly_usage_hour_14",
    "hourly_usage_hour_15"      : "hourly_usage_hour_15",
    "hourly_usage_hour_16"      : "hourly_usage_hour_16",
    "hourly_usage_hour_17"      : "hourly_usage_hour_17",
    "hourly_usage_hour_18"      : "hourly_usage_hour_18",
    "hourly_usage_hour_19"      : "hourly_usage_hour_19",
    "hourly_usage_hour_20"      : "hourly_usage_hour_20",
    "hourly_usage_hour_21"      : "hourly_usage_hour_21",
    "hourly_usage_hour_22"      : "hourly_usage_hour_22",
    "hourly_usage_hour_23"      : "hourly_usage_hour_23",
    "hourly_usage_hour_24"      : "hourly_usage_hour_24",
    "iron_setting"              : "iron_value",
    "last_regen_date_time"      : "last_regen_date_time_tank_1",
    "manual_salt_level_rem_calc": "manual_salt_level_rem_calc",
    "next_regen_on_date"        : "next_regen_date_time",
    "regen_interval_days_setting": "regen_interval_days_setting",
    "regen_tonight_pending"     : "regen_tonight_pending",
    "rssi"                      : "rssi",
    "salt_dosage_in_lbs"        : "manual_salt_dosage",
    "sbt_salt_level_low"        : "salt_alarm_mode",
    "status"                    : "unit_status_tank_1",
    "time_rem_in_position"      : "time_rem_in_position",
    "total_gallons_today"       : "total_water_usage_today_tank_1",
    "total_gallons_since_install": "total_water_usage_since_install_tank_1",
    "total_regens_since_install": "total_regens_since_install",
    "vacation_mode"             : "away_mode",
    "valve_position"            : "valve_position_1"
}
