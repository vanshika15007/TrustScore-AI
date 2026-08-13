import requests
from bs4 import BeautifulSoup

def get_reviews(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=5)

        soup = BeautifulSoup(res.text, "html.parser")

        reviews = []

        # Amazon
        if "amazon" in url:
            for r in soup.select(".review-text-content span"):
                text = r.get_text(strip=True)
                if len(text) > 20:
                    reviews.append(text)

        # Flipkart
        elif "flipkart" in url:
            for r in soup.select(".t-ZTKy"):
                text = r.get_text(strip=True)
                if len(text) > 20:
                    reviews.append(text)

        # Generic fallback
        if not reviews:
            texts = soup.get_text().split("\n")
            reviews = [t.strip() for t in texts if len(t.strip()) > 30][:20]

        return reviews[:10]

    except Exception as e:
        print("Scraper error:", e)
        return []