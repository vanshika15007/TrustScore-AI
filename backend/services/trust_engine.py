import logging
import os
import asyncio
from datetime import datetime, timezone
from typing import Any

from models.bert_model import analyze_chunks
from services.scraper import ScrapeResult
from utils.helpers import domain_from_url, spam_ratio, text_length_score

logger = logging.getLogger("trustscore.trust_engine")

SCAM_KEYWORDS = {
    "free money",
    "urgent",
    "act now",
    "guaranteed profit",
    "scam",
    "fraud",
    "fake",
    "winner",
    "claim prize",
    "limited time",
    "instant cash",
    "crypto giveaway",
}


async def _fetch_domain_age_days(domain: str) -> int | None:
    """Fetch domain age from WHOISXML when configured, otherwise return a neutral fallback."""
    api_key = os.getenv("WHOISXML_API_KEY")
    if not api_key:
        return None

    url = "https://www.whoisxmlapi.com/whoisserver/WhoisService"
    params = {"apiKey": api_key, "domainName": domain, "outputFormat": "JSON"}

    try:
        try:
            import httpx

            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                payload = response.json()
        except ModuleNotFoundError:
            import requests

            response = await asyncio.to_thread(requests.get, url, params=params, timeout=10)
            response.raise_for_status()
            payload = response.json()
    except Exception as exc:  # pragma: no cover - network dependent
        logger.warning("WHOIS API lookup failed for %s: %s", domain, exc)
        return None

    created_raw = (
        payload.get("WhoisRecord", {}).get("createdDate")
        or payload.get("WhoisRecord", {}).get("registryData", {}).get("createdDate")
    )
    if not created_raw:
        return None

    try:
        created = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
    except ValueError:
        return None

    return max(0, (datetime.now(timezone.utc) - created).days)


def _keyword_detection(text: str) -> dict[str, Any]:
    lowered = text.lower()
    hits = sorted(keyword for keyword in SCAM_KEYWORDS if keyword in lowered)
    score = max(0.0, min(1.0, 1 - (len(hits) * 0.14)))
    return {"score": round(score, 4), "hits": hits}


def _security_score(url: str, domain_age_days: int | None) -> dict[str, Any]:
    https_enabled = url.startswith("https://")
    score = 0.45 if https_enabled else 0.12
    age_label = "Unknown"

    if domain_age_days is not None:
        if domain_age_days > 365 * 5:
            score += 0.45
            age_label = "Established"
        elif domain_age_days > 365:
            score += 0.28
            age_label = "Mature"
        elif domain_age_days > 90:
            score += 0.16
            age_label = "Recent"
        else:
            score += 0.05
            age_label = "Very new"
    else:
        score += 0.18

    return {
        "score": round(min(score, 1.0), 4),
        "https": https_enabled,
        "domain_age_days": domain_age_days,
        "domain_age_label": age_label,
    }


def _content_quality(text: str) -> dict[str, Any]:
    length_score = text_length_score(len(text))
    spam = spam_ratio(text)
    quality_score = max(0.0, min(1.0, length_score - spam * 0.55))

    if quality_score >= 0.75:
        label = "Good"
    elif quality_score >= 0.45:
        label = "Moderate"
    else:
        label = "Poor"

    return {
        "score": round(quality_score, 4),
        "text_length": len(text),
        "spam_ratio": round(spam, 4),
        "label": label,
    }


def _risk_level(score: float) -> str:
    if score >= 75:
        return "Low"
    if score >= 45:
        return "Medium"
    return "High"


def _summary(
    trust_score: float,
    keyword_hits: list[str],
    security_info: dict[str, Any],
    content_info: dict[str, Any],
    sentiment_score: float,
) -> str:
    tone = (
        "strong trust indicators"
        if trust_score >= 75
        else "mixed trust signals"
        if trust_score >= 45
        else "multiple risk indicators"
    )
    parts = [f"This website shows {tone}."]

    if keyword_hits:
        parts.append(f"Risky phrases detected include {', '.join(keyword_hits[:4])}.")

    if security_info["https"]:
        parts.append("The site is served over HTTPS.")
    else:
        parts.append("The site is not using HTTPS, which weakens trust.")

    if security_info["domain_age_label"] != "Unknown":
        parts.append(f"Domain age looks {security_info['domain_age_label'].lower()}.")

    parts.append(
        f"Content quality appears {content_info['label'].lower()} and the AI sentiment score is {round(sentiment_score * 100)} out of 100."
    )
    return " ".join(parts)


async def build_trust_report(url: str, scrape_result: ScrapeResult) -> dict[str, Any]:
    """Combine sentiment, scam keywords, domain checks, and content quality into one report."""
    sentiment_result = await analyze_chunks(scrape_result.chunks)
    domain_age_days = await _fetch_domain_age_days(domain_from_url(scrape_result.final_url))

    keyword_result = _keyword_detection(scrape_result.visible_text)
    security_result = _security_score(scrape_result.final_url, domain_age_days)
    content_result = _content_quality(scrape_result.visible_text)

    final_score = (
        sentiment_result["score"] * 0.35
        + keyword_result["score"] * 0.25
        + security_result["score"] * 0.20
        + content_result["score"] * 0.20
    ) * 100
    final_score = round(max(0.0, min(final_score, 100.0)), 2)
    risk_level = _risk_level(final_score)

    summary = _summary(
        final_score,
        keyword_result["hits"],
        security_result,
        content_result,
        sentiment_result["score"],
    )

    return {
        "trust_score": final_score,
        "risk_level": risk_level,
        "status": "success",
        "factors": {
            "sentiment": round(sentiment_result["score"], 4),
            "keywords": keyword_result["hits"],
            "security": "HTTPS" if security_result["https"] else "HTTP",
            "content_quality": content_result["label"],
            "domain_age_days": domain_age_days,
            "spam_ratio": content_result["spam_ratio"],
            "text_length": content_result["text_length"],
        },
        "summary": summary,
        "analysis_method": sentiment_result["model_used"],
        "confidence": sentiment_result["confidence"],
        "title": scrape_result.title,
        "description": scrape_result.description,
        "sample_sentences": scrape_result.sample_sentences,
        "chunks": sentiment_result["chunks"],
        "links": {
            "internal": scrape_result.internal_links,
            "external": scrape_result.external_links,
        },
        "meta": {
            "source_url": url,
            "final_url": scrape_result.final_url,
            "blocked": scrape_result.blocked,
        },
    }
