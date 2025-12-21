"""Constants for the eeproperty integration."""

DOMAIN = "eeproperty"

# API URLs
LOGIN_API_URL = "https://login.eeproperty.com"
VESTA_API_URL = "https://vesta.eeproperty.com"

# Configuration
CONF_BUILDING_CODE = "building_code"
CONF_PERSONAL_CODE = "personal_code"
CONF_2FA = "2fa_code"
CONF_TOKEN_DATE = "token_date"
CONF_TOKEN_EXPIRY = "token_expiry"
CONF_USER_ID = "user_id"
CONF_USER_LABEL = "user_label"

# Default values
DEFAULT_SCAN_INTERVAL = 15  # seconds

# API Headers
HEADER_TOKEN = "X-Token"
HEADER_APP_VERSION = "X-App-Version"
HEADER_REQUESTED_WITH = "X-Requested-With"
APP_VERSION = "1.7.6"
REQUESTED_WITH = "ch.eeproperty.vesta"

# Attributes
ATTR_MACHINE_TYPE = "machine_type"
ATTR_MACHINE_NUMBER = "machine_number"
ATTR_ROOM = "room"
ATTR_PRICING = "pricing"
ATTR_COST_PER_CYCLE = "cost_per_cycle"
ATTR_BALANCE = "balance"

# Symbols
CURRENCY = 'CHF'
