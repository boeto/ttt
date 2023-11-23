FROM python:3.10-slim

ENV TZ=Asia/Shanghai

USER root
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    curl \
    vim \
    wget \
    unzip \
    gosu \
    jq \
    ffmpeg
RUN apt-get clean && rm -rf /var/lib/apt/lists/*
RUN groupadd -r -g 991 myuser && useradd -r -u 991 -g 991 -m -s /bin/bash myuser

WORKDIR /app
COPY *.sh poetry.toml poetry.lock pyproject.toml README.md /app/
COPY media_web_dl /app/media_web_dl
RUN chmod +x /app/*.sh && chown -R myuser:myuser /app

USER myuser
RUN /usr/bin/env bash -c /app/init.sh

USER root
ENV PATH=/home/myuser/.local/bin:/app/.venv/bin:$PATH
ENTRYPOINT [ "/usr/bin/env","bash","-c","/app/entrypoint.sh" ]
