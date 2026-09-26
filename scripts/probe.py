"""probe.py: check that a cited page actually says what a record claims.

A live `source_url` only proves the link works (CLAUDE.md, v1.19 lesson). This
fetches the page the way a browser would, strips it to text, and looks for the
exact phrase the record relies on. It is the cheapest reviewer this project
has: the 2026-09-22 pass spot-checked 21 agent findings with it in minutes.

    python3 scripts/probe.py URL "phrase one" "phrase two"   # show each phrase in context
    python3 scripts/probe.py URL --text [N]                  # dump the first N chars of page text
    python3 scripts/probe.py --evidence FILE.jsonl           # gate: check every evidence line

Evidence lines are JSON objects with at least `id`, `action`, `source_url` and
`verbatim` (the page's own sentences that support the change). `--evidence`
prints HIT / MISS / BLOCKED per line and exits 1 if any line is a MISS. A MISS
means one of three things: a clause of the quote is not on the page; the row
changed data (any action except no_change / held / not_found) but has no
source_url; or it has no quote to check. That is the case to act on. BLOCKED
means the site refuses scripted fetches (403, bot wall, timeout). Blocked
lines need a manual or WebFetch re-read, and the run report should say so.

Matching normalizes curly quotes, dashes, non-breaking spaces and whitespace
on both sides, so a curly apostrophe on the page still matches a straight one
in the evidence. PDFs get a best-effort text pull (Flate streams, Tj/TJ
operators): enough to confirm a date or docket number, not to read layout.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
import zlib
from pathlib import Path

import requests

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0 Safari/537.36"
)
NORMALIZE = {
    "’": "'", "‘": "'", "“": '"', "”": '"',
    "–": "-", "—": "-", "\xa0": " ", " ": " ", "​": "",
}
BLOCKED_STATUSES = {401, 403, 406, 429, 451, 503}
MIN_TEXT = 400  # a bot-wall interstitial is short; real article text is not


def norm(s: str) -> str:
    for a, b in NORMALIZE.items():
        s = s.replace(a, b)
    s = re.sub(r"\s+", " ", s)
    # Page layout leaves spaces the prose never had: "News , the" from an
    # inline link, "1 - cent" from PDF text runs. Collapse them on both sides.
    s = re.sub(r" ([,.;:!?)])", r"\1", s)
    s = re.sub(r" ?- ?", "-", s)
    return s.strip()


def html_text(raw: str) -> str:
    raw = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", raw)
    raw = re.sub(r"(?s)<[^>]+>", " ", raw)
    return norm(html.unescape(raw))


def pdf_text(data: bytes) -> str:
    out = []
    for m in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", data, re.S):
        chunk = m.group(1)
        try:
            chunk = zlib.decompress(chunk)
        except zlib.error:
            pass
        for t in re.finditer(rb"\((.*?)(?<!\\)\)\s*Tj|\[(.*?)\]\s*TJ", chunk, re.S):
            if t.group(1) is not None:
                out.append(t.group(1))
            else:
                out.append(b"".join(re.findall(rb"\((.*?)(?<!\\)\)", t.group(2), re.S)))
            out.append(b" ")
    text = b"".join(out).decode("latin-1", "ignore")
    return norm(text.replace("\\(", "(").replace("\\)", ")"))


def fetch(url: str) -> tuple[int, str, str]:
    """Return (status, final_url, text). Status 0 means the fetch itself failed."""
    try:
        r = requests.get(
            url,
            headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"},
            timeout=40,
            allow_redirects=True,
        )
    except requests.RequestException as exc:
        return 0, url, f"FETCH-ERROR: {exc}"
    is_pdf = "pdf" in r.headers.get("content-type", "") or r.content[:5] == b"%PDF-"
    return r.status_code, r.url, pdf_text(r.content) if is_pdf else html_text(r.text)


def find(text: str, phrase: str) -> list[int]:
    return [m.start() for m in re.finditer(re.escape(norm(phrase).lower()), text.lower())]


SKIP_ACTIONS = ("no_change", "held", "not_found")
MIN_CLAUSE = 12  # shorter pieces ("Aug.", "No. 5") carry no checkable fact on their own


def clauses(quote: str) -> list[str]:
    """The pieces of a quote that must each appear on the page: its sentences,
    and any passages an ellipsis joins. Every piece is checked, not just the
    longest. A page that holds the first sentence but contradicts the second
    must not pass (Codex review, PR #49)."""
    parts = re.split(r"(?<=[.;:!?])\s+|…|\.\.\.", norm(quote))
    # Quoting the front of a sentence and closing it with a period is normal
    # ("…applications Tuesday." for "…applications Tuesday, opting…"), so a
    # piece's trailing punctuation is not part of what must match. Every word is.
    pieces = [part.strip(" \"'").rstrip(".;:!?,").strip() for part in parts]
    return [piece for piece in pieces if len(piece) >= MIN_CLAUSE]


def check_evidence(path: Path, delay: float) -> int:
    """Exit 1 if any changed row fails. A row that changed data (any action but
    no_change / held / not_found) must carry `source_url` and `verbatim`, and
    every clause of the quote must be on the page. Skipping a malformed row
    would let an unsupported change through the gate (Codex review, PR #49)."""
    lines = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    cache: dict[str, tuple[int, str, str]] = {}
    misses = blocked = hits = skipped = 0
    for rec in lines:
        url, quote = rec.get("source_url"), (rec.get("verbatim") or "").strip()
        rid = rec.get("id", "?")
        if rec.get("action") in SKIP_ACTIONS:
            skipped += 1
            continue
        pieces = clauses(quote)
        if not url or not pieces:
            misses += 1
            what = "no source_url" if not url else "no verbatim quote long enough to check"
            print(f"MISS    {rid}: changed row ({rec.get('action') or 'no action'}) has {what}")
            continue
        if url not in cache:
            if cache:
                time.sleep(delay)  # CLAUDE.md: be polite to any single host
            cache[url] = fetch(url)
        status, _, text = cache[url]
        if status in BLOCKED_STATUSES or status == 0 or len(text) < MIN_TEXT:
            blocked += 1
            print(f"BLOCKED {rid}: HTTP {status} {url}")
            continue
        missing = [piece for piece in pieces if not find(text, piece)]
        if missing:
            misses += 1
            print(f"MISS    {rid}: {len(missing)} of {len(pieces)} clause(s) not on {url} "
                  f"(HTTP {status}); first: {missing[0][:90]!r}")
        else:
            hits += 1
            print(f"HIT     {rid} ({len(pieces)} clause(s))")
    print(f"\n{hits} hit, {misses} miss, {blocked} blocked, {skipped} skipped (no change)")
    return 1 if misses else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Check a cited page for the phrase a record relies on.")
    ap.add_argument("url", nargs="?")
    ap.add_argument("phrases", nargs="*")
    ap.add_argument("--text", nargs="?", const=6000, type=int, metavar="N")
    ap.add_argument("--evidence", type=Path, metavar="FILE.jsonl")
    ap.add_argument("--delay", type=float, default=1.5, help="seconds between fetches (default 1.5)")
    args = ap.parse_args(argv)

    if args.evidence:
        return check_evidence(args.evidence, args.delay)
    if not args.url:
        ap.print_help()
        return 2
    status, final, text = fetch(args.url)
    print(f"HTTP {status}  final={final}  chars={len(text)}")
    if args.text:
        print(text[: args.text])
        return 0
    for phrase in args.phrases:
        hits = find(text, phrase)
        if not hits:
            print(f"  MISS  {phrase!r}")
        for h in hits[:3]:
            print(f"  HIT   {phrase!r}: …{text[max(0, h - 200): h + len(phrase) + 200]}…")
    return 0 if status and status < 400 else 1


if __name__ == "__main__":
    sys.exit(main())
