"""
Auto-updates the Featured Projects section in README.md
using the GitHub API to fetch the latest public repositories.
"""

import os
import requests
import json
from datetime import datetime

USERNAME = os.environ.get("GITHUB_USERNAME", "leonardoramcke")
TOKEN    = os.environ.get("GITHUB_TOKEN", "")

HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# Repos to always skip (boilerplate, profile repo itself, forks you don't want shown)
SKIP_REPOS = {USERNAME, f"{USERNAME}.github.io"}

def get_repos():
    """Fetch public repos sorted by last push, skip forks and unwanted ones."""
    url = f"https://api.github.com/users/{USERNAME}/repos"
    params = {"sort": "pushed", "direction": "desc", "per_page": 50, "type": "owner"}
    resp = requests.get(url, headers=HEADERS, params=params)
    repos = resp.json()

    result = []
    for r in repos:
        if r.get("fork"):
            continue
        if r["name"] in SKIP_REPOS:
            continue
        result.append({
            "name":        r["name"],
            "description": r.get("description") or "No description provided.",
            "url":         r["html_url"],
            "language":    r.get("language") or "—",
            "stars":       r.get("stargazers_count", 0),
            "updated":     r.get("pushed_at", "")[:10],
        })

    return result[:6]  # show up to 6 most recent projects

def build_table(repos):
    """Build the markdown table of projects."""
    if not repos:
        return "_No public projects yet._\n"

    lines = []
    lines.append("| Project | Description | Language | Stars |")
    lines.append("|---|---|---|---|")
    for r in repos:
        name  = f"[{r['name']}]({r['url']})"
        desc  = r["description"][:80] + ("..." if len(r["description"]) > 80 else "")
        lang  = r["language"]
        stars = f"⭐ {r['stars']}" if r["stars"] > 0 else "—"
        lines.append(f"| {name} | {desc} | {lang} | {stars} |")

    updated = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    lines.append(f"\n<sub>Last updated: {updated}</sub>")
    return "\n".join(lines)

def update_readme(table):
    """Replace the projects section in README.md."""
    with open("README.md", "r", encoding="utf-8") as f:
        content = f.read()

    start_marker = "<!-- PROJECTS:START -->"
    end_marker   = "<!-- PROJECTS:END -->"

    if start_marker not in content:
        print("Markers not found in README.md — nothing to update.")
        return

    before = content.split(start_marker)[0]
    after  = content.split(end_marker)[1]
    new_content = f"{before}{start_marker}\n{table}\n{end_marker}{after}"

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"README updated with {table.count('|') // 5} projects.")

if __name__ == "__main__":
    print(f"Fetching repos for @{USERNAME}...")
    repos = get_repos()
    print(f"Found {len(repos)} public repos.")
    table = build_table(repos)
    update_readme(table)
    print("Done!")
