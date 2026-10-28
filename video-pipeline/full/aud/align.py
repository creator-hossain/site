# -*- coding: utf-8 -*-
"""Word timings without ASR: transcript segments (trusted starts) + pause detection.

Strong pauses (>= MIN_PAUSE) split each segment into spans. A DP assigns contiguous
word groups to spans so that each span's voiced duration matches its words' spoken
length; inside a span words are spread over voiced time by spoken length.
"""
import json, numpy as np

MIN_PAUSE = 0.15
BONUS = 0.12
iv = json.load(open("voiced.json"))

SEGS = [  # (start, end, [(display, spoken-for-weighting)])
 (0.03, 5.55, "আপনারা কিন্তু ইতোমধ্যেই আমাদের চিটাগাং স্টকের করোলা ক্রস সম্পর্কে ধারণা চলে এসেছে।"),
 (5.55, 15.27, "বেশ কয়েকটি ইউনিট কিন্তু আমাদের চিটাগাং রেডি স্টকে অ্যাভেলেবল, সাথে কিন্তু আমাদের শোরুমেও "
               "পার্ল কালার এবং ব্ল্যাক কালার, দুইটাই কিন্তু অ্যাভেলেবল পেয়ে যাচ্ছেন।"),
 (15.27, 23.85, "আমার সামনে যে গাড়িটা দেখতেছেন, ZVG13 এর 2023 এর মডেল, পার্ল কালার টু টোন। "
                "উপরে হার্ড টপ এবং মডেলিস্টা বডি কিট সহ"),
 (23.85, 31.59, "গাড়িটির সঙ্গে কিন্তু অটো পার্কিং, 360 ক্যামেরা, অ্যালয় হুইলস, ফগ লাইট, সিট হিটার, "
                "ক্রুজ কন্ট্রোল, সবকিছুই কিন্তু পাচ্ছেন।"),
 (31.59, 35.73, "গাড়িটির মাইলেজ আছে মাত্র 33,000 কিলো, এবং অকশন গ্রেড রয়েছে ফোর।"),
 (35.73, 41.80, "দেরি না করে আজই ভিজিট করুন আমাদের শোরুম; আমাদের শোরুমের ঠিকানা: আব্দুল হামিদ রোড, পাবনা সদর, পাবনা।"),
]
SPOKEN = {"ZVG13": "জেডভিজি থার্টিন", "2023": "টুয়েন্টি টুয়েন্টি থ্রি",
          "360": "থ্রি সিক্সটি", "33,000": "তেত্রিশ হাজার"}
def weight(w):
    s = SPOKEN.get(w, w)
    return sum(1 for ch in s if ch not in "\u09cd\u09bc\u200c\u200d") + 1.2   # vowel signs count, virama/nukta do not

out = []
for s, e, text in SEGS:
    raw = text.split()
    PUNCT = ",;:।—"
    brk = [w[-1] in PUNCT for w in raw]            # pause expected AFTER this word
    words = [w.rstrip(PUNCT) for w in raw]
    W = [weight(w) for w in words]
    vin = [(max(a, s), min(b, e)) for a, b in iv if b > s and a < e]
    spans, cur = [], [vin[0]]                      # merge chunks across short dips
    for a, b in vin[1:]:
        if a - cur[-1][1] >= MIN_PAUSE: spans.append(cur); cur = [(a, b)]
        else: cur.append((a, b))
    spans.append(cur)
    K, N = len(spans), len(words)
    dur = [sum(b - a for a, b in sp) for sp in spans]
    rate = sum(dur) / sum(W)
    pre = np.concatenate([[0], np.cumsum(W)])
    INF = 1e18
    dp = np.full((K + 1, N + 1), INF); bk = np.zeros((K + 1, N + 1), int); dp[0, 0] = 0
    for k in range(1, K + 1):
        for j in range(k, N - (K - k) + 1):
            for i in range(k - 1, j):
                c = dp[k - 1, i] + (dur[k - 1] - rate * (pre[j] - pre[i])) ** 2 / max(dur[k - 1], 0.05)
                if j < N: c += -BONUS if brk[j - 1] else 0.0     # span ends where the text has a comma
                if c < dp[k, j]: dp[k, j], bk[k, j] = c, i
    cuts, j = [], N
    for k in range(K, 0, -1): i = bk[k, j]; cuts.append((i, j)); j = i
    cuts.reverse()
    for (i, j), sp in zip(cuts, spans):
        # map cumulative spoken length onto voiced time within the span
        vt = sum(b - a for a, b in sp); tot = pre[j] - pre[i]
        def at(x):                                  # voiced-time offset -> real time
            for a, b in sp:
                if x <= b - a: return a + x
                x -= b - a
            return sp[-1][1]
        for k in range(i, j):
            st = at(vt * (pre[k] - pre[i]) / tot); en = at(vt * (pre[k + 1] - pre[i]) / tot)
            out.append({"w": words[k], "t": round(st, 3), "e": round(en, 3)})
    print(" | ".join(" ".join(words[i:j]) for i, j in cuts))
json.dump(out, open("words.json", "w"), ensure_ascii=False, indent=0)
print(len(out), "words")
