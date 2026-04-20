from crm_facet_library import Facet, Library, load_library


def test_load_bundled_library():
    lib = load_library()
    assert isinstance(lib, Library)
    assert lib.version == "0.1.3"
    assert len(lib) >= 3


def test_worked_example_temporal_modeling_present():
    lib = load_library()
    facet = lib.get("history.relationship.temporal_modeling")
    assert isinstance(facet, Facet)
    assert facet.status == "active"
    assert facet.answer_schema.type == "rating"
    assert "full" in facet.answer_schema.allowed_values
    assert "unknown" in facet.answer_schema.allowed_values
    assert facet.family == "history"


def test_structured_facet_parses():
    lib = load_library()
    facet = lib.get("history.field.audit_trail")
    assert facet.answer_schema.type == "structured"
    assert "auto_recorded" in facet.answer_schema.fields
    qva = facet.answer_schema.fields["queryable_via_api"]
    assert qva.type == "boolean"
    assert qva.allowed_values == ["yes", "no", "unknown"]


def test_all_seed_facets_have_family_and_crm_dim_tags():
    lib = load_library()
    for facet in lib:
        assert any(t.startswith("family:") for t in facet.tags), facet.id
        assert any(t.startswith("crm-dim:") for t in facet.tags), facet.id
