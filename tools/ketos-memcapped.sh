#!/usr/bin/env bash
# ketos inside a systemd user scope with a hard memory cap (K3, 22 October 2026):
# the kernel's OOM killer then takes ketos before the WSL2 VM runs out of memory,
# which is how the machine went down twice that morning. Pass it to
# `leibniz bench train-kraken --ketos tools/ketos-memcapped.sh`; the cap is
# KETOS_MEMORY_MAX (default 7G); the environment goes through unchanged.
set -u
exec systemd-run --user --scope -p "MemoryMax=${KETOS_MEMORY_MAX:-7G}" --quiet \
  "${KETOS_BIN:-ketos}" "$@"
