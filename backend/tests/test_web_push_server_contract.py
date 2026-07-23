from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SERVER = (ROOT / "backend/server.py").read_text()


def test_web_push_request_models_are_registered():
    assert "class WebPushKeysRequest(BaseModel)" in SERVER
    assert "class WebPushSubscriptionRequest(BaseModel)" in SERVER
    assert "class WebPushPreferencesRequest(BaseModel)" in SERVER
    assert "class WebPushUnsubscribeRequest(BaseModel)" in SERVER


def test_public_push_config_is_registered():
    assert '@notifications_router.get("/push/config")' in SERVER
    assert '"WEB_PUSH_VAPID_PUBLIC_KEY"' in SERVER
    assert '"max_notifications_per_day": 2' in SERVER
    assert '"Africa/Nairobi"' in SERVER


def test_subscription_route_validates_hotspot_and_session():
    assert '@notifications_router.post(' in SERVER
    assert '"/push/subscribe"' in SERVER
    assert "build_web_push_subscription_payload(" in SERVER
    assert '"id": request.hotspot_id' in SERVER
    assert '"id": request.session_id' in SERVER
    assert '"hotspot_id": request.hotspot_id' in SERVER


def test_subscription_is_upserted_by_endpoint_hash():
    assert "db.web_push_subscriptions.update_one" in SERVER
    assert '"endpoint_hash": payload["endpoint_hash"]' in SERVER
    assert '"$setOnInsert"' in SERVER
    assert "upsert=True" in SERVER


def test_preferences_and_unsubscribe_routes_exist():
    assert '@notifications_router.put("/push/preferences")' in SERVER
    assert '@notifications_router.delete("/push/unsubscribe")' in SERVER
    assert "normalize_push_preferences(" in SERVER
    assert '"is_active": False' in SERVER


def test_web_push_indexes_are_created():
    assert '"web_push_endpoint"' in SERVER
    assert '"web_push_hotspot_delivery"' in SERVER
    assert "unique=True" in SERVER
