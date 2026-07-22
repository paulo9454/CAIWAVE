from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SERVER = (ROOT / "backend/server.py").read_text()
SETTINGS = (ROOT / "backend/models/settings.py").read_text()


def test_affiliate_routes_are_registered():
    assert '@marketplace_router.get("/admin")' in SERVER
    assert '@marketplace_router.get("/")' in SERVER
    assert '@marketplace_router.post("/", status_code=201)' in SERVER
    assert '@marketplace_router.get("/{item_id}/visit")' in SERVER


def test_admin_marketplace_listing_is_protected():
    assert "get_admin_marketplace_items" in SERVER
    assert "Depends(require_admin)" in SERVER


def test_public_listing_hides_destination_url():
    assert 'public_item.pop("purchase_url", None)' in SERVER
    assert 'public_item["visit_url"]' in SERVER


def test_affiliate_creation_uses_validated_contract():
    assert "build_affiliate_product_payload(" in SERVER
    assert "AffiliateMarketValidationError" in SERVER


def test_affiliate_redirect_is_active_only_and_tracked():
    assert '"is_active": True' in SERVER
    assert '"$inc": {"click_count": 1}' in SERVER
    assert "normalize_affiliate_url(" in SERVER
    assert "RedirectResponse(" in SERVER
    assert '"Cache-Control": "no-store"' in SERVER


def test_affiliate_marketplace_indexes_are_created():
    assert '"affiliate_public_listing"' in SERVER
    assert '"affiliate_category"' in SERVER
    assert '"affiliate_click_analytics"' in SERVER


def test_marketplace_models_include_affiliate_fields():
    required_fields = [
        "merchant_name",
        "original_price",
        "currency",
        "is_featured",
        "click_count",
        "last_clicked_at",
    ]

    for field in required_fields:
        assert field in SERVER
        assert field in SETTINGS
