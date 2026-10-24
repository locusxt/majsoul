# 生成本地预览页（用 hands.json 模拟 db），仅供截图检查
import json,sys
hs=json.load(open('hands.json',encoding='utf-8'))  # 由 tools/build_hands.py 生成
pick=sys.argv[1] if len(sys.argv)>1 else None
page=open('cuoti.html',encoding='utf-8').read()
mock="""<script>
const __H=%s, __PICK=%s;
window.claude={use:async n=>n!=='db'?null:{collection:()=>({orderBy:()=>({onSnapshot:(cb)=>{setTimeout(()=>{cb({docs:__H.map(x=>({id:x.id,data:()=>x}))}); if(__PICK){curId=__PICK; renderAll(); if(location.hash==='#hover') setTimeout(()=>document.querySelector('.hand .tile').dispatchEvent(new Event('mouseenter')),50); if(location.hash==='#ans'||location.hash==='#fold') setTimeout(()=>{const b=document.querySelector('.hand button.tile')||document.querySelector('.act'); b&&b.click(); if(location.hash==='#fold') setTimeout(()=>document.querySelector('.card .head .btn').click(),30)},50)}},0); return ()=>{}}})})}};
</script>""" % (json.dumps(hs,ensure_ascii=False), json.dumps(pick))
html='<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><style>:root{color-scheme:light}body{margin:0;font-size:14px}[hidden]{display:none!important}img{max-width:100%}</style></head><body>'+mock+page+'</body></html>'
open('preview.html','w',encoding='utf-8').write(html)
