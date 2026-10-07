#!/usr/bin/env bash
set -euo pipefail

# Capture one valid frame from a MediaMTX/RTSP stream without disturbing
# the long-running process that owns the USB camera.
# Usage: capture_rtsp_frame.sh OUTPUT.jpg [RTSP_URL]

output=${1:?"usage: capture_rtsp_frame.sh OUTPUT.jpg [RTSP_URL]"}
url=${2:-rtsp://127.0.0.1:8554/ipcam}
mkdir -p "$(dirname "$output")"
tmp="${output}.tmp.jpg"
trap 'rm -f "$tmp"' EXIT

for attempt in 1 2 3; do
  rm -f "$tmp"
  if ffmpeg -hide_banner -loglevel error \
      -rtsp_transport tcp \
      -i "$url" \
      -frames:v 1 \
      -y "$tmp" \
    && test -s "$tmp" \
    && ffprobe -v error -select_streams v:0 \
      -show_entries stream=codec_name,width,height \
      -of csv=p=0 "$tmp" >/dev/null; then
    mv "$tmp" "$output"
    trap - EXIT
    printf '%s\n' "$output"
    exit 0
  fi
  sleep 1
done

printf 'Failed to capture a valid RTSP frame after 3 attempts: %s\n' "$url" >&2
exit 1
