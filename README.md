# Investor Data Agent (LangChain + SerpAPI + LLM)

This project:
1. Uses **SerpAPI** to search the web for pages related to your investor query.
2. Fetches readable text from the top results.
3. Uses **OpenAI or Gemini** (via LangChain) to extract investor records.
4. Saves everything into a CSV (`investors.csv` by default).

## Setup

1. Copy env example:
   - `.env.example` -> `.env`
2. Put your keys:
   - `SERPAPI_KEY`
   - `OPENAI_API_KEY` **or** `GEMINI_API_KEY`

## Install dependencies

```powershell
pip install -r requirements.txt
```

## Run

```powershell
python main.py "Fintech investors in India investing $500k–$2M" --max-results 8 --output-csv investors.csv
```

If you want to just print extracted records (no CSV):

```powershell
python main.py "Fintech investors in India investing $500k–$2M" --print-only
```

## Output CSV columns

`query, search_title, investor_name, investor_type, investor_location_city, investor_location_country, investment_stage_min_usd, investment_stage_max_usd, focus_industries, evidence_quote, source_url`

## Notes

- Web pages may block automated requests; the agent will skip pages it can't fetch.
- Extraction quality depends on page text; using higher `--max-page-chars` can help.

## Web UI (FastAPI)

Run the API + web page:

```powershell
uvicorn app:app --reload --port 8000
```

Open in browser:
`http://localhost:8000/`

The UI `/api/run` endpoint pe agent run karke records dikhaega aur `CSV` download link dega.

