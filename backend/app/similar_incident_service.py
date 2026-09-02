from collections.abc import Sequence

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def build_incident_text(
    title: str,
    description: str,
) -> str:
    return f"{title} {description}".strip()


def find_similar_incidents(
    target_title: str,
    target_description: str,
    candidate_incidents: Sequence[object],
    limit: int = 3,
) -> list[tuple[object, float]]:
    if not candidate_incidents:
        return []

    target_text = build_incident_text(
        title=target_title,
        description=target_description,
    )

    candidate_texts = [
        build_incident_text(
            title=str(incident.title),
            description=str(incident.description),
        )
        for incident in candidate_incidents
    ]

    vectorizer = TfidfVectorizer(stop_words="english")
    text_matrix = vectorizer.fit_transform(
        [target_text, *candidate_texts],
    )

    similarity_scores = cosine_similarity(
        text_matrix[0:1],
        text_matrix[1:],
    ).flatten()

    matches = list(
        zip(candidate_incidents, similarity_scores)
    )

    matches.sort(
        key=lambda match: match[1],
        reverse=True,
    )

    return [
        (incident, float(score))
        for incident, score in matches[:limit]
        if score > 0
    ]