# -*- coding: utf-8 -*-
"""script.txt -> spec.json ; word times spread across each segment by character weight."""
import json, re, sys

MERGE_GAP = 0.20     # room for the shrink-into-history move

segs, cur = [], None
for raw in open(sys.argv[1], encoding="utf-8"):
    line = raw.strip()
    if not line or line.startswith("#"):
        continue
    m = re.match(r"^SEG\s+([\d.]+)\s+([\d.]+)$", line)
    if m:
        cur = {"start": float(m.group(1)), "end": float(m.group(2)), "phrases": []}
        segs.append(cur); continue
    for ph in line.split("|"):
        ws = ph.split()
        if ws: cur["phrases"].append(ws)

out = []
for s in segs:
    flat = [w for ph in s["phrases"] for w in ph]
    weight = [len(w.lstrip("*")) + 1.6 for w in flat]       # +1.6 ~ inter-word pause
    tot = sum(weight)
    span = s["end"] - s["start"]
    t, times = s["start"], []
    for wt in weight:
        times.append(round(t, 3)); t += span * wt / tot
    phrases, k = [], 0
    for pi, ph in enumerate(s["phrases"]):
        words = []
        for w in ph:
            gold = w.startswith("*")
            words.append([w.lstrip("*"), "g" if gold else "w", times[k]]); k += 1
        nxt = times[k] if k < len(times) else s["end"]
        end = nxt - MERGE_GAP if k < len(times) else s["end"]
        phrases.append({"words": words, "end": round(max(end, words[-1][2] + 0.12), 3)})
    out.append({"phrases": phrases})

json.dump(out, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"{len(out)} segments, {sum(len(s['phrases']) for s in out)} phrases, "
      f"{sum(len(p['words']) for s in out for p in s['phrases'])} words")
