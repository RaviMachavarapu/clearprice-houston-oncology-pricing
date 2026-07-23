from __future__ import annotations

import re

from src.ingestion.charge_record import PayerRate


def verify_payer_rates(payer_rates: list[PayerRate], raw_mrf_text: str) -> list[PayerRate]:
    """Two independent passes over the hospital's own raw MRF text confirming each
    named payer/plan row before it can be marked verified (Constitution Principle II).

    The two passes use different matching algorithms (literal substring vs.
    tokenized word-boundary matching) so they can genuinely disagree — e.g. a
    payer name that is a substring of an unrelated longer word passes the
    substring scan but fails the word-boundary scan.

    The lowercase copy and tokenization of raw_mrf_text are each computed ONCE
    here and reused for every rate, instead of once per rate — for a large MRF
    (hundreds of MB) with many payer columns, redoing a full-text .lower() and
    regex tokenize per rate turned a few-second job into a multi-hour one.

    CMS tall-format files repeat the same handful of payer/plan column names
    across every row, so the (payer_name, plan_name) pair is usually shared by
    thousands of rates. The substring check is cached per unique pair so it
    runs once per distinct name, not once per rate.
    """
    text_lower = raw_mrf_text.lower()
    tokens = set(re.findall(r"[a-z0-9]+", text_lower))

    def _words_present(name: str) -> bool:
        words = re.findall(r"[a-z0-9]+", name.lower())
        return bool(words) and all(word in tokens for word in words)

    cache: dict[tuple[str, str], tuple[bool, bool]] = {}
    for rate in payer_rates:
        key = (rate.payer_name, rate.plan_name)
        result = cache.get(key)
        if result is None:
            pass_one = rate.payer_name.lower() in text_lower and rate.plan_name.lower() in text_lower
            pass_two = _words_present(rate.payer_name) and _words_present(rate.plan_name)
            result = (pass_one, pass_two)
            cache[key] = result
        pass_one, pass_two = result
        rate.verification_checks = [pass_one, pass_two]
        rate.verified = pass_one and pass_two
    return payer_rates


def verify_payer_rates_streaming(
    payer_rates: list[PayerRate],
    file_path: str,
    chunk_size: int = 16 * 1024 * 1024,
) -> list[PayerRate]:
    """Streaming equivalent of verify_payer_rates for MRF files too large to
    hold as a single string in memory. Reads the file once in bounded chunks,
    with a small overlap so a name split across a chunk boundary is still
    found, and accumulates only the (bounded-size) vocabulary of distinct
    tokens/substrings seen — never the file's full text.
    """
    substrings_needed = {rate.payer_name.lower() for rate in payer_rates} | {
        rate.plan_name.lower() for rate in payer_rates
    }
    max_len = max((len(s) for s in substrings_needed), default=0)
    overlap = max(max_len, 1)

    found_substrings: set[str] = set()
    tokens: set[str] = set()

    prev_tail = ""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            combined_lower = (prev_tail + chunk).lower()
            for s in substrings_needed:
                if s and s not in found_substrings and s in combined_lower:
                    found_substrings.add(s)
            tokens.update(re.findall(r"[a-z0-9]+", combined_lower))
            prev_tail = chunk[-overlap:] if len(chunk) > overlap else chunk

    def _words_present(name: str) -> bool:
        words = re.findall(r"[a-z0-9]+", name.lower())
        return bool(words) and all(word in tokens for word in words)

    for rate in payer_rates:
        pass_one = rate.payer_name.lower() in found_substrings and rate.plan_name.lower() in found_substrings
        pass_two = _words_present(rate.payer_name) and _words_present(rate.plan_name)
        rate.verification_checks = [pass_one, pass_two]
        rate.verified = pass_one and pass_two
    return payer_rates
