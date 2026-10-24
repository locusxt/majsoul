"""牌效公共函数：牌序、向听数（一般形 + 七对子）、有效牌。"""
from functools import lru_cache
ORDER=[f"{n}{s}" for s in 'mps' for n in range(1,10)]+list('ESWNPFC')
def norm(t): return t[:2] if t.endswith('r') else t
def idx(t): return ORDER.index(norm(t))
@lru_cache(None)
def _std(c,melds_need):
    # min shanten for standard form with counts tuple
    best=[8]
    c=list(c)
    def dfs(i,m,t,p):
        while i<34 and c[i]==0: i+=1
        if i>=34:
            mm=min(m,melds_need); tt=min(t,melds_need-mm)
            s=2*(melds_need-mm)-tt-p
            best[0]=min(best[0],s); return
        if c[i]>=3:
            c[i]-=3; dfs(i,m+1,t,p); c[i]+=3
        if i<27 and i%9<=6 and c[i+1] and c[i+2]:
            c[i]-=1;c[i+1]-=1;c[i+2]-=1; dfs(i,m+1,t,p); c[i]+=1;c[i+1]+=1;c[i+2]+=1
        if c[i]>=2:
            if not p:
                c[i]-=2; dfs(i,m,t,1); c[i]+=2
            c[i]-=2; dfs(i,m,t+1,p); c[i]+=2
        if i<27 and i%9<=7 and c[i+1]:
            c[i]-=1;c[i+1]-=1; dfs(i,m,t+1,p); c[i]+=1;c[i+1]+=1
        if i<27 and i%9<=6 and c[i+2]:
            c[i]-=1;c[i+2]-=1; dfs(i,m,t+1,p); c[i]+=1;c[i+2]+=1
        c[i]-=1; dfs(i+1,m,t,p); c[i]+=1
    dfs(0,0,0,0); return best[0]
def shanten(c,nfuuro):
    s=_std(tuple(c),4-nfuuro)
    if nfuuro==0:
        pairs=sum(1 for x in c if x>=2); kinds=sum(1 for x in c if x>=1)
        s=min(s,6-pairs+max(0,7-kinds))
    return s
def ukeire(c,nf,visible):
    s=shanten(c,nf); tot=0; tiles=[]
    for i in range(34):
        if c[i]>=4: continue
        c[i]+=1
        if shanten(c,nf)<s:
            left=4-visible[i]-c[i]+1
            if left>0: tot+=left; tiles.append(ORDER[i])
        c[i]-=1
    return s,tot,tiles
