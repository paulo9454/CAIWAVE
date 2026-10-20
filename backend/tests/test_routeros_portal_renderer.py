import pytest

from backend.services.provisioning_v2.routeros_portal_renderer import (
    _ensure_safe_portal_public_url,
    _quote_routeros_preserving_backslashes,
)


@pytest.mark.parametrize(
    "unsafe_url",
    [
        'https://portal.example/"; /system reset-configuration; #',
        'https://portal.example/"; :put "pwned"; #',
        "https://portal.example/\r\n/system reboot",
        r'https://portal.example/\\\"; /system reboot; #',
        "https://portal.example/$[ /system reset-configuration ]",
        "https://portal.example/\x01path",
    ],
)
def test_renderer_rejects_unsafe_portal_urls(unsafe_url):
    with pytest.raises(ValueError, match="unsafe"):
        _ensure_safe_portal_public_url(unsafe_url)


@pytest.mark.parametrize(
    "unsafe_contents",
    [
        'unescaped"quote',
        "unescaped$variable",
        "line\nbreak",
        "control\x01byte",
    ],
)
def test_routeros_contents_quoting_rejects_unsafe_values(unsafe_contents):
    with pytest.raises(ValueError):
        _quote_routeros_preserving_backslashes(unsafe_contents)


def test_routeros_contents_quoting_preserves_intended_hotspot_escapes():
    contents = r'<a href=\"https://portal.example/?mac=\$(mac)&ip=\$(ip)\">'

    assert _quote_routeros_preserving_backslashes(contents) == f'"{contents}"'


def test_routeros_contents_quoting_rejects_trailing_unescaped_backslash():
    with pytest.raises(ValueError, match="unescaped backslash"):
        _quote_routeros_preserving_backslashes("trailing\\")
