from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class BuildOutputsTest(unittest.TestCase):
    def test_build_pipeline_generates_expected_files(self) -> None:
        subprocess.run([sys.executable, "gather_links.py"], cwd=ROOT, check=True)
        subprocess.run([sys.executable, "build_dates.py"], cwd=ROOT, check=True)
        subprocess.run([sys.executable, "build_index.py"], cwd=ROOT, check=True)

        tools = json.loads((ROOT / "tools.json").read_text(encoding="utf-8"))
        self.assertTrue(any(tool["slug"] == "html-preview" for tool in tools))

        index_html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("HTML Tools", index_html)
        self.assertIn("HTML Preview", index_html)


if __name__ == "__main__":
    unittest.main()
