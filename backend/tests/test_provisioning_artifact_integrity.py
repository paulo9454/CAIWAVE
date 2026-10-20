import hashlib

from backend.services.provisioning.artifact_repository import (
    artifact_record_matches_expected,
)


def build_record():
    content = "/ip firewall filter add action=drop chain=input"
    return {
        "artifact_id": "artifact-1",
        "bundle_id": "bundle-1",
        "snapshot_id": "snapshot-1",
        "router_id": "router-1",
        "content_type": "text/routeros-script",
        "filename": "router-1.rsc",
        "status": "rendered",
        "manifest": {"router_id": "router-1", "snapshot_id": "snapshot-1"},
        "sections": [{"name": "firewall", "content": content}],
        "content": content,
        "checksum": hashlib.sha256(content.encode("utf-8")).hexdigest(),
    }


def test_artifact_record_accepts_exact_matching_record():
    expected = build_record()
    assert artifact_record_matches_expected(dict(expected), expected)


def test_artifact_record_rejects_different_router():
    expected = build_record()
    stored = dict(expected)
    stored["router_id"] = "router-elsewhere"
    assert not artifact_record_matches_expected(stored, expected)


def test_artifact_record_rejects_conflicting_bundle_or_content():
    expected = build_record()
    stored = dict(expected)
    stored["bundle_id"] = "different-bundle"
    assert not artifact_record_matches_expected(stored, expected)

    stored = dict(expected)
    stored["content"] += "\\n# tampered"
    assert not artifact_record_matches_expected(stored, expected)


def test_artifact_record_rejects_bad_checksum_even_if_records_match():
    expected = build_record()
    expected["checksum"] = "not-the-content-hash"
    assert not artifact_record_matches_expected(dict(expected), expected)
