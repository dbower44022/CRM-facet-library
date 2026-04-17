import textwrap
from pathlib import Path

from crm_facet_library.validation import run_all


_BASE_FACET = """\
id: {id}
version: 0.1.0
status: active
name: Test facet
description: A test facet.
question: Does this work?
answer_schema:
  type: rating
  allowed_values: [full, none, unknown]
applies_to: [entity]
tags:
  - family:history
  - crm-dim:entity
"""


def _write_library(
    tmp_path: Path,
    families=("entity", "history"),
    facets=None,
) -> Path:
    root = tmp_path / "lib"
    root.mkdir()
    (root / "LIBRARY.yaml").write_text(
        textwrap.dedent(
            f"""\
            library_version: 0.1.0
            schema_version: 1
            rating_vocabulary: [full, partial, read_only, indirect, workaround, none, na, unknown]
            families: [{", ".join(families)}]
            tag_namespaces: [family, "applies-to", axis, "crm-dim", complexity, impact]
            applies_to_values: [entity, process, persona, cross-cutting]
            status_values: [active, deprecated, draft]
            answer_schema_types: [rating, boolean, scalar, structured]
            """
        )
    )
    facets_dir = root / "facets"
    facets_dir.mkdir()
    for family, name, content in facets or []:
        fam_dir = facets_dir / family
        fam_dir.mkdir(exist_ok=True)
        (fam_dir / f"{name}.yaml").write_text(content)
    return root


def test_clean_library_produces_no_errors(tmp_path):
    root = _write_library(
        tmp_path,
        facets=[("history", "foo", _BASE_FACET.format(id="history.foo"))],
    )
    findings = run_all(root)
    errors = [f for f in findings if f.severity == "error"]
    assert errors == []


def test_duplicate_id_is_error(tmp_path):
    dup = _BASE_FACET.format(id="history.foo")
    root = _write_library(
        tmp_path,
        facets=[
            ("history", "foo", dup),
            ("history", "foo_copy", dup),  # same id, different filename
        ],
    )
    findings = run_all(root)
    assert any(f.rule == "structural.duplicate_id" for f in findings)


def test_filename_must_match_id(tmp_path):
    root = _write_library(
        tmp_path,
        facets=[("history", "wrong_name", _BASE_FACET.format(id="history.foo"))],
    )
    findings = run_all(root)
    assert any(
        f.rule == "structural.filename_matches_id" and f.severity == "error"
        for f in findings
    )


def test_unknown_family_in_id_is_error(tmp_path):
    root = _write_library(
        tmp_path,
        families=("entity",),
        facets=[("history", "foo", _BASE_FACET.format(id="history.foo"))],
    )
    findings = run_all(root)
    assert any(f.rule == "enumeration.family_in_id" for f in findings)


def test_rating_must_include_unknown(tmp_path):
    bad = _BASE_FACET.format(id="history.foo").replace(
        "allowed_values: [full, none, unknown]",
        "allowed_values: [full, none]",
    )
    root = _write_library(
        tmp_path,
        facets=[("history", "foo", bad)],
    )
    findings = run_all(root)
    assert any(
        f.rule == "enumeration.rating_allowed_values"
        and "unknown" in f.message
        for f in findings
    )


def test_prerequisite_cycle_detected(tmp_path):
    a = _BASE_FACET.format(id="history.a") + "prerequisites: [history.b]\n"
    b = _BASE_FACET.format(id="history.b") + "prerequisites: [history.a]\n"
    root = _write_library(
        tmp_path,
        facets=[("history", "a", a), ("history", "b", b)],
    )
    findings = run_all(root)
    assert any(f.rule == "cross_ref.prerequisites_acyclic" for f in findings)


def test_missing_crm_dim_tag_is_error(tmp_path):
    bad = _BASE_FACET.format(id="history.foo").replace(
        "  - crm-dim:entity\n", ""
    )
    root = _write_library(
        tmp_path,
        facets=[("history", "foo", bad)],
    )
    findings = run_all(root)
    assert any(
        f.rule == "conventions.required_tag_kinds" and "crm-dim" in f.message
        for f in findings
    )
