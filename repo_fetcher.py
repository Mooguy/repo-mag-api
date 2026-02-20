# repo_fetcher.py
import os
import re
import requests
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse

BASE_URL = "https://api.github.com"
GITHUB_HEADERS = {"User-Agent": "RepoSummarizer/1.0"}
if token := os.getenv("GITHUB_TOKEN"):
    GITHUB_HEADERS["Authorization"] = f"token {token}"


def parse_github_url(url: str) -> tuple[str, str, Optional[str]]:
    """Extract owner, repo, branch (None if default)."""
    parsed = urlparse(url.rstrip("/"))
    if parsed.netloc != "github.com":
        raise ValueError("Invalid GitHub URL")

    path_parts = [p for p in parsed.path.lstrip("/").split("/") if p]
    if len(path_parts) < 2:
        raise ValueError("URL must be https://github.com/owner/repo")

    owner, repo = path_parts[0], path_parts[1]
    branch = (
        path_parts[2] if len(path_parts) >= 3 else None
    )  # CHANGED: None for default
    return owner, repo, branch


def get_default_branch(owner: str, repo: str) -> str:
    """Get repo's default branch."""
    url = f"{BASE_URL}/repos/{owner}/{repo}"
    resp = requests.get(url, headers=GITHUB_HEADERS)
    resp.raise_for_status()
    return resp.json()["default_branch"]


def get_repo_tree(owner: str, repo: str, branch: str = None) -> Dict[str, Any]:
    if branch is None:
        branch = get_default_branch(owner, repo)
    url = f"{BASE_URL}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    resp = requests.get(url, headers=GITHUB_HEADERS)
    if resp.status_code == 404:
        raise ValueError(f"Repo or branch not found: {owner}/{repo}/{branch}")
    resp.raise_for_status()
    return resp.json()


def should_ignore(path: str, is_dir: bool = False) -> bool:
    """Check if file/dir should be ignored."""
    ignore_patterns = [
        r"\.git/",
        r"__pycache__/",
        r"node_modules/",
        r"dist/",
        r"build/",
        r"\.pytest_cache/",
        r"\.egg-info/",
        r"\.(pyc|pyo|log|lock|DS_Store)$",
        r"\.(png|jpg|jpeg|gif|ico|pdf|zip|exe|dll|so|tar\.gz)$",
    ]

    if is_dir and any(re.search(p, path, re.IGNORECASE) for p in ignore_patterns):
        return True
    return False


def get_file_content(owner: str, repo: str, path: str) -> Optional[str]:
    url = f"{BASE_URL}/repos/{owner}/{repo}/contents/{path}"
    resp = requests.get(
        url, headers={**GITHUB_HEADERS, "Accept": "application/vnd.github.v3.raw"}
    )
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.text


def build_snapshot(tree_data: Dict[str, Any], owner: str, repo: str) -> str:
    """Build compact repo snapshot for LLM."""
    tree = tree_data["tree"]

    # Filter tree
    filtered_tree = []
    for item in tree:
        # ignore dirs/files based on patterns:
        if should_ignore(item["path"], item["type"] == "tree"):
            continue
        filtered_tree.append(
            f"- {item['path']} ({item['type']}, size: {item.get('size', 'N/A')})"
        )

    tree_str = "\n".join(filtered_tree[:100])

    # Priority files (full content if small)
    priority_patterns = [
        r"^README\.md$",
        r"^README\.rst$",
        r"^README$",
        r"^package\.json$",
        r"^pyproject\.toml$",
        r"^setup\.py$",
        r"^requirements\.txt$",
        r"^Cargo\.toml$",
        r"^go\.mod$",
        r"^\.gitignore$",
        r"^Dockerfile$",
    ]

    key_files = []
    for item in tree:
        if item["type"] != "blob" or should_ignore(item["path"]):
            continue
        # Exact path match (case insensitive)
        if any(re.match(p, item["path"], re.IGNORECASE) for p in priority_patterns):
            content = get_file_content(owner, repo, item["path"])
            if content:
                preview = content[:2000] + "..." if len(content) > 2000 else content
                lines = len(content.splitlines())
                key_files.append(f"**{item['path']}** ({lines} lines):\n{preview}\n")
        if len(key_files) >= 8:
            break

    # Top source files (first 1k chars)
    source_exts = [".py", ".js", ".ts", ".go", ".java", ".cpp", ".rs"]
    sources = []
    source_candidates = sorted(
        [
            i
            for i in tree
            if i["type"] == "blob"
            and not should_ignore(i["path"])
            and any(i["path"].endswith(ext) for ext in source_exts)
        ],
        key=lambda x: x.get("size", 0),
        reverse=True,
    )[:3]  # CHANGED: top 3

    for item in source_candidates:
        content = get_file_content(owner, repo, item["path"])
        if content:
            preview = (
                content[:800] + "..." if len(content) > 800 else content
            )  # CHANGED: 800
            sources.append(f"{item['path']} (preview):\n{preview}\n")

    snapshot = (
        f"""Repo tree (filtered, top 100):
        {tree_str}

        Priority files:
        """
        + "\n\n".join(key_files[:5])
        + "\n\nSource previews (top 10 by size):\n"
        + "\n\n".join(sources[:3])
    )

    return snapshot[:15000]  # Hard cap for LLM


# Test helper
if __name__ == "__main__":
    try:
        owner, repo, branch = parse_github_url("https://github.com/psf/requests")
        # owner, repo, branch = parse_github_url("https://github.com/tiangolo/fastapi")
        tree = get_repo_tree(owner, repo, branch)
        snapshot = build_snapshot(tree, owner, repo)
        # print(snapshot[:500] + "...")  # Preview
        # save snapshot to file for inspection
        with open("snapshot.txt", "w", encoding="utf-8") as f:
            f.write(snapshot)
        # print("Snapshot saved to snapshot.txt")
        # count number of characters in snapshot
        print(f"Snapshot length: {len(snapshot)} characters")
    except Exception as e:
        print(f"Error: {e}")
