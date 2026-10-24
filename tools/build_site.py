"""把错题本打包成静态网站（GitHub Pages 用）：site/index.html + hands.json + tiles.js + tiles/。
用法: python tools/build_site.py [输出目录，默认 site]"""
import os,shutil,sys
root=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'); src=os.path.join(root,'practice')
out=sys.argv[1] if len(sys.argv)>1 else os.path.join(root,'site')
shutil.rmtree(out,ignore_errors=True); os.makedirs(out)
page=open(os.path.join(src,'cuoti.html'),encoding='utf-8').read()
head=('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
      '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
      '<style>body{margin:0}[hidden]{display:none!important}</style></head><body>')
open(os.path.join(out,'index.html'),'w',encoding='utf-8').write(head+page+'</body></html>')
shutil.copy(os.path.join(src,'hands.json'),out)
shutil.copytree(os.path.join(src,'tiles'),os.path.join(out,'tiles'))
shutil.copy(os.path.join(src,'tiles.js'),out)
open(os.path.join(out,'.nojekyll'),'w').close()
print('site →',os.path.abspath(out))
