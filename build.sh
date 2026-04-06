#!/usr/bin/env bash
set -euo pipefail

echo "Building HTML Tools..."
python gather_links.py
python build_dates.py
python build_index.py
echo "Build complete."
