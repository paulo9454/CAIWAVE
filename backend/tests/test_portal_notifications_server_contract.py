from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SERVER = (ROOT / "backend/server.py").read_text()


def test_portal_notification_service_is_imported():
    assert "PortalNotificationValidationError" in SERVER
    assert "build_portal_notification_payload" in SERVER
    assert "build_public_notification" in SERVER
    assert "select_portal_notification" in SERVER


def test_portal_notification_request_has_targeting_fields():
    assert "class PortalNotificationRequest(BaseModel)" in SERVER

    required_fields = [
        "source_type",
        "source_id",
        "action_label",
        "action_path",
        "coverage_scope",
        "target_counties",
        "target_constituencies",
        "target_hotspot_ids",
        "starts_at",
        "expires_at",
        "priority",
    ]

    for field in required_fields:
        assert field in SERVER


def test_portal_notification_indexes_are_created():
    assert '"portal_notification_delivery"' in SERVER
    assert '"portal_notification_source"' in SERVER
    assert "db.portal_notifications.create_index" in SERVER

def test_portal_notification_admin_crud_is_registered():
    required_routes = [
        '@notifications_router.get("/admin")',
        '@notifications_router.post("/", status_code=201)',
        '@notifications_router.put("/{notification_id}")',
        '@notifications_router.put("/{notification_id}/status")',
        '@notifications_router.delete("/{notification_id}")',
    ]

    for route in required_routes:
        assert route in SERVER

    assert "Depends(require_admin)" in SERVER


def test_notification_creation_uses_validated_service():
    assert "_build_notification_request_payload" in SERVER
    assert "build_portal_notification_payload(" in SERVER
    assert "PortalNotificationValidationError" in SERVER
    assert "db.portal_notifications.insert_one" in SERVER


def test_public_latest_notification_is_hotspot_targeted():
    assert '@notifications_router.get("/latest")' in SERVER
    assert 'hotspot_id: str = Query(...)' in SERVER
    assert "select_portal_notification(" in SERVER
    assert "build_public_notification(selected)" in SERVER
    assert '"poll_after_seconds": 60' in SERVER


def test_notification_update_preserves_managed_fields():
    assert 'notification_id=notification_id' in SERVER
    assert 'created_by=existing.get("created_by")' in SERVER
    assert 'existing.get("is_active", True)' in SERVER
    assert 'payload["created_at"]' in SERVER


def test_notification_status_and_delete_are_persisted():
    assert '"is_active": is_active' in SERVER
    assert "db.portal_notifications.update_one" in SERVER
    assert "db.portal_notifications.delete_one" in SERVER

