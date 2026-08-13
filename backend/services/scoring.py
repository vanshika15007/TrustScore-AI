from services.scraper import ScrapedContent
from services.sentiment import analyze_chunks

FAKE_KEYWORDS = {
    "scam",
    "fake",
    "fraud",
    "duplicate",
    "counterfeit",
    "phishing",
    "warning",
    "complaint",
    "chargeback",
    "suspicious",
    "refund scam",
    "not genuine",
}

POSITIVE_KEYWORDS = {
    "official",
    "secure checkout",
    "encrypted",
    "privacy policy",
    "customer support",
    "verified",
    "authentic",
    "money back",
    "contact us",
    "refund policy",
}

SECURITY_HEADERS = {
    "strict-transport-security": 7,
    "content-security-policy": 5,
    "x-frame-options": 3,
    "x-content-type-options": 3,
    "referrer-policy": 2,
}


def _keyword_analysis(text: str) -> dict[str, object]:
    lowered = text.lower()
    fake_hits = sorted(keyword for keyword in FAKE_KEYWORDS if keyword in lowered)
    positive_hits = sorted(keyword for keyword in POSITIVE_KEYWORDS if keyword in lowered)

    score = 55 + len(positive_hits) * 6 - len(fake_hits) * 12
    score = max(0, min(100, score))

    reasons = []
    if positive_hits:
        reasons.append(f"Positive trust keywords found: {', '.join(positive_hits[:4])}")
    if fake_hits:
        reasons.append(f"Risk keywords detected: {', '.join(fake_hits[:4])}")
    if not reasons:
        reasons.append("Keyword scan found mixed or limited trust signals")

    return {
        "score": score,
        "fake_hits": fake_hits,
        "positive_hits": positive_hits,
        "reasons": reasons,
    }


def _security_analysis(url: str, headers: dict[str, str]) -> dict[str, object]:
    score = 40
    reasons = []

    if url.startswith("https://"):
        score += 25
        reasons.append("Website uses HTTPS")
    else:
        reasons.append("Website is missing HTTPS")

    present_headers = []
    missing_headers = []

    for header, points in SECURITY_HEADERS.items():
        if header in headers:
            score += points
            present_headers.append(header)
        else:
            missing_headers.append(header)

    score = max(0, min(100, score))

    if present_headers:
        reasons.append(f"Security headers present: {', '.join(present_headers[:3])}")
    if missing_headers:
        reasons.append(f"Some security headers are missing: {', '.join(missing_headers[:3])}")

    return {
        "score": score,
        "present_headers": present_headers,
        "missing_headers": missing_headers,
        "reasons": reasons,
    }


def _sentiment_reasons(score: float, model_used: str) -> list[str]:
    if score >= 70:
        tone = "Page language looks mostly trustworthy"
    elif score >= 45:
        tone = "Page language is mixed with both good and risky signals"
    else:
        tone = "Page language looks suspicious or negative"

    return [f"{tone} ({model_used})"]


def build_analysis_response(url: str, scraped: ScrapedContent) -> dict[str, object]:
    sentiment = analyze_chunks(scraped.chunks)
    keywords = _keyword_analysis(scraped.text)
    security = _security_analysis(scraped.final_url, scraped.headers)

    trust_score = round(
        sentiment["sentiment_score"] * 0.55
        + keywords["score"] * 0.25
        + security["score"] * 0.20,
        2,
    )
    trust_score = max(0, min(100, trust_score))
    real_percentage = round(trust_score, 2)
    fake_percentage = round(100 - trust_score, 2)

    reasons = []
    reasons.extend(_sentiment_reasons(sentiment["sentiment_score"], sentiment["model_used"]))
    reasons.extend(keywords["reasons"])
    reasons.extend(security["reasons"])

    if trust_score >= 75:
        verdict = "trusted"
    elif trust_score >= 45:
        verdict = "moderate"
    else:
        verdict = "risky"

    return {
        "url": scraped.final_url,
        "trust_score": trust_score,
        "real_percentage": real_percentage,
        "fake_percentage": fake_percentage,
        "verdict": verdict,
        "reasons": reasons[:6],
        "sentiment_score": round(sentiment["sentiment_score"], 2),
        "keyword_score": round(keywords["score"], 2),
        "security_score": round(security["score"], 2),
        "confidence": sentiment["confidence"],
        "analysis_method": sentiment["model_used"],
        "sample_sentences": scraped.sample_sentences,
        "chunk_count": len(scraped.chunks),
        "chunks": sentiment["chunks"],
        "security_headers_present": security["present_headers"],
        "security_headers_missing": security["missing_headers"],
    }
