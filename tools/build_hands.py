"""由人工题目 + Mortal 报告生成错题本题库。
用法: python tools/build_hands.py practice/questions.json practice/hands.json practice/seed  records/<报告>.json [更多报告...]
报告文件名以对局日期开头，题目按 date 找同一天的报告。

questions.json 每题只写人工判断的部分：
  id, date, category(牌效/防守/副露), type(discard/call/riichi), src, answers, lesson, explain, situation
  可选: added（加入题库的日期，默认等于 date）, notes {牌: 备注}（选项表备注列）, threat [座位]（没有立直时也按这些人算现物/生张，如 ["上家"]）
  副露题另写: choices（如 ["吃","不碰"]，"不碰"显示为跳过）, options（各选择的向听、有效牌、备注，cut 填选择名）
  立直题（听牌时立不立）: choices ["立直","不立直"], options 同上；src 用 discard，实战按当时有没有宣言立直判定
src: {"kyoku":"E1-1","discard":5}（第 5 次切牌前）、{"kyoku":"E4-1","call":true,"n":1}（第 1 次副露前）
     或 {"kyoku":"E1-1","pass":{"tile":"8s","n":1}}（别家第 1 次打出 8s、你没鸣的时候）

自动生成：手牌、摸牌、实战、巡目、选项表（向听、有效牌含七对子 / 只算一般形、现物或生张）、
牌桌（四家牌河、副露、点数、余牌、宝牌）、Mortal 推荐率 ai。
同时检查：正解是否在手里、解析里写的「N 枚」能否在选项表里找到。"""
import json,sys,os,re
from collections import Counter
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from mj import ORDER,norm,idx,shanten,_std

qs_path,out_path,seed_dir,*reports=sys.argv[1:]
qs=json.load(open(qs_path,encoding='utf-8'))
LABEL=['自己','下家','对家','上家']; WIND='东南西北'

def snapshot(rep,key,date):
    """回放到 src 指定的时刻（实战动作之前），返回当时的完整状态；找不到返回 None。"""
    me=rep.get('player_id',0); st=None
    for ev in rep['mjai_log']:
        t=ev['type']
        if t=='start_kyoku':
            k=f"{ev['bakaze']}{ev['kyoku']}-{ev['honba']}"
            st=dict(k=k,me=me,oya=ev['oya'],bakaze=ev['bakaze'],kyoku=ev['kyoku'],honba=ev['honba'],kyotaku=ev['kyotaku'],
                    scores=list(ev['scores']),dora=[ev['dora_marker']],left=70,river=[[] for _ in range(4)],all_disc=[[] for _ in range(4)],
                    melds=[[] for _ in range(4)],reach=[False]*4,after=[None]*4,pend=[False]*4,nd=0,nc=0,np=0,hand=list(ev['tehais'][me]),draw=None)
            continue
        if st is None or st['k']!=key['kyoku']: continue
        if t=='dahai' and ev['actor']!=me and 'pass' in key and norm(ev['pai'])==norm(key['pass']['tile']):
            st['np']+=1
            if st['np']==key['pass'].get('n',1): st['act']=ev; return st
        if t=='dahai' and ev['actor']==me and 'discard' in key and st['nd']+1==key['discard']:
            st['act']=ev; return st
        if t in('chi','pon','daiminkan') and ev['actor']==me and key.get('call') and st['nc']+1==key.get('n',1):
            st['act']=ev; return st
        if t=='tsumo':
            st['left']-=1
            if ev['actor']==me: st['hand'].append(ev['pai']); st['draw']=ev['pai']
        elif t=='dora': st['dora'].append(ev['dora_marker'])
        elif t=='reach': st['pend'][ev['actor']]=True; st['after'][ev['actor']]=set()
        elif t=='reach_accepted':
            a=ev['actor']; st['reach'][a]=True; st['scores'][a]-=1000; st['kyotaku']+=1
        elif t=='dahai':
            a=ev['actor']; st['river'][a].append({'t':ev['pai'],'tg':ev['tsumogiri'],'r':st['pend'][a]}); st['pend'][a]=False
            st['all_disc'][a].append(norm(ev['pai']))
            for p in range(4):   # 立直后任何人打出、立直家没和的牌也是现物（见逃振听）
                if st['after'][p] is not None: st['after'][p].add(norm(ev['pai']))
            if a==me: st['nd']+=1; st['hand'].remove(ev['pai']); st['draw']=None
        elif t in('chi','pon','daiminkan','ankan','kakan'):
            a=ev['actor']
            if a==me:
                for x in ev['consumed'] if t!='kakan' else [ev['pai']]: st['hand'].remove(x)
                st['draw']=None
            if t in('chi','pon','daiminkan'):
                st['river'][ev['target']].pop()
                if a==me: st['nc']+=1
            if t=='kakan':
                for m in st['melds'][a]:
                    if len(m['t'])==3 and norm(m['t'][0])==norm(ev['pai']): m['t'].append(ev['pai'])
            elif t=='ankan':
                st['melds'][a].append({'t':list(ev['consumed']),'f':0})
            else:
                # f: 被鸣的牌来自谁（相对鸣牌者）1=下家 2=对家 3=上家；t 的最后一张是被鸣的牌
                st['melds'][a].append({'t':list(ev['consumed'])+[ev['pai']],'f':(ev['target']-a)%4})
    return None

