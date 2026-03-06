"""BLE packet helpers for Govee devices."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SegmentCommandSupport:
    """Tracks confidence of segment command support."""

    supported: bool
    confidence_note: str


def build_packet(command: int, payload: list[int]) -> bytes:
    """Build a 20-byte Govee packet with XOR checksum."""
    data = [0x33, command] + payload
    data += [0x00] * (19 - len(data))
    checksum = 0
    for byte in data:
        checksum ^= byte
    data.append(checksum)
    return bytes(data)


def power_packet(on: bool) -> bytes:
    return build_packet(0x01, [0x01 if on else 0x00])


def brightness_packet(brightness: int) -> bytes:
    """Map HA brightness (0..255) to govee scale (0..254)."""
    scaled = max(0, min(254, round((brightness / 255) * 254)))
    return build_packet(0x04, [scaled])


def rgb_packet(red: int, green: int, blue: int) -> bytes:
    return build_packet(0x05, [0x15, 0x01, red, green, blue, 0, 0, 0, 0, 0, 0xFF, 0x7F])


def scene_packet(scene_id: int) -> bytes:
    return build_packet(0x05, [0x04, scene_id])


def experimental_segment_packet(segment_index: int, red: int, green: int, blue: int) -> bytes:
    """Best-effort segment packet.

    NOTE: This packet format is intentionally marked experimental and must not be
    treated as protocol-guaranteed for all firmware revisions.
    """
    return build_packet(0x05, [0x15, segment_index & 0xFF, red, green, blue])


def parse_hex_packet(packet_hex: str) -> bytes:
    cleaned = packet_hex.strip().replace(" ", "")
    if len(cleaned) != 40:
        raise ValueError("Govee packet must be exactly 20 bytes (40 hex chars)")
    return bytes.fromhex(cleaned)
