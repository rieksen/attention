"""
Summarisation and saliency scoring using flan-t5-base.

Saliency approach:
  1. Split input into sentences.
  2. Run T5 with output_attentions=True to get cross-attention weights
     (decoder attending to encoder tokens).
  3. For each encoder token, average attention received across all decoder
     steps and all attention heads → token saliency score.
  4. Map token scores back to sentences by aligning tokenised spans.
  5. Normalise sentence scores to [0, 1].
"""

import re
import numpy as np
import torch
from transformers import T5ForConditionalGeneration, T5Tokenizer

MODEL_NAME = "google/flan-t5-base"

_tokenizer = None
_model = None


def _load():
    global _tokenizer, _model
    if _model is None:
        _tokenizer = T5Tokenizer.from_pretrained(MODEL_NAME)
        _model = T5ForConditionalGeneration.from_pretrained(
            MODEL_NAME, output_attentions=True
        )
        _model.eval()


def split_sentences(text: str) -> list[str]:
    """Simple sentence splitter that preserves structure."""
    text = text.strip()
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def summarise_and_score(text: str) -> dict:
    """
    Returns:
        {
            "summary": str,
            "sentences": [{"index": int, "text": str, "score": float}, ...]
        }
    """
    _load()

    # Truncate to T5's max input (512 tokens)
    prompt = f"summarize: {text}"
    inputs = _tokenizer(
        prompt,
        return_tensors="pt",
        max_length=512,
        truncation=True,
        padding=False,
    )
    input_ids = inputs["input_ids"]         # (1, seq_len)
    input_len = input_ids.shape[1]

    with torch.no_grad():
        outputs = _model.generate(
            input_ids,
            max_new_tokens=150,
            num_beams=4,
            early_stopping=True,
            output_attentions=True,
            return_dict_in_generate=True,
        )

    summary_ids = outputs.sequences[0]
    summary = _tokenizer.decode(summary_ids, skip_special_tokens=True)

    # ── Extract cross-attention weights ──────────────────────────────────────
    # cross_attentions: tuple of decoder steps, each is tuple of layers,
    # each tensor is (batch, heads, 1, encoder_seq_len)
    cross_attentions = outputs.cross_attentions   # may be None if beam search
    token_scores = np.zeros(input_len)

    if cross_attentions is not None:
        for step_attns in cross_attentions:
            # step_attns: tuple over layers
            for layer_attn in step_attns:
                # layer_attn: (batch, heads, 1, enc_len) or (batch*beams, ...)
                attn = layer_attn[0]              # first beam/batch
                attn = attn.mean(dim=0)           # average heads → (1, enc_len)
                attn = attn[0].cpu().numpy()      # (enc_len,)
                # Pad/trim to input_len
                length = min(len(attn), input_len)
                token_scores[:length] += attn[:length]

        # Normalise
        if token_scores.max() > 0:
            token_scores = token_scores / token_scores.max()

    # ── Map token scores to sentences ────────────────────────────────────────
    sentences = split_sentences(text)
    sentence_scores = []

    # Re-tokenise prompt to find character spans per token
    token_offsets = _tokenizer(
        prompt,
        return_offsets_mapping=True,
        max_length=512,
        truncation=True,
    )["offset_mapping"]

    prompt_prefix_len = len("summarize: ")

    for idx, sent in enumerate(sentences):
        # Find where this sentence appears in the original text
        sent_start = text.find(sent)
        sent_end = sent_start + len(sent)

        scores_for_sentence = []
        for tok_idx, (char_start, char_end) in enumerate(token_offsets):
            # Adjust for "summarize: " prefix
            adj_start = char_start - prompt_prefix_len
            adj_end = char_end - prompt_prefix_len
            if adj_end <= sent_start or adj_start >= sent_end:
                continue
            if tok_idx < len(token_scores):
                scores_for_sentence.append(float(token_scores[tok_idx]))

        score = float(np.mean(scores_for_sentence)) if scores_for_sentence else 0.0
        sentence_scores.append({"index": idx, "text": sent, "score": score})

    # Normalise sentence scores to [0, 1]
    raw = [s["score"] for s in sentence_scores]
    if max(raw) > 0:
        mn, mx = min(raw), max(raw)
        for s in sentence_scores:
            s["score"] = round((s["score"] - mn) / (mx - mn + 1e-9), 4) if mx > mn else 0.5
    else:
        for s in sentence_scores:
            s["score"] = 0.5

    return {"summary": summary, "sentences": sentence_scores}
