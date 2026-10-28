# -*- coding: utf-8 -*-
"""Measure SFX class levels in the SIDE channel, same way for reference and output."""
import numpy as np, json, wave, sys
def load(p):
    w=wave.open(p); a=np.frombuffer(w.readframes(w.getnframes()),np.int16).reshape(-1,2).astype(np.float32)/32768; return a, w.getframerate()
def r10(x,sr):
    h=sr//100; n=len(x)//h; return 20*np.log10(np.sqrt((x[:n*h].reshape(n,h)**2).mean(1))+1e-9)
def pk(arr,t,d=0.35): i=max(0,int(t*100)); return arr[i:i+int(d*100)].max()
def classes(wav, events):
    a,sr=load(wav); side=r10((a[:,0]-a[:,1])/2,sr); v=np.percentile(r10(a.mean(1),sr),90)
    return {k:float(np.median([pk(side,t)-v for t in ts])) for k,ts in events.items() if ts}
REF_EVENTS={"boom":[73.92,26.88],"riser":[73.49,26.13],"swoosh":[27.15,40.15,3.65],"chime":[29.74,31.80],
            "swish":[0.40,8.98,37.71],"thump":[59.74,60.64,61.84],"pop":[16.80,16.92,19.17],"tick":[48.96,54.83]}
if __name__=="__main__":
    log=json.load(open(sys.argv[2])); mine_ev={}
    # only isolated cues (no other cue within 0.4 s) so overlaps don't inflate the reading
    starts=[s for s,_,_,_ in log]
    for s,ev,snd,g in log:
        near=[ (ss,so) for ss,_,so,_ in log if abs(ss-s)<0.4 and not (ss==s and so==snd)]
        if snd in REF_EVENTS and (not near or (snd=='boom' and all(so=='riser' for _,so in near))) and g>=sorted([gg for _,_,so,gg in log if so==snd])[-1]-0.01:
            mine_ev.setdefault(snd,[]).append(s)
    ref=classes("aud/ref.wav",REF_EVENTS); mine=classes(sys.argv[1],mine_ev)
    print(f"{'sound':<8}{'REF':>8}{'MINE':>8}{'adjust':>8}")
    adj={}
    for k in REF_EVENTS:
        if k in mine: adj[k]=round(ref[k]-mine[k],1); print(f"{k:<8}{ref[k]:8.1f}{mine[k]:8.1f}{adj[k]:8.1f}  n={len(mine_ev[k])}")
        else: print(f"{k:<8}{ref[k]:8.1f}{'-':>8}")
    json.dump(adj,open("calib_adj.json","w"))
