#!/usr/bin/env bash

if [ -n "${PUID}" ] && [ "$(id -u myuser)" != "${PUID}" ]; then
    usermod -o -u "${PUID}" myuser
fi
if [ -n "${PGID}" ] && [ "$(id -g myuser)" != "${PGID}" ]; then
    groupmod -o -g "${PGID}" myuser
fi

chown -R myuser:myuser \
    "${HOME}" \
    /app

exec gosu myuser /app/user.sh
