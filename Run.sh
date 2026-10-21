#!/usr/bin/env bash
# ==============================================================================
# run.sh — Linux / macOS launcher for Huawei Storage Log Parser
# ==============================================================================
#
# Использование:
#   ./run.sh                 → запуск GUI
#   ./run.sh log.txt         → один файл
#   ./run.sh /path/to/logs   → batch-режим
#   ./run.sh --help          → справка
#
# Перед первым запуском:
#   chmod +x run.sh
#
# Рекомендуется создать venv:
#   python3 -m venv .venv
#   source .venv/bin/activate
#   pip install openpyxl PyQt6
#
# Скрипт автоматически активирует .venv, если он есть рядом.
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Авто-активация venv, если он есть
if [ -f "$SCRIPT_DIR/.venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    source "$SCRIPT_DIR/.venv/bin/activate"
fi

# Определяем Python
if command -v python3 >/dev/null 2>&1; then
    PYTHON=python3
elif command -v python >/dev/null 2>&1; then
    PYTHON=python
else
    echo "Error: python3 not found in PATH." >&2
    echo "Install Python 3.10+ (macOS: brew install python)." >&2
    echo "Or create a venv: python3 -m venv .venv && source .venv/bin/activate" >&2
    exit 1
fi

exec "$PYTHON" "$SCRIPT_DIR/Main.py" "$@"