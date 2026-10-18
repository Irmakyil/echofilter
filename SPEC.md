# EchoFilter AI — Product Specification

## Objective
Give crisis-desk operators a single English-language screen for reviewing disaster messages. Keep every raw message, group likely duplicates, highlight low-visibility urgent incidents, and route uncertain records for human review.

## Stack and commands
- Python 3.10+, Streamlit, pandas, Pydantic, SQLite, and optional Gemini via Google's `google-genai` SDK.
- Install: `python -m pip install -r requirements.txt`
- Run: `streamlit run app.py`
- Gemini: set `GEMINI_API_KEY` in the environment. The app remains usable in local demo mode without it.

## Project structure
- `app.py`: Streamlit operator workspace.
- `crisis_triage.py`: ingestion, validation, analysis, grouping, privacy, and persistence.
- `data/`: attributed public reference data, a privacy-preserving benchmark derivative, and clearly fictional demo data.
- `README.md`: setup, attribution, limitations, and safe-use guidance.

## Acceptance criteria
- Import CSV/JSON, analyze a demo batch, and add a live simulated message.
- Classify noise, extract only stated details, group likely duplicates, and score urgency 1–100 with a concise reason.
- Low-retweet critical incidents are visibly flagged; incomplete/ambiguous reports remain in a human-review queue.
- Preserve raw messages in SQLite and expose them under their incident; mask phone numbers by default.
- Optional Gemini or OpenAI processing uses one structured batch request, temperature 0, and a bounded batch size. Local heuristics work without credentials.
- All user-facing copy and project documentation are in English.
- Include a recent, relevant, privacy-preserving benchmark derivative with clear attribution and limitations.

## Boundaries and limitations
- The public reference corpus is historical, has no retweet counts or operational location schema, and is not live incident data. It is for reference/classification demonstrations only.
- The 2023 DepremKit benchmark derivative includes labels and entity counts only; tweet IDs and text are intentionally omitted, so it supports distribution/schema review, not NLP scoring.
- The DepremKit tab displays label and entity-count distributions and offers the anonymized derivative for download.
- Synthetic demo records use fictional locations and identifiers. Never use this prototype as an autonomous dispatch or verification system.
- External Gemini/OpenAI requests send selected, phone-masked message text to the provider. The UI must disclose this and require operator consent before analysis.
- Human review is required before any real-world action.
