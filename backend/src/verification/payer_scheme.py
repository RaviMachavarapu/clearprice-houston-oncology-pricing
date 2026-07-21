from __future__ import annotations

import re

from src.ingestion.charge_record import PayerRate


def _scan_substring(raw_mrf_text: str, payer_name: str, plan_name: str) -> bool:
    """Pass 1: literal case-insensitive substring scan of the raw MRF text."""
    text = raw_mrf_text.lower()
    return payer_name.lower() in text and plan_name.lower() in text


def _scan_word_boundary(raw_mrf_text: str, payer_name: str, plan_name: str) -> bool:
    """Pass 2: tokenizes the raw MRF text on non-alphanumeric boundaries and
    requires every word of the payer/plan name to appear as its own token,
    catching false positives the substring scan would miss (e.g. a payer name
    that is merely a substring of an unrelated longer word).
    """
    tokens = set(re.findall(r"[a-z0-9]+", raw_mrf_text.lower()))

    def _words_present(name: str) -> bool:
        words = re.findall(r"[a-z0-9]+", name.lower())
        return bool(words) and all(word in tokens for word in words)

    return _words_present(payer_name) and _words_present(plan_name)


def verify_payer_rates(payer_rates: list[PayerRate], raw_mrf_text: str) -> list[PayerRate]:
    """Two independent passes over the hospital's own raw MRF text confirming each
    named payer/plan row before it can be marked verified (Constitution Principle II).

    The two passes use different matching algorithms (literal substring vs.
    tokenized word-boundary matching) so they can genuinely disagree — e.g. a
    payer name that is a substring of an unrelated longer word passes the
    substring scan but fails the word-boundary scan.
    """
    for rate in payer_rates:
        pass_one = _scan_substring(raw_mrf_text, rate.payer_name, rate.plan_name)
        pass_two = _scan_word_boundary(raw_mrf_text, rate.payer_name, rate.plan_name)
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
