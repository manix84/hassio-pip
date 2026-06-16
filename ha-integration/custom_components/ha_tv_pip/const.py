"""Constants for the HA TV PiP integration."""

DOMAIN = "ha_tv_pip"

BUTTON_DOMAIN = "button"
CONF_API_VERSION = "api_version"
CONF_DEVICE_ID = "device_id"
CONF_HOST = "host"
CONF_NAME = "name"
CONF_PAIRING = "pairing"
CONF_PORT = "port"
CONF_TOKEN = "token"
CONF_VERSION = "version"
SENSOR_DOMAIN = "sensor"
BINARY_SENSOR_DOMAIN = "binary_sensor"

DEFAULT_PORT = 8765
DISCOVERY_SERVICE_TYPE = "_ha-tv-pip._tcp.local."
SERVICE_SHOW_CAMERA = "show_camera"
SERVICE_SHOW_SNAPSHOT = "show_snapshot"
PLATFORMS = [SENSOR_DOMAIN, BINARY_SENSOR_DOMAIN, BUTTON_DOMAIN]
