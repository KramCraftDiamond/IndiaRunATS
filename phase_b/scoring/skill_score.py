"""Skill relevance scoring and reusable assessment-mismatch detection."""


PROFICIENCY_RANK = {
    "beginner": 1,
    "intermediate": 2,
    "advanced": 3,
    "expert": 4,
}

CORE_SKILLS = {
    "python",
    "embeddings",
    "information retrieval",
    "information retrieval systems",
    "vector search",
    "semantic search",
    "ranking systems",
    "learning to rank",
    "recommendation systems",
    "search infrastructure",
    "search backend",
    "search & discovery",
    "sentence transformers",
}

SUPPORTING_SKILLS = {
    "nlp",
    "natural language processing",
    "llms",
    "rag",
    "fine-tuning llms",
    "lora",
    "qlora",
    "peft",
    "hugging face transformers",
    "pytorch",
    "tensorflow",
    "scikit-learn",
    "machine learning",
    "mlops",
    "model adaptation",
    "feature engineering",
}

VECTOR_INFRA_SKILLS = {
    "vector search",
    "semantic search",
    "search infrastructure",
    "search backend",
    "search & discovery",
    "faiss",
    "milvus",
    "pinecone",
    "qdrant",
    "weaviate",
    "opensearch",
    "elasticsearch",
    "pgvector",
    "bm25",
    "haystack",
}

LOW_SIGNAL_SKILLS = {
    "langchain",
    "llamaindex",
    "prompt engineering",
}


def has_assessment_mismatch(skill, assessment_scores, low_score_threshold=45.0):
    """Return True when self-rating materially exceeds Redrob assessment."""
    name = skill.get("name")
    if not name or not isinstance(assessment_scores, dict):
        return False
    if name not in assessment_scores:
        return False

    proficiency = str(skill.get("proficiency") or "").lower()
    rank = PROFICIENCY_RANK.get(proficiency, 0)
    score = _to_float(assessment_scores.get(name), default=None)
    if score is None:
        return False

    if rank >= PROFICIENCY_RANK["expert"] and score < low_score_threshold:
        return True
    if rank >= PROFICIENCY_RANK["advanced"] and score < 35.0:
        return True
    return False


def score_skills(candidate):
    skills = candidate.get("skills") or []
    signals = candidate.get("redrob_signals") or {}
    assessments = signals.get("skill_assessment_scores") or {}

    matched_core = []
    matched_supporting = []
    matched_vector_infra = []
    matched_low_signal = []
    endorsement_total = 0
    duration_total = 0
    mismatch_skills = []

    for skill in skills:
        name = skill.get("name") or ""
        norm = _normalize(name)
        endorsements = _to_int(skill.get("endorsements"), default=0)
        duration_months = _to_int(skill.get("duration_months"), default=0)
        proficiency = str(skill.get("proficiency") or "").lower()
        proficiency_rank = PROFICIENCY_RANK.get(proficiency, 0)

        endorsement_total += endorsements
        duration_total += duration_months

        trace = {
            "name": name,
            "proficiency": proficiency,
            "endorsements": endorsements,
            "duration_months": duration_months,
        }
        if norm in CORE_SKILLS:
            matched_core.append(trace)
        if norm in SUPPORTING_SKILLS:
            matched_supporting.append(trace)
        if norm in VECTOR_INFRA_SKILLS:
            matched_vector_infra.append(trace)
        if norm in LOW_SIGNAL_SKILLS:
            matched_low_signal.append(trace)
        if has_assessment_mismatch(skill, assessments):
            mismatch_skills.append(
                {
                    "name": name,
                    "proficiency": proficiency,
                    "assessment_score": assessments.get(name),
                }
            )

    core_score = min(1.0, len({item["name"] for item in matched_core}) / 4.0)
    supporting_score = min(1.0, len({item["name"] for item in matched_supporting}) / 5.0)
    vector_score = min(1.0, len({item["name"] for item in matched_vector_infra}) / 3.0)
    assessment_score = _assessment_quality_score(assessments)
    duration_score = min(1.0, duration_total / 360.0)
    endorsement_score = min(1.0, endorsement_total / 250.0)
    low_signal_penalty = min(0.15, 0.04 * len(matched_low_signal))
    mismatch_penalty = min(0.25, 0.06 * len(mismatch_skills))

    score = (
        0.30 * core_score
        + 0.20 * supporting_score
        + 0.20 * vector_score
        + 0.15 * assessment_score
        + 0.10 * duration_score
        + 0.05 * endorsement_score
        - low_signal_penalty
        - mismatch_penalty
    )
    score = _clamp(score, 0.0, 1.0)

    return {
        "skill_score": round(score, 6),
        "core_skill_score": round(core_score, 6),
        "supporting_skill_score": round(supporting_score, 6),
        "vector_infra_score": round(vector_score, 6),
        "assessment_score": round(assessment_score, 6),
        "total_skill_endorsements": endorsement_total,
        "total_skill_duration_months": duration_total,
        "matched_core_skills": matched_core,
        "matched_supporting_skills": matched_supporting,
        "matched_vector_infra_skills": matched_vector_infra,
        "low_signal_skills": matched_low_signal,
        "assessment_mismatch_skills": mismatch_skills,
        "skill_assessment_count": len(assessments),
    }


def _assessment_quality_score(assessments):
    if not assessments:
        return 0.45
    relevant_scores = [
        _to_float(score, default=0.0)
        for name, score in assessments.items()
        if _normalize(name) in CORE_SKILLS
        or _normalize(name) in SUPPORTING_SKILLS
        or _normalize(name) in VECTOR_INFRA_SKILLS
    ]
    if not relevant_scores:
        return 0.5
    return _clamp(sum(relevant_scores) / len(relevant_scores) / 100.0, 0.0, 1.0)


def _normalize(value):
    return " ".join(str(value or "").strip().lower().split())


def _to_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _clamp(value, low, high):
    return max(low, min(high, value))