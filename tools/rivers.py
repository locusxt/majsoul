import json,sys
r=json.load(open(sys.argv[1],encoding='utf-8'))
out=open(sys.argv[2],'w',encoding='utf-8')
log=r['mjai_log']; ki=-1
for ev in log:
    t=ev['type']
    if t=='start_kyoku':
        ki+=1; disc={i:[] for i in range(4)}; out.write(f"\n## {ev['bakaze']}{ev['kyoku']}-{ev['honba']} 亲P{ev['oya']} dora指示{ev['dora_marker']}\n")
    elif t=='dahai': disc[ev['actor']].append(ev['pai']+('*' if ev['tsumogiri'] else ''))
    elif t=='reach': disc[ev['actor']].append('[R]')
    elif t in('chi','pon','daiminkan'): disc[ev['actor']].append(f"[{t}{ev['pai']}<P{ev['target']}]")
    if t=='dahai' and ev['actor']==0:
        out.write(f"  P0第{len([x for x in disc[0] if not x.startswith('[')])}打 {ev['pai']} | " + ' || '.join(f"P{i}:{' '.join(disc[i])}" for i in (1,2,3))+"\n")
    if t in('hora','ryukyoku'): out.write(f"  END {t} {ev.get('actor')}<-{ev.get('target')} {ev.get('deltas')}\n")
