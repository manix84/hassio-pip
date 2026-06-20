"""Constants for the HA TV PiP integration."""

DOMAIN = "ha_tv_pip"

BUTTON_DOMAIN = "button"
CONF_API_VERSION = "api_version"
CONF_DEVICE_ID = "device_id"
CONF_HOST = "host"
CONF_NAME = "name"
CONF_PAIRING = "pairing"
CONF_PORT = "port"
CONF_DEFAULT_DURATION_SECONDS = "default_duration_seconds"
CONF_DEFAULT_HEIGHT = "default_height"
CONF_DEFAULT_POSITION = "default_position"
CONF_DEFAULT_SNAPSHOT_FALLBACK = "default_snapshot_fallback"
CONF_DEFAULT_STREAM_TYPE = "default_stream_type"
CONF_DEFAULT_WIDTH = "default_width"
CONF_CAMERA_DEFAULTS = "camera_defaults"
CONF_REMOTE_ACCESS_TOKEN = "remote_access_token"
CONF_REMOTE_HOME_ASSISTANT_URL = "remote_home_assistant_url"
CONF_PREFER_REMOTE_TRANSPORT = "prefer_remote_transport"
CONF_SHOW_ADVANCED_OPTIONS = "show_advanced_options"
CONF_TOKEN = "token"
CONF_VERSION = "version"
SENSOR_DOMAIN = "sensor"
BINARY_SENSOR_DOMAIN = "binary_sensor"
SWITCH_DOMAIN = "switch"

DEFAULT_PORT = 8765
DISCOVERY_SERVICE_TYPE = "_ha-tv-pip._tcp.local."
NOTIFICATION_POSITIONS = ("top_right", "top_left", "bottom_right", "bottom_left")
SERVICE_SHOW_CAMERA = "show_camera"
SERVICE_SHOW_NOTIFICATION = "show_notification"
SERVICE_SHOW_SNAPSHOT = "show_snapshot"
SERVICE_CALIBRATE_CAMERA = "calibrate_camera"
SERVICE_CLEAR_CAMERA_DEFAULTS = "clear_camera_defaults"
SERVICE_SET_CAMERA_DEFAULTS = "set_camera_defaults"
SERVICE_TEST_CAMERA_STREAM = "test_camera_stream"
STREAM_TYPE_AUTO = "auto"
STREAM_TYPE_HLS = "hls"
STREAM_TYPE_MJPEG = "mjpeg"
STREAM_TYPE_MJPEG_FIRST = "mjpeg_first"
STREAM_TYPE_NOTIFICATION = "notification"
STREAM_TYPE_SNAPSHOT = "snapshot"
STREAM_TYPES = (
    STREAM_TYPE_AUTO,
    STREAM_TYPE_HLS,
    STREAM_TYPE_MJPEG,
    STREAM_TYPE_MJPEG_FIRST,
    STREAM_TYPE_SNAPSHOT,
)
PLATFORMS = [SENSOR_DOMAIN, BINARY_SENSOR_DOMAIN, BUTTON_DOMAIN, SWITCH_DOMAIN]
