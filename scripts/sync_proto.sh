#!/usr/bin/env bash
set -euo pipefail

echo "Syncing services protos..."

rm -rf proto
mkdir -p proto

cp -r proto_src/services/*.proto proto/

echo "Done."
