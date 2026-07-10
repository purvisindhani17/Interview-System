"""
Semantic similarity between a resume and a job description using TF-IDF +
cosine similarity (scikit-learn).

This complements skill_matcher.py: exact/fuzzy skill-name matching misses
cases like a candidate's project description demonstrating "built a caching
layer" satisfying a JD's "Redis" requirement without ever saying the word
"Redis". A bag-of-words semantic similarity over the full text catches some
of that signal that literal skill-string matching cannot.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.modules.job_parser.schema import ParsedJobDescription
from app.modules.resume_parser.schema import ParsedResume


def _resume_to_text(resume: ParsedResume) -> str:
    parts = list(resume.skills) + list(resume.technologies)
    parts += [p.description for p in resume.projects if p.description]
    parts += [e.description for e in resume.experience if e.description]
    return " ".join(parts)


def _jd_to_text(jd: ParsedJobDescription) -> str:
    parts = list(jd.required_skills) + list(jd.preferred_skills) + list(jd.technologies)
    parts += list(jd.responsibilities)
    return " ".join(parts)


def compute_semantic_similarity(resume: ParsedResume, jd: ParsedJobDescription) -> float:
    """Return a 0-100 semantic similarity score between resume and JD content."""
    resume_text = _resume_to_text(resume).strip()
    jd_text = _jd_to_text(jd).strip()

    if not resume_text or not jd_text:
        return 0.0

    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform([resume_text, jd_text])
    similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]

    return round(float(similarity) * 100, 1)
