import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import pickle

# Sample dataset (replace with Kaggle later)
data = {
    "review": [
        "This product is amazing",
        "Worst product ever",
        "Loved it so much",
        "Fake fake fake product",
        "Highly recommended",
        "Do not buy this",
        "Excellent quality",
        "Terrible experience"
    ],
    "label": [1, 0, 1, 0, 1, 0, 1, 0]  # 1 = real, 0 = fake
}

df = pd.DataFrame(data)

# Convert text to vectors
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(df["review"])

# Train model
model = LogisticRegression()
model.fit(X, df["label"])

# Save model
pickle.dump(model, open("ml_models/model.pkl", "wb"))
pickle.dump(vectorizer, open("ml_models/vectorizer.pkl", "wb"))

print("Model trained and saved!")