import pickle

model = pickle.load(open("ml_models/model.pkl", "rb"))
vectorizer = pickle.load(open("ml_models/vectorizer.pkl", "rb"))

def check_reviews(reviews_list):
    X = vectorizer.transform(reviews_list)
    predictions = model.predict(X)

    real = sum(predictions)
    total = len(predictions)

    score = int((real / total) * 100)
    return score