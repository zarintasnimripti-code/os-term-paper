#!/usr/bin/env python3
"""Track 1: FIFO / LRU / Optimal vs learned eviction (logistic regression), with a mid-trace pattern shift."""
import random, collections, numpy as np, pandas as pd, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier

NPAGES, FRAMES, LEN = 200, 16, 20000
MODEL = "logreg"   # or "tree"

def gen_trace(seed, n=LEN):
    """first half: locality-heavy loop over small hot set; second half: random + bursts"""
    r = random.Random(seed); t = []; half = n // 2
    hot = list(range(24)); i = 0
    while len(t) < half:
        if r.random() < 0.85: t.append(hot[i % len(hot)]); i += 1
        else: t.append(r.choice(hot))
    while len(t) < n:
        if r.random() < 0.15:
            b = r.randrange(NPAGES - 8); t += [b + r.randrange(8) for _ in range(r.randint(5, 20))]
        else: t.append(r.randrange(NPAGES))
    return t[:n]

def next_use(trace):
    nxt = [0] * len(trace); last = {}
    for i in range(len(trace) - 1, -1, -1):
        nxt[i] = last.get(trace[i], 10**9); last[trace[i]] = i
    return nxt

def feats(p, t, last, cnt, hist):
    age = t - last[p]
    recent = sum(1 for x in hist if x == p)   # frequency in last 64 accesses
    return [age, np.log1p(age), cnt[p], recent]

def make_model(k): return LogisticRegression(max_iter=500) if k == "logreg" else DecisionTreeClassifier(max_depth=4)

def simulate(trace, policy, model=None, retrain=None):
    nxt = next_use(trace); mem = {}; fifo = collections.deque()
    last, cnt, hist = {}, collections.Counter(), collections.deque(maxlen=64)
    hits = []; bufX, bufy = [], []; m = model
    for t, p in enumerate(trace):
        hit = p in mem; hits.append(hit)
        if not hit and len(mem) >= FRAMES:
            if policy == "FIFO": v = fifo[0]
            elif policy == "LRU": v = min(mem, key=lambda q: last[q])
            elif policy == "OPT": v = max(mem, key=lambda q: mem[q])
            else:
                cand = list(mem); X = [feats(q, t, last, cnt, hist) for q in cand]
                v = cand[int(np.argmax(m.predict_proba(X)[:, 1]))] if m is not None else min(mem, key=lambda q: last[q])
                if retrain:
                    for q, x in zip(cand, X): bufX.append(x); bufy.append(int(mem[q] - t > FRAMES * 2))
            fifo.remove(v); del mem[v]
        if not hit: fifo.append(p)
        mem[p] = nxt[t]
        last[p] = t; cnt[p] += 1; hist.append(p)
        if policy == "LEARN" and retrain and (t + 1) % retrain == 0 and len(set(bufy[-4000:])) > 1:
            m = make_model(MODEL).fit(bufX[-4000:], bufy[-4000:])
    return hits

def train_static(seed):
    """trained only on PRE-shift (locality) behaviour -> exposes degradation after shift"""
    tr = gen_trace(seed + 999)[:LEN // 2]; nxt = next_use(tr)
    mem = {}; last, cnt, hist = {}, collections.Counter(), collections.deque(maxlen=64); X, y = [], []
    for t, p in enumerate(tr):
        if p not in mem and len(mem) >= FRAMES:
            for q in mem: X.append(feats(q, t, last, cnt, hist)); y.append(int(mem[q] - t > FRAMES * 2))
            del mem[min(mem, key=lambda q: last[q])]
        mem[p] = nxt[t]; last[p] = t; cnt[p] += 1; hist.append(p)
    if len(set(y)) < 2: raise SystemExit("training labels single-class; adjust trace")
    return make_model(MODEL).fit(X, y)

if __name__ == "__main__":
    rows = []; roll = {}; half = LEN // 2
    for seed in range(10):
        tr = gen_trace(seed); static = train_static(seed)
        for name, pol, mdl, rt in [("FIFO","FIFO",None,None),("LRU","LRU",None,None),("OPT","OPT",None,None),
                                   ("Learned-static","LEARN",static,None),("Learned-adaptive","LEARN",static,500)]:
            h = np.array(simulate(tr, pol, mdl, rt))
            for ph, seg in [("before_shift", h[:half]), ("after_shift", h[half:])]:
                rows.append(dict(seed=seed, policy=name, phase=ph, hit_ratio=seg.mean(), faults=int((~seg).sum())))
            if seed == 0: roll[name] = pd.Series(h.astype(float)).rolling(500).mean()
    d = pd.DataFrame(rows); d.to_csv("../results/page_raw.csv", index=False)
    s = d.groupby(["policy","phase"]).agg(hit_mean=("hit_ratio","mean"), hit_std=("hit_ratio","std"),
                                          faults_mean=("faults","mean")).round(4).reset_index()
    s.to_csv("../results/page_summary.csv", index=False)
    piv = s.pivot(index="policy", columns="phase", values="hit_mean")
    piv["degradation"] = piv["before_shift"] - piv["after_shift"]
    print(piv.round(3)); piv.round(4).to_csv("../results/page_degradation.csv")
    piv[["before_shift","after_shift"]].plot.bar(figsize=(7,4)); plt.ylabel("Hit ratio (mean of 10 seeds)")
    plt.title("Hit ratio before vs after shift"); plt.tight_layout(); plt.savefig("../results/page_hit_ratio.png", dpi=200); plt.close()
    plt.figure(figsize=(8,4))
    for k, v in roll.items(): plt.plot(v, label=k)
    plt.axvline(half, color="k", ls="--"); plt.legend(); plt.xlabel("Access #"); plt.ylabel("Rolling hit ratio (500)")
    plt.title("Hit ratio over time (dashed = shift)"); plt.tight_layout(); plt.savefig("../results/page_rolling.png", dpi=200)
