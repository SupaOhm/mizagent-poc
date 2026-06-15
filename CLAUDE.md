# CLAUDE.md

This file gives Claude Code context for working in this repository.

## Project Overview

This repo contains a **POC for Project 2 — Internal AI Agent**, part of
Ohm's internship at Mizuhada Group (Bonn Team, COO Office / IT,
June 4 – July 31, 2026).

Project 2 is a **function-calling agent layer** (Phase 2 of the internal
knowledge system) — distinct from Project 6 (OpsBot), which is a
RAG-based document Q&A chatbot. This repo covers Project 2 only.

This POC demonstrates the agent architecture **against a mock SQLite
database**, built while waiting on the real data dictionary / DB access
from the company. The goal is a working, demoable pattern that swaps
cleanly onto the real database later.

## Tech Stack

- **Agent orchestration**: Google ADK (`LlmAgent`)
- **LLM**: Gemini 3.1 Flash Lite (`gemini-3.1-flash-lite`) via Google AI
  Studio API key (no GCP account)
- **Database**: SQLite (mock for POC; real company DB later via DBeaver)
- **UI**: Streamlit (POC stage — React UI is the eventual target per the
  unified SRS, but not in scope for this repo)

## Architecture Principles (do not violate these)

1. **`db_tools.py` is the only file that knows the database schema and
   connection details.** When the real database is connected, only this
   file should change — function signatures must stay stable, since
   `agent.py` and `app.py` depend on them as a contract.

2. **All numeric calculations happen in Python, not in LLM reasoning.**
   Functions like `calculate_stock_coverage` and `get_low_stock_items`
   compute their results in `db_tools.py`. The agent's job is to call
   these tools and explain the results in natural language — never to
   do arithmetic itself over raw rows. This is intentional (ties to
   hallucination-rate concerns in the broader SRS).

3. **No-auth POC.** There is no session-based identity. Any tool that
   needs an `employee_id` takes it as an explicit parameter. If a user
   asks something personal ("my leave balance") without providing an
   `employee_id`, the agent should ask for it — not guess or assume.

4. **Read-only, side-effect-free tools.** All `db_tools.py` functions
   are SELECT-only. Do not add write/update/delete operations without
   discussing first — this mirrors the "Phase 2 actions are read-only
   for the internship scope" constraint from the SRS.

## Naming & Synthetic Data Constraints

**Do not use real people's names** anywhere in this repo (seed data,
comments, docstrings, example queries, UI text) — except "Ohm", which
refers to the intern building this and is fine to reference. All mock
employee names must be generic/fictional placeholders.

**Do not use real Mizuhada brand or product names.** This repo uses
synthetic brand names:
- **Mihihi** — skincare/sunscreen brand (Skincare category only)
- **Bobi** — supplements/pills brand (Wellness category only)
- **Harshcolor** — makeup brand (Cosmetics category only)

Product names should be generic/descriptive (e.g. "Facial Sunscreen
SPF50", "Probiotic Capsules", "Lip Tint") — not specific real product
names from any company.

If asked to regenerate or expand seed data, preserve this brand/category
alignment and the synthetic naming conventions.

## Current Seed Data (snapshot)

- **employees**: 23 rows. IDs `E001`–`E023`, emails `<name>@mizahaha.example`,
  manager hierarchy with `E001` (CEO) at the top (`manager_id` NULL).
- **products**: 15 rows, 5 per brand.
  - Mihihi Skincare: `MH-SK-001`–`005`
  - Bobi Wellness: `BB-WL-001`–`005`
  - Harshcolor Cosmetics: `HC-CO-001`–`005`
- **Edge cases**: zero-sales product is `MH-SK-005` (Calming Sheet Mask,
  `avg_daily_sales = 0`); 7 products sit below their reorder_point across all
  three brands. Preserve both when editing seed data.

## File Structure

- `seed_db.py` — creates and seeds `mock_company.db` (employees +
  products tables). Run this first / after any schema change.
- `db_tools.py` — data access layer. 5 functions: `search_employees`,
  `get_employee_record`, `query_products`, `calculate_stock_coverage`,
  `get_low_stock_items`. Has a `__main__` smoke test.
- `agent.py` — ADK `LlmAgent` wiring the 5 tools + system instruction
  with routing rules. Exports `get_agent_response(user_message,
  session_id)` for use by `app.py`.
- `app.py` — Streamlit chat UI calling `agent.get_agent_response`.
- `requirements.txt` — runtime deps + optional dev tools section
  (e.g. `sqlite-web`).
- `.env.example` — copy to `.env` and set `GOOGLE_API_KEY`.
- `README.md` — setup and run instructions.

## Common Tasks

- **Reseed the database**: `python3 seed_db.py` (run from repo root —
  it writes `mock_company.db` relative to its own location).
- **Smoke test the data layer**: `python3 db_tools.py`
- **Run the demo**: `streamlit run app.py` (requires `GOOGLE_API_KEY`
  in `.env`)
- **Browse the DB**: `sqlite_web mock_company.db` →
  `http://localhost:8080`

## After Any Schema/Data Change

When editing `seed_db.py` (schema, seed data, brand/product names):
1. Delete `mock_company.db` and re-run `seed_db.py`.
2. Re-run `db_tools.py`'s smoke test to confirm all 5 functions still
   work, especially edge cases (zero `avg_daily_sales`, low-stock
   filtering).
3. Check `db_tools.py`, `agent.py`, and `app.py` for hardcoded
   example IDs/SKUs/names that may now be stale or invalid.
4. Grep for any leaked real names/brands before considering the change
   complete.
