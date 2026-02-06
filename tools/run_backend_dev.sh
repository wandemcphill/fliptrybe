#!/usr/bin/env bash
set -euo pipefail

# FlipTrybe: run Flask backend locally (dev)

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"

cd "$BACKEND_DIR"
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export FLIPTRYBE_ENV=dev
python main.py
