"""
Evidence-based MikroTik topology inference.

This module observes an already-validated RouterDiscoverySnapshot and
infers WAN/client topology from configuration evidence.

It MUST NOT:
- assume ether1 is WAN
- assume ether2/ether3/etc. are LAN
- mutate RouterOS
- silently select a topology when evidence is ambiguous
"""

from __future__ import annotations

import ipaddress
from typing import List

from pydantic import BaseModel, ConfigDict, Field

from backend.services.provisioning_v2.router_discovery_models import (
    RouterDiscoverySnapshot,
)


class TopologyInferenceError(ValueError):
    """Raised when topology cannot be inferred safely."""


class StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )


class TopologyEvidence(StrictModel):
    interface: str
    score: int
    reasons: List[str] = Field(default_factory=list)


class TopologyInferenceResult(StrictModel):
    status: str
    wan_interface: str | None = None
    client_interfaces: List[str] = Field(default_factory=list)
    client_bridge_interfaces: List[str] = Field(default_factory=list)
    confidence: str = "LOW"
    evidence: List[TopologyEvidence] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


def _interface_names(snapshot: RouterDiscoverySnapshot) -> list[str]:
    return [
        interface.name
        for interface in snapshot.interfaces
        if interface.name
    ]

def _physical_ethernet_interfaces(
    snapshot: RouterDiscoverySnapshot,
) -> list[str]:
    """
    Return discovered physical Ethernet interfaces.

    Discovery-time link state is intentionally ignored. A disconnected
    physical port is still a valid client candidate for a fresh router.
    """
    interfaces: list[str] = []

    for interface in snapshot.interfaces:
        if not interface.name or interface.disabled:
            continue

        interface_type = (interface.type or "").strip().lower()

        if interface_type not in {
            "ethernet",
            "ether",
            "physical_ethernet",
        }:
            continue

        if interface.name not in interfaces:
            interfaces.append(interface.name)

    return interfaces

def _bridge_members(snapshot: RouterDiscoverySnapshot) -> set[str]:
    return {
        port.interface_name
        for port in snapshot.bridge_ports
        if port.interface_name
    }


def _bridge_names(snapshot: RouterDiscoverySnapshot) -> set[str]:
    return {
        bridge.name
        for bridge in snapshot.bridges
        if bridge.name
    }


def _hotspot_interfaces(snapshot: RouterDiscoverySnapshot) -> set[str]:
    return {
        hotspot.interface
        for hotspot in snapshot.hotspots
        if hotspot.interface
    }


def _dhcp_server_interfaces(snapshot: RouterDiscoverySnapshot) -> set[str]:
    return {
        server.interface
        for server in snapshot.dhcp_servers
        if server.interface
    }


def _dhcp_client_interfaces(snapshot: RouterDiscoverySnapshot) -> set[str]:
    return {
        client.interface
        for client in snapshot.dhcp_clients
        if client.interface
    }


def _default_route_interfaces(snapshot: RouterDiscoverySnapshot) -> set[str]:
    interfaces: set[str] = set()
    known_interfaces = set(_interface_names(snapshot))

    for route in snapshot.routes:
        if route.destination != "0.0.0.0/0":
            continue

        # An explicitly discovered route interface is direct evidence.
        if route.interface:
            interfaces.add(route.interface)

        gateway = (route.gateway or "").strip()
        if not gateway:
            continue

        # RouterOS can encode an interface in the gateway as IP%interface.
        # Trust the suffix only when that interface was actually discovered.
        if "%" in gateway:
            gateway_interface = gateway.rsplit("%", 1)[1].strip()
            if gateway_interface in known_interfaces:
                interfaces.add(gateway_interface)
            continue

        # When the route has no interface, use a gateway address that falls
        # inside a discovered interface subnet as grounded interface evidence.
        # Do not override an explicitly provided route interface.
        if route.interface:
            continue

        try:
            gateway_address = ipaddress.ip_address(gateway)
        except ValueError:
            continue

        for address in snapshot.addresses:
            try:
                discovered_address = ipaddress.ip_interface(address.address)
            except ValueError:
                continue

            if (
                discovered_address.version == gateway_address.version
                and gateway_address in discovered_address.network
            ):
                interfaces.add(address.interface)

    return interfaces


def _score_interface(
    interface_name: str,
    *,
    snapshot: RouterDiscoverySnapshot,
    bridge_members: set[str],
    bridge_names: set[str],
    hotspot_interfaces: set[str],
    dhcp_server_interfaces: set[str],
    dhcp_client_interfaces: set[str],
    default_route_interfaces: set[str],
) -> TopologyEvidence:
    score = 0
    reasons: list[str] = []

    if interface_name in dhcp_client_interfaces:
        score += 50
        reasons.append("DHCP client is bound to this interface")

    if interface_name in default_route_interfaces:
        score += 50
        reasons.append("default route uses this interface")

    if interface_name in bridge_members:
        score -= 40
        reasons.append("interface is a bridge member")

    if interface_name in hotspot_interfaces:
        score -= 50
        reasons.append("HotSpot is attached to this interface")

    if interface_name in dhcp_server_interfaces:
        score -= 50
        reasons.append("DHCP server is attached to this interface")

    if interface_name in bridge_names:
        score -= 30
        reasons.append("interface is itself a bridge")

    return TopologyEvidence(
        interface=interface_name,
        score=score,
        reasons=reasons,
    )


