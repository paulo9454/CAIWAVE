"""
CAIWAVE Revenue Utilities
Dynamic revenue sharing calculation.
"""
from ..database import db
from ..models import RevenueConfig, DynamicRevenue


async def calculate_dynamic_revenue(hotspot_id: str, amount: float) -> DynamicRevenue:
    """Calculate dynamic revenue sharing based on hotspot metrics."""
    hotspot = await db.hotspots.find_one({"id": hotspot_id}, {"_id": 0})
    if not hotspot:
        # Default split if hotspot not found (30% to owner)
        return DynamicRevenue(
            total_amount=amount,
            owner_share=amount * 0.3,
            platform_share=amount * 0.7,
            owner_percentage=30.0,
            breakdown={"base": 30.0},
            capped=False
        )
    
    # Get revenue config
    config = await db.settings.find_one({"type": "revenue_config"}, {"_id": 0})
    if not config:
        config = RevenueConfig().model_dump()
    else:
        config = config.get("config", RevenueConfig().model_dump())
    
    # Calculate dynamic percentage
    breakdown = {"base": config.get("base_owner_percentage", 30.0)}
    owner_percentage = config.get("base_owner_percentage", 30.0)
    
    # Coverage bonus
    coverage_area = hotspot.get("coverage_area_sqm", 100)
    coverage_bonus = (coverage_area / 100) * config.get("coverage_bonus_per_100sqm", 0.5)
    breakdown["coverage_bonus"] = min(coverage_bonus, 5.0)
    owner_percentage += breakdown["coverage_bonus"]
    
    # Client bonus
    avg_clients = hotspot.get("avg_daily_clients", 0)
    client_bonus = (avg_clients / 10) * config.get("client_bonus_per_10", 0.5)
    breakdown["client_bonus"] = min(client_bonus, 5.0)
    owner_percentage += breakdown["client_bonus"]
    
    # Ad impression bonus
    ad_impressions = hotspot.get("ad_impressions_delivered", 0)
    ad_bonus = (ad_impressions / 1000) * config.get("ad_impression_bonus_per_1000", 1.0)
    breakdown["ad_bonus"] = min(ad_bonus, 5.0)
    owner_percentage += breakdown["ad_bonus"]
    
    # Uptime bonus
    uptime = hotspot.get("uptime_percentage", 100)
    if uptime >= config.get("uptime_bonus_threshold", 99.0):
        breakdown["uptime_bonus"] = config.get("uptime_bonus_percentage", 2.0)
        owner_percentage += breakdown["uptime_bonus"]
    
    # Check if cap needs to be applied
    max_percentage = config.get("max_owner_percentage", 50.0)
    capped = owner_percentage > max_percentage
    owner_percentage = min(owner_percentage, max_percentage)
    
    owner_share = amount * (owner_percentage / 100)
    platform_share = amount - owner_share
    
    return DynamicRevenue(
        total_amount=amount,
        owner_share=round(owner_share, 2),
        platform_share=round(platform_share, 2),
        owner_percentage=round(owner_percentage, 2),
        breakdown=breakdown,
        capped=capped
    )
