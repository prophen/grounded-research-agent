# Grounded Research Agent

A small Python demo built on [SerpApi](https://serpapi.com): ask a question,
get back an answer assembled from live search results, with every claim
traced to a numbered source.

## How it works

1. **Plan.** One question becomes three searches from different angles:
   the question itself, a background variant (`... explained`), and a
   recency variant (`... 2026`). The planner is intentionally simple and
   readable; in a larger agent you would swap it for an LLM call.
2. **Search.** Each angle runs through SerpApi's Google Search API.
   Results are tagged with the angle that surfaced them and deduped by URL.
3. **Synthesize.** The report is assembled extractively from real snippets.
   No LLM call, no paraphrasing, so what is grounded stays visible: every
   key point carries a citation, and the source list is right below it.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export SERPAPI_API_KEY="your-key-here"
```

Get a free API key at [serpapi.com](https://serpapi.com) (250 free searches).

## Run it

```bash
python research.py "What is retrieval-augmented generation?"
python research.py "Best Python web frameworks for beginners" --out report.md
```

## Why this shape

A research agent that trusts a single search is just a search box with
extra steps. Planning multiple angles is the smallest thing that makes it
an agent: it decides what to look for, not just how to display it. Keeping
synthesis extractive makes the grounding claim checkable, which is the
whole point of the demo.

## Ideas to extend

- Swap the rule-based planner for an LLM that writes follow-up queries
  from the first page of results.
- Add an LLM synthesis step, but keep the extractive citations alongside
  it so grounding stays auditable.
- Try other SerpApi engines: `google_news` for the recency angle,
  `google_scholar` for the background angle.
