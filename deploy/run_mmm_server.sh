#!/usr/bin/env bash
set -euo pipefail
HERE=$(cd "$(dirname "$0")/.." && pwd)
cd "$HERE"
# Run the backend as a background process (uses module style to allow relative imports)
python3 -m mmm_server.app "$@" &
echo $!
