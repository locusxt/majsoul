import json,sys
r=json.load(open(sys.argv[1],encoding='utf-8'))
print({k:v for k,v in r.items() if k not in('review','mjai_log','split_logs')}.keys())
for k,v in r.items():
    if k!='review': print(k, str(v)[:300])
rv=r['review']
print('total',rv['total_reviewed'],rv['total_matches'],rv['rating'])
winds='ESWN'
def fmt(a):
    if a is None: return 'None'
    t=a['type']
    if t=='dahai': return f"切{a['pai']}"+("(摸切)" if a.get('tsumogiri') else "")
    if t in('chi','pon','daiminkan','ankan','kakan'): return f"{t} {a.get('pai','')} {a.get('consumed','')}"
    return t
for k in rv['kyokus']:
    kn=k['kyoku']; print(f"\n=== {winds[kn//4]}{kn%4+1}局 {k['honba']}本场 分数{k['relative_scores']} 结束{[ (e['type'],e.get('actor'),e.get('target'),e.get('deltas')) for e in k['end_status']]}")
    for e in k['entries']:
        if e['is_equal']: continue
        d=e['details']; ex=e['expected']; ac=e['actual']
        qe=d[0]['q_value']; qa=None; pa=None
        for x in d:
            if x['action']==ac: qa=x['q_value']; pa=x['prob']
        th=' '.join(e['state']['tehai']); fu=e['state']['fuuros']
        print(f" 巡{e['junme']} 余{e['tiles_left']} 摸/见{e['tile']} 手[{th}] 副露{fu} | AI:{fmt(ex)} 你:{fmt(ac)} Δq={None if qa is None else round(qe-qa,3)} p你={None if pa is None else round(pa,4)} 立直时={e['at_self_riichi']} 鸣={e['at_self_chi_pon']}")
