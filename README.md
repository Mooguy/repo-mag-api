# Repo Summarizer API

POST `/summarize` analyzes GitHub repos and returns LLM-generated summaries.

## Setup (Clean Python 3.10+ machine)
1. Clone/extract this project.
2. `python -m venv .venv`
3. Activate: `source .venv/bin/activate` (Linux/Mac) or `.venv\Scripts\activate` (Windows)
4. `pip install -r requirements.txt`
5. `export NEBIUS_API_KEY=your_key_here` (provided by evaluators)
6. `uvicorn main:app --host 0.0.0.0 --port 8000 --reload`

## Test Endpoint
```bash
curl -X POST http://localhost:8000/summarize \
  -H "Content-Type: application/json" \
  -d '{"github_url": "https://github.com/psf/requests"}'
```

## Design Summary
- **LLM**: Llama 3.1 70B Instruct (reliable JSON).
- **Repo handling**: GitHub tree API (no clone). Filters binaries/locks, prioritizes README/configs + top-3 source previews (~12k chars total).
- **Why**: Efficient context usage, captures purpose/tech/structure perfectly.

**Files for zip** (your current project):
- main.py
- repo_fetcher.py
- llm_client.py
- requirements.txt (paste below)
- README.md (above)
- .gitignore (optional)

**requirements.txt** (create):
- fastapi
- uvicorn[standard]
- requests
- openai
- python-dotenv