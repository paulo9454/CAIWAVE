import pytest

from backend.services.provisioning_v2.routeros_renderer_contracts import (
    RenderStatus,
    RendererContractError,
    RouterOSRenderedSection,
    RouterOSSectionName,
    build_render_context,
    default_routeros_section_order,
)


def test_default_section_order_contains_required_sections():
    order = default_routeros_section_order()

    assert order[0] == RouterOSSectionName.HEADER
    assert RouterOSSectionName.BRIDGE in order
    assert RouterOSSectionName.HOTSPOT in order
    assert RouterOSSectionName.RADIUS in order
    assert order[-1] == RouterOSSectionName.FOOTER


def test_build_render_context_defaults_to_routeros_7():
    context = build_render_context()

    assert context.routeros_major_version == 7
    assert context.safe_mode_required is True
    assert context.idempotent is True
    assert context.section_order == default_routeros_section_order()


def test_rejects_routeros_6_for_renderer_v2():
    with pytest.raises(RendererContractError):
        build_render_context(routeros_major_version=6)


def test_rendered_section_is_initially_planned():
    section = RouterOSRenderedSection(name=RouterOSSectionName.BRIDGE)

    assert section.status == RenderStatus.PLANNED
    assert section.content == ""
    assert section.warnings == []
