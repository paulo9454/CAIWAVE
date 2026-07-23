"""CAIMART affiliate-market service contracts."""

from .service import (
    AFFILIATE_IMAGE_HEIGHT,
    AFFILIATE_IMAGE_WIDTH,
    AffiliateMarketValidationError,
    build_affiliate_product_payload,
    normalize_affiliate_category,
    normalize_affiliate_url,
    validate_affiliate_image,
)

__all__ = [
    "AFFILIATE_IMAGE_HEIGHT",
    "AFFILIATE_IMAGE_WIDTH",
    "AffiliateMarketValidationError",
    "build_affiliate_product_payload",
    "normalize_affiliate_category",
    "normalize_affiliate_url",
    "validate_affiliate_image",
]
