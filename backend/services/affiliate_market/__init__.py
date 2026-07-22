"""CAIMART affiliate-market service contracts."""

from .service import (
    AffiliateMarketValidationError,
    build_affiliate_product_payload,
    normalize_affiliate_category,
    normalize_affiliate_url,
)

__all__ = [
    "AffiliateMarketValidationError",
    "build_affiliate_product_payload",
    "normalize_affiliate_category",
    "normalize_affiliate_url",
]
