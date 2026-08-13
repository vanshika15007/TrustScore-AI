import os
import pickle

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "ml_models")

model_path = os.path.join(MODEL_DIR, "model.pkl")
vectorizer_path = os.path.join(MODEL_DIR, "vectorizer.pkl")

# Load model safely
if not os.path.exists(model_path):
    raise Exception("❌ model.pkl not found! Run model.py first")

if not os.path.exists(vectorizer_path):
    raise Exception("❌ vectorizer.pkl not found! Run model.py first")

with open(model_path, "rb") as f:
    model = pickle.load(f)

with open(vectorizer_path, "rb") as f:
    vectorizer = pickle.load(f)


def predict_review(text):
    vec = vectorizer.transform([text])
    prob = model.predict_proba(vec)[0][1]
    return prob


def analyze_reviews(reviews):
    if not reviews:
        return 50

    scores = [predict_review(r) for r in reviews]
    avg = sum(scores) / len(scores)

    return int((1 - avg) * 100)