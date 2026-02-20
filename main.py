# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import os
from dotenv import load_dotenv
import requests

load_dotenv()

from repo_fetcher import parse_github_url, get_cached_snapshot
from llm_client import summarize_repo

app = FastAPI(title="Repo Summarizer")


# User must provide a GitHub URL to summarize
class SummarizeRequest(BaseModel):
    github_url: str


# Guaranteed response format for successful summaries
class SummarizeResponse(BaseModel):
    summary: str
    technologies: List[str]
    structure: str


# Ensure error responses are consistent and informative
class ErrorResponse(BaseModel):
    status: str = "error"
    message: str


@app.post("/summarize", response_model=Dict)
# This allows the server to handle other requests while
# it waits for GitHub or the LLM to respond
async def summarize(request: SummarizeRequest):
    try:
        owner, repo, branch = parse_github_url(request.github_url)
        snapshot = get_cached_snapshot(owner, repo, branch)  # CACHED!
        llm_result = summarize_repo(snapshot)
        return SummarizeResponse(**llm_result).dict()
    except ValueError as e:
        raise HTTPException(
            status_code=400, detail={"status": "error", "message": str(e)}
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500, detail={"status": "error", "message": "Repo fetch failed"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail={"status": "error", "message": str(e)}
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
