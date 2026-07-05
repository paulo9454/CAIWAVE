"""
Dry-run Provisioning Snapshot Builder for CAIWAVE Provisioning Engine v2.

Safety:
- no database access
- no environment access
- no RouterOS generation
- no live route wiring
- no mutation of input dictionaries
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
        raise ProvisioningSnapshotBuildError(f"Missing required {source} field: {key}")
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


def build_provisioning_snapshot(
    router: dict,
    hotspot: dict,
    config: dict | None = None,
    created_by: str = "system",
) -> ProvisioningSnapshot:
    """
    Build an immutable ProvisioningSnapshot from plain dictionaries.

    This is a dry-run foundation builder. It intentionally does not persist,
    render, call RouterOS, or connect to legacy provisioning.
    """

    router_data = deepcopy(router or {})
    hotspot_data = deepcopy(hotspot or {})
    config_data = deepcopy(config or {})

    router_id = str(_required(router_data, "id", "router"))
    router_name = str(router_data.get("name") or router_data.get("router_name") or router_id)
    hotspot_id = str(router_data.get("hotspot_id") or _required(hotspot_data, "id", "hotspot"))
    owner_id = str(router_data.get("owner_id") or _required(hotspot_data, "owner_id", "hotspot"))
    nas_identifier = str(_required(router_data, "nas_identifier", "router"))

    wan_interface = str(_required(router_data, "wan_interface", "router"))
    lan_interfaces = router_data.get("lan_interfaces")
    if not isinstance(lan_interfaces, list) or not lan_interfaces:
        raise ProvisioningSnapshotBuildError(
            "Missing required router field: lan_interfaces"
        )
    lan_interfaces = [str(item) for item in lan_interfaces if str(item).strip()]
    if not lan_interfaces:
        raise ProvisioningSnapshotBuildError(
            "Missing required router field: lan_interfaces"
        )
    if wan_interface in lan_interfaces:
        raise ProvisioningSnapshotBuildError(
            "Invalid topology: wan_interface must not appear in lan_interfaces"
        )

    dhcp_pool_start, dhcp_pool_end = _split_dhcp_pool(
        str(_required(router_data, "dhcp_pool", "router"))
    )

    hotspot_cidr = str(_required(router_data, "hotspot_cidr", "router"))
    hotspot_gateway = str(_required(router_data, "hotspot_gateway", "router"))

    bridge_name = router_data.get("bridge_name")
    create_bridge = bool(router_data.get("create_bridge", True))
    client_interface = (
        router_data.get("effective_lan_interface")
        or router_data.get("client_interface")
        or bridge_name
        or lan_interfaces[0]
    )

    radius_secret_ref = (
        router_data.get("radius_secret_ref")
        or config_data.get("radius_secret_ref")
        or f"router-radius-secret:{router_id}"
    )

    heartbeat_token_ref = (
        router_data.get("heartbeat_token_ref")
        or config_data.get("heartbeat_token_ref")
        or f"router-heartbeat-token:{router_id}"
    )

    snapshot_id = str(config_data.get("snapshot_id") or f"snapshot:{router_id}")
    now = datetime.now(timezone.utc)

    radius_host = str(_required(config_data, "radius_host", "config"))
    portal_public_url = str(_required(config_data, "portal_public_url", "config"))
    api_public_url = str(_required(config_data, "api_public_url", "config"))
    heartbeat_url = str(_required(config_data, "heartbeat_url", "config"))

    return ProvisioningSnapshot(
        snapshot_id=snapshot_id,
        router_id=router_id,
        owner_id=owner_id,
        hotspot_id=hotspot_id,
        created_at=now,
        created_by=created_by,
        environment=_environment(config_data.get("environment")),
        identity={
            "router_id": router_id,
            "router_name": router_name,
            "owner_id": owner_id,
            "hotspot_id": hotspot_id,
            "nas_identifier": nas_identifier,
        },
        topology={
            "deployment_mode": str(router_data.get("mode") or "fresh"),
            "wan_interface": wan_interface,
            "lan_interfaces": lan_interfaces,
            "client_interface": str(client_interface),
            "create_bridge": create_bridge,
            "bridge_name": str(bridge_name) if bridge_name else None,
        },
        networking={
            "hotspot_cidr": hotspot_cidr,
            "hotspot_gateway": hotspot_gateway,
            "dhcp_pool_start": dhcp_pool_start,
            "dhcp_pool_end": dhcp_pool_end,
            "client_dns_servers": list(
                config_data.get("client_dns_servers") or [hotspot_gateway]
            ),
            "router_dns_upstreams": list(
                config_data.get("router_dns_upstreams") or []
            ),
        },
        hotspot={
            "server_name": str(
                router_data.get("hotspot_server_name") or "caiwave-hotspot"
            ),
            "profile_name": str(
                router_data.get("hotspot_profile_name") or "caiwave-profile"
            ),
            "dns_name": str(router_data.get("dns_name") or "wifi.caiwave.com"),
            "login_methods": list(config_data.get("login_methods") or ["http-pap"]),
        },
        portal={
            "portal_public_url": portal_public_url,
            "api_public_url": api_public_url,
            "portal_strategy": str(config_data.get("portal_strategy") or "redirect"),
            "portal_contract_version": str(
                config_data.get("portal_contract_version") or "1.0"
            ),
        },
        radius={
            "radius_host": radius_host,
            "radius_auth_port": int(config_data.get("radius_auth_port") or 1812),
            "radius_accounting_port": int(
                config_data.get("radius_accounting_port") or 1813
            ),
            "radius_secret_ref": str(radius_secret_ref),
            "nas_identifier": nas_identifier,
        },
        heartbeat={
            "heartbeat_url": heartbeat_url,
            "heartbeat_interval_seconds": int(
                config_data.get("heartbeat_interval_seconds") or 300
            ),
            "heartbeat_token_ref": str(heartbeat_token_ref),
        },
        diagnostics={
            "required_checks": list(
                config_data.get("required_checks")
                or ["heartbeat", "radius", "hotspot", "portal"]
            ),
            "validation_plan_id": config_data.get("validation_plan_id"),
        },
        security={
            "provisioning_token_id": config_data.get("provisioning_token_id"),
            "artifact_download_token_id": config_data.get(
                "artifact_download_token_id"
            ),
            "callback_signing_key_ref": config_data.get(
                "callback_signing_key_ref"
            ),
            "secret_policy": str(config_data.get("secret_policy") or "redact"),
        },
        versioning=VersionManifest(
            snapshot_schema_version=str(
                config_data.get("snapshot_schema_version") or "1.0"
            ),
            artifact_schema_version=str(
                config_data.get("artifact_schema_version") or "1.0"
            ),
            engine_version=str(config_data.get("engine_version") or "2.0.0"),
            module_versions=dict(config_data.get("module_versions") or {}),
            routeros_compatibility=list(
                config_data.get("routeros_compatibility") or []
            ),
        ),
    )
