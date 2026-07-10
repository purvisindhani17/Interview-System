"""
Deterministic skill overlap calculation.

Kept LLM-free and reproducible on purpose: the headline match percentage
should not change between runs just because the LLM sampled differently.
Fuzzy matching (via difflib) handles near-matches like "JS" vs "JavaScript"
or "Postgres" vs "PostgreSQL" without needing a hand-maintained synonym list.
"""

import difflib
import re

FUZZY_MATCH_THRESHOLD = 0.82


def _normalize(skill: str) -> str:
    """Lowercase, strip punctuation/whitespace so 'Node.js' ~= 'nodejs' ~= 'node js'."""
    return re.sub(r"[^a-z0-9]", "", skill.lower())


def _is_match(candidate: str, target: str) -> bool:
    """True if two (already-normalized) skill strings should be considered the same skill."""
    if not candidate or not target:
        return False
    if candidate == target:
        return True
    if candidate in target or target in candidate:
        return True
    return difflib.SequenceMatcher(None, candidate, target).ratio() >= FUZZY_MATCH_THRESHOLD


def compute_skill_overlap(
    resume_skills: list[str],
    required_skills: list[str],
    preferred_skills: list[str],
) -> dict:
    """Compare candidate skills against JD required/preferred skills.

    Returns matched/missing lists (original casing preserved for display)
    plus an overall overlap percentage weighted toward required skills
    (required skills count double, since missing a "must-have" matters
    more than missing a "nice-to-have").
    """
    normalized_resume = [_normalize(s) for s in resume_skills]

    def match_against(jd_skill_list: list[str]) -> tuple[list[str], list[str]]:
        matched, missing = [], []
        for jd_skill in jd_skill_list:
            norm_jd = _normalize(jd_skill)
            if any(_is_match(r, norm_jd) for r in normalized_resume):
                matched.append(jd_skill)
            else:
                missing.append(jd_skill)
        return matched, missing

    matched_required, missing_required = match_against(required_skills)
    matched_preferred, missing_preferred = match_against(preferred_skills)

    # Weight required skills 2x preferred skills when computing the overlap percentage.
    total_weight = (len(required_skills) * 2) + len(preferred_skills)
    achieved_weight = (len(matched_required) * 2) + len(matched_preferred)
    overlap_percentage = round((achieved_weight / total_weight) * 100, 1) if total_weight > 0 else 0.0

    return {
        "matched_required": matched_required,
        "missing_required": missing_required,
        "matched_preferred": matched_preferred,
        "missing_preferred": missing_preferred,
        "overlap_percentage": overlap_percentage,
    }
