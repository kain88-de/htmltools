#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).parent
OUTPUT_PATH = ROOT / "tools.json"
LINKS_PATH = ROOT / "gathered_links.json"
SITE_CONFIG_PATH = ROOT / "site-config.json"


def load_site_config() -> dict:
    if not SITE_CONFIG_PATH.exists():
        return {}
    return json.loads(SITE_CONFIG_PATH.read_text(encoding="utf-8"))


def slug_to_url(slug: str, domain: str) -> str:
    path = "/" if slug == "index" else f"/{slug}"
    return f"https://{domain}{path}" if domain else path


def extract_urls(text: str) -> list[str]:
    return re.findall(r"(https?://[^\s]+)", text)


def extract_title(html_path: Path) -> str:
    content = html_path.read_text(encoding="utf-8", errors="ignore")
    match = re.search(r"<title>(.*?)</title>", content, re.IGNORECASE | re.DOTALL)
    if match:
        return html.unescape(match.group(1).strip())
    return html_path.stem.replace("-", " ").title()


def extract_description(docs_path: Path) -> str:
    if not docs_path.exists():
        return ""
    content = docs_path.read_text(encoding="utf-8").strip()
    if "<!--" in content:
        content = content.split("<!--", 1)[0]
    lines: list[str] = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped:
            if lines:
                break
            continue
        lines.append(stripped)
    return " ".join(lines)


def git_commits_for(path: Path) -> list[dict]:
    result = subprocess.run(
        ["git", "log", "--format=%H|%aI|%B%x00", "--", path.name],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    commits = []
    for raw_commit in result.stdout.strip().split("\0"):
        if not raw_commit.strip():
            continue
        first = raw_commit.find("|")
        second = raw_commit.find("|", first + 1)
        if first == -1 or second == -1:
            continue
        commits.append(
            {
                "hash": raw_commit[:first],
                "date": raw_commit[first + 1 : second],
                "message": raw_commit[second + 1 :].strip(),
            }
        )
    return commits


def main() -> None:
    config = load_site_config()
    domain = config.get("site_domain", "")

    pages = {}
    tools = []
    for html_path in sorted(ROOT.glob("*.html")):
        if html_path.name == "index.html":
            continue
        commits = git_commits_for(html_path)
        urls: list[str] = []
        for commit in commits:
            for url in extract_urls(commit["message"]):
                if url not in urls:
                    urls.append(url)

        pages[html_path.name] = {"commits": commits, "urls": urls}

        docs_path = html_path.with_suffix(".docs.md")
        tools.append(
            {
                "filename": html_path.name,
                "slug": html_path.stem,
                "title": extract_title(html_path),
                "description": extract_description(docs_path),
                "created": commits[-1]["date"] if commits else None,
                "updated": commits[0]["date"] if commits else None,
                "url": slug_to_url(html_path.stem, domain),
            }
        )

    tools.sort(key=lambda item: item["title"].lower())
    LINKS_PATH.write_text(
        json.dumps({"pages": pages}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    OUTPUT_PATH.write_text(
        json.dumps(tools, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
