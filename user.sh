#!/usr/bin/env bash
set -e

# poetry install
if [[ ! -d .venv/lib ]]; then
    poetry install --no-interaction --no-ansi
fi

tail -f /dev/null
