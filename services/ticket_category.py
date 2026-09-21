"""Neural-network based NLP classifier for SmartCompany ticket categories.

The classifier uses TF-IDF text features followed by an MLP neural network.
The seed examples are intentionally small and should be replaced/expanded
with reviewed company ticket labels as real data becomes available.
"""

from functools import lru_cache

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline


TRAINING_EXAMPLES = [
    ("laptop not connecting to wifi", "it"),
    ("cannot login to company email", "it"),
    ("vpn is not working", "it"),
    ("software installation failed", "it"),
    ("server error on dashboard", "it"),
    ("password reset and account locked", "it"),
    ("leave request and holiday policy", "hr"),
    ("salary slip is missing", "hr"),
    ("employee attendance correction", "hr"),
    ("new employee onboarding issue", "hr"),
    ("benefits and payroll question", "hr"),
    ("performance review process", "hr"),
    ("invoice payment is pending", "finance"),
    ("expense reimbursement issue", "finance"),
    ("budget approval request", "finance"),
    ("customer payment failed", "finance"),
    ("billing amount is incorrect", "finance"),
    ("purchase order finance question", "finance"),
    ("office chair is broken", "facilities"),
    ("air conditioning is not working", "facilities"),
    ("meeting room needs repair", "facilities"),
    ("office access card is not working", "facilities"),
    ("cleaning request for office floor", "facilities"),
    ("general company information request", "general"),
    ("need help with company process", "general"),
    ("suggestion for improving workflow", "general"),
    ("question about internal process", "general"),
    ("company announcement information", "general"),
]


@lru_cache(maxsize=1)
def _model():
    texts, labels = zip(*TRAINING_EXAMPLES)
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), lowercase=True, sublinear_tf=True)),
        ("classifier", MLPClassifier(
            hidden_layer_sizes=(32, 16),
            activation="relu",
            solver="lbfgs",
            max_iter=1000,
            random_state=42,
        )),
    ])
    pipeline.fit(texts, labels)
    return pipeline


def predict_category(subject, description=None):
    text = " ".join(
        part.strip()
        for part in (subject or "", description or "")
        if part and part.strip()
    )

    if not text:
        return {"category": "general", "confidence": 0.0, "source": "fallback"}

    model = _model()
    probabilities = model.predict_proba([text])[0]
    best_index = int(probabilities.argmax())

    return {
        "category": str(model.classes_[best_index]),
        "confidence": round(float(probabilities[best_index]), 4),
        "source": "neural_nlp",
    }
