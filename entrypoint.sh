#!/usr/bin/env bash

logs_path=/app/media_web_dl/logs
log_path=${logs_path}/entrypoint.log

if [ ! -d "${logs_path}" ]; then
    mkdir "${logs_path}"
fi

if [ -n "${PUID}" ] && [ "$(id -u myuser)" != "${PUID}" ]; then
    usermod -o -u "${PUID}" myuser
fi
if [ -n "${PGID}" ] && [ "$(id -g myuser)" != "${PGID}" ]; then
    groupmod -o -g "${PGID}" myuser
fi

chown -R myuser:myuser \
    "${HOME}" \
    /app

echo "hi entrypoint" >${log_path}

exec gosu myuser /app/user.sh
