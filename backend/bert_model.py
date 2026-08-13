from transformers import pipeline
import requests
from bs4 import BeautifulSoup

# ✅ Load BERT sentiment model (runs once)
sentiment_pipeline = pipeline(
    "sentiment-analysis",
    model="distilbert-base-uncased-finetuned-sst-2-english"
)


# ---------------- SCRAPE REVIEWS ----------------
def get_reviews(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=5)

        soup = BeautifulSoup(res.text, "html.parser")
        texts = soup.get_text().split("\n")

        # Clean + filter
        reviews = [t.strip() for t in texts if len(t.strip()) > 30][:20]

        if not reviews:
            return ["This product is good", "Bad experience overall"]

        return reviews

    except Exception as e:
        print("Scraping error:", e)
        return ["Good product", "Not worth buying"]


# ---------------- BERT ANALYSIS ----------------
def analyze_reviews(url):
    try:
        reviews = get_reviews(url)

        results = sentiment_pipeline(reviews)

        score = 0

        for r in results:
            if r["label"] == "POSITIVE":
                score += r["score"]
            else:
                score += (1 - r["score"])

        final_score = int((score / len(results)) * 100)

        return final_score

    except Exception as e:
        print("BERT error:", e)
        return 50