"""Constants for the Govee H617E integration."""
from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN: Final = "govee_h617e"
PLATFORMS: Final = ["light", "select", "number", "switch"]

DEFAULT_NAME: Final = "Govee H617E"
DEFAULT_POLL_INTERVAL = timedelta(seconds=30)
DEFAULT_CONNECT_TIMEOUT: Final = 12.0
DEFAULT_RETRY_COUNT: Final = 2
DEFAULT_OPTIMISTIC_MODE: Final = "auto"

CONF_POLL_INTERVAL: Final = "poll_interval"
CONF_CONNECT_TIMEOUT: Final = "connect_timeout"
CONF_RETRY_COUNT: Final = "retry_count"
CONF_EXPERIMENTAL_SEGMENTS: Final = "experimental_segments"
CONF_SEGMENT_COUNT_OVERRIDE: Final = "segment_count_override"
CONF_OPTIMISTIC_MODE: Final = "optimistic_mode"
CONF_DEBUG_LOGGING: Final = "debug_logging"
CONF_PREFERRED_ADDRESS: Final = "preferred_address"

OPTIMISTIC_AUTO: Final = "auto"
OPTIMISTIC_STRICT: Final = "strict"
OPTIMISTIC_PARTIAL: Final = "partial"

SERVICE_SET_SEGMENT_COLOR: Final = "set_segment_color"
SERVICE_APPLY_SCENE_PAYLOAD: Final = "apply_scene_payload"

ATTR_SEGMENT_INDEX: Final = "segment_index"
ATTR_RGB_COLOR: Final = "rgb_color"
ATTR_BRIGHTNESS: Final = "brightness"
ATTR_PACKET_HEX: Final = "packet_hex"
ATTR_PACKET_SEQUENCE: Final = "packet_sequence"

GOVEE_WRITE_CHAR_UUID: Final = "00010203-0405-0607-0809-0a0b0c0d2b11"
