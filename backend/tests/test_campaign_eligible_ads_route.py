from backend.server import app


def get_route_index(path):
    for index, route in enumerate(app.routes):
        if getattr(route, "path", None) == path:
            return index
    raise AssertionError(f"Route not found: {path}")


def test_eligible_ads_route_is_registered():
    routes = [
        route
        for route in app.routes
        if getattr(route, "path", None)
        == "/api/campaigns/eligible-ads"
    ]

    assert len(routes) == 1
    assert routes[0].methods == {"GET"}


def test_eligible_ads_route_precedes_dynamic_campaign_route():
    eligible_index = get_route_index(
        "/api/campaigns/eligible-ads"
    )
    dynamic_index = get_route_index(
        "/api/campaigns/{campaign_id}"
    )

    assert eligible_index < dynamic_index
