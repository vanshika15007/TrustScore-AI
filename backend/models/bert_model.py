import asyncio
import logging
import os
from functools import lru_cache

logger = logging.getLogger("trustscore.bert")

MODEL_NAME = "distilbert-base-uncased-finetuned-sst-2-english"
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")


@lru_cache(maxsize=1)
def _load_pipeline():
    """Load the BERT sentiment pipeline once for reuse across requests."""
    try:
        from transformers import pipeline

        sentiment_pipeline = pipeline("sentiment-analysis", model=MODEL_NAME, truncation=True)
        logger.info("Loaded BERT sentiment pipeline: %s", MODEL_NAME)
        return sentiment_pipeline
    except Exception as exc:  # pragma: no cover - depends on runtime model availability
        logger.warning("Falling back from BERT model: %s", exc)
        return None


def _fallback_sentiment(text: str) -> dict[str, float | str]:
    positive_words = {"secure", "official", "trusted", "verified", "support", "authentic"}
    negative_words = {"scam", "fraud", "fake", "urgent", "free money", "risk", "guaranteed"}

    lowered = text.lower()
    positive_hits = sum(word in lowered for word in positive_words)
    negative_hits = sum(word in lowered for word in negative_words)

    if negative_hits > positive_hits:
        score = min(0.95, 0.58 + negative_hits * 0.08)
        return {"label": "NEGATIVE", "score": round(score, 4)}

    score = min(0.95, 0.60 + positive_hits * 0.06)
    return {"label": "POSITIVE", "score": round(score, 4)}


async def analyze_chunks(chunks: list[str]) -> dict[str, object]:
    """Run sentiment analysis on extracted content chunks and average the result."""
    model = _load_pipeline()
    chunk_results: list[dict[str, object]] = []

    if model is not None:
        try:
            raw_results = await asyncio.to_thread(model, chunks)
            for chunk, result in zip(chunks, raw_results):
                chunk_results.append(
                    {
                        "text": chunk,
                        "label": result["label"],
                        "score": round(float(result["score"]), 4),
                    }
                )
        except Exception as exc:  # pragma: no cover - runtime safeguard
            logger.warning("BERT inference failed, using fallback sentiment: %s", exc)
            model = None

    if model is None:
        for chunk in chunks:
            result = _fallback_sentiment(chunk)
            chunk_results.append(
                {"text": chunk, "label": result["label"], "score": round(float(result["score"]), 4)}
            )

    sentiment_values = []
    for item in chunk_results:
        if item["label"] == "POSITIVE":
            sentiment_values.append(item["score"])
        else:
            sentiment_values.append(1 - item["score"])

    average_score = round(sum(sentiment_values) / len(sentiment_values), 4) if sentiment_values else 0.5
    confidence = round(sum(item["score"] for item in chunk_results) / len(chunk_results), 4) if chunk_results else 0.5

    return {
        "score": average_score,
        "confidence": confidence,
        "model_used": "bert" if model is not None else "fallback-lexicon",
        "chunks": chunk_results,
    }