def counts(tiles):
    c=[0]*34
    for t in tiles: c[idx(t)]+=1
    return c

def ukeire2(c,nf,vis):
    """有效牌：(向听, 含七对子的枚数, 一般形向听, 一般形枚数)。vis 为场上可见张数（含自己手牌）。"""
    def uk(f):
        s=f(c); tot=0
        for i in range(34):
            if c[i]>=4: continue
            c[i]+=1
            if f(c)<s: tot+=max(0,4-vis[i])
            c[i]-=1
        return s,tot
    s,u=uk(lambda c:shanten(c,nf)); ss,us=uk(lambda c:_std(tuple(c),4-nf))
    return s,u,ss,us

def build(q,rep,st):
    me=st['me']; nf=len(st['melds'][me])
    seats=[]
    for rel in range(4):
        p=(me+rel)%4
        seats.append({'label':LABEL[rel],'wind':WIND[(p-st['oya'])%4],'score':st['scores'][p],'river':st['river'][p],
                      'melds':st['melds'][p],'riichi':st['reach'][p],'oya':p==st['oya']})
    table={'round':f"{'东南西北'['ESWN'.index(st['bakaze'])]}{st['kyoku']}局",'honba':st['honba'],'kyotaku':st['kyotaku'],
           'left':st['left'],'dora':st['dora'],'seats':seats}
    act=st['act']; hand=sorted(st['hand'],key=lambda t:(idx(t),t))
    o=dict(q); o['table']=table
    if q['type']=='call':
        o['hand']=hand; o['draw']=None
        o['callTile']=act['pai']; o['callFrom']=LABEL[((act['actor'] if act['type']=='dahai' else act['target'])-me)%4]
        o['pick']={'pon':'碰','chi':'吃','daiminkan':'杠','dahai':'不碰'}[act['type']]
        o['turn']=f"第{st['nd']+1}巡"
    elif q['type']=='riichi':
        d=st['draw']
        if d: hand.remove(d)
        o['hand']=hand; o['draw']=d; o['pick']='立直' if st['pend'][me] else '不立直'; o['turn']=f"第{st['nd']+1}打"
        o['riichiTile']=act['pai']
    else:
        d=st['draw']
        if d: hand.remove(d)
        o['hand']=hand; o['draw']=d; o['pick']=act['pai']; o['turn']=f"第{st['nd']+1}打"
        # 选项表
        vis=[0]*34
        for t in st['dora']: vis[idx(t)]+=1
        for s in seats:
            for x in s['river']: vis[idx(x['t'])]+=1
            for m in s['melds']:
                for t in m['t']: vis[idx(t)]+=1
        full=st['hand']
        for t in full: vis[idx(t)]+=1
        threats=[(me+r)%4 for r in range(1,4) if st['reach'][(me+r)%4]]
        threats+=[(me+LABEL.index(l))%4 for l in q.get('threat',[]) if (me+LABEL.index(l))%4 not in threats]
        c=counts(full); rows=[]
        for b in sorted({norm(t) for t in full},key=idx):
            c[idx(b)]-=1; s,u,ss,us=ukeire2(c,nf,vis); c[idx(b)]+=1
            row={'cut':b,'shanten':s,'ukeire':u,'ukStd':us if ss==s else None}
            if threats: row['safe']='现物' if all(b in st['all_disc'][p] or (st['after'][p] and b in st['after'][p]) for p in threats) else '生张'
            note=q.get('notes',{}).get(b)
            if note: row['safe']=(row.get('safe','')+'，' if row.get('safe') else '')+note
            rows.append(row)
        ans={norm(a) for a in q['answers']}
        rows.sort(key=lambda r:(r['shanten'],-r['ukeire'],r['cut'] not in ans))
        miss=ans-{r['cut'] for r in rows}
        if miss: raise SystemExit(f"{q['id']}: 正解 {miss} 不在手牌里")
        best=rows[0]
        show=[r for i,r in enumerate(rows) if i<3 or r['cut'] in ans or r['cut']==norm(o['pick'])]
        for r in show:   # 退向听的选项不列枚数，避免和同向听的比
            if r['shanten']>best['shanten']: r['ukeire']=None; r['ukStd']=None
        o['options']=show
    # Mortal 推荐率
    want=Counter(st['hand']); entries=[e for k in rep['review']['kyokus'] for e in k['entries']]
    es=[e for e in entries if Counter(e['state']['tehai'])==want and
        (any(x['action']['type'] in('pon','chi','daiminkan') for x in e['details']) and e['tile']==act['pai'] if q['type']=='call'
         else e['actual']['type'] in('dahai','reach') if q['type']=='riichi' else e['actual']['type']=='dahai')]
    if len(es)>1 and q['type']!='call':   # 同一手牌出现多次（如摸切同一张），用摸到的牌区分
        es=[e for e in es if e['tile']==st['draw']] or es
    if len(es)>1 and q['type']=='discard':
        es=[e for e in es if e['actual'].get('pai')==act['pai']] or es
        if len(es)>1 and len({json.dumps(e['actual'],sort_keys=True) for e in es})==1: es=es[:1]   # 同一手牌连续摸切同一张：取第一次
    if len(es)>1 and q['type']=='riichi':
        es=[e for e in es if (e['actual']['type']=='reach')==(o['pick']=='立直')] or es
    if len(es)==1:
        acc={}
        for x in es[0]['details']:
            a=x['action']; t=a['type']
            if q['type']=='riichi': k='立直' if t=='reach' else '不立直'
            else: k=a['pai'] if t=='dahai' else {'pon':'碰','chi':'吃','daiminkan':'杠','none':'不碰','reach':'立直'}.get(t,t)
            acc[k]=acc.get(k,0)+x['prob']
        o['ai']=[{'a':k,'p':round(v,4)} for k,v in sorted(acc.items(),key=lambda x:-x[1])]
    else: print(f"  ! {q['id']}: Mortal 记录匹配到 {len(es)} 条，跳过推荐率")
    # 解析里的「N 枚」要能在选项表里找到
    nums={x for r in o.get('options',[]) for x in (r.get('ukeire'),r.get('ukStd')) if x is not None}
    for t in q.get('explain',[]):
        for n in re.findall(r'(\d+)\s*枚',t):
            if q['type']=='discard' and int(n) not in nums: print(f"  ! {q['id']}: 解析写了 {n} 枚，选项表里没有这个数（{sorted(nums)}）")
    return o

