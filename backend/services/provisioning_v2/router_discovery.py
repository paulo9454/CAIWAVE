"""
Router Discovery Builder for CAIWAVE Provisioning Engine v2.

Safety:
- no database access
- no RouterOS generation
- no topology planning
- no provisioning mutation

This module validates and normalizes discovery snapshots.
"""

from __future__ import annotations

from backend.services.provisioning_v2.router_discovery_models import (
    RouterDiscoverySnapshot,
)


class RouterDiscoveryError(ValueError):
    """Raised when discovery data is invalid."""


def build_router_discovery_snapshot(
    snapshot: RouterDiscoverySnapshot,
) -> RouterDiscoverySnapshot:
    interface_names = [
        item.name
        for item in snapshot.interfaces
    ]

    if len(interface_names) != len(set(interface_names)):
        raise RouterDiscoveryError(
            "Duplicate discovered interface names"
        )

    bridge_names = [
        item.name
        for item in snapshot.bridges
    ]

    if len(bridge_names) != len(set(bridge_names)):
        raise RouterDiscoveryError(
            "Duplicate discovered bridge names"
        )

    vlan_names = [
        item.name
        for item in snapshot.vlans
    ]

    if len(vlan_names) != len(set(vlan_names)):
        raise RouterDiscoveryError(
            "Duplicate discovered VLAN names"
        )

    known_interfaces = set(interface_names)

    for vlan in snapshot.vlans:
        if vlan.parent_interface not in known_interfaces:
            raise RouterDiscoveryError(
                f"VLAN parent interface does not exist: "
                f"{vlan.parent_interface}"
            )

    for address in snapshot.addresses:
        if address.interface not in known_interfaces:
            raise RouterDiscoveryError(
                f"Address references unknown interface: "
                f"{address.interface}"
            )

    for port in snapshot.bridge_ports:
        if port.interface_name not in known_interfaces:
            raise RouterDiscoveryError(
                f"Bridge port references unknown interface: "
                f"{port.interface_name}"
        )

    for route in snapshot.routes:
        if route.interface and route.interface not in known_interfaces:
            raise RouterDiscoveryError(
                f"Route references unknown interface: "
                f"{route.interface}"
            )

    for dhcp_client in snapshot.dhcp_clients:
        if dhcp_client.interface not in known_interfaces:
            raise RouterDiscoveryError(
                f"DHCP client references unknown interface: "
                f"{dhcp_client.interface}"
            )

    # A RouterOS interface must not be assigned to multiple bridges.
    # Reject ambiguous membership rather than allowing unsafe provisioning.
    bridge_by_interface = {}
    for port in snapshot.bridge_ports:
        previous_bridge = bridge_by_interface.get(port.interface_name)
        if previous_bridge is not None and previous_bridge != port.bridge_name:
            raise RouterDiscoveryError(
                f"Interface {port.interface_name} is assigned to multiple "
                f"bridges: {previous_bridge}, {port.bridge_name}"
            )
        bridge_by_interface[port.interface_name] = port.bridge_name

    known_bridges = set(bridge_names)

    for port in snapshot.bridge_ports:
        if port.bridge_name not in known_bridges:
            raise RouterDiscoveryError(
                f"Bridge port references unknown bridge: "
                f"{port.bridge_name}"
            )

    for dhcp in snapshot.dhcp_servers:
        if dhcp.interface not in known_interfaces:
            raise RouterDiscoveryError(
                f"DHCP server references unknown interface: "
                f"{dhcp.interface}"
            )

    for hotspot in snapshot.hotspots:
        if hotspot.interface not in known_interfaces:
            raise RouterDiscoveryError(
                f"Hotspot references unknown interface: "
                f"{hotspot.interface}"
            )

    return snapshot
