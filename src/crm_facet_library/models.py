"""Pydantic models for the facet library.

Reference: PRD 02 — Facet Library Schema & Conventions.
"""
from __future__ import annotations

import re
from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

AppliesTo = Literal["entity", "process", "persona", "cross-cutting"]
FacetStatus = Literal["active", "deprecated", "draft"]
AnswerSchemaType = Literal["rating", "boolean", "scalar", "structured"]

_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*){1,4}$")
_TAG_PATTERN = re.compile(r"^[a-z][a-z0-9-]*:[a-z0-9][a-z0-9_.-]*$")
_SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+(?:[-+].+)?$")


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AnswerSchemaField(_StrictModel):
    """One leaf field inside a ``structured`` answer schema. Per PRD 02
    §11 FQ-1, only one level of nesting is supported in V0.1 — a
    structured field cannot itself be structured.
    """

    type: Literal["rating", "boolean", "scalar"]
    allowed_values: list[Any] | None = None
    scoring_hints: dict[str, str] | None = None
    unit: str | None = None
    min: float | int | None = None
    max: float | int | None = None
    typical_range: list[Any] | None = None
    allowed_special: list[Any] | None = None


class AnswerSchema(_StrictModel):
    type: AnswerSchemaType
    allowed_values: list[Any] | None = None
    scoring_hints: dict[str, str] | None = None
    unit: str | None = None
    min: float | int | None = None
    max: float | int | None = None
    typical_range: list[Any] | None = None
    allowed_special: list[Any] | None = None
    fields: dict[str, AnswerSchemaField] | None = None


class Example(_StrictModel):
    requirement: str
    expected_answer: Any
    commentary: str | None = None


class SourceHints(_StrictModel):
    corpus_refs: list[str] = Field(default_factory=list)
    standards_refs: list[str] = Field(default_factory=list)


class Facet(_StrictModel):
    """One facet entry. Matches the schema in PRD 02 §2.1."""

    id: str
    version: str
    status: FacetStatus
    name: str
    description: str
    question: str
    answer_schema: AnswerSchema
    applies_to: list[AppliesTo]

    tags: list[str] = Field(default_factory=list)
    examples: list[Example] = Field(default_factory=list)

    related_facets: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)
    supersedes: list[str] = Field(default_factory=list)
    superseded_by: str | None = None

    source_hints: SourceHints = Field(default_factory=SourceHints)

    created: date | None = None
    modified: date | None = None
    author: str | None = None
    reviewer: str | None = None

    @field_validator("id")
    @classmethod
    def _valid_id(cls, v: str) -> str:
        if not _ID_PATTERN.match(v):
            raise ValueError(
                f"id {v!r} does not match <family>.<...>.<leaf> with 2–5 "
                f"lowercase segments matching [a-z][a-z0-9_]*"
            )
        return v

    @field_validator("version")
    @classmethod
    def _valid_version(cls, v: str) -> str:
        if not _SEMVER_PATTERN.match(v):
            raise ValueError(f"version {v!r} is not semver")
        return v

    @field_validator("tags")
    @classmethod
    def _valid_tags(cls, tags: list[str]) -> list[str]:
        for tag in tags:
            if not _TAG_PATTERN.match(tag):
                raise ValueError(f"tag {tag!r} is not of form <namespace>:<value>")
        return tags

    @property
    def family(self) -> str:
        return self.id.split(".", 1)[0]


class LibraryMeta(_StrictModel):
    """Contents of LIBRARY.yaml."""

    library_version: str
    schema_version: int
    rating_vocabulary: list[str]
    families: list[str]
    tag_namespaces: list[str]
    applies_to_values: list[str]
    status_values: list[str]
    answer_schema_types: list[str]

    @field_validator("library_version")
    @classmethod
    def _valid_library_version(cls, v: str) -> str:
        if not _SEMVER_PATTERN.match(v):
            raise ValueError(f"library_version {v!r} is not semver")
        return v


class Library(_StrictModel):
    """Materialized in-memory library. Returned by :func:`load_library`."""

    meta: LibraryMeta
    facets: dict[str, Facet]

    @property
    def version(self) -> str:
        return self.meta.library_version

    def get(self, facet_id: str) -> Facet:
        return self.facets[facet_id]

    def __iter__(self):  # type: ignore[override]
        return iter(self.facets.values())

    def __len__(self) -> int:
        return len(self.facets)


class LibraryVersion(_StrictModel):
    """Thin value wrapper — kept as a distinct name per the API in PRD 04 §2.4."""

    version: str
    schema_version: int
