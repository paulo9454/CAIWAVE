def normalize_router(router: dict) -> dict:
    """
    Ensures router data is safe for provisioning pipeline
    """

    return {
        **router,
        "nas_identifier": router.get("nas_identifier") or "",
        "hotspot_cidr": router.get("hotspot_cidr") or "",
        "radius_secret": router.get("radius_secret") or "",
    }
