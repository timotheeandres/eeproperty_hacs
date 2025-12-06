"""Constants for the eeProperty integration."""

DOMAIN = "eeproperty"

# API URLs
LOGIN_API_URL = "https://login.eeproperty.com"
VESTA_API_URL = "https://vesta.eeproperty.com"

# Configuration
CONF_CODE = "code"
CONF_PIN = "pin"
CONF_TOKEN = "token"
CONF_USER_ID = "user_id"
CONF_USER_LABEL = "user_label"

# Default values
DEFAULT_SCAN_INTERVAL = 30  # seconds

# API Headers
HEADER_TOKEN = "X-Token"
HEADER_APP_VERSION = "X-App-Version"
HEADER_REQUESTED_WITH = "X-Requested-With"
APP_VERSION = "1.7.6"
REQUESTED_WITH = "ch.eeproperty.vesta"

# Machine states
STATE_DEACTIVATED = "DEACTIVATED"  # Available
STATE_ACTIVATED = "ACTIVATED"  # Occupied/Running
STATE_ERROR = "ERROR"  # Unavailable

# Machine types
TYPE_WASHER = "WASHER"
TYPE_DRYER = "DRYER"

# Attributes
ATTR_MACHINE_TYPE = "machine_type"
ATTR_MACHINE_NUMBER = "machine_number"
ATTR_ROOM = "room"
ATTR_PRICING = "pricing"
ATTR_COST_PER_CYCLE = "cost_per_cycle"
ATTR_BALANCE = "balance"
