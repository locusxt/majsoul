"""把 practice/tiles/*.svg 压缩后打包成 practice/tiles.js（一个文件、一次请求，牌面随页面一起到位）。
用法: python tools/build_tiles.py   （需要 pip install scour）"""
import os,json,re
from urllib.parse import quote
from scour import scour
root=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','practice')
o=scour.parse_args(['--enable-id-stripping','--shorten-ids','--remove-metadata','--strip-xml-prolog',
    '--enable-comment-stripping','--no-line-breaks','--set-precision=3','--indent=none'])
out={}; before=after=0
for f in sorted(os.listdir(os.path.join(root,'tiles'))):
    if not f.endswith('.svg'): continue
    src=open(os.path.join(root,'tiles',f),encoding='utf-8').read(); before+=len(src.encode())
    svg=scour.scourString(src,o)
    svg=re.sub(r'\s+',' ',svg).strip(); after+=len(svg.encode())
    # 属性引号换成单引号，放进 url("...") 不用转义；# 必须编码，否则会被当成片段标识
    out[f[:-4]]='data:image/svg+xml,'+quote(svg.replace('"',"'"),safe=" =:/;,'()-.")
js='// 由 tools/build_tiles.py 生成，不要手改。牌面图：riichi-mahjong-tiles（CC0）\nwindow.TILE_SVG='+json.dumps(out,separators=(',',':'))+';\n'
open(os.path.join(root,'tiles.js'),'w',encoding='utf-8').write(js)
print(f'{len(out)} 张，{before//1024}KB → {after//1024}KB，tiles.js {len(js.encode())//1024}KB')
