from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Dict, List, Tuple


@dataclass
class TopicCluster:
    topic_id: str
    chunk_indices: List[int]
    chunks: List[str]
    top_terms: List[str]


class TopicClusterer:
    """
    Lightweight topic clustering for multi-document summarization.

    Implementation choices:
    - TF-IDF (fast, explainable, offline)
    - KMeans (stable, low compute)
    """

    def __init__(self, max_topics: int = 6):
        self.max_topics = max_topics

    def cluster(self, chunks: List[str]) -> List[TopicCluster]:
        if not chunks:
            return []
        if len(chunks) <= 2:
            return [TopicCluster(topic_id="topic_1", chunk_indices=list(range(len(chunks))), chunks=chunks, top_terms=[])]

        # Local import so the app still runs even if sklearn isn't installed (fallback behavior).
        try:
            from sklearn.cluster import KMeans
            from sklearn.feature_extraction.text import TfidfVectorizer
            import numpy as np
        except Exception:
            # Fallback: everything in one topic
            return [TopicCluster(topic_id="topic_1", chunk_indices=list(range(len(chunks))), chunks=chunks, top_terms=[])]

        n = len(chunks)
        k = min(self.max_topics, max(2, int(round(sqrt(n)))))

        vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            max_features=4000,
        )
        X = vectorizer.fit_transform(chunks)

        # n_init changed across sklearn versions; try modern default, fallback otherwise.
        try:
            km = KMeans(n_clusters=k, random_state=42, n_init="auto")
        except TypeError:
            km = KMeans(n_clusters=k, random_state=42, n_init=10)

        labels = km.fit_predict(X)

        clusters: Dict[int, List[int]] = {}
        for idx, lab in enumerate(labels):
            clusters.setdefault(int(lab), []).append(idx)

        feature_names = vectorizer.get_feature_names_out()
        topics: List[TopicCluster] = []

        for i, indices in sorted(clusters.items(), key=lambda kv: (-len(kv[1]), kv[0])):
            X_sub = X[indices]
            mean_tfidf = np.asarray(X_sub.mean(axis=0)).ravel()
            top_idx = mean_tfidf.argsort()[::-1][:6]
            top_terms = [str(feature_names[j]) for j in top_idx if mean_tfidf[j] > 0][:6]

            topics.append(
                TopicCluster(
                    topic_id=f"topic_{len(topics) + 1}",
                    chunk_indices=indices,
                    chunks=[chunks[j] for j in indices],
                    top_terms=top_terms,
                )
            )

        return topics

