#!/bin/bash
# Bash strict mode, to help catch problems and bugs in the shell
set -euo pipefail
# No manual feedback
export DEBIAN_FRONTEND=noninteractive
# Install security updates:
apt-get update
apt-get -y upgrade
# Upgrade pip
pip install --upgrade pip
# Cleanup
apt-get clean
rm -rf /var/lib/apt/lists/*
