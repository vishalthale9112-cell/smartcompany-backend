"""Small, deterministic text classifier for ticket priority.

The model is trained in memory from labelled support examples so the project
has a real ML pipeline without shipping a large binary model file. Replace the
seed dataset with reviewed production labels as the application grows.
"""

from functools import lru_cache

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


TRAINING_EXAMPLES = [
    ("production server is down all employees blocked", "critical"),
    ("security breach suspected account data exposed", "critical"),
    ("payroll failed for the entire company", "critical"),
    ("database unavailable business operations stopped", "critical"),
    ("cannot login and urgent client deadline today", "high"),
    ("laptop crashes repeatedly cannot complete work", "high"),
    ("customer payment is failing", "high"),
    ("internet unavailable for our department", "high"),
    ("need software access for my current task", "medium"),
    ("email synchronization is slow", "medium"),
    ("request approval for leave correction", "medium"),
    ("printer is not working on my floor", "medium"),
    ("please update my profile photo", "low"),
    ("suggestion for dashboard color", "low"),
    ("need information about holiday policy", "low"),
    ("minor typo in knowledge article", "low"),
]


@lru_cache(maxsize=1)
def _model():
    texts, labels = zip(*TRAINING_EXAMPLES)
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), lowercase=True)),
        ("classifier", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)),
    ])
    pipeline.fit(texts, labels)
    return pipeline


def predict_priority(subject, description=None):
    text = " ".join(part.strip() for part in (subject or "", description or "") if part and part.strip())
    if not text:
        return {"priority": "medium", "confidence": 0.0, "source": "fallback"}

    model = _model()
    probabilities = model.predict_proba([text])[0]
    best_index = int(probabilities.argmax())
    return {
        "priority": str(model.classes_[best_index]),
        "confidence": round(float(probabilities[best_index]), 4),
        "source": "ml",
    }
