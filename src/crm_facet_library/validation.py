"""Facet library validator + ``crm-facet-lint`` CLI.

Rules map directly to PRD 02 §8. The validator loads each facet file
individually, accumulating findings rather than aborting on first error.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import os
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Iterator, Literal

from pydantic import ValidationError

from ._yaml import load_yaml
from .loader import _BUNDLED_ROOT, _FACETS_DIR, _LIBRARY_FILE
from .models import Facet, LibraryMeta

Severity = Literal["error", "warning"]


@dataclass
class Finding:
    severity: Severity
    rule: str
    message: str
    facet_id: str | None = None
    path: str | None = None


# --------------------------------------------------------------------------- #
# Rule registry
# --------------------------------------------------------------------------- #

RuleFn = Callable[["ValidationContext"], Iterator[Finding]]
_RULES: list[tuple[str, RuleFn]] = []


def rule(name: str) -> Callable[[RuleFn], RuleFn]:
    def _register(fn: RuleFn) -> RuleFn:
        _RULES.append((name, fn))
        return fn

    return _register


@dataclass
class ValidationContext:
    root: Path
    meta: LibraryMeta
    facets: dict[str, Facet]
    facet_paths: dict[str, Path]


# --------------------------------------------------------------------------- #
# Load with per-file error capture
# --------------------------------------------------------------------------- #


def _load_meta(root: Path) -> tuple[LibraryMeta | None, list[Finding]]:
    meta_path = root / _LIBRARY_FILE
    if not meta_path.is_file():
        return None, [
            Finding("error", "structural.library_file_missing",
                    f"LIBRARY.yaml not found at {meta_path}",
                    path=str(meta_path))
        ]
    try:
        data = load_yaml(meta_path.read_text())
        meta = LibraryMeta.model_validate(data)
    except ValidationError as e:
        return None, [
            Finding("error", "structural.library_schema",
                    f"LIBRARY.yaml failed schema: {e}",
                    path=str(meta_path))
        ]
    except Exception as e:
        return None, [
            Finding("error", "structural.library_parse",
                    f"LIBRARY.yaml failed to parse: {e}",
                    path=str(meta_path))
        ]
    return meta, []


def _load_facets(
    root: Path,
) -> tuple[dict[str, Facet], dict[str, Path], list[Finding]]:
    facets: dict[str, Facet] = {}
    paths: dict[str, Path] = {}
    findings: list[Finding] = []

    facets_dir = root / _FACETS_DIR
    if not facets_dir.is_dir():
        return facets, paths, findings

    for yaml_path in sorted(facets_dir.rglob("*.yaml")):
        rel = yaml_path.relative_to(root)
        try:
            data = load_yaml(yaml_path.read_text())
        except Exception as e:
            findings.append(Finding(
                "error", "structural.yaml_parse",
                f"YAML parse failed: {e}", path=str(rel)))
            continue
        if data is None:
            findings.append(Finding(
                "error", "structural.empty_file",
                "Facet file is empty", path=str(rel)))
            continue
        try:
            facet = Facet.model_validate(data)
        except ValidationError as e:
            findings.append(Finding(
                "error", "structural.schema",
                f"Facet failed schema: {e}",
                facet_id=data.get("id") if isinstance(data, dict) else None,
                path=str(rel)))
            continue
        if facet.id in facets:
            findings.append(Finding(
                "error", "structural.duplicate_id",
                f"Duplicate facet id {facet.id!r} "
                f"(also in {paths[facet.id].relative_to(root)})",
                facet_id=facet.id, path=str(rel)))
            continue
        facets[facet.id] = facet
        paths[facet.id] = yaml_path

    return facets, paths, findings


# --------------------------------------------------------------------------- #
# Rules — PRD 02 §8
# --------------------------------------------------------------------------- #


@rule("structural.filename_matches_id")
def _filename_matches_id(ctx: ValidationContext) -> Iterator[Finding]:
    for facet_id, path in ctx.facet_paths.items():
        family, _, tail = facet_id.partition(".")
        expected_name = f"{tail}.yaml"
        expected_dir = ctx.root / _FACETS_DIR / family
        if path.name != expected_name:
            yield Finding(
                "error", "structural.filename_matches_id",
                f"filename {path.name!r} does not match "
                f"expected {expected_name!r} for id {facet_id!r}",
                facet_id=facet_id, path=str(path.relative_to(ctx.root)))
        if path.parent != expected_dir:
            yield Finding(
                "error", "structural.filename_matches_id",
                f"facet {facet_id!r} should live under "
                f"facets/{family}/, found {path.parent.relative_to(ctx.root)}",
                facet_id=facet_id, path=str(path.relative_to(ctx.root)))


@rule("enumeration.family_in_id")
def _family_in_id(ctx: ValidationContext) -> Iterator[Finding]:
    allowed = set(ctx.meta.families)
    for facet in ctx.facets.values():
        if facet.family not in allowed:
            yield Finding(
                "error", "enumeration.family_in_id",
                f"family {facet.family!r} is not in LIBRARY.yaml families",
                facet_id=facet.id)


@rule("enumeration.tag_namespaces")
def _tag_namespaces(ctx: ValidationContext) -> Iterator[Finding]:
    allowed = set(ctx.meta.tag_namespaces)
    for facet in ctx.facets.values():
        for tag in facet.tags:
            ns, _, _ = tag.partition(":")
            if ns not in allowed:
                yield Finding(
                    "error", "enumeration.tag_namespaces",
                    f"tag namespace {ns!r} (tag {tag!r}) "
                    f"is not in LIBRARY.yaml tag_namespaces",
                    facet_id=facet.id)


@rule("enumeration.family_tag_matches_library")
def _family_tag_matches_library(ctx: ValidationContext) -> Iterator[Finding]:
    allowed = set(ctx.meta.families)
    for facet in ctx.facets.values():
        for tag in facet.tags:
            if not tag.startswith("family:"):
                continue
            value = tag.split(":", 1)[1]
            if value not in allowed:
                yield Finding(
                    "error", "enumeration.family_tag_matches_library",
                    f"family tag value {value!r} is not a declared family",
                    facet_id=facet.id)


@rule("enumeration.rating_allowed_values")
def _rating_allowed_values(ctx: ValidationContext) -> Iterator[Finding]:
    vocab = set(ctx.meta.rating_vocabulary)

    def check(facet_id: str, path: str, values: list | None) -> Iterator[Finding]:
        if not values:
            yield Finding(
                "error", "enumeration.rating_allowed_values",
                f"{path}: rating answer_schema must declare allowed_values",
                facet_id=facet_id)
            return
        for v in values:
            if v not in vocab:
                yield Finding(
                    "error", "enumeration.rating_allowed_values",
                    f"{path}: rating value {v!r} is not in rating_vocabulary",
                    facet_id=facet_id)
        if "unknown" not in values:
            yield Finding(
                "error", "enumeration.rating_allowed_values",
                f"{path}: rating answer_schema must include 'unknown'",
                facet_id=facet_id)

    for facet in ctx.facets.values():
        schema = facet.answer_schema
        if schema.type == "rating":
            yield from check(facet.id, "answer_schema", schema.allowed_values)
        elif schema.type == "structured" and schema.fields:
            for field_name, sub in schema.fields.items():
                if sub.type == "rating":
                    yield from check(
                        facet.id,
                        f"answer_schema.fields.{field_name}",
                        sub.allowed_values,
                    )


@rule("cross_ref.targets_exist")
def _targets_exist(ctx: ValidationContext) -> Iterator[Finding]:
    known = set(ctx.facets)
    for facet in ctx.facets.values():
        for field_name in ("related_facets", "prerequisites", "supersedes"):
            for target in getattr(facet, field_name):
                if target not in known:
                    yield Finding(
                        "error", "cross_ref.targets_exist",
                        f"{field_name}: {target!r} does not exist",
                        facet_id=facet.id)
        if facet.superseded_by and facet.superseded_by not in known:
            yield Finding(
                "error", "cross_ref.targets_exist",
                f"superseded_by: {facet.superseded_by!r} does not exist",
                facet_id=facet.id)


@rule("cross_ref.prerequisites_acyclic")
def _prereq_acyclic(ctx: ValidationContext) -> Iterator[Finding]:
    graph = {f.id: [p for p in f.prerequisites if p in ctx.facets]
             for f in ctx.facets.values()}

    WHITE, GREY, BLACK = 0, 1, 2
    color = {k: WHITE for k in graph}
    reported: set[tuple[str, ...]] = set()

    def dfs(node: str, stack: list[str]) -> None:
        color[node] = GREY
        stack.append(node)
        for nbr in graph.get(node, []):
            if color.get(nbr) == GREY:
                cycle = stack[stack.index(nbr):] + [nbr]
                key = tuple(cycle)
                if key not in reported:
                    reported.add(key)
                    yield_cycle(cycle)
            elif color.get(nbr) == WHITE:
                yield from dfs(nbr, stack)
        stack.pop()
        color[node] = BLACK

    findings: list[Finding] = []

    def yield_cycle(cycle: list[str]) -> None:
        findings.append(Finding(
            "error", "cross_ref.prerequisites_acyclic",
            f"prerequisites cycle: {' -> '.join(cycle)}",
            facet_id=cycle[0]))

    for node in graph:
        if color[node] == WHITE:
            # Exhaust generator so side effects happen
            for _ in dfs(node, []) or ():
                pass

    yield from findings


@rule("cross_ref.deprecated_has_successor")
def _deprecated_has_successor(ctx: ValidationContext) -> Iterator[Finding]:
    for facet in ctx.facets.values():
        if facet.status == "deprecated" and not facet.superseded_by:
            yield Finding(
                "warning", "cross_ref.deprecated_has_successor",
                "deprecated facet has no superseded_by",
                facet_id=facet.id)


@rule("cross_ref.related_symmetric")
def _related_symmetric(ctx: ValidationContext) -> Iterator[Finding]:
    for facet in ctx.facets.values():
        for target in facet.related_facets:
            other = ctx.facets.get(target)
            if other is None:
                continue
            if facet.id not in other.related_facets:
                yield Finding(
                    "warning", "cross_ref.related_symmetric",
                    f"related_facets asymmetric: {facet.id} -> {target} "
                    f"but not reverse",
                    facet_id=facet.id)


@rule("conventions.required_tag_kinds")
def _required_tag_kinds(ctx: ValidationContext) -> Iterator[Finding]:
    for facet in ctx.facets.values():
        has_family = any(t.startswith("family:") for t in facet.tags)
        has_crm_dim = any(t.startswith("crm-dim:") for t in facet.tags)
        if not has_family:
            yield Finding(
                "error", "conventions.required_tag_kinds",
                "facet has no family: tag", facet_id=facet.id)
        if not has_crm_dim:
            yield Finding(
                "error", "conventions.required_tag_kinds",
                "facet has no crm-dim: tag", facet_id=facet.id)


@rule("conventions.length_limits")
def _length_limits(ctx: ValidationContext) -> Iterator[Finding]:
    for facet in ctx.facets.values():
        if len(facet.name) > 60:
            yield Finding(
                "error", "conventions.length_limits",
                f"name is {len(facet.name)} chars (>60)",
                facet_id=facet.id)
        if len(facet.description) > 500:
            yield Finding(
                "error", "conventions.length_limits",
                f"description is {len(facet.description)} chars (>500)",
                facet_id=facet.id)
        if len(facet.question) > 200:
            yield Finding(
                "error", "conventions.length_limits",
                f"question is {len(facet.question)} chars (>200)",
                facet_id=facet.id)


@rule("conventions.tag_value_singletons")
def _tag_value_singletons(ctx: ValidationContext) -> Iterator[Finding]:
    counts: Counter[str] = Counter()
    owners: dict[str, list[str]] = defaultdict(list)
    for facet in ctx.facets.values():
        for tag in facet.tags:
            counts[tag] += 1
            owners[tag].append(facet.id)

    for tag, count in counts.items():
        if count == 1:
            yield Finding(
                "warning", "conventions.tag_value_singletons",
                f"tag {tag!r} appears on only one facet — "
                "possible typo or one-off",
                facet_id=owners[tag][0])


# --------------------------------------------------------------------------- #
# Entry points
# --------------------------------------------------------------------------- #


def run_all(root: str | os.PathLike[str] | None = None) -> list[Finding]:
    """Run every registered rule against the library at ``root``."""

    root_path = Path(root) if root is not None else _BUNDLED_ROOT
    meta, findings = _load_meta(root_path)
    if meta is None:
        return findings

    facets, paths, load_findings = _load_facets(root_path)
    findings.extend(load_findings)

    ctx = ValidationContext(
        root=root_path, meta=meta, facets=facets, facet_paths=paths,
    )
    for _name, fn in _RULES:
        findings.extend(fn(ctx))

    return findings


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def _print_human(findings: Iterable[Finding]) -> None:
    from rich.console import Console
    from rich.table import Table

    findings_list = list(findings)
    errors = [f for f in findings_list if f.severity == "error"]
    warnings = [f for f in findings_list if f.severity == "warning"]

    console = Console()
    err_console = Console(stderr=True)

    if errors:
        t = Table(title=f"{len(errors)} error(s)", show_lines=False,
                  header_style="bold red")
        t.add_column("rule")
        t.add_column("facet / path")
        t.add_column("message")
        for f in errors:
            locus = f.facet_id or f.path or "-"
            t.add_row(f.rule, locus, f.message)
        console.print(t)
    if warnings:
        t = Table(title=f"{len(warnings)} warning(s)", show_lines=False,
                  header_style="bold yellow")
        t.add_column("rule")
        t.add_column("facet / path")
        t.add_column("message")
        for f in warnings:
            locus = f.facet_id or f.path or "-"
            t.add_row(f.rule, locus, f.message)
        err_console.print(t)
    if not findings_list:
        console.print("[bold green]facet library clean[/] — no findings")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="crm-facet-lint",
        description="Validate the CRM facet library against PRD 02 §8.",
    )
    parser.add_argument(
        "root", nargs="?", default=None,
        help="Library root (containing LIBRARY.yaml + facets/). "
             "Defaults to the installed bundled library.",
    )
    parser.add_argument("--json", action="store_true",
                        help="Emit findings as JSON to stdout")
    args = parser.parse_args(argv)

    findings = run_all(args.root)
    error_count = sum(1 for f in findings if f.severity == "error")

    if args.json:
        json.dump([dataclasses.asdict(f) for f in findings],
                  sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        _print_human(findings)

    return 1 if error_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
