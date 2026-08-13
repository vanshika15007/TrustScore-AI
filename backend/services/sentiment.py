import logging
import os
from functools import lru_cache

logger = logging.getLogger("trustscore.sentiment")

MODEL_NAME = "distilbert-base-uncased-finetuned-sst-2-english"

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")


@lru_cache(maxsize=1)
def _load_pipeline():
    try:
        from transformers import pipeline

        sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model=MODEL_NAME,
            truncation=True,
        )
        logger.info("Loaded BERT sentiment pipeline: %s", MODEL_NAME)
        return sentiment_pipeline
    except Exception as exc:  # pragma: no cover - runtime environment dependent
        logger.warning("Falling back from BERT pipeline: %s", exc)
        return None


def _fallback_sentiment(chunk: str) -> dict[str, float | str]:
    positive_words = {
        "safe",
        "secure",
        "trusted",
        "official",
        "guarantee",
        "support",
        "authentic",
        "verified",
        "protected",
    }
    negative_words = {
        "fake",
        "fraud",
        "scam",
        "risk",
        "stolen",
        "suspicious",
        "duplicate",
        "urgent",
        "warning",
        "unsafe",
    }

    lowered = chunk.lower()
    positive_hits = sum(word in lowered for word in positive_words)
    negative_hits = sum(word in lowered for word in negative_words)

    if negative_hits > positive_hits:
        score = min(0.95, 0.55 + negative_hits * 0.08)
        return {"label": "NEGATIVE", "score": round(score, 2)}

    score = min(0.95, 0.58 + positive_hits * 0.07)
    return {"label": "POSITIVE", "score": round(score, 2)}


def analyze_chunks(chunks: list[str]) -> dict[str, object]:
    model = _load_pipeline()
    chunk_results = []

    if model is not None:
        try:
            raw_results = model(chunks)
            for chunk, result in zip(chunks, raw_results):
                chunk_results.append(
                    {
                        "text": chunk,
                        "label": result["label"],
                        "score": round(float(result["score"]), 4),
                    }
                )
        except Exception as exc:  # pragma: no cover - runtime environment dependent
            logger.warning("BERT inference failed, using fallback sentiment: %s", exc)
            model = None

    if model is None:
        for chunk in chunks:
            result = _fallback_sentiment(chunk)
            chunk_results.append(
                {
                    "text": chunk,
                    "label": result["label"],
                    "score": round(float(result["score"]), 4),
                }
            )

    trust_values = []
    for item in chunk_results:
        if item["label"] == "POSITIVE":
            trust_values.append(item["score"] * 100)
        else:
            trust_values.append((1 - item["score"]) * 100)

    trust_score = round(sum(trust_values) / len(trust_values), 2)
    confidence = round(sum(item["score"] for item in chunk_results) / len(chunk_results), 2)

    return {
        "model_used": "bert" if model is not None else "fallback-lexicon",
        "sentiment_score": trust_score,
        "confidence": confidence,
        "chunks": chunk_results,
    }
