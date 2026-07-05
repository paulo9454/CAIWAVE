"""
Resource Registry Builder for CAIWAVE Provisioning Engine v2.

Safety:
- no database access
- no RouterOS generation
- no route wiring
- no legacy provisioning changes

This builder converts a ProvisioningSnapshot into expected CRS-managed
ResourceRegistryEntry objects.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Dict, List

from backend.schemas.provisioning_v2 import (
    DriftStatus,
    ProvisioningSnapshot,
    ResourceLifecycleState,
    ResourceOwner,
    ResourceRegistryEntry,
    SecurityClassification,
)


class ResourceRegistryBuildError(ValueError):
    """Raised when the resource registry cannot be safely built."""


def _module_versions(snapshot: ProvisioningSnapshot) -> Dict[str, str]:
    return dict(snapshot.versioning.module_versions or {})


def _version(snapshot: ProvisioningSnapshot, module: str) -> str:
    return _module_versions(snapshot).get(module, "1.0.0")


def _artifact_id(snapshot: ProvisioningSnapshot) -> str:
    return f"artifact:{snapshot.snapshot_id}"


def _resource(
    snapshot: ProvisioningSnapshot,
    *,
    key: str,
    resource_type: str,
    logical_name: str,
    physical_name: str | None,
    module: str,
    expected_state: dict,
    dependencies: list[str] | None = None,
    security_classification: SecurityClassification = SecurityClassification.INTERNAL,
) -> ResourceRegistryEntry:
    resource_id = f"{key}:{snapshot.router_id}"

    return ResourceRegistryEntry(
        resource_id=resource_id,
        router_id=snapshot.router_id,
        hotspot_id=snapshot.hotspot_id,
        artifact_id=_artifact_id(snapshot),
        snapshot_id=snapshot.snapshot_id,
        resource_type=resource_type,
        logical_name=logical_name,
        physical_name=physical_name,
        owner=ResourceOwner.CAIWAVE,
        module=module,
        module_version=_version(snapshot, module),
        expected_state=deepcopy(expected_state),
        observed_state={},
        lifecycle_state=ResourceLifecycleState.PLANNED,
        validation_evidence=[],
        security_classification=security_classification,
        dependencies=dependencies or [],
        rollback_metadata={"strategy": "module_defined"},
        drift_status=DriftStatus.UNKNOWN,
    )


def build_resource_registry(
    snapshot: ProvisioningSnapshot,
) -> List[ResourceRegistryEntry]:
    """
    Build deterministic expected resource registry entries from a snapshot.

    This does not generate RouterOS and does not persist anything.
    """

    if not snapshot.identity.router_id:
        raise ResourceRegistryBuildError("Snapshot identity.router_id is required")
    if not snapshot.topology.wan_interface:
        raise ResourceRegistryBuildError("Snapshot topology.wan_interface is required")
    if not snapshot.topology.lan_interfaces:
        raise ResourceRegistryBuildError("Snapshot topology.lan_interfaces is required")
    if not snapshot.networking.hotspot_gateway:
        raise ResourceRegistryBuildError("Snapshot networking.hotspot_gateway is required")
    if not snapshot.radius.radius_host:
        raise ResourceRegistryBuildError("Snapshot radius.radius_host is required")

    bridge_id = f"bridge:{snapshot.router_id}"
    ip_id = f"ip-address:{snapshot.router_id}"
    dhcp_pool_id = f"dhcp-pool:{snapshot.router_id}"
    dhcp_server_id = f"dhcp-server:{snapshot.router_id}"
    dns_id = f"dns:{snapshot.router_id}"
    radius_id = f"radius:{snapshot.router_id}"
    hotspot_profile_id = f"hotspot-profile:{snapshot.router_id}"
    hotspot_server_id = f"hotspot-server:{snapshot.router_id}"
    walled_garden_id = f"walled-garden:{snapshot.router_id}"
    portal_id = f"portal-redirect:{snapshot.router_id}"

    resources: List[ResourceRegistryEntry] = []

    resources.append(
        _resource(
            snapshot,
            key="identity",
            resource_type="system_identity",
            logical_name="Router identity",
            physical_name=snapshot.identity.router_name,
            module="identity",
            expected_state={
                "router_name": snapshot.identity.router_name,
                "nas_identifier": snapshot.identity.nas_identifier,
            },
        )
    )

    resources.append(
        _resource(
            snapshot,
            key="bridge",
            resource_type="bridge",
            logical_name="Hotspot client bridge",
            physical_name=snapshot.topology.bridge_name,
            module="bridge",
            expected_state={
                "bridge_name": snapshot.topology.bridge_name,
                "create_bridge": snapshot.topology.create_bridge,
                "client_interface": snapshot.topology.client_interface,
            },
        )
    )

    for interface_name in snapshot.topology.lan_interfaces:
        resources.append(
            _resource(
                snapshot,
                key=f"bridge-port-{interface_name}",
                resource_type="bridge_port",
                logical_name=f"Bridge port {interface_name}",
                physical_name=interface_name,
                module="bridge",
                expected_state={
                    "interface": interface_name,
                    "bridge": snapshot.topology.bridge_name,
                },
                dependencies=[bridge_id],
            )
        )

    resources.append(
        _resource(
            snapshot,
            key="ip-address",
            resource_type="ip_address",
            logical_name="Hotspot gateway IP address",
            physical_name=snapshot.networking.hotspot_gateway,
            module="ip_addressing",
            expected_state={
                "address": snapshot.networking.hotspot_gateway,
                "cidr": snapshot.networking.hotspot_cidr,
                "interface": snapshot.topology.client_interface,
            },
            dependencies=[bridge_id],
        )
    )

    resources.append(
        _resource(
            snapshot,
            key="dhcp-pool",
            resource_type="ip_pool",
            logical_name="Hotspot DHCP pool",
            physical_name="caiwave-pool-hotspot",
            module="dhcp",
            expected_state={
                "start": snapshot.networking.dhcp_pool_start,
                "end": snapshot.networking.dhcp_pool_end,
            },
            dependencies=[ip_id],
        )
    )

    resources.append(
        _resource(
            snapshot,
            key="dhcp-server",
            resource_type="dhcp_server",
            logical_name="Hotspot DHCP server",
            physical_name="caiwave-dhcp-hotspot",
            module="dhcp",
            expected_state={
                "interface": snapshot.topology.client_interface,
                "pool": "caiwave-pool-hotspot",
            },
            dependencies=[bridge_id, ip_id, dhcp_pool_id],
        )
    )

    resources.append(
        _resource(
            snapshot,
            key="dhcp-network",
            resource_type="dhcp_network",
            logical_name="Hotspot DHCP network",
            physical_name=snapshot.networking.hotspot_cidr,
            module="dhcp",
            expected_state={
                "network": snapshot.networking.hotspot_cidr,
                "gateway": snapshot.networking.hotspot_gateway,
                "dns_servers": snapshot.networking.client_dns_servers,
            },
            dependencies=[ip_id, dns_id],
        )
    )

    resources.append(
        _resource(
            snapshot,
            key="dns",
            resource_type="dns",
            logical_name="Router DNS policy",
            physical_name=None,
            module="dns",
            expected_state={
                "client_dns_servers": snapshot.networking.client_dns_servers,
                "router_dns_upstreams": snapshot.networking.router_dns_upstreams,
                "hotspot_dns_name": snapshot.hotspot.dns_name,
            },
        )
    )

    resources.append(
        _resource(
            snapshot,
            key="firewall-filter",
            resource_type="firewall_filter",
            logical_name="CAIWAVE firewall policy",
            physical_name="caiwave-firewall-policy",
            module="firewall",
            expected_state={"policy": "managed-minimal"},
            dependencies=[dns_id, radius_id],
        )
    )

    resources.append(
        _resource(
            snapshot,
            key="nat",
            resource_type="firewall_nat",
            logical_name="Hotspot client NAT",
            physical_name="caiwave-nat-hotspot",
            module="nat",
            expected_state={
                "wan_interface": snapshot.topology.wan_interface,
                "source_cidr": snapshot.networking.hotspot_cidr,
            },
            dependencies=[ip_id],
        )
    )

    resources.append(
        _resource(
            snapshot,
            key="radius",
            resource_type="radius_server_entry",
            logical_name="RADIUS server entry",
            physical_name=snapshot.radius.radius_host,
            module="radius",
            expected_state={
                "host": snapshot.radius.radius_host,
                "auth_port": snapshot.radius.radius_auth_port,
                "accounting_port": snapshot.radius.radius_accounting_port,
                "secret_ref": snapshot.radius.radius_secret_ref,
                "nas_identifier": snapshot.radius.nas_identifier,
            },
            dependencies=[dns_id],
            security_classification=SecurityClassification.SECRET,
        )
    )

    resources.append(
        _resource(
            snapshot,
            key="accounting",
            resource_type="accounting_configuration",
            logical_name="RADIUS accounting configuration",
            physical_name="caiwave-accounting",
            module="accounting",
            expected_state={"enabled": True, "radius_host": snapshot.radius.radius_host},
            dependencies=[radius_id],
            security_classification=SecurityClassification.CONFIDENTIAL,
        )
    )

    resources.append(
        _resource(
            snapshot,
            key="hotspot-profile",
            resource_type="hotspot_profile",
            logical_name="Hotspot profile",
            physical_name=snapshot.hotspot.profile_name,
            module="hotspot",
            expected_state={
                "profile_name": snapshot.hotspot.profile_name,
                "dns_name": snapshot.hotspot.dns_name,
                "login_methods": snapshot.hotspot.login_methods,
                "use_radius": True,
            },
            dependencies=[dns_id, radius_id],
        )
    )

    resources.append(
        _resource(
            snapshot,
            key="hotspot-server",
            resource_type="hotspot_server",
            logical_name="Hotspot server",
            physical_name=snapshot.hotspot.server_name,
            module="hotspot",
            expected_state={
                "server_name": snapshot.hotspot.server_name,
                "interface": snapshot.topology.client_interface,
                "profile": snapshot.hotspot.profile_name,
            },
            dependencies=[dhcp_server_id, dns_id, radius_id, hotspot_profile_id],
        )
    )

    resources.append(
        _resource(
            snapshot,
            key="portal-redirect",
            resource_type="portal_redirect",
            logical_name="CAIWAVE portal redirect",
            physical_name=snapshot.portal.portal_public_url,
            module="portal_redirect",
            expected_state={
                "portal_public_url": snapshot.portal.portal_public_url,
                "api_public_url": snapshot.portal.api_public_url,
                "portal_strategy": snapshot.portal.portal_strategy,
                "portal_contract_version": snapshot.portal.portal_contract_version,
            },
            dependencies=[hotspot_server_id, walled_garden_id],
        )
    )

    resources.append(
        _resource(
            snapshot,
            key="walled-garden",
            resource_type="walled_garden",
            logical_name="CAIWAVE walled garden",
            physical_name="caiwave-walled-garden",
            module="walled_garden",
            expected_state={
                "portal_public_url": snapshot.portal.portal_public_url,
                "api_public_url": snapshot.portal.api_public_url,
            },
            dependencies=[dns_id, hotspot_server_id],
        )
    )

    resources.append(
        _resource(
            snapshot,
            key="heartbeat-scheduler",
            resource_type="scheduler",
            logical_name="Heartbeat scheduler",
            physical_name="caiwave-heartbeat",
            module="heartbeat",
            expected_state={
                "heartbeat_url": snapshot.heartbeat.heartbeat_url,
                "interval_seconds": snapshot.heartbeat.heartbeat_interval_seconds,
                "token_ref": snapshot.heartbeat.heartbeat_token_ref,
            },
            dependencies=[dns_id],
            security_classification=SecurityClassification.SECRET,
        )
    )

    resources.append(
        _resource(
            snapshot,
            key="diagnostics-scheduler",
            resource_type="scheduler",
            logical_name="Diagnostics scheduler",
            physical_name="caiwave-diagnostics",
            module="diagnostics",
            expected_state={"required_checks": snapshot.diagnostics.required_checks},
            dependencies=[bridge_id, dhcp_server_id, hotspot_server_id, radius_id],
        )
    )

    resource_ids = [resource.resource_id for resource in resources]
    if len(resource_ids) != len(set(resource_ids)):
        raise ResourceRegistryBuildError("Duplicate resource IDs generated")

    return resources