def infer_topology(
    snapshot: RouterDiscoverySnapshot,
) -> TopologyInferenceResult:
    """
    Infer topology from discovery evidence.

    High-confidence WAN requires multiple independent signals.
    No port-number ordering is used.
    """

    names = _interface_names(snapshot)

    if not names:
        return TopologyInferenceResult(
            status="AMBIGUOUS",
            confidence="LOW",
            warnings=["Discovery contains no interfaces"],
        )

    bridge_members = _bridge_members(snapshot)
    bridge_names = _bridge_names(snapshot)
    hotspot_interfaces = _hotspot_interfaces(snapshot)
    dhcp_server_interfaces = _dhcp_server_interfaces(snapshot)
    dhcp_client_interfaces = _dhcp_client_interfaces(snapshot)
    default_route_interfaces = _default_route_interfaces(snapshot)

    evidence = [
        _score_interface(
            name,
            snapshot=snapshot,
            bridge_members=bridge_members,
            bridge_names=bridge_names,
            hotspot_interfaces=hotspot_interfaces,
            dhcp_server_interfaces=dhcp_server_interfaces,
            dhcp_client_interfaces=dhcp_client_interfaces,
            default_route_interfaces=default_route_interfaces,
        )
        for name in names
    ]

    ranked = sorted(
        evidence,
        key=lambda item: item.score,
        reverse=True,
    )

    positive_wan = [
        item
        for item in ranked
        if item.score >= 50
    ]
    strong_wan_candidates = sorted(
        dhcp_client_interfaces & default_route_interfaces
    )

    if len(strong_wan_candidates) > 1:
        return TopologyInferenceResult(
            status="AMBIGUOUS",
            confidence="LOW",
            evidence=evidence,
            warnings=[
                "Multiple interfaces have both DHCP-client and "
                "default-route WAN evidence: "
                + ", ".join(strong_wan_candidates)
            ],
        )

    if not positive_wan:
        return TopologyInferenceResult(
            status="AMBIGUOUS",
            confidence="LOW",
            evidence=evidence,
            warnings=[
                "No interface has sufficient independent WAN evidence"
            ],
        )

    top = positive_wan[0]

    tied = [
        item
        for item in positive_wan
        if item.score == top.score
    ]

    if len(tied) > 1:
        return TopologyInferenceResult(
            status="AMBIGUOUS",
            confidence="LOW",
            evidence=evidence,
            warnings=[
                "Multiple interfaces have equal WAN evidence: "
                + ", ".join(item.interface for item in tied)
            ],
        )

    if top.score >= 100:
        confidence = "HIGH"
    elif top.score >= 50:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    # Bridges carrying HotSpot/DHCP services are client-side candidates.
    client_bridges = sorted(
        (
            bridge
            for bridge in bridge_names
            if bridge in hotspot_interfaces
            or bridge in dhcp_server_interfaces
        )
    )

    # A router with multiple service-bearing bridges does not have a
    # uniquely identifiable CAIWAVE client topology.
    if len(client_bridges) > 1:
        return TopologyInferenceResult(
            status="AMBIGUOUS",
            confidence="LOW",
            evidence=evidence,
            warnings=[
                "Multiple service-bearing client bridges were discovered: "
                + ", ".join(client_bridges)
            ],
        )

    # Physical bridge members are client-facing candidates, but only when
    # they belong to the identified service-bearing client bridge.
    client_members: list[str] = []

    if client_bridges:
        client_bridge = client_bridges[0]
        client_members = sorted(
            port.interface_name
            for port in snapshot.bridge_ports
            if port.bridge_name == client_bridge
            and port.interface_name
            and port.interface_name != top.interface
        )

    else:
        # Fresh-router topology:
        #
        # No existing service-bearing client bridge was discovered.
        # Enabled physical Ethernet ports are valid client candidates
        # for a fresh router, regardless of current link state.
        physical_ethernet = _physical_ethernet_interfaces(snapshot)

        client_candidates = [
            interface.name
            for interface in snapshot.interfaces
            if (
                interface.name
                and interface.name in physical_ethernet
                and interface.name != top.interface
                and not interface.disabled
            )
        ]

        client_candidates = list(dict.fromkeys(client_candidates))


        if not client_candidates:
            return TopologyInferenceResult(
                status="AMBIGUOUS",
                wan_interface=top.interface,
                client_interfaces=[],
                client_bridge_interfaces=[],
                confidence="LOW",
                evidence=evidence,
                warnings=[
                    "WAN was identified, but no active physical Ethernet "
                    "client interface was discovered. Connect the intended "
                    "client-side interface and run discovery again."
                ],
            )

        return TopologyInferenceResult(
            status="INFERRED",
            wan_interface=top.interface,
            client_interfaces=client_candidates,
            client_bridge_interfaces=[],
            confidence=confidence,
            evidence=evidence,
            warnings=[
                "No existing service-bearing client bridge was discovered; "
                "client interfaces were derived from active discovered "
                "physical Ethernet links excluding the verified WAN. "
                "A new client bridge may be created."
            ],
        )

    warnings: list[str] = []

    if not client_members:
        warnings.append(
            "Client bridge was identified but no physical bridge members "
            "were discovered"
        )

    return TopologyInferenceResult(
        status="INFERRED",
        wan_interface=top.interface,
        client_interfaces=client_members,
        client_bridge_interfaces=client_bridges,
        confidence=confidence,
        evidence=evidence,
        warnings=warnings,
    )
