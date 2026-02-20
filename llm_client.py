# llm_client.py
import os
from dotenv import load_dotenv
from typing import Dict, Any, List
from openai import OpenAI

load_dotenv()

NEBIUS_BASE_URL = "https://api.tokenfactory.nebius.com/v1/"
NEBIUS_MODEL = "meta-llama/Llama-3.3-70B-Instruct"

client = OpenAI(base_url=NEBIUS_BASE_URL, api_key=os.getenv("NEBIUS_API_KEY"))

SYSTEM_PROMPT = """You are a code repository expert. Analyze the GitHub repo snapshot and return a concise JSON response.

Analyze:
- What the project does (1-2 sentences)
- Main technologies/languages/frameworks
- Project structure/layout

Respond ONLY with valid JSON:
{{"summary": "str", "technologies": ["list"], "structure": "str"}}"""


def summarize_repo(snapshot: str) -> Dict[str, Any]:
    """Call Nebius LLM, return structured summary."""
    if not os.getenv("NEBIUS_API_KEY"):
        raise ValueError("NEBIUS_API_KEY env var required")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Repo snapshot:\n\n{snapshot}"},
    ]

    response = client.chat.completions.create(
        model=NEBIUS_MODEL,
        messages=messages,
        temperature=0.1,  # Low for consistent JSON
        max_tokens=1000,
        response_format={"type": "json_object"},  # Forces JSON
    )

    content = response.choices[0].message.content
    import json

    return json.loads(content)


# Test (requires NEBIUS_API_KEY)
if __name__ == "__main__":
    from repo_fetcher import parse_github_url, get_repo_tree, build_snapshot

    try:
        owner, repo, _ = parse_github_url("https://github.com/tiangolo/fastapi")
        tree = get_repo_tree(owner, repo)
        snapshot = build_snapshot(tree, owner, repo)
        summary = summarize_repo(snapshot)
        print(summary)
    except Exception as e:
        print(f"Error: {e}")
