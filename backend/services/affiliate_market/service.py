"""Pure validation helpers for CAIMART affiliate products."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from ipaddress import ip_address
import re
from urllib.parse import urlparse
import uuid


class AffiliateMarketValidationError(ValueError):
    """Raised when an affiliate product field is invalid."""

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(message)


def normalize_affiliate_url(value: object) -> str:
    """Validate and normalize an external affiliate destination URL."""

    url = str(value or "").strip()

    if not url:
        raise AffiliateMarketValidationError(
            "purchase_url",
            "Affiliate purchase URL is required.",
        )

    if any(character.isspace() for character in url):
        raise AffiliateMarketValidationError(
            "purchase_url",
            "Affiliate purchase URL cannot contain spaces.",
        )

    parsed = urlparse(url)

    if parsed.scheme.lower() not in {"http", "https"}:
        raise AffiliateMarketValidationError(
            "purchase_url",
            "Affiliate purchase URL must use HTTP or HTTPS.",
        )

    if not parsed.hostname:
        raise AffiliateMarketValidationError(
            "purchase_url",
            "Affiliate purchase URL must include a valid hostname.",
        )

    if parsed.username or parsed.password:
        raise AffiliateMarketValidationError(
            "purchase_url",
            "Affiliate purchase URL cannot include credentials.",
        )

    hostname = parsed.hostname.lower().rstrip(".")

    if hostname == "localhost" or hostname.endswith(".local"):
        raise AffiliateMarketValidationError(
            "purchase_url",
            "Affiliate purchase URL must point to a public merchant.",
        )

    try:
        address = ip_address(hostname)
    except ValueError:
        address = None

    if address is not None and not address.is_global:
        raise AffiliateMarketValidationError(
            "purchase_url",
            "Affiliate purchase URL must point to a public merchant.",
        )

    return parsed.geturl()


def _required_text(
    value: object,
    *,
    field: str,
    label: str,
    maximum_length: int,
) -> str:
    normalized = str(value or "").strip()

    if not normalized:
        raise AffiliateMarketValidationError(
            field,
            f"{label} is required.",
        )

    if len(normalized) > maximum_length:
        raise AffiliateMarketValidationError(
            field,
            f"{label} must be {maximum_length} characters or fewer.",
        )

    return normalized


def _money(value: object, *, field: str, label: str) -> float:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise AffiliateMarketValidationError(
            field,
            f"{label} must be a valid amount.",
        ) from None

    if not amount.is_finite() or amount < 0:
        raise AffiliateMarketValidationError(
            field,
            f"{label} cannot be negative.",
        )

    return float(amount)


def build_affiliate_product_payload(
    *,
    name: object,
    description: object,
    merchant_name: object,
    category: object,
    price: object,
    purchase_url: object,
    original_price: object = None,
    currency: object = "KES",
    image_url: object = None,
    is_featured: bool = False,
    is_active: bool = True,
    product_id: object = None,
    now: datetime | None = None,
) -> dict[str, object]:
    """Build a normalized CAIMART affiliate-product document."""

    normalized_name = _required_text(
        name,
        field="name",
        label="Product name",
        maximum_length=160,
    )
    normalized_description = _required_text(
        description,
        field="description",
        label="Product description",
        maximum_length=2000,
    )
    normalized_merchant = _required_text(
        merchant_name,
        field="merchant_name",
        label="Merchant name",
        maximum_length=120,
    )

    raw_category = _required_text(
        category,
        field="category",
        label="Category",
        maximum_length=80,
    )
    normalized_category = re.sub(
        r"[^a-z0-9]+",
        "_",
        raw_category.lower(),
    ).strip("_")

    if not normalized_category:
        raise AffiliateMarketValidationError(
            "category",
            "Category must contain letters or numbers.",
        )

    normalized_price = _money(
        price,
        field="price",
        label="Current price",
    )

    normalized_original_price = None

    if original_price not in (None, ""):
        normalized_original_price = _money(
            original_price,
            field="original_price",
            label="Original price",
        )

        if normalized_original_price < normalized_price:
            raise AffiliateMarketValidationError(
                "original_price",
                "Original price cannot be lower than current price.",
            )

    normalized_currency = str(currency or "KES").strip().upper()

    if (
        len(normalized_currency) != 3
        or not normalized_currency.isalpha()
    ):
        raise AffiliateMarketValidationError(
            "currency",
            "Currency must be a three-letter code such as KES.",
        )

    normalized_image_url = str(image_url or "").strip() or None
    normalized_purchase_url = normalize_affiliate_url(purchase_url)

    moment = now or datetime.now(timezone.utc)

    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)

    identifier = str(product_id or "").strip() or str(uuid.uuid4())
    timestamp = moment.astimezone(timezone.utc).isoformat()

    return {
        "id": identifier,
        "name": normalized_name,
        "description": normalized_description,
        "merchant_name": normalized_merchant,
        "category": normalized_category,
        "price": normalized_price,
        "original_price": normalized_original_price,
        "currency": normalized_currency,
        "image_url": normalized_image_url,
        "purchase_url": normalized_purchase_url,
        "is_featured": bool(is_featured),
        "is_active": bool(is_active),
        "click_count": 0,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
