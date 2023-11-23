#!/usr/bin/env bash
set -e

logs_path=/app/media_web_dl/logs
log_path=${logs_path}/entrypoint.log

id
echo "hi,$(id)" >>${log_path}
echo "$PATH"
poetry -V

# poetry install
if [[ ! -d .venv/lib ]]; then
    poetry install --no-interaction --no-ansi
fi

tail -f /dev/null
