"""
Production input validation for CAIWAVE Provisioning Engine v2.

This module prevents production RouterOS artifacts from being generated with
development placeholders, silent interface assumptions, or incomplete router
records.
"""

from __future__ import annotations

from dataclasses import dataclass
from ipaddress import ip_address, ip_network
from typing import Any
from urllib.parse import urlparse


class ProductionProvisioningInputError(ValueError):
    """Raised when production provisioning data is incomplete or unsafe."""


FORBIDDEN_PLACEHOLDERS = {
    "router-1",
    "hotspot-1",
    "owner-1",
    "wifi.caiwave.com",
    "router-radius-secret:router-1",
    "testing123",
}


@dataclass(frozen=True)
class ValidatedProductionRouterInput:
    router_id: str
    router_name: str
    owner_id: str
    hotspot_id: str
    nas_identifier: str
    wan_interface: str
    lan_interfaces: tuple[str, ...]
    create_bridge: bool
    bridge_name: str
    hotspot_cidr: str
    hotspot_gateway: str
    dhcp_pool: str
    captive_dns_name: str
    radius_host: str
    radius_secret: str
    portal_public_url: str
    api_public_url: str
    heartbeat_url: str


def _required_string(data: dict[str, Any], field: str) -> str:
    value = data.get(field)

    if value is None:
        raise ProductionProvisioningInputError(
            f"{field} is required for production provisioning"
        )

    value = str(value).strip()

    if not value:
        raise ProductionProvisioningInputError(
            f"{field} cannot be blank"
        )

    if value in FORBIDDEN_PLACEHOLDERS:
        raise ProductionProvisioningInputError(
            f"{field} contains a forbidden development placeholder"
        )

    return value


def _validate_url(value: str, field: str) -> str:
    parsed = urlparse(value)

    if parsed.scheme != "https":
        raise ProductionProvisioningInputError(
            f"{field} must use HTTPS"
        )

    if not parsed.netloc:
        raise ProductionProvisioningInputError(
            f"{field} must include a hostname"
        )

    return value.rstrip("/")


def _validate_radius_host(value: str) -> str:
    try:
        ip_address(value)
        return value
    except ValueError:
        pass

    if "." not in value or " " in value:
        raise ProductionProvisioningInputError(
            "radius_host must be a valid IP address or hostname"
        )

    return value


def _validate_interfaces(
    wan_interface: str,
    lan_interfaces: Any,
) -> tuple[str, ...]:
    if not isinstance(lan_interfaces, (list, tuple)):
        raise ProductionProvisioningInputError(
            "lan_interfaces must be a non-empty list"
        )

    cleaned = tuple(
        str(interface).strip()
        for interface in lan_interfaces
        if str(interface).strip()
    )

    if not cleaned:
        raise ProductionProvisioningInputError(
            "lan_interfaces must contain at least one interface"
        )

    if len(set(cleaned)) != len(cleaned):
        raise ProductionProvisioningInputError(
            "lan_interfaces cannot contain duplicates"
        )

    if wan_interface in cleaned:
        raise ProductionProvisioningInputError(
            "WAN interface cannot also be a LAN interface"
        )

    return cleaned


def _validate_network(cidr: str, gateway: str) -> None:
    try:
        network = ip_network(cidr, strict=False)
        gateway_ip = ip_address(gateway)
    except ValueError as exc:
        raise ProductionProvisioningInputError(
            "hotspot_cidr and hotspot_gateway must be valid IP values"
        ) from exc

    if gateway_ip not in network:
        raise ProductionProvisioningInputError(
            "hotspot_gateway must belong to hotspot_cidr"
        )


def validate_production_router_input(
    router: dict[str, Any],
) -> ValidatedProductionRouterInput:
    router_id = _required_string(router, "id")
    router_name = _required_string(router, "name")
    owner_id = _required_string(router, "owner_id")
    hotspot_id = _required_string(router, "hotspot_id")
    nas_identifier = _required_string(router, "nas_identifier")

    wan_interface = _required_string(router, "wan_interface")
    lan_interfaces = _validate_interfaces(
        wan_interface,
        router.get("lan_interfaces"),
    )

    bridge_name = _required_string(router, "bridge_name")
    hotspot_cidr = _required_string(router, "hotspot_cidr")
    hotspot_gateway = _required_string(router, "hotspot_gateway")
    dhcp_pool = _required_string(router, "dhcp_pool")

    captive_dns_name = _required_string(router, "dns_name")
    if captive_dns_name != "login.caiwave.local":
        raise ProductionProvisioningInputError(
            "dns_name must be login.caiwave.local"
        )

    radius_host = _validate_radius_host(
        _required_string(router, "radius_host")
    )
    radius_secret = _required_string(router, "radius_secret")

    portal_public_url = _validate_url(
        _required_string(router, "portal_public_url"),
        "portal_public_url",
    )
    api_public_url = _validate_url(
        _required_string(router, "api_public_url"),
        "api_public_url",
    )
    heartbeat_url = _validate_url(
        _required_string(router, "heartbeat_url"),
        "heartbeat_url",
    )

    _validate_network(hotspot_cidr, hotspot_gateway)

    return ValidatedProductionRouterInput(
        router_id=router_id,
        router_name=router_name,
        owner_id=owner_id,
        hotspot_id=hotspot_id,
        nas_identifier=nas_identifier,
        wan_interface=wan_interface,
        lan_interfaces=lan_interfaces,
        create_bridge=bool(router.get("create_bridge", True)),
        bridge_name=bridge_name,
        hotspot_cidr=hotspot_cidr,
        hotspot_gateway=hotspot_gateway,
        dhcp_pool=dhcp_pool,
        captive_dns_name=captive_dns_name,
        radius_host=radius_host,
        radius_secret=radius_secret,
        portal_public_url=portal_public_url,
        api_public_url=api_public_url,
        heartbeat_url=heartbeat_url,
    )


def build_persisted_production_router_record(
    router_record: dict[str, Any],
    *,
    radius_host: str,
    portal_public_url: str,
    api_public_url: str,
    heartbeat_url: str,
) -> dict[str, Any]:
    """
    Complete and validate the normalized router snapshot that is both
    persisted to MongoDB and supplied to Provisioning Engine v2.
    """

    hotspot_network = _required_string(
        router_record,
        "hotspot_network",
    )

    completed = {
        **router_record,
        "hotspot_cidr": hotspot_network,
        "dns_name": "login.caiwave.local",
        "radius_host": radius_host,
        "portal_public_url": portal_public_url,
        "api_public_url": api_public_url,
        "heartbeat_url": heartbeat_url,
    }

    validate_production_router_input(completed)

    return completed
