# OS Term Paper: Memory Management & Virtualization under Resource Constraints

Two parts, one theme (page replacement / memory pressure):
1. **VM experiment** (`vm_experiment/`): same workload in Ubuntu/VMware under 3 RAM x 3 vCPU settings; measures runtime, page faults, swap, CPU.
2. **Page-replacement simulator** (`page_sim/`, Track 1): FIFO, LRU, Optimal vs a learned eviction policy (logistic regression), with a locality -> random workload shift.

## Setup
    sudo apt update && sudo apt install -y python3-pip
    pip3 install -r requirements.txt

## Run
    # Part 2 (any machine, ~40 s)
    cd page_sim && python3 pagesim.py
    # Part 1 (inside the Ubuntu VM; repeat per VMware config)
    bash vm_experiment/setup_swap.sh
    bash vm_experiment/run_experiments.sh <RAM_GB> <vCPUs> 5
    python3 vm_experiment/analyze_vm.py        # run from repo root
Outputs: `results/*.csv`, `results/*.png`.

## Summary of results

- VM experiment: with 4 GB vRAM the 1.5 GB workload finishes in 2-4 s with no swapping; with 2 GB it takes 64-101 s (16-44x slower) with 172k-239k major faults. At 1 GB the OS terminated the workload.
- Page replacement: a learned eviction model trained only before the workload shift degraded most (hit ratio 0.655 -> 0.201); retraining every 500 references recovered part of the loss (0.374). Optimal is the upper bound (0.699 -> 0.545).
- Full details: report/report.pdf, tables in results/vm_summary.csv and results/page_degradation.csv.

## AI assistance disclosure
Code scaffolding and report template were generated with Claude (Anthropic); I ran all experiments, verified outputs, and wrote the analysis.
