#!/usr/bin/env bash

set -e

pypoetry_path=${HOME}/.local/share/pypoetry
local_bin_path=${HOME}/.local/bin
assets_path=/app/assets

# poetry
if [[ ! -d ${pypoetry_path} ]]; then
    curl -sSL https://install.python-poetry.org | python3 -
    "${local_bin_path}"/poetry completions bash >>"${HOME}"/.bash_completion
fi

if [ ! -d "${local_bin_path}" ]; then
    mkdir -p "${local_bin_path}"
fi

if [ ! -d "${assets_path}" ]; then
    mkdir "${assets_path}"
fi

download_lastest_asset_version() {
    local owner="$1"
    local repo="$2"
    local contain_name="$3"

    url="https://api.github.com/repos/$owner/$repo/releases/latest"
    response=$(curl -s "$url")
    asset_url=$(echo "$response" | jq -r --arg contain_name "$contain_name" 'first(.assets[] | select(.name | contains($contain_name)) | .browser_download_url)')

    echo "asset_url:${asset_url}"

    filename=$(basename "$asset_url")
    echo "Downloading $filename..."

    wget -O "${assets_path}/$filename" "$asset_url"
    wait
    echo "Extracting $filename..."
    tar -xf "${assets_path}/$filename" -C assets
    rm "${assets_path}/$filename"
}

# N_m3u8DL-RE
if ! command -v N_m3u8DL-RE &>/dev/null; then
    m3u8_owner="nilaoda"
    m3u8_repo="N_m3u8DL-RE"
    download_lastest_asset_version "$m3u8_owner" "$m3u8_repo" "linux-x64"
    mv ${assets_path}/N_m3u8DL-RE_Beta_linux-x64/N_m3u8DL-RE "${local_bin_path}"
    chmod +x "${local_bin_path}"/N_m3u8DL-RE
fi

# mp4decrypt
if ! command -v mp4decrypt &>/dev/null; then
    bento4_filename="Bento4-SDK-1-6-0-640.x86_64-unknown-linux"
    wget -O "${assets_path}/$bento4_filename.zip" https://www.bok.net/Bento4/binaries/$bento4_filename.zip
    unzip ${assets_path}/$bento4_filename.zip -d ${assets_path}
    mv ${assets_path}/$bento4_filename/bin/* "${local_bin_path}"
    rm -rf ${assets_path}/$bento4_filename.zip
fi

# cleanup
rm -rf ${assets_path}
