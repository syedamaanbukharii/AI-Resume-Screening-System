"""Deterministic normalization of extracted profile data."""

from __future__ import annotations

import re

from backend.resume.schemas import CandidateProfile

# Canonical forms for common skill aliases. Extend as taxonomy grows.
_SKILL_ALIASES: dict[str, str] = {
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "postgres": "postgresql",
    "postgre": "postgresql",
    "k8s": "kubernetes",
    "node": "node.js",
    "nodejs": "node.js",
    "reactjs": "react",
    "tf": "tensorflow",
    "sklearn": "scikit-learn",
    "ml": "machine learning",
    "nlp": "natural language processing",
    "gcp": "google cloud platform",
}

_DEGREE_ALIASES: dict[str, str] = {
    "b.tech": "bachelor of technology",
    "btech": "bachelor of technology",
    "b.e": "bachelor of engineering",
    "be": "bachelor of engineering",
    "b.sc": "bachelor of science",
    "bsc": "bachelor of science",
    "m.tech": "master of technology",
    "mtech": "master of technology",
    "m.sc": "master of science",
    "msc": "master of science",
    "mba": "master of business administration",
    "phd": "doctor of philosophy",
}


def _normalize_skill(skill: str) -> str:
    """Lowercase, trim, and canonicalize a single skill token."""
    cleaned = skill.strip().lower()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return _SKILL_ALIASES.get(cleaned, cleaned)


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    """Deduplicate a list case-insensitively, preserving first occurrence."""
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = item.lower()
        if key and key not in seen:
            seen.add(key)
            out.append(item)
    return out


def _normalize_degree(degree: str) -> str:
    """Canonicalize a degree string against known aliases."""
    cleaned = degree.strip().lower().replace(".", "").replace(" ", "")
    for alias, canonical in _DEGREE_ALIASES.items():
        alias_key = alias.replace(".", "").replace(" ", "")
        if cleaned.startswith(alias_key):
            return canonical
    return degree.strip()


def normalize_profile(profile: CandidateProfile) -> CandidateProfile:
    """Return a normalized copy of a CandidateProfile.

    Normalizes and deduplicates skill lists and canonicalizes degree names.
    Pure and deterministic — no LLM involvement.
    """
    data = profile.model_copy(deep=True)

    data.technical_skills = _dedupe_preserve_order(
        [_normalize_skill(s) for s in data.technical_skills]
    )
    data.tools_and_frameworks = _dedupe_preserve_order(
        [_normalize_skill(s) for s in data.tools_and_frameworks]
    )
    data.soft_skills = _dedupe_preserve_order([s.strip().lower() for s in data.soft_skills])
    data.certifications = _dedupe_preserve_order([c.strip() for c in data.certifications])

    for edu in data.education:
        edu.degree = _normalize_degree(edu.degree)

    for exp in data.experience:
        exp.technologies = _dedupe_preserve_order(
            [_normalize_skill(t) for t in exp.technologies]
        )

    return data
