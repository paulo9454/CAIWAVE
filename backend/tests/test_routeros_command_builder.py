import pytest

from backend.services.provisioning_v2.routeros_command_builder import (
    RouterOSCommandBuilderError,
    build_command,
    build_comment,
    build_section,
    build_set_arg,
    join_script,
    quote_routeros_value,
)


def test_quotes_plain_value():
    assert quote_routeros_value("bridge-hotspot") == '"bridge-hotspot"'


def test_escapes_quotes_and_backslashes():
    assert quote_routeros_value('a"b\\c') == '"a\\"b\\\\c"'


def test_booleans_are_routeros_yes_no():
    assert quote_routeros_value(True) == "yes"
    assert quote_routeros_value(False) == "no"


def test_rejects_newlines():
    with pytest.raises(RouterOSCommandBuilderError):
        quote_routeros_value("bad\nvalue")


def test_builds_set_arg():
    assert build_set_arg("name", "bridge-hotspot") == 'name="bridge-hotspot"'


def test_rejects_unsafe_arg_key():
    with pytest.raises(RouterOSCommandBuilderError):
        build_set_arg("bad key", "value")


def test_builds_command_deterministically_sorted_args():
    command = build_command(
        "/interface bridge",
        "add",
        {"comment": "CAIWAVE", "name": "bridge-hotspot"},
    )

    assert command == '/interface bridge add comment="CAIWAVE" name="bridge-hotspot"'


def test_skips_none_arguments():
    command = build_command(
        "/interface bridge",
        "add",
        {"name": "bridge-hotspot", "disabled": None},
    )

    assert command == '/interface bridge add name="bridge-hotspot"'


def test_rejects_unsafe_path():
    with pytest.raises(RouterOSCommandBuilderError):
        build_command("/interface; reboot", "add", {})


def test_build_comment():
    assert build_comment("CAIWAVE") == "# CAIWAVE"


def test_build_section():
    section = build_section(
        "Bridge",
        [build_command("/interface bridge", "add", {"name": "bridge-hotspot"})],
    )

    assert "# Bridge" in section
    assert '/interface bridge add name="bridge-hotspot"' in section


def test_join_script_trailing_newline():
    script = join_script([
        build_section("One", ["cmd-one"]),
        build_section("Two", ["cmd-two"]),
    ])

    assert script.endswith("\n")
    assert "cmd-one" in script
    assert "cmd-two" in script
