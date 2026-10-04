#!/usr/bin/env bash
# One-time: make sure a 3GB swapfile exists so low-RAM runs thrash instead of getting OOM-killed
[ -f /swapfile ] || { sudo fallocate -l 3G /swapfile; sudo chmod 600 /swapfile; sudo mkswap /swapfile; }
grep -q swapfile /etc/fstab || echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
sudo swapon -a; free -m; nproc
