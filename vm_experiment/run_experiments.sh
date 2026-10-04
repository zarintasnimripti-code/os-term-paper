#!/usr/bin/env bash
# Usage: ./run_experiments.sh <RAM_GB> <vCPUs> [reps=5]
# Run once per VMware configuration (after changing VM settings & rebooting). Appends to ../results/vm_raw.csv
RAM=$1; CPU=$2; REPS=${3:-5}
OUT="$(dirname "$0")/../results/vm_raw.csv"
[ -f "$OUT" ] || echo "ram_gb,vcpu,rep,mem_total_mb,swap_total_mb,nproc,wall_s,user_s,sys_s,minflt,majflt,pswpin,pswpout,cpu_pct" > "$OUT"
MT=$(awk '/MemTotal/{printf "%d",$2/1024}' /proc/meminfo)
ST=$(awk '/SwapTotal/{printf "%d",$2/1024}' /proc/meminfo)
NP=$(nproc)
for i in $(seq 1 $REPS); do
  sync; echo 3 | sudo tee /proc/sys/vm/drop_caches >/dev/null   # fair start
  sudo swapoff -a && sudo swapon -a                              # clear swap
  LINE=$(python3 "$(dirname "$0")/workload.py")
  VALS=$(echo "$LINE" | sed 's/[a-z_]*=//g')
  echo "$RAM,$CPU,$i,$MT,$ST,$NP,$VALS" >> "$OUT"
  echo "[RAM=${RAM}G vCPU=$CPU rep=$i] $LINE"
done
