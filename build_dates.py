#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).parent
TOOLS_JSON_PATH = ROOT / "tools.json"
OUTPUT_PATH = ROOT / "dates.json"


def format_display_date(value: str | None) -> str | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt.strftime("%Y-%m-%d")


def main() -> None:
    if not TOOLS_JSON_PATH.exists():
        OUTPUT_PATH.write_text("{}\n", encoding="utf-8")
        return

    tools = json.loads(TOOLS_JSON_PATH.read_text(encoding="utf-8"))
    dates = {
        tool["filename"]: formatted
        for tool in tools
        if (formatted := format_display_date(tool.get("updated")))
    }
    OUTPUT_PATH.write_text(
        json.dumps(dates, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
