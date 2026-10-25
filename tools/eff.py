"""对每次 P0 切牌：计算各候选切牌的向听数/有效进张（扣除可见牌），以及对立直家的安全度（现物含立直后别家打出、立直家没和的牌）。
用法: python tools/eff.py report.json out.txt [player]"""
import json,sys
r=json.load(open(sys.argv[1],encoding='utf-8')); out=open(sys.argv[2],'w',encoding='utf-8')
me=int(sys.argv[3]) if len(sys.argv)>3 else r.get('player_id',0)
from mj import ORDER,norm,idx,shanten,ukeire
kyoku=None
for ev in r['mjai_log']:
    t=ev['type']
    if t=='start_kyoku':
        kyoku=f"{ev['bakaze']}{ev['kyoku']}-{ev['honba']}"; hand=[norm(x) for x in ev['tehais'][me]]; nf=0
        vis=[0]*34; vis[idx(ev['dora_marker'])]+=1; riv={i:[] for i in range(4)}; reach={}; after={}; turn=0
        out.write(f"\n## {kyoku} 亲P{ev['oya']} dora指示{ev['dora_marker']}\n")
    elif t=='dora': vis[idx(ev['dora_marker'])]+=1
    elif t=='tsumo' and ev['actor']==me: hand.append(norm(ev['pai']))
    elif t=='reach': reach[ev['actor']]=len(riv[ev['actor']]); after[ev['actor']]=set()
    elif t in('chi','pon','daiminkan','ankan','kakan'):
        if ev['actor']==me:
            for x in ev['consumed']: hand.remove(norm(x))
            nf+=1
        else:
            for x in ev['consumed']: vis[idx(x)]+=1
    elif t=='dahai':
        a=ev['actor']; p=norm(ev['pai'])
        if a==me:
            turn+=1
            c=[0]*34
            for x in hand: c[idx(x)]+=1
            res=[]
            for d in sorted(set(hand),key=idx):
                c[idx(d)]-=1; s,u,tl=ukeire(c,nf,vis); c[idx(d)]+=1
                safe=[]
                for o,ri in reach.items():
                    # 现物：立直家自己打过的，或立直后任何人打出、立直家没和的（立直后见逃即振听）
                    gen = d in [norm(x) for x in riv[o]] or d in after[o]
                    safe.append(f"P{o}:{'现物' if gen else '生'}")
                res.append((s,-u,d,tl,safe))
            res.sort()
            best=res[0]
            mine=[x for x in res if x[2]==p][0]
            flag='' if (mine[0],mine[1])==(best[0],best[1]) else '  <<差'
            out.write(f" {turn}打 手[{' '.join(sorted(hand,key=idx))}] 副露{nf} 实切{p}: {mine[0]}向听 {-mine[1]}枚 {' '.join(mine[4])}{flag}\n")
            for s,u,d,tl,sf in res[:5]:
                out.write(f"      切{d}: {s}向听 {-u}枚 {''.join(tl)} {' '.join(sf)}\n")
            hand.remove(p)
        else:
            vis[idx(p)]+=1
        riv[a].append(p)
        for o in after: after[o].add(p)
