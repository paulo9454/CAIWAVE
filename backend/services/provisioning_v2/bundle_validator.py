"""
Provisioning Bundle Validator for CAIWAVE Provisioning Engine v2.

Safety:
- no database access
- no RouterOS generation
- no route wiring
- no legacy provisioning changes

This validator performs cross-plan consistency checks before any renderer
is allowed to consume a provisioning bundle.
"""

from __future__ import annotations

from ipaddress import ip_address, ip_network
from typing import List

from pydantic import BaseModel, ConfigDict, Field

from backend.services.provisioning_v2.provisioning_bundle import ProvisioningBundle


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class BundleValidationResult(StrictModel):
    valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


def validate_provisioning_bundle(bundle: ProvisioningBundle) -> BundleValidationResult:
    errors: List[str] = []
    warnings: List[str] = list(bundle.warnings)

    try:
        network = ip_network(bundle.address.cidr, strict=False)
        gateway = ip_address(bundle.address.gateway_ip)
        pool_start = ip_address(bundle.address.dhcp_pool_start)
        pool_end = ip_address(bundle.address.dhcp_pool_end)

        if gateway not in network:
            errors.append("Gateway IP is outside address CIDR")
        if pool_start not in network or pool_end not in network:
            errors.append("DHCP pool is outside address CIDR")
        if int(pool_start) > int(pool_end):
            errors.append("DHCP pool start is after pool end")
        if int(pool_start) <= int(gateway) <= int(pool_end):
            errors.append("Gateway IP is inside DHCP pool")
    except ValueError as exc:
        errors.append(f"Invalid bundle addressing: {exc}")

    if bundle.topology.upstream_interface in bundle.topology.client_interfaces:
        errors.append("Topology WAN interface also appears as client interface")

    if bundle.address.target_interface != bundle.dhcp.target_interface:
        errors.append("Address and DHCP target interfaces differ")

    if bundle.hotspot.target_interface != bundle.address.target_interface:
        errors.append("Hotspot and address target interfaces differ")

    if bundle.hotspot.dns_name != bundle.dns.captive_dns_name:
        errors.append("Hotspot DNS name does not match DNS captive name")

    if bundle.portal.captive_dns_name != bundle.dns.captive_dns_name:
        errors.append("Portal captive DNS name does not match DNS captive name")

    if bundle.radius.enabled and not bundle.hotspot.use_radius:
        errors.append("RADIUS is enabled while Hotspot is not using RADIUS")

    if bundle.firewall.wan_interface != bundle.topology.upstream_interface:
        errors.append("Firewall WAN interface does not match topology upstream")

    if bundle.address.cidr not in bundle.firewall.client_networks:
        errors.append("Firewall client networks do not include address CIDR")

    missing_portal_hosts = [
        host for host in bundle.portal.walled_garden_hosts
        if host not in bundle.firewall.portal_hosts
    ]
    if missing_portal_hosts:
        errors.append(
            "Firewall portal hosts missing walled garden hosts: "
            + ", ".join(missing_portal_hosts)
        )

    if bundle.radius.enabled and bundle.radius.auth_host not in bundle.firewall.radius_hosts:
        errors.append("Firewall radius hosts do not include RADIUS auth host")

    if not bundle.nat.enabled:
        warnings.append("NAT is disabled in provisioning bundle")

    return BundleValidationResult(
        valid=not errors,
        errors=errors,
        warnings=warnings,
    )
