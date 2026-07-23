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


def test_affiliate_product_image_upload_is_square_and_admin_only():
    assert '@marketplace_router.post("/{item_id}/upload-image")' in SERVER
    assert "upload_marketplace_image" in SERVER
    assert "validate_affiliate_image(content)" in SERVER
    assert "UPLOAD_DIR_MARKETPLACE" in SERVER
    assert '"width": 680' in SERVER
    assert '"height": 680' in SERVER
    assert "Depends(require_admin)" in SERVER

def test_affiliate_product_update_preserves_managed_fields():
    assert '@marketplace_router.put("/{item_id}")' in SERVER
    assert "update_marketplace_item" in SERVER
    assert 'image_url=existing.get("image_url")' in SERVER
    assert 'existing.get("is_active", True)' in SERVER
    assert 'payload["created_at"]' in SERVER
    assert 'payload["click_count"]' in SERVER
    assert 'payload["last_clicked_at"]' in SERVER

def test_affiliate_product_status_management_is_admin_only():
    assert '@marketplace_router.put("/{item_id}/status")' in SERVER
    assert "update_marketplace_item_status" in SERVER
    assert '"is_active": is_active' in SERVER
    assert "Depends(require_admin)" in SERVER


def test_affiliate_product_delete_removes_only_local_image():
    assert '@marketplace_router.delete("/{item_id}")' in SERVER
    assert "delete_marketplace_item" in SERVER
    assert 'db.marketplace.delete_one(' in SERVER
    assert '"/api/uploads/marketplace/"' in SERVER
    assert "Path(image_url).name" in SERVER
    assert "image_path.unlink()" in SERVER

