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
(paste 3-4 lines from results/page_degradation.csv and vm_summary.csv)

## AI assistance disclosure
Code scaffolding and report template were generated with Claude (Anthropic); I ran all experiments, verified outputs, and wrote the analysis.
