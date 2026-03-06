from custom_components.govee_h617e.ble.protocol import (
    brightness_packet,
    parse_hex_packet,
    power_packet,
    rgb_packet,
)


def test_power_packet_has_20_bytes() -> None:
    payload = power_packet(True)
    assert len(payload) == 20
    assert payload[0] == 0x33


def test_brightness_packet_scaling() -> None:
    payload = brightness_packet(255)
    assert payload[2] == 0xFE


def test_rgb_packet_prefix() -> None:
    payload = rgb_packet(1, 2, 3)
    assert payload[1] == 0x05


def test_parse_hex_packet_length_validation() -> None:
    try:
        parse_hex_packet("AA")
        assert False
    except ValueError:
        assert True
