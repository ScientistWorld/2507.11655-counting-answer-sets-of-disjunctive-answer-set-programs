#!/bin/bash
# Download all data and models needed for this environment.
#
# Run on a node with internet access BEFORE building the container
# or submitting compute jobs.
#
# This script should be idempotent — safe to run multiple times.
# It should skip files that already exist.
#
# Update the storage estimate below as you add downloads.
#
# Estimated total download size: 0 GB
# Estimated disk usage after extraction: <1 MB
#
# No external downloads are needed. The benchmark instances are generated
# deterministically into data/ so a future user with just the workspace can
# reproduce them.

set -e

cd /home/user

python data/make_benchmarks.py
