# Internal Agent - POC

A **function-calling agent** over a mock SQLite database. It answers staff/org-chart
and warehouse/inventory questions by calling read-only tools — **not** a RAG system.

## Stack
- **Google ADK** `LlmAgent` (`gemini-3.1-flash-lite`) with 5 wired tools
- **SQLite** mock database (`mock_company.db`)
- **Streamlit** chat UI

## Setup

```bash
# 1. Create + activate a virtualenv
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure your API key
cp .env.example .env             # then edit .env and set GOOGLE_API_KEY

# 4. Build the mock database
python seed_db.py

# 5. Run the app
streamlit run app.py
```

> The agent reads `GOOGLE_API_KEY` from the environment. With python-dotenv it is
> picked up from `.env`; otherwise `export GOOGLE_API_KEY=...` before running.

## Quick checks (no API key needed)
```bash
python seed_db.py        # prints row counts
python db_tools.py       # smoke-tests all 5 tools, prints JSON
```

## Example questions
- "Who is Quinn and who do they report to?"
- "List all MizuMi products that are low on stock."
- "How many days of supply does SKU MZ-SK-001 have?"
- "What needs reordering across the whole company?"

Employee IDs look like `E001`–`E023` (e.g. `E004` = Ohm, `E009` = Quinn, `E012` = Reese).

## About this POC

This is a **no-auth, mock-database POC** for the function-calling agent layer
(Project 2). There is no login or permissioning — it is meant for a local demo
only, with fictional placeholder data. When the real company database is wired in
later, **`db_tools.py` is the only file that needs to change**: it is the sole
module that knows connection and schema details. The 5 tool function signatures
are a stable contract — keep them identical and the agent and UI keep working
unchanged.
