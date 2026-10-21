#!/usr/bin/env bash
# A memory guard for a training job on the 6 GB card under WSL2 (K3).
#
# Samples nvidia-smi every INTERVAL seconds into CSV (memory.used MiB, GPU
# utilisation %, host MemAvailable MiB) while a process matching PATTERN runs,
# and kills that process (SIGTERM, then SIGKILL after 10 s) the first time the
# card's used memory exceeds LIMIT MiB. Under WSL2 an allocation past the card's
# memory spills into shared host memory instead of failing; the K3 kraken pilots
# of 21 October 2026 climbed to 5.9 GB that way and the machine crashed. The
# guard stops a job before it gets there; the CSV is the job's memory record.
#
#   tools/gpu-guard.sh '<pgrep pattern>' <limit MiB> <csv> [interval s]
set -u
pattern=${1:?pgrep pattern}
limit=${2:?limit in MiB}
csv=${3:?csv path}
interval=${4:-2}
mkdir -p "$(dirname "$csv")"
echo "# guard start $(date -Is) pattern=$pattern limit=${limit}MiB" >> "$csv"
while pgrep -f "$pattern" >/dev/null; do
  line=$(nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader,nounits 2>/dev/null | head -1)
  avail=$(awk '/MemAvailable/ {print int($2/1024)}' /proc/meminfo)
  echo "$(date +%s),${line// /},$avail" >> "$csv"
  used=${line%%,*}
  if [ -n "$used" ] && [ "$used" -gt "$limit" ]; then
    echo "# guard kill $(date -Is): used ${used} MiB > ${limit} MiB" >> "$csv"
    pkill -TERM -f "$pattern"
    sleep 10
    pkill -KILL -f "$pattern" 2>/dev/null
    break
  fi
  sleep "$interval"
done
echo "# guard end $(date -Is)" >> "$csv"
