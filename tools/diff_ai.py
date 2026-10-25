"""列出实战选择和 Mortal 推荐率差异明显的地方，作为挑错题的候选（是不是错题仍按自己的分析判断）。
用法: python tools/diff_ai.py report.json [out.txt] [--gap 0.4]
差异明显：Mortal 第一推荐率 - 实战选择的推荐率 >= gap（默认 0.4）。"""
import json,sys
args=[a for a in sys.argv[1:] if not a.startswith('--')]
gap=float(sys.argv[sys.argv.index('--gap')+1]) if '--gap' in sys.argv else 0.4
if '--gap' in sys.argv: args.remove(sys.argv[sys.argv.index('--gap')+1])
r=json.load(open(args[0],encoding='utf-8'))
out=open(args[1],'w',encoding='utf-8') if len(args)>1 else sys.stdout
me=r.get('player_id',0)

def name(a):
    t=a['type']
    return a['pai'] if t=='dahai' else {'pon':'碰','chi':'吃','daiminkan':'杠','ankan':'暗杠','kakan':'加杠','none':'跳过','reach':'立直','hora':'和'}.get(t,t)

# 按局数出每局自己第几次切牌，方便对上 questions.json 的 src.discard
nd={}; label=[]
for ev in r['mjai_log']:
    if ev['type']=='start_kyoku': k=f"{ev['bakaze']}{ev['kyoku']}-{ev['honba']}"; label.append(k); nd[k]=0
for ki,k in enumerate(r['review']['kyokus']):
    lab=label[ki]; n=0
    for e in k['entries']:
        acc={}
        for d in e['details']:
            acc[name(d['action'])]=acc.get(name(d['action']),0)+d['prob']
        act=name(e['actual'])
        top=max(acc.items(),key=lambda x:x[1])
        if e['actual']['type']=='dahai': n+=1
        if top[1]-acc.get(act,0)>=gap:
            ranks=' '.join(f"{a}:{p:.2f}" for a,p in sorted(acc.items(),key=lambda x:-x[1])[:4])
            where=f"第{n}打" if e['actual']['type']=='dahai' else f"第{e.get('junme','?')}巡"
            out.write(f"{lab} {where} 手[{' '.join(e['state']['tehai'])}] 摸{e['tile']} | 实战 {act}:{acc.get(act,0):.2f} | Mortal {ranks}\n")
