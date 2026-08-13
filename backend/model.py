# model.py

import pandas as pd
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

# Sample dataset (you can replace with Kaggle dataset later)
data = {
    "review": [
        "Amazing product very good",
        "Worst product ever",
        "Highly recommend this",
        "Fake product do not buy",
        "Excellent quality",
        "Terrible waste of money",
        "Loved it so much",
        "Not worth it totally fake"
    ],
    "label": [0, 1, 0, 1, 0, 1, 0, 1]  # 0 = genuine, 1 = fake
}

df = pd.DataFrame(data)

# Vectorization
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(df["review"])

# Model
model = LogisticRegression()
model.fit(X, df["label"])

# Save model
with open("model.pkl", "wb") as f:
    pickle.dump(model, f)

with open("vectorizer.pkl", "wb") as f:
    pickle.dump(vectorizer, f)

print("✅ Model trained & saved!")