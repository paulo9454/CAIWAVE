import pytest

from backend.services.provisioning_v2.routeros_interface_renderer import (
    RouterOSInterfaceRendererError,
    render_interface_section,
)
from backend.services.provisioning_v2.routeros_renderer_contracts import (
    RenderStatus,
    RouterOSSectionName,
)
from backend.tests.test_routeros_firewall_renderer import build_bundle


def test_renders_wan_dhcp_client():
    section = render_interface_section(build_bundle())

    assert section.name == RouterOSSectionName.INTERFACES
    assert section.status == RenderStatus.RENDERED
    assert section.checksum

    assert "# CAIWAVE Interfaces" in section.content
    assert "# WAN interface: ether1" in section.content

    assert (
        '/ip dhcp-client remove '
        '[find where interface="ether1"]'
    ) in section.content

    assert "/ip dhcp-client add" in section.content
    assert 'interface="ether1"' in section.content
    assert "add-default-route=yes" in section.content
    assert 'default-route-distance="1"' in section.content
    assert "use-peer-dns=yes" in section.content
    assert "use-peer-ntp=yes" in section.content
    assert "disabled=no" in section.content


def test_uses_planned_upstream_interface_not_hardcoded():
    bundle = build_bundle().model_copy(
        update={
            "topology": build_bundle().topology.model_copy(
                update={
                    "upstream_interface": "sfp1",
                }
            ),
            "firewall": build_bundle().firewall.model_copy(
                update={
                    "wan_interface": "sfp1",
                }
            ),
        }
    )

    section = render_interface_section(bundle)

    assert 'interface="sfp1"' in section.content
    assert 'interface="ether1"' not in section.content


def test_rejects_missing_upstream_interface():
    bundle = build_bundle().model_copy(
        update={
            "topology": build_bundle().topology.model_copy(
                update={
                    "upstream_interface": "",
                }
            )
        }
    )

    with pytest.raises(
        RouterOSInterfaceRendererError,
        match="upstream interface is required",
    ):
        render_interface_section(bundle)