reps=[(os.path.basename(p),json.load(open(p,encoding='utf-8'))) for p in reports]
out=[]
for i,q in enumerate(qs):
    # 报告文件名以日期开头（records/2026-10-25_mortal_xxx.json），优先用同一天的报告，避免不同对局的同名局混淆
    cand=[r for n,r in reps if n.startswith(q.get('date',''))] or [r for _,r in reps]
    for rep in cand:
        st=snapshot(rep,q['src'],q.get('date'))
        if st: break
    else: raise SystemExit(f"{q['id']}: 在报告里找不到 {q['src']}")
    o=build(q,rep,st); o['order']=i+1; o.setdefault('added',q['date']); out.append(o)
    print(o['id'],o['turn'],'实战',o['pick'],'|',' '.join(f"{r['cut']}:{r['shanten']}向{r['ukeire']}/{r.get('ukStd')}" for r in o.get('options',[])))
json.dump(out,open(out_path,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
os.makedirs(seed_dir,exist_ok=True)
ids={o['id'] for o in out}
for f in os.listdir(seed_dir):
    if f.endswith('.json') and f[:-5] not in ids: os.remove(os.path.join(seed_dir,f)); print('  删除种子',f)
for o in out:
    json.dump({k:v for k,v in o.items() if k!='id'},open(os.path.join(seed_dir,o['id']+'.json'),'w',encoding='utf-8'),ensure_ascii=False)
print(f"共 {len(out)} 题 → {out_path}，种子 → {seed_dir}")
