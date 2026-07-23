from datetime import datetime, timezone
from io import BytesIO

from PIL import Image as PILImage
import pytest

from backend.services.affiliate_market import (
    AffiliateMarketValidationError,
    build_affiliate_product_payload,
    normalize_affiliate_category,
    normalize_affiliate_url,
    validate_affiliate_image,
)


@pytest.mark.parametrize(
    ("raw_url", "expected"),
    [
        (
            "https://www.jumia.co.ke/product?utm_source=caiwave",
            "https://www.jumia.co.ke/product?utm_source=caiwave",
        ),
        (
            " http://merchant.example/deal ",
            "http://merchant.example/deal",
        ),
    ],
)
def test_accepts_public_http_affiliate_urls(raw_url, expected):
    assert normalize_affiliate_url(raw_url) == expected


@pytest.mark.parametrize(
    "raw_url",
    [
        "",
        None,
        "merchant.example/product",
        "javascript:alert(1)",
        "ftp://merchant.example/product",
        "https://user:password@merchant.example/product",
        "https://localhost/product",
        "https://merchant.local/product",
        "http://127.0.0.1/product",
        "http://10.0.0.1/product",
        "http://169.254.169.254/latest/meta-data",
        "https://merchant.example/bad path",
    ],
)
def test_rejects_unsafe_affiliate_urls(raw_url):
    with pytest.raises(AffiliateMarketValidationError) as exc:
        normalize_affiliate_url(raw_url)

    assert exc.value.field == "purchase_url"


NOW = datetime(2026, 7, 23, 9, 0, tzinfo=timezone.utc)


def valid_product(**changes):
    values = {
        "name": "Portable WiFi Router",
        "description": "Fast portable internet router.",
        "merchant_name": "Jumia Kenya",
        "category": "Network Equipment",
        "price": 3500,
        "original_price": 4200,
        "currency": "kes",
        "image_url": "/api/uploads/marketplace/router.webp",
        "purchase_url": "https://www.jumia.co.ke/router?aff=caiwave",
        "is_featured": True,
        "is_active": True,
        "product_id": "product-1",
        "now": NOW,
    }
    values.update(changes)
    return build_affiliate_product_payload(**values)


def test_builds_normalized_affiliate_product():
    result = valid_product()

    assert result["id"] == "product-1"
    assert result["merchant_name"] == "Jumia Kenya"
    assert result["category"] == "network_equipment"
    assert result["price"] == 3500.0
    assert result["original_price"] == 4200.0
    assert result["currency"] == "KES"
    assert result["click_count"] == 0
    assert result["created_at"] == NOW.isoformat()
    assert result["updated_at"] == NOW.isoformat()


@pytest.mark.parametrize(
    ("field", "changes"),
    [
        ("name", {"name": ""}),
        ("description", {"description": ""}),
        ("merchant_name", {"merchant_name": ""}),
        ("category", {"category": "---"}),
        ("price", {"price": -1}),
        ("price", {"price": "not-money"}),
        ("original_price", {"original_price": 3000}),
        ("currency", {"currency": "KE"}),
        ("purchase_url", {"purchase_url": "javascript:alert(1)"}),
    ],
)
def test_rejects_invalid_affiliate_product_fields(field, changes):
    with pytest.raises(AffiliateMarketValidationError) as exc:
        valid_product(**changes)

    assert exc.value.field == field


def test_original_price_is_optional():
    result = valid_product(original_price=None)

    assert result["original_price"] is None


def test_client_cannot_supply_click_count():
    result = valid_product()

    assert result["click_count"] == 0


@pytest.mark.parametrize(
    ("raw_category", "expected"),
    [
        ("Network Equipment", "network_equipment"),
        ("Phones & Tablets", "phones_tablets"),
        ("  Home--Appliances  ", "home_appliances"),
    ],
)
def test_normalizes_affiliate_categories(raw_category, expected):
    assert normalize_affiliate_category(raw_category) == expected


def image_bytes(width, height):
    buffer = BytesIO()
    PILImage.new("RGB", (width, height), "white").save(
        buffer,
        format="PNG",
    )
    return buffer.getvalue()


def test_accepts_exact_affiliate_image_dimensions():
    assert validate_affiliate_image(
        image_bytes(680, 680)
    ) == (680, 680)


@pytest.mark.parametrize(
    ("width", "height"),
    [
        (679, 680),
        (680, 679),
        (681, 680),
        (680, 681),
        (1200, 1200),
    ],
)
def test_rejects_wrong_affiliate_image_dimensions(width, height):
    with pytest.raises(AffiliateMarketValidationError) as exc:
        validate_affiliate_image(image_bytes(width, height))

    assert exc.value.field == "image"
    assert "680 × 680" in exc.value.message


@pytest.mark.parametrize("content", [b"", b"not-an-image"])
def test_rejects_invalid_affiliate_image_files(content):
    with pytest.raises(AffiliateMarketValidationError) as exc:
        validate_affiliate_image(content)

    assert exc.value.field == "image"
