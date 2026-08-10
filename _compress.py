# -*- coding: utf-8 -*-
"""Compress data.js: deduplicate, shorten keys, shorten URLs, minify"""
import re, json

with open('d:/语文/data.js', 'r', encoding='utf-8') as f:
    content = f.read()

match = re.search(r'const poemData\s*=\s*(\{.*?\n\});', content, re.DOTALL)
data = json.loads(match.group(1))

# 1. Deduplicate audio entries within each poem
for cat, poems in data.items():
    for p in poems:
        seen = set()
        unique = []
        for a in p.get('audios', []):
            if a['url'] not in seen:
                seen.add(a['url'])
                unique.append(a)
        p['audios'] = unique

# 2. Shorten keys: poem->p, author->au, dynasty->dy, content->c, audios->a, videos->v, name->n, url->u
# 3. Shorten URLs: store just the filename, reconstruct at runtime
#    http://gswys.bjkmrz.com/cmsupload/1589335624079.mp3 -> 1589335624079
URL_PREFIX = 'http://gswys.bjkmrz.com/cmsupload/'

compressed = {}
for cat, poems in data.items():
    compressed[cat] = []
    for p in poems:
        item = {'p': p.get('poem', '')}
        if p.get('author'): item['au'] = p['author']
        if p.get('dynasty'): item['dy'] = p['dynasty']
        if p.get('content'): item['c'] = p['content']
        if p.get('audios'):
            item['a'] = [{'n': a['name'], 'u': a['url'].replace(URL_PREFIX, '')} for a in p['audios']]
        if p.get('videos'):
            item['v'] = [{'n': v.get('name',''), 'u': v['url'].replace(URL_PREFIX, '')} for v in p['videos']]
        compressed[cat].append(item)

# 4. Minify (no indentation, no extra spaces)
minified = json.dumps(compressed, ensure_ascii=False, separators=(',', ':'))

# 5. Write compressed data.js with decompression code
js_code = f'''// Compressed poemData — keys: p=poem,au=author,dy=dynasty,c=content,a=audios,v=videos,n=name,u=url(filename)
// URLs are filenames only; prefix is added at runtime.
const _PD={minified};
const poemData=(function(){{
const U='http://gswys.bjkmrz.com/cmsupload/';
const r={{}};
for(const cat in _PD){{
r[cat]=_PD[cat].map(function(p){{
const o={{poem:p.p||''}};
if(p.au)o.author=p.au;
if(p.dy)o.dynasty=p.dy;
if(p.c)o.content=p.c;
if(p.a)o.audios=p.a.map(function(a){{return{{name:a.n,url:U+a.u}};}});
if(p.v)o.videos=p.v.map(function(v){{return{{name:v.n,url:U+v.u}};}});
return o;
}});
}}
return r;
}})();
'''

with open('d:/语文/data.js', 'w', encoding='utf-8') as f:
    f.write(js_code)

import os
orig_size = os.path.getsize('d:/语文/index.html')  # already split
data_size = os.path.getsize('d:/语文/data.js')
print(f'data.js: {data_size/1024:.0f} KB')
print(f'index.html: {orig_size/1024:.0f} KB')
print(f'Total: {(orig_size+data_size)/1024:.0f} KB')

# Verify decompression works
with open('d:/语文/data.js', 'r', encoding='utf-8') as f:
    verify = f.read()
# Check the minified JSON is valid
m = re.search(r'const _PD=(\{.*?\});', verify, re.DOTALL)
test = json.loads(m.group(1))
total = sum(len(v) for v in test.values())
print(f'Verified: {len(test)} categories, {total} poems')
