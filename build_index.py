#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent
README_PATH = ROOT / "README.md"
TOOLS_JSON_PATH = ROOT / "tools.json"
SITE_CONFIG_PATH = ROOT / "site-config.json"
OUTPUT_PATH = ROOT / "index.html"


def load_site_config() -> dict:
    if not SITE_CONFIG_PATH.exists():
        return {}
    return json.loads(SITE_CONFIG_PATH.read_text(encoding="utf-8"))


def parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def ordinal(day: int) -> str:
    if 10 <= day % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    return f"{day}{suffix}"


def display_date(value: str | None) -> str:
    parsed = parse_date(value)
    if not parsed:
        return ""
    return f"{ordinal(parsed.day)} {parsed.strftime('%B %Y')}"


def format_inline(text: str) -> str:
    parts: list[str] = []
    index = 0
    pattern = r"`([^`]+)`|\[([^\]]+)\]\(([^)]+)\)"
    for match in re.finditer(pattern, text):
        start, end = match.span()
        if start > index:
            parts.append(html.escape(text[index:start]))
        code_text, link_label, link_href = match.groups()
        if code_text is not None:
            parts.append(f"<code>{html.escape(code_text)}</code>")
        else:
            parts.append(
                f'<a href="{html.escape(link_href, quote=True)}">{html.escape(link_label)}</a>'
            )
        index = end
    if index < len(text):
        parts.append(html.escape(text[index:]))
    return "".join(parts)


def render_markdownish(text: str) -> str:
    lines = text.splitlines()
    output: list[str] = []
    paragraph: list[str] = []
    list_items: list[str] = []
    in_code_block = False
    code_lines: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            output.append(f"<p>{format_inline(' '.join(paragraph))}</p>")
            paragraph = []

    def flush_list() -> None:
        nonlocal list_items
        if list_items:
            items = "".join(f"<li>{format_inline(item)}</li>" for item in list_items)
            output.append(f"<ul>{items}</ul>")
            list_items = []

    def flush_code() -> None:
        nonlocal code_lines
        if code_lines:
            output.append(
                "<pre><code>"
                + html.escape("\n".join(code_lines))
                + "</code></pre>"
            )
            code_lines = []

    for raw_line in lines:
        line = raw_line.rstrip()

        if line.startswith("```"):
            flush_paragraph()
            flush_list()
            if in_code_block:
                flush_code()
                in_code_block = False
            else:
                in_code_block = True
            continue

        if in_code_block:
            code_lines.append(raw_line)
            continue

        if not line.strip():
            flush_paragraph()
            flush_list()
            continue

        if line.startswith("<!--") and line.endswith("-->"):
            flush_paragraph()
            flush_list()
            output.append(line)
            continue

        if line.startswith("## "):
            flush_paragraph()
            flush_list()
            output.append(f"<h2>{format_inline(line[3:])}</h2>")
            continue

        if line.startswith("# "):
            flush_paragraph()
            flush_list()
            output.append(f"<h1>{format_inline(line[2:])}</h1>")
            continue

        if line.startswith("- "):
            flush_paragraph()
            list_items.append(line[2:].strip())
            continue

        paragraph.append(line.strip())

    flush_paragraph()
    flush_list()
    flush_code()
    return "\n".join(output)


def render_recent(tools: list[dict]) -> str:
    dated = [tool for tool in tools if parse_date(tool.get("created"))]
    dated.sort(key=lambda tool: parse_date(tool.get("created")), reverse=True)
    if not dated:
        dated = tools[:]
    items = []
    for tool in dated[:5]:
        items.append(
            f'<li><a href="{tool["url"]}">{tool["title"]}</a>'
            f'{f"<span class=\"recent-date\"> {display_date(tool.get("created"))}</span>" if tool.get("created") else ""}</li>'
        )
    if not items:
        items.append("<li>No tools yet.</li>")
    return "\n".join(items)


def main() -> None:
    config = load_site_config()
    site_name = config.get("site_name", "HTML Tools")
    site_description = config.get("site_description", "")

    readme_html = render_markdownish(README_PATH.read_text(encoding="utf-8"))

    tools = []
    if TOOLS_JSON_PATH.exists():
        tools = json.loads(TOOLS_JSON_PATH.read_text(encoding="utf-8"))

    recent_html = f"""
<div class="recent-block">
  <h2>Recently added</h2>
  <ul>
    {render_recent(tools)}
  </ul>
</div>
""".strip()

    start_marker = "<!-- recently starts -->"
    end_marker = "<!-- recently stops -->"
    if start_marker in readme_html and end_marker in readme_html:
        start_index = readme_html.find(start_marker)
        end_index = readme_html.find(end_marker)
        if start_index < end_index:
            readme_html = (
                readme_html[: start_index + len(start_marker)]
                + "\n"
                + recent_html
                + "\n"
                + readme_html[end_index:]
            )

    output = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{site_name}</title>
  <meta name="description" content="{site_description}">
  <style>
    :root {{
      color-scheme: light;
      --bg: #f4efe7;
      --panel: #fffaf2;
      --ink: #1f2328;
      --muted: #5c6670;
      --accent: #8a3b12;
      --accent-soft: #ead8c8;
      --border: #d9c7b5;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, #fff7dc 0, transparent 28rem),
        linear-gradient(180deg, #f9f4ea 0%, var(--bg) 100%);
    }}
    .shell {{
      max-width: 960px;
      margin: 0 auto;
      padding: 32px 18px 64px;
    }}
    .hero {{
      background: linear-gradient(135deg, rgba(138, 59, 18, 0.12), rgba(255, 250, 242, 0.88));
      border: 1px solid var(--border);
      border-radius: 20px;
      padding: 28px 22px;
      box-shadow: 0 12px 30px rgba(99, 67, 41, 0.08);
    }}
    .hero h1 {{
      margin: 0 0 8px;
      font-size: clamp(2rem, 5vw, 3.5rem);
      line-height: 1;
    }}
    .hero p {{
      margin: 0;
      max-width: 42rem;
      color: var(--muted);
      font-size: 1.05rem;
    }}
    .content {{
      margin-top: 24px;
      background: rgba(255, 250, 242, 0.88);
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 24px 22px;
      box-shadow: 0 10px 25px rgba(99, 67, 41, 0.06);
    }}
    h2, h3 {{
      font-family: "Helvetica Neue", Arial, sans-serif;
      margin-top: 1.6em;
    }}
    a {{
      color: var(--accent);
    }}
    code {{
      background: var(--accent-soft);
      padding: 0.1rem 0.35rem;
      border-radius: 6px;
    }}
    .recent-block {{
      padding: 16px 18px;
      border-radius: 14px;
      background: #fff;
      border: 1px solid var(--border);
      margin: 12px 0 24px;
    }}
    .recent-block h2 {{
      margin-top: 0;
    }}
    .recent-date {{
      color: var(--muted);
      margin-left: 0.35rem;
      font-size: 0.95rem;
    }}
    ul {{
      padding-left: 1.2rem;
    }}
    @media (max-width: 640px) {{
      .shell {{
        padding: 18px 12px 40px;
      }}
      .hero, .content {{
        padding: 18px 16px;
      }}
    }}
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <h1>{site_name}</h1>
      <p>{site_description}</p>
    </section>
    <section class="content">
      {readme_html}
    </section>
  </main>
</body>
</html>
"""
    OUTPUT_PATH.write_text(output, encoding="utf-8")


if __name__ == "__main__":
    main()
