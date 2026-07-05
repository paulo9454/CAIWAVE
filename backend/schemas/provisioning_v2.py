"""
Provisioning Engine v2 foundation contracts.

These CPAS/CMIS/CRS contracts are intentionally isolated:
- no database I/O
- no route registration
- no legacy provisioning changes
- no RouterOS generation
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProvisioningLifecycleState(str, Enum):
    REGISTERED = "registered"
    SNAPSHOT_CREATED = "snapshot_created"
    SNAPSHOT_VALIDATED = "snapshot_validated"
    ARTIFACT_GENERATED = "artifact_generated"
    ARTIFACT_DOWNLOADED = "artifact_downloaded"
    IMPORT_PENDING = "import_pending"
    IMPORT_CONFIRMED = "import_confirmed"
    HEARTBEAT_SEEN = "heartbeat_seen"
    VALIDATED = "validated"
    PRODUCTION_READY = "production_ready"
    OFFLINE = "offline"
    RECOVERING = "recovering"
    DECOMMISSIONED = "decommissioned"


class ResourceLifecycleState(str, Enum):
    PLANNED = "planned"
    RENDERED = "rendered"
    IMPORTED = "imported"
    REPORTED = "reported"
    VERIFIED = "verified"
    MODIFIED = "modified"
    OUT_OF_SYNC = "out_of_sync"
    DEPRECATED = "deprecated"
    REMOVED = "removed"


class ArtifactStatus(str, Enum):
    GENERATED = "generated"
    READY_FOR_DOWNLOAD = "ready_for_download"
    DOWNLOADED = "downloaded"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUPERSEDED = "superseded"


class ModuleStatus(str, Enum):
    SUCCESS = "success"
    WARNING = "warning"
    FAILED = "failed"
    SKIPPED = "skipped"


class ResourceOwner(str, Enum):
    CAIWAVE = "caiwave"
    OPERATOR = "operator"
    SYSTEM = "system"
    THIRD_PARTY = "third_party"
    UNKNOWN = "unknown"


class SecurityClassification(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    SECRET = "secret"
    HIGHLY_SENSITIVE = "highly_sensitive"


class ValidationLevel(str, Enum):
    EXPECTED = "expected"
    RENDERED = "rendered"
    IMPORTED = "imported"
    REPORTED = "reported"
    VERIFIED = "verified"
    FAILED = "failed"


class DriftStatus(str, Enum):
    UNKNOWN = "unknown"
    IN_SYNC = "in_sync"
    OUT_OF_SYNC = "out_of_sync"
    WAIVED = "waived"


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    LAB = "lab"


class ErrorSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    SECURITY = "security"


class VersionManifest(StrictModel):
    snapshot_schema_version: str = "1.0"
    artifact_schema_version: str = "1.0"
    engine_version: str = "2.0.0"
    module_versions: Dict[str, str] = Field(default_factory=dict)
    routeros_compatibility: List[str] = Field(default_factory=list)


class SnapshotIdentity(StrictModel):
    router_id: str
    router_name: str
    owner_id: str
    hotspot_id: str
    nas_identifier: str


class SnapshotTopology(StrictModel):
    deployment_mode: str
    wan_interface: str
    lan_interfaces: List[str]
    client_interface: Optional[str] = None
    create_bridge: bool = True
    bridge_name: Optional[str] = None


class SnapshotNetworking(StrictModel):
    hotspot_cidr: str
    hotspot_gateway: str
    dhcp_pool_start: str
    dhcp_pool_end: str
    client_dns_servers: List[str] = Field(default_factory=list)
    router_dns_upstreams: List[str] = Field(default_factory=list)


class SnapshotHotspot(StrictModel):
    server_name: str
    profile_name: str
    dns_name: str
    login_methods: List[str] = Field(default_factory=list)


class SnapshotPortal(StrictModel):
    portal_public_url: str
    api_public_url: str
    portal_strategy: str
    portal_contract_version: str = "1.0"


class SnapshotRadius(StrictModel):
    radius_host: str
    radius_auth_port: int = 1812
    radius_accounting_port: int = 1813
    radius_secret_ref: str
    nas_identifier: str


class SnapshotHeartbeat(StrictModel):
    heartbeat_url: str
    heartbeat_interval_seconds: int = 300
    heartbeat_token_ref: str


class SnapshotDiagnostics(StrictModel):
    required_checks: List[str] = Field(default_factory=list)
    validation_plan_id: Optional[str] = None


class SnapshotSecurity(StrictModel):
    provisioning_token_id: Optional[str] = None
    artifact_download_token_id: Optional[str] = None
    callback_signing_key_ref: Optional[str] = None
    secret_policy: str = "redact"


class ProvisioningSnapshot(StrictModel):
    snapshot_id: str
    router_id: str
    owner_id: str
    hotspot_id: str
    created_at: datetime
    created_by: str
    environment: Environment
    identity: SnapshotIdentity
    topology: SnapshotTopology
    networking: SnapshotNetworking
    hotspot: SnapshotHotspot
    portal: SnapshotPortal
    radius: SnapshotRadius
    heartbeat: SnapshotHeartbeat
    diagnostics: SnapshotDiagnostics
    security: SnapshotSecurity
    versioning: VersionManifest


class ValidationHook(StrictModel):
    validation_id: str
    module: str
    resource_id: Optional[str] = None
    level: ValidationLevel
    evidence_source: str
    expected_value: Optional[Any] = None
    blocking: bool = True
    timeout_seconds: int = 60
    failure_message: str
    remediation_hint: Optional[str] = None


class ResourceRegistryEntry(StrictModel):
    resource_id: str
    router_id: str
    hotspot_id: str
    artifact_id: str
    snapshot_id: str
    resource_type: str
    logical_name: str
    physical_name: Optional[str] = None
    owner: ResourceOwner = ResourceOwner.CAIWAVE
    module: str
    module_version: str
    expected_state: Dict[str, Any] = Field(default_factory=dict)
    observed_state: Dict[str, Any] = Field(default_factory=dict)
    lifecycle_state: ResourceLifecycleState = ResourceLifecycleState.PLANNED
    validation_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    security_classification: SecurityClassification = SecurityClassification.INTERNAL
    dependencies: List[str] = Field(default_factory=list)
    rollback_metadata: Dict[str, Any] = Field(default_factory=dict)
    drift_status: DriftStatus = DriftStatus.UNKNOWN
    last_verified_at: Optional[datetime] = None


class ModuleResult(StrictModel):
    module_name: str
    module_version: str
    status: ModuleStatus
    resources: List[ResourceRegistryEntry] = Field(default_factory=list)
    rendered_fragments: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    events: List[Dict[str, Any]] = Field(default_factory=list)
    metrics: List[Dict[str, Any]] = Field(default_factory=list)
    validation_hooks: List[ValidationHook] = Field(default_factory=list)
    rollback_hooks: List[Dict[str, Any]] = Field(default_factory=list)
    security_notes: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)


class ValidationPlan(StrictModel):
    validation_plan_id: str
    hooks: List[ValidationHook] = Field(default_factory=list)
    production_readiness_required: bool = True


class ProvisioningArtifact(StrictModel):
    artifact_id: str
    snapshot_id: str
    router_id: str
    hotspot_id: str
    generated_at: datetime
    generated_by: str
    status: ArtifactStatus = ArtifactStatus.GENERATED
    artifact_version: str
    engine_version: str
    module_versions: Dict[str, str] = Field(default_factory=dict)
    sha256: Optional[str] = None
    script_sha256: Optional[str] = None
    redacted_sha256: Optional[str] = None
    filename: str
    content_type: str = "text/plain"
    content: str
    redacted_content: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    validation_plan: Optional[ValidationPlan] = None
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    superseded_by: Optional[str] = None
