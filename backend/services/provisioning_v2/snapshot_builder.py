"""
Provisioning Snapshot Builder for CAIWAVE Provisioning Engine v2.

Safety:
- no database access
- no environment access
- no RouterOS generation
- no live route wiring
- no mutation of input dictionaries
- no fabricated production identifiers
- no fabricated production network configuration
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from backend.schemas.provisioning_v2 import (
    Environment,
    ProvisioningSnapshot,
    VersionManifest,
)


class ProvisioningSnapshotBuildError(ValueError):
    """Raised when a ProvisioningSnapshot cannot be safely built."""


def _required(data: Dict[str, Any], key: str, source: str) -> Any:
    value = data.get(key)

    if value is None or value == "":
        raise ProvisioningSnapshotBuildError(
            f"Missing required {source} field: {key}"
        )

    return value


def _split_dhcp_pool(pool: str) -> Tuple[str, str]:
    if not isinstance(pool, str) or "-" not in pool:
        raise ProvisioningSnapshotBuildError(
            "Invalid dhcp_pool; expected format 'start_ip-end_ip'"
        )

    start, end = [part.strip() for part in pool.split("-", 1)]

    if not start or not end:
        raise ProvisioningSnapshotBuildError(
            "Invalid dhcp_pool; both start and end IPs are required"
        )

    return start, end


def _environment(value: Optional[str]) -> Environment:
    if not value:
        return Environment.LAB

    try:
        return Environment(value)
    except ValueError as exc:
        allowed = ", ".join(item.value for item in Environment)

        raise ProvisioningSnapshotBuildError(
            f"Invalid environment '{value}'. Expected one of: {allowed}"
        ) from exc


def _optional_list(
    data: Dict[str, Any],
    key: str,
    default: list,
    source: str = "config",
) -> list:
    value = data.get(key)

    if value is None:
        return list(default)

    if not isinstance(value, list):
        raise ProvisioningSnapshotBuildError(
            f"{source} field '{key}' must be a list"
        )

    return list(value)


def _positive_int(
    data: Dict[str, Any],
    key: str,
    default: int,
    source: str = "config",
) -> int:
    value = data.get(key)

    if value is None or value == "":
        return default

    try:
        value = int(value)
    except (TypeError, ValueError) as exc:
        raise ProvisioningSnapshotBuildError(
            f"{source} field '{key}' must be an integer"
        ) from exc

    if value <= 0:
        raise ProvisioningSnapshotBuildError(
            f"{source} field '{key}' must be greater than zero"
        )

    return value


def build_provisioning_snapshot(
    router: dict,
    hotspot: dict,
    config: dict | None = None,
    created_by: str = "system",
) -> ProvisioningSnapshot:
    """
    Build an immutable ProvisioningSnapshot from plain dictionaries.

    Required production identity, topology, networking, service URLs,
    hotspot configuration, and secret references must be supplied by
    the caller.

    Compatibility defaults are retained for optional configuration
    fields so existing provisioning-v2 planning and snapshot contracts
    continue to work.
    """

    router_data = deepcopy(router or {})
    hotspot_data = deepcopy(hotspot or {})
    config_data = deepcopy(config or {})

    # ---------------------------------------------------------
    # REQUIRED IDENTITY
    # ---------------------------------------------------------

    router_id = str(
        _required(router_data, "id", "router")
    )

    router_name = str(
        _required(router_data, "name", "router")
    )

    hotspot_id = str(
        router_data.get("hotspot_id")
        or _required(hotspot_data, "id", "hotspot")
    )

    owner_id = str(
        router_data.get("owner_id")
        or _required(hotspot_data, "owner_id", "hotspot")
    )

    nas_identifier = str(
        _required(router_data, "nas_identifier", "router")
    )

    # ---------------------------------------------------------
    # REQUIRED TOPOLOGY
    # ---------------------------------------------------------

    wan_interface = str(
        _required(router_data, "wan_interface", "router")
    )

    lan_interfaces_value = router_data.get("lan_interfaces")

    if not isinstance(lan_interfaces_value, list) or not lan_interfaces_value:
        raise ProvisioningSnapshotBuildError(
            "Missing required router field: lan_interfaces"
        )

    lan_interfaces = [
        str(item).strip()
        for item in lan_interfaces_value
        if str(item).strip()
    ]

    if not lan_interfaces:
        raise ProvisioningSnapshotBuildError(
            "Missing required router field: lan_interfaces"
        )

    if wan_interface in lan_interfaces:
        raise ProvisioningSnapshotBuildError(
            "Invalid topology: wan_interface must not appear in lan_interfaces"
        )

    bridge_name = router_data.get("bridge_name")

    create_bridge = router_data.get("create_bridge", True)

    if not isinstance(create_bridge, bool):
        raise ProvisioningSnapshotBuildError(
            "Router field 'create_bridge' must be boolean"
        )

    client_interface = (
        router_data.get("effective_lan_interface")
        or router_data.get("client_interface")
        or bridge_name
        or lan_interfaces[0]
    )

    if not client_interface:
        raise ProvisioningSnapshotBuildError(
            "effective_lan_interface or client_interface is required "
            "for production provisioning"
        )

    client_interface = str(client_interface)

    deployment_mode = str(
        router_data.get("mode") or "fresh"
    )

    # ---------------------------------------------------------
    # REQUIRED NETWORKING
    # ---------------------------------------------------------

    dhcp_pool = str(
        _required(router_data, "dhcp_pool", "router")
    )

    dhcp_pool_start, dhcp_pool_end = _split_dhcp_pool(
        dhcp_pool
    )

    hotspot_cidr = str(
        _required(router_data, "hotspot_cidr", "router")
    )

    hotspot_gateway = str(
        _required(router_data, "hotspot_gateway", "router")
    )

    client_dns_servers = _optional_list(
        config_data,
        "client_dns_servers",
        [hotspot_gateway],
    )

    router_dns_upstreams = _optional_list(
        config_data,
        "router_dns_upstreams",
        [],
    )

    # ---------------------------------------------------------
    # SECRET REFERENCES
    # ---------------------------------------------------------

    radius_secret_ref = (
        router_data.get("radius_secret_ref")
        or config_data.get("radius_secret_ref")
    )

    if radius_secret_ref is None:
       radius_secret_ref = f"router-radius-secret:{router_id}"

    heartbeat_token_ref = (
        router_data.get("heartbeat_token_ref")
        or config_data.get("heartbeat_token_ref")
    )

    if heartbeat_token_ref is None:
        heartbeat_token_ref = f"router-heartbeat-token:{router_id}"

    radius_secret_ref = str(radius_secret_ref)
    heartbeat_token_ref = str(heartbeat_token_ref)

    # ---------------------------------------------------------
    # SNAPSHOT ID
    # ---------------------------------------------------------

    snapshot_id = config_data.get("snapshot_id")

    if not snapshot_id:
        snapshot_id = f"snapshot:{router_id}"

    snapshot_id = str(snapshot_id)

    # ---------------------------------------------------------
    # REQUIRED EXTERNAL SERVICES
    # ---------------------------------------------------------

    radius_host = str(
        _required(config_data, "radius_host", "config")
    )

    portal_public_url = str(
        _required(config_data, "portal_public_url", "config")
    )

    api_public_url = str(
        _required(config_data, "api_public_url", "config")
    )

    heartbeat_url = str(
        _required(config_data, "heartbeat_url", "config")
    )

    # ---------------------------------------------------------
    # HOTSPOT CONFIGURATION
    # ---------------------------------------------------------

    hotspot_server_name = str(
        router_data.get("hotspot_server_name")
        or "caiwave-hotspot"
    )

    hotspot_profile_name = str(
        router_data.get("hotspot_profile_name")
        or "caiwave-profile"
    )

    dns_name = str(
        _required(router_data, "dns_name", "router")
    )

    login_methods = _optional_list(
        config_data,
        "login_methods",
        ["http-pap"],
    )

    # ---------------------------------------------------------
    # PORTAL CONFIGURATION
    # ---------------------------------------------------------

    portal_strategy = str(
        config_data.get("portal_strategy")
        or "redirect"
    )

    portal_contract_version = str(
        config_data.get("portal_contract_version")
        or "1.0"
    )

    # ---------------------------------------------------------
    # RADIUS CONFIGURATION
    # ---------------------------------------------------------

    radius_auth_port = _positive_int(
        config_data,
        "radius_auth_port",
        1812,
    )

    radius_accounting_port = _positive_int(
        config_data,
        "radius_accounting_port",
        1813,
    )

    # ---------------------------------------------------------
    # HEARTBEAT CONFIGURATION
    # ---------------------------------------------------------

    heartbeat_interval_seconds = _positive_int(
        config_data,
        "heartbeat_interval_seconds",
        300,
    )

    # ---------------------------------------------------------
    # DIAGNOSTICS
    # ---------------------------------------------------------

    required_checks = _optional_list(
        config_data,
        "required_checks",
        ["heartbeat", "radius", "hotspot", "portal"],
    )

    validation_plan_id = config_data.get(
        "validation_plan_id"
    )

    # ---------------------------------------------------------
    # SECURITY
    # ---------------------------------------------------------

    provisioning_token_id = config_data.get(
        "provisioning_token_id"
    )

    artifact_download_token_id = config_data.get(
        "artifact_download_token_id"
    )

    callback_signing_key_ref = config_data.get(
        "callback_signing_key_ref"
    )

    secret_policy = str(
        config_data.get("secret_policy") or "redact"
    )

    # ---------------------------------------------------------
    # VERSIONING
    # ---------------------------------------------------------

    snapshot_schema_version = str(
        config_data.get("snapshot_schema_version") or "1.0"
    )

    artifact_schema_version = str(
        config_data.get("artifact_schema_version") or "1.0"
    )

    engine_version = str(
        config_data.get("engine_version") or "2.0.0"
    )

    module_versions = config_data.get(
        "module_versions"
    )

    if module_versions is None:
        module_versions = {}

    if not isinstance(module_versions, dict):
        raise ProvisioningSnapshotBuildError(
            "config field 'module_versions' must be a dictionary"
        )

    routeros_compatibility = _optional_list(
        config_data,
        "routeros_compatibility",
        [],
    )

    # ---------------------------------------------------------
    # BUILD SNAPSHOT
    # ---------------------------------------------------------

    now = datetime.now(timezone.utc)

    return ProvisioningSnapshot(
        snapshot_id=snapshot_id,
        router_id=router_id,
        owner_id=owner_id,
        hotspot_id=hotspot_id,
        created_at=now,
        created_by=created_by,
        environment=_environment(
            config_data.get("environment")
        ),
        identity={
            "router_id": router_id,
            "router_name": router_name,
            "owner_id": owner_id,
            "hotspot_id": hotspot_id,
            "nas_identifier": nas_identifier,
        },
        topology={
            "deployment_mode": deployment_mode,
            "wan_interface": wan_interface,
            "lan_interfaces": list(lan_interfaces),
            "client_interface": client_interface,
            "create_bridge": create_bridge,
            "bridge_name": str(bridge_name) if bridge_name else None,
        },
        networking={
            "hotspot_cidr": hotspot_cidr,
            "hotspot_gateway": hotspot_gateway,
            "dhcp_pool_start": dhcp_pool_start,
            "dhcp_pool_end": dhcp_pool_end,
            "client_dns_servers": list(client_dns_servers),
            "router_dns_upstreams": list(router_dns_upstreams),
        },
        hotspot={
            "server_name": hotspot_server_name,
            "profile_name": hotspot_profile_name,
            "dns_name": dns_name,
            "login_methods": list(login_methods),
        },
        portal={
            "portal_public_url": portal_public_url,
            "api_public_url": api_public_url,
            "portal_strategy": portal_strategy,
            "portal_contract_version": portal_contract_version,
        },
        radius={
            "radius_host": radius_host,
            "radius_auth_port": radius_auth_port,
            "radius_accounting_port": radius_accounting_port,
            "radius_secret_ref": radius_secret_ref,
            "nas_identifier": nas_identifier,
        },
        heartbeat={
            "heartbeat_url": heartbeat_url,
            "heartbeat_interval_seconds": heartbeat_interval_seconds,
            "heartbeat_token_ref": heartbeat_token_ref,
        },
        diagnostics={
            "required_checks": list(required_checks),
            "validation_plan_id": validation_plan_id,
        },
        security={
            "provisioning_token_id": provisioning_token_id,
            "artifact_download_token_id": artifact_download_token_id,
            "callback_signing_key_ref": callback_signing_key_ref,
            "secret_policy": secret_policy,
        },
        versioning=VersionManifest(
            snapshot_schema_version=snapshot_schema_version,
            artifact_schema_version=artifact_schema_version,
            engine_version=engine_version,
            module_versions=dict(module_versions),
            routeros_compatibility=list(routeros_compatibility),
        ),
    )
