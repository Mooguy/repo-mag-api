# Repo Summarizer API

POST `/summarize` analyzes GitHub repos and returns LLM-generated summaries.

## Setup (Clean Python 3.10+ machine)
1. Clone/extract this project.
2. `python -m venv .venv`
3. Activate: `source .venv/bin/activate` (Linux/Mac) or `.venv\Scripts\activate` (Windows)
4. `pip install -r requirements.txt`
5. `export NEBIUS_API_KEY=your_key_here` 
6. `uvicorn main:app --host 0.0.0.0 --port 8000 --reload`

**Optional**: `export GITHUB_TOKEN=ghp_xxx` (Pro: 5k/hr vs 60/hr unauth)

## Test Endpoint
```bash
curl -X POST http://localhost:8000/summarize \
  -H "Content-Type: application/json" \
  -d '{"github_url": "https://github.com/psf/requests"}'
```

## Example Response
{
  "summary": "Requests is an elegant and simple HTTP library for Python, built for human beings.",
  "technologies": ["Python", "HTTP/1.1", "urllib3", "Certifi"],
  "structure": "The core logic resides in /src/requests, with tests in /tests and documentation in /docs."
}

## Design Choices
- **LLM**: Llama 3.1 70B Instruct (reliable JSON).
- **GitHub**: Tree API (no clone). **Ignores**: binaries/locks/`node_modules/`. **Prioritizes**: README/configs + top-3 src previews (~12k chars). Why: Fits LLM context, captures purpose/tech/structure efficiently.
- **Caching**: `cachetools` (100 repos, 1hr TTL). Why: 1st request full fetch, repeats instant → solves unauth GitHub limits.
- **Auth**: User-Agent always. Optional `GITHUB_TOKEN` env var auto-detected (60/hr → 5k/hr). Why: Works out-of-box, scales with Pro.
- **Errors**: 400 invalid URL, 500 fetch/LLM fail.


## Project Structure

├── .env              
├── .gitignore        
├── README.md           
├── llm_client.py       
├── main.py             
├── repo_fetcher.py     
└── requirements.txt

