#!/bin/bash
# Install Python packages into the container overlay.
#
# This script is run by the system on the login node (which has internet)
# inside the container with a persistent overlay. Changes persist across
# job submissions without rebuilding the container.
#
# Put ALL pip installs here, NOT in container.def.
# Only use container.def for the base Docker image and apt-get packages.
#
# IMPORTANT: Install into the SYSTEM Python, not a virtual environment.
# Use: uv pip install --system <packages>

set -e

# clingo: answer-set enumeration (the paper's enumeration baseline and the
# enumeration stage of the paper's hybrid counter).
uv pip install --system "clingo==5.8.3"

# The GANAK model counter is a static binary fetched by scripts/download.sh into
# data/downloads/ganak (inside the bind-mounted workspace).
