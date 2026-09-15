#!/usr/bin/env python3
"""
Grounded research agent (SerpApi demo).

Ask a question. The agent plans a few searches from different angles,
runs them through SerpApi, and synthesizes an extractive answer with
numbered source citations.

Usage:
    python research.py "What is retrieval-augmented generation?"
    python research.py "Best Python web frameworks" --out report.md

Setup:
    pip install -r requirements.txt
    export SERPAPI_API_KEY="your-key-here"   # free tier at serpapi.com

The synthesis here is intentionally extractive (no LLM call): it quotes
and cites real snippets from real results. That keeps the demo honest
about what is grounded and what is not.
"""

import argparse
import datetime
import os
import sys

from serpapi import Client


# ---------------------------------------------------------------------------
# Planning: turn one question into searches from a few different angles.
# This planner is deliberately simple and transparent. In a bigger agent
# you would swap this for an LLM call; the rest of the pipeline would
# not need to change.
# ---------------------------------------------------------------------------
def plan_searches(question):
    q = question.strip().rstrip("?")
    year = datetime.date.today().year
    return [
        ("direct", q),                 # best-match results for the question
        ("background", q + " explained"),  # explainer-style coverage
        ("recent", f"{q} {year}"),     # recency-biased coverage
    ]


# ---------------------------------------------------------------------------
# Searching: one SerpApi call per planned angle.
# ---------------------------------------------------------------------------
def run_searches(client, planned):
    all_results = []
    first_raw = None
    for angle, query in planned:
        print(f"  [search] ({angle}) {query}", file=sys.stderr)
        results = client.search(q=query, engine="google", num=10)
        if first_raw is None:
            first_raw = results  # keep page 1 for the answer box
        for r in results.get("organic_results", []) or []:
            r["_angle"] = angle  # remember which query surfaced this
            all_results.append(r)
    return all_results, first_raw

def interleave_results(results):
    """Round-robin across search angles so each angle gets represented."""
    if not results:
        return []
    by_angle = {}
    for r in results:
        by_angle.setdefault(r.get("_angle"), []).append(r)
    groups = list(by_angle.values())
    interleaved = []
    for i in range(max(len(g) for g in groups)):
        for g in groups:
            if i < len(g):
                interleaved.append(g[i])
    return interleaved

def dedupe_results(results):
    seen = {}
    for r in results:
        link = r.get("link")
        if link and link not in seen:
            seen[link] = r
    return list(seen.values())


# ---------------------------------------------------------------------------
# Synthesis: build a cited answer from the collected snippets.
# ---------------------------------------------------------------------------
def synthesize(question, results, answer_box=None):
    lines = []
    lines.append(f"# Research: {question}")
    lines.append("")

    if answer_box and answer_box.get("answer"):
        lines.append("## Direct answer")
        lines.append("")
        lines.append(answer_box["answer"].strip())
        lines.append("")

    lines.append("## Key points")
    lines.append("")
    for i, r in enumerate(results[:6], start=1):
        snippet = (r.get("snippet") or "").strip().replace("\n", " ")
        if len(snippet) > 280:
            snippet = snippet[:277] + "..."
        title = (r.get("title") or "").strip()
        lines.append(f"- {snippet} [{i}]")
        lines.append(f"  ({title}, via the '{r.get('_angle')}' search)")
    lines.append("")

    lines.append("## Sources")
    lines.append("")
    for i, r in enumerate(results[:8], start=1):
        title = (r.get("title") or "Untitled").strip()
        lines.append(f"[{i}] {title}")
        lines.append(f"    {r.get('link')}")
        lines.append("")
    lines.append("")

    lines.append(
        "_Answer assembled extractively from live search results. "
        "Every claim above traces to a numbered source._"
    )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Grounded research agent: plan searches, run them via "
                    "SerpApi, synthesize a cited answer."
    )
    parser.add_argument("question", help="The research question to answer.")
    parser.add_argument("--out", help="Write the report to this file as well.")
    args = parser.parse_args()

    api_key = os.environ.get("SERPAPI_API_KEY")
    if not api_key:
        print(
            "Set SERPAPI_API_KEY first:\n"
            '  export SERPAPI_API_KEY="your-key-here"\n'
            "Get a free key at https://serpapi.com (250 free searches).",
            file=sys.stderr,
        )
        sys.exit(1)

    client = Client(api_key=api_key)

    planned = plan_searches(args.question)
    print(f"Planned {len(planned)} searches:", file=sys.stderr)
    try:
        raw, first_raw = run_searches(client, planned)
    except Exception as exc:  # surface API errors plainly
        print(f"Search failed: {exc}", file=sys.stderr)
        sys.exit(1)

    results = interleave_results(dedupe_results(raw))

    print(f"Collected {len(results)} unique results.", file=sys.stderr)

    answer_box = (first_raw or {}).get("answer_box")

    report = synthesize(args.question, results, answer_box)
    print()
    print(report)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(report + "\n")
        print(f"\nSaved to {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
