"""Skill matching: blended lexical (exact) + semantic, each with evidence.

Design: exact lexical matches are high-precision and count fully; semantic-only
matches are high-recall and count at a discount. This resolves the lexical-vs-
semantic tension inside the sub-score rather than via a global weight tilt —
the disagreement becomes typed evidence, not a hidden bias.
"""

from __future__ import annotations

from backend.embeddings.base import BaseEmbedder
from backend.matching.schemas import SkillMatchEvidence, SkillScore

# A semantic match must clear this cosine similarity to count.
SEMANTIC_THRESHOLD = 0.72
# Semantic-only matches contribute at this fraction of an exact match.
SEMANTIC_DISCOUNT = 0.7
# Preferred skills count at this fraction of required skills.
PREFERRED_WEIGHT = 0.5


def _norm(skill: str) -> str:
    """Normalize a skill token for lexical comparison."""
    return skill.strip().lower()


def _cosine(a: list[float], b: list[float]) -> float:
    """Cosine similarity of two equal-length vectors (no numpy dependency)."""
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = sum(x * x for x in a) ** 0.5 or 1.0
    nb = sum(y * y for y in b) ** 0.5 or 1.0
    return dot / (na * nb)


async def score_skills(
    *,
    candidate_skills: list[str],
    required_skills: list[str],
    preferred_skills: list[str],
    embedder: BaseEmbedder | None = None,
) -> SkillScore:
    """Score candidate skills against a JD's required + preferred skills.

    Exact matches are found lexically first. Remaining unmatched JD skills are
    matched semantically (if an embedder is provided) against candidate skills,
    counting at a discount. Score is weighted coverage of JD skills, normalized
    to [0, 1]. Required skills weight 1.0; preferred weight PREFERRED_WEIGHT.

    Args:
        candidate_skills: Normalized candidate skill list.
        required_skills: JD required skills.
        preferred_skills: JD preferred skills.
        embedder: Optional embedder for semantic fallback matching.

    Returns:
        A SkillScore with score in [0, 1] and full evidence.
    """
    cand_set = {_norm(s) for s in candidate_skills if s.strip()}

    jd_skills: list[tuple[str, float]] = [(_norm(s), 1.0) for s in required_skills if s.strip()]
    jd_skills += [(_norm(s), PREFERRED_WEIGHT) for s in preferred_skills if s.strip()]
    if not jd_skills:
        return SkillScore(score=1.0, rationale="No skills specified on the job.")

    total_weight = sum(w for _, w in jd_skills)
    achieved = 0.0
    exact: list[SkillMatchEvidence] = []
    semantic: list[SkillMatchEvidence] = []
    missing_required: list[str] = []

    unmatched: list[tuple[str, float]] = []
    for skill, weight in jd_skills:
        if skill in cand_set:
            achieved += weight
            exact.append(SkillMatchEvidence(skill=skill, match_type="exact", weight=weight))
        else:
            unmatched.append((skill, weight))

    # Semantic fallback for unmatched JD skills.
    if unmatched and embedder is not None and cand_set:
        cand_list = sorted(cand_set)
        cand_vecs = await embedder.embed_batch(cand_list)
        jd_vecs = await embedder.embed_batch([s for s, _ in unmatched])
        for (skill, weight), jd_vec in zip(unmatched, jd_vecs, strict=True):
            best_sim = 0.0
            for cvec in cand_vecs:
                sim = _cosine(jd_vec, cvec)
                if sim > best_sim:
                    best_sim = sim
            if best_sim >= SEMANTIC_THRESHOLD:
                achieved += weight * SEMANTIC_DISCOUNT
                semantic.append(
                    SkillMatchEvidence(
                        skill=skill,
                        match_type="semantic",
                        similarity=round(best_sim, 4),
                        weight=weight,
                    )
                )
            elif weight >= 1.0:
                missing_required.append(skill)
    else:
        missing_required = [s for s, w in unmatched if w >= 1.0]

    score = min(achieved / total_weight, 1.0) if total_weight else 1.0
    rationale = (
        f"{len(exact)} exact and {len(semantic)} semantic matches "
        f"across {len(jd_skills)} JD skills; "
        f"{len(missing_required)} required skill(s) unmet."
    )
    return SkillScore(
        score=round(score, 4),
        matched_exact=exact,
        matched_semantic=semantic,
        missing_required=missing_required,
        rationale=rationale,
    )
