"""Notification-based WiFi reward server contracts."""

from pathlib import Path
import ast


SERVER_PATH = Path(__file__).resolve().parents[1] / "server.py"
SERVER = SERVER_PATH.read_text()


def _function_source(function_name: str) -> str:
    tree = ast.parse(SERVER)

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == function_name:
                return ast.get_source_segment(SERVER, node) or ""

    raise AssertionError(f"Function {function_name!r} not found")


def test_notification_reward_request_model_exists():
    assert "class NotificationRewardRequest(BaseModel):" in SERVER
    assert "endpoint: str = Field(min_length=1)" in SERVER
    assert "hotspot_id: str = Field(min_length=1)" in SERVER
    assert "user_mac: Optional[str] = None" in SERVER
    assert "user_ip: Optional[str] = None" in SERVER


def test_notification_reward_routes_are_registered():
    assert '@api_router.get("/portal/notification-reward-status")' in SERVER
    assert '@api_router.post("/portal/notification-reward")' in SERVER


def test_notification_enrollment_contract_exists():
    assert "class NotificationEnrollmentRequest(BaseModel):" in SERVER
    assert (
        '@api_router.post("/portal/notification-enrollment")'
        in SERVER
    )
    assert "NOTIFICATION_ENROLLMENT_DURATION_SECONDS = 60" in SERVER
    assert "NOTIFICATION_ENROLLMENT_COOLDOWN_HOURS = 24" in SERVER
    assert 'package_id="notification-enrollment"' in SERVER


def test_notification_enrollment_is_backend_controlled():
    source = _function_source("create_notification_enrollment")

    assert "db.notification_enrollment_claims" in source
    assert "find_one_and_update" in source
    assert "upsert=True" in source
    assert "ReturnDocument.AFTER" in source
    assert "except DuplicateKeyError" in source
    assert "generate_radius_credentials" in source
    assert "await db.sessions.insert_one" in source
    assert "NOTIFICATION_ENROLLMENT_DURATION_SECONDS" in source


def test_notification_enrollment_indexes_exist():
    assert '"notification_enrollment_device_claim"' in SERVER
    assert '"notification_enrollment_eligibility"' in SERVER


def test_notification_enrollment_does_not_require_push_subscription():
    source = _function_source("create_notification_enrollment")

    assert "web_push_subscriptions" not in source
    assert "hash_push_endpoint" not in source


def test_notification_reward_requires_active_push_subscription():
    source = _function_source("create_notification_reward")

    assert "hash_push_endpoint(request.endpoint)" in source
    assert "db.web_push_subscriptions.find_one" in source
    assert '"hotspot_id": request.hotspot_id' in source
    assert '"is_active": True' in source
    assert "Enable browser notifications" in source


def test_notification_reward_uses_atomic_claim():
    source = _function_source("create_notification_reward")

    assert "db.notification_reward_claims.find_one_and_update" in source
    assert "upsert=True" in source
    assert "ReturnDocument.AFTER" in source
    assert "except DuplicateKeyError" in source
    assert "NOTIFICATION_REWARD_COOLDOWN_HOURS" in source


def test_notification_reward_creates_distinct_session_metadata():
    source = _function_source("create_notification_reward")

    assert 'package_id="notification-reward"' in source
    assert 'session_dict["reward_type"] = "notification"' in source
    assert 'session_dict["reward_claim_id"] = claim_id' in source
    assert 'session_dict["push_subscription_id"]' in source
    assert "NOTIFICATION_REWARD_DURATION_MINUTES" in source


def test_failed_session_creation_restores_or_releases_claim():
    source = _function_source("create_notification_reward")

    assert "previous_claim = await" in source
    assert "db.notification_reward_claims.update_one" in source
    assert "db.notification_reward_claims.delete_one" in source
    assert '"claim_id": claim_id' in source
    assert "active_claim_filter" in source


def test_notification_reward_claim_indexes_exist():
    assert '"notification_reward_device_claim"' in SERVER
    assert '"notification_reward_eligibility"' in SERVER
    assert "unique=True" in SERVER


def test_advert_reward_route_remains_independent():
    source = _function_source("create_free_session")

    assert "ad_id: str" in source
    assert "db.ads.find_one" in source
    assert "MAX_FREE_ADS = 2" in source
