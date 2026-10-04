#!/usr/bin/env python3
"""Fixed memory+CPU workload. SAME work in every experiment (only VM resources change).
W worker processes, each owns (TOTAL_MB/W) MB, does sequential then random page touches + small compute."""
import os, sys, time, random, resource, multiprocessing as mp

TOTAL_MB = int(os.environ.get("TOTAL_MB", 1536))   # total working set (fixed)
WORKERS  = int(os.environ.get("WORKERS", 4))       # fixed
RANDOM_TOUCHES = int(os.environ.get("TOUCHES", 400000))  # per worker (fixed)
PAGE = 4096

def worker(_):
    random.seed(42)
    n = TOTAL_MB // WORKERS * 1024 * 1024
    buf = bytearray(n)
    pages = n // PAGE
    for p in range(pages):                 # sequential pass (locality)
        buf[p * PAGE] = 1
    acc = 0
    for _i in range(RANDOM_TOUCHES):       # random pass (stress)
        p = random.randrange(pages)
        buf[p * PAGE] = (buf[p * PAGE] + 1) & 255
        acc += (p * 31) % 7                # tiny compute
    for p in range(pages):                 # final sequential pass
        acc += buf[p * PAGE]
    return acc

def vmstat():
    d = {}
    with open("/proc/vmstat") as f:
        for l in f:
            k, v = l.split(); d[k] = int(v)
    return d

if __name__ == "__main__":
    v0 = vmstat(); t0 = time.time()
    with mp.Pool(WORKERS) as pool:
        pool.map(worker, range(WORKERS))
    wall = time.time() - t0; v1 = vmstat()
    r = resource.getrusage(resource.RUSAGE_CHILDREN)
    out = dict(wall_s=round(wall, 3), user_s=round(r.ru_utime, 3), sys_s=round(r.ru_stime, 3),
               minflt=r.ru_minflt, majflt=r.ru_majflt,
               pswpin=v1["pswpin"] - v0["pswpin"], pswpout=v1["pswpout"] - v0["pswpout"],
               cpu_pct=round(100 * (r.ru_utime + r.ru_stime) / wall, 1))
    print(",".join(f"{k}={v}" for k, v in out.items()))
