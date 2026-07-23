from datetime import datetime, timedelta, timezone

import pytest

from backend.services.portal_notifications import (
    PortalNotificationValidationError,
    build_portal_notification_payload,
    build_public_notification,
    normalize_action_path,
    notification_targets_hotspot,
    select_portal_notification,
)


NOW = datetime(2026, 7, 23, 12, 0, tzinfo=timezone.utc)


def build_notification(**overrides):
    values = {
        "title": "Live football now",
        "message": "Watch the live stream on CAIWAVE TV.",
        "source_type": "live_stream",
        "action_label": "Watch Live",
        "action_path": "#tv",
        "starts_at": NOW - timedelta(minutes=5),
        "expires_at": NOW + timedelta(hours=2),
        "now": NOW,
    }
    values.update(overrides)
    return build_portal_notification_payload(**values)


def test_builds_national_notification():
    result = build_notification()
    assert result["coverage_scope"] == "national"
    assert result["country_code"] == "KE"
    assert result["target_hotspot_ids"] == []


def test_requires_title():
    with pytest.raises(PortalNotificationValidationError) as exc:
        build_notification(title=" ")
    assert exc.value.field == "title"


def test_rejects_external_action_url():
    with pytest.raises(PortalNotificationValidationError) as exc:
        normalize_action_path("https://example.com")
    assert exc.value.field == "action_path"


def test_allows_internal_path_and_section():
    assert normalize_action_path("/portal/demo") == "/portal/demo"
    assert normalize_action_path("#tv") == "#tv"


def test_rejects_expiry_before_start():
    with pytest.raises(PortalNotificationValidationError) as exc:
        build_notification(
            starts_at=NOW,
            expires_at=NOW - timedelta(minutes=1),
        )
    assert exc.value.field == "expires_at"


def test_county_scope_requires_county():
    with pytest.raises(PortalNotificationValidationError) as exc:
        build_notification(coverage_scope="county")
    assert exc.value.field == "target_counties"


def test_hotspot_scope_requires_hotspot():
    with pytest.raises(PortalNotificationValidationError) as exc:
        build_notification(
            coverage_scope="specific_hotspots"
        )
    assert exc.value.field == "target_hotspot_ids"


def test_national_notification_matches_country():
    notification = build_notification()
    assert notification_targets_hotspot(
        notification,
        {"id": "one", "country_code": "KE"},
        now=NOW,
    )


def test_county_notification_matches_case_insensitively():
    notification = build_notification(
        coverage_scope="county",
        target_counties=["Kisii"],
    )
    assert notification_targets_hotspot(
        notification,
        {"id": "one", "county": "kisii"},
        now=NOW,
    )


def test_constituency_notification_matches():
    notification = build_notification(
        coverage_scope="constituency",
        target_constituencies=["Nyaribari Masaba"],
    )
    assert notification_targets_hotspot(
        notification,
        {
            "id": "one",
            "constituency": "Nyaribari Masaba",
        },
        now=NOW,
    )


def test_specific_hotspot_notification_matches():
    notification = build_notification(
        coverage_scope="specific_hotspots",
        target_hotspot_ids=["hotspot-1"],
    )
    assert notification_targets_hotspot(
        notification,
        {"id": "hotspot-1"},
        now=NOW,
    )


def test_inactive_or_expired_notification_does_not_match():
    inactive = build_notification(is_active=False)
    expired = build_notification(
        starts_at=NOW - timedelta(hours=2),
        expires_at=NOW - timedelta(hours=1),
    )
    hotspot = {"id": "one", "country_code": "KE"}

    assert not notification_targets_hotspot(
        inactive,
        hotspot,
        now=NOW,
    )
    assert not notification_targets_hotspot(
        expired,
        hotspot,
        now=NOW,
    )


def test_selects_highest_priority_eligible_notification():
    normal = build_notification(
        notification_id="normal",
        priority=10,
    )
    urgent = build_notification(
        notification_id="urgent",
        priority=90,
    )

    selected = select_portal_notification(
        [normal, urgent],
        {"id": "one", "country_code": "KE"},
        now=NOW,
    )

    assert selected["id"] == "urgent"


def test_public_notification_hides_targeting_and_admin_fields():
    public = build_public_notification(build_notification())

    assert "created_by" not in public
    assert "target_hotspot_ids" not in public
    assert public["action_path"] == "#tv"
