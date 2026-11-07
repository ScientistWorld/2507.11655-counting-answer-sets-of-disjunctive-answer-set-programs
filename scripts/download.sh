#!/bin/bash
# Download all external artifacts needed for this environment.
#
# Run on a node with internet access BEFORE submitting compute jobs.
# Idempotent: skips files that already exist and verify.
#
# Estimated total download size: ~30 MB (GANAK release tarball)
# Estimated disk usage after extraction: ~75 MB
#
# Artifacts:
#   data/downloads/ganak  -- GANAK v2.8.0 exact (projected) model counter, static
#                            linux-amd64 binary from the official GitHub release
#                            (the projected model counter used by the paper).
# Python packages (clingo) are installed by environment/setup.sh.
# Benchmark programs are tracked in git (data/train/ and eval/test/); they are
# regenerated only by data/make_benchmarks.py / eval/test/build_hidden.py.

set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p data/downloads

GANAK_URL="https://github.com/meelgroup/ganak/releases/download/release/v2.8.0/ganak-v2.8.0-linux-amd64.tar.gz"
GANAK_TGZ_SHA256="bea7150787a1e8f2b1bd658cb5a3c227d631d25054f5ff77ce23422e1c8b040c"
GANAK_BIN_SHA256="934a79a3db2f5b3928ce89edde20837f652e4679b099320ac71c198699c709dd"

if [ -x data/downloads/ganak ] && echo "${GANAK_BIN_SHA256}  data/downloads/ganak" | sha256sum -c --status; then
  echo "GANAK present: data/downloads/ganak"
else
  tmpdir="$(mktemp -d)"
  trap 'rm -rf "$tmpdir"' EXIT
  curl -fsSL --retry 3 -o "$tmpdir/ganak.tar.gz" "$GANAK_URL"
  echo "${GANAK_TGZ_SHA256}  $tmpdir/ganak.tar.gz" | sha256sum -c -
  tar -xzf "$tmpdir/ganak.tar.gz" -C "$tmpdir" ganak
  install -m 0755 "$tmpdir/ganak" data/downloads/ganak
  echo "${GANAK_BIN_SHA256}  data/downloads/ganak" | sha256sum -c -
  echo "GANAK installed: data/downloads/ganak"
fi
