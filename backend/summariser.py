"""
Summarisation via Hugging Face Inference API (facebook/bart-large-cnn).
Saliency computed by sentence-summary word overlap — no local model needed.
"""

import re
import os
import time
import requests
import numpy as np
from typing import List

HF_API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
HF_TOKEN = os.getenv("HF_TOKEN", "")


def _hf_headers():
    return {"Authorization": f"Bearer {HF_TOKEN}"}


def split_sentences(text: str) -> List[str]:
    text = text.strip()
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def _call_hf(text: str, retries: int = 5) -> str:
    """Call HF Inference API, retrying if model is loading."""
    # BART has a 1024 token limit — truncate input
    truncated = text[:3000]
    payload = {
        "inputs": truncated,
        "parameters": {
            "max_length": 150,
            "min_length": 50,
            "do_sample": False,
        }
    }
    for attempt in range(retries):
        resp = requests.post(HF_API_URL, headers=_hf_headers(), json=payload, timeout=60)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list) and data:
                return data[0].get("summary_text", "")
            return ""
        elif resp.status_code == 503:
            # Model is loading — wait and retry
            wait = resp.json().get("estimated_time", 20)
            time.sleep(min(wait, 30))
        else:
            resp.raise_for_status()
    raise RuntimeError("HF Inference API unavailable after retries.")


def _sentence_saliency(sentences: List[str], summary: str) -> List[float]:
    """
    Score each sentence by normalised word overlap with the summary.
    Simple but effective — sentences the model drew from score higher.
    """
    summary_words = set(re.findall(r'\w+', summary.lower()))
    if not summary_words:
        return [0.5] * len(sentences)

    scores = []
    for sent in sentences:
        sent_words = set(re.findall(r'\w+', sent.lower()))
        if not sent_words:
            scores.append(0.0)
            continue
        overlap = len(sent_words & summary_words) / len(sent_words)
        scores.append(overlap)

    # Normalise to [0, 1]
    mn, mx = min(scores), max(scores)
    if mx > mn:
        scores = [(s - mn) / (mx - mn) for s in scores]
    else:
        scores = [0.5] * len(scores)

    return scores


def summarise_and_score(text: str) -> dict:
    """
    Returns:
        {
            "summary": str,
            "sentences": [{"index": int, "text": str, "score": float}, ...]
        }
    """
    summary = _call_hf(text)
    sentences = split_sentences(text)
    scores = _sentence_saliency(sentences, summary)

    return {
        "summary": summary,
        "sentences": [
            {"index": i, "text": s, "score": round(scores[i], 4)}
            for i, s in enumerate(sentences)
        ]
    }
