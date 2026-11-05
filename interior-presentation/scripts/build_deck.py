#!/usr/bin/env python3
"""Build an interior-design presentation (HTML + PDF) from a folder tree.
Usage: python3 build_deck.py <root_folder> <out_dir> [--title "NAME"]"""
import sys, os, re, io, base64, math, json, subprocess, argparse, tempfile
from PIL import Image

IMG = ('.jpg', '.jpeg', '.png', '.jfif', '.webp', '.bmp', '.gif', '.tif', '.tiff')
PLAN = re.compile(r'(sketch|plan|layout|drawing|elevation|section)', re.I)
SKIP = {'.ds_store', 'thumbs.db'}

def clean(name):  # "01 BED BACK WALL" / "01_bed-back" -> "BED BACK WALL"
    name = os.path.splitext(name)[0] if os.path.isfile(name) else name
    name = re.sub(r'^\s*\d+[\s._-]+', '', os.path.basename(name))
    return re.sub(r'[_-]+', ' ', name).strip().upper()

def sortkey(n):
    m = re.match(r'^\s*(\d+)', n)
    return (int(m.group(1)) if m else 10**6, n.lower())

def pdf_to_img(path, tmp):
    out = os.path.join(tmp, re.sub(r'\W', '_', path)[-60:])
    subprocess.run(['pdftoppm', '-r', '110', '-png', '-f', '1', '-l', '1', '-singlefile', path, out], check=True)
    return out + '.png'

def b64(path, mx=1500):
    im = Image.open(path)
    if im.mode in ('RGBA', 'LA', 'P') and path.lower().endswith('.png') and 'logo' in path.lower():
        im = im.convert('RGBA'); im.thumbnail((mx, mx)); b = io.BytesIO(); im.save(b, 'PNG')
        return 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode()
    im = im.convert('RGB'); im.thumbnail((mx, mx)); b = io.BytesIO(); im.save(b, 'JPEG', quality=85)
    return 'data:image/jpeg;base64,' + base64.b64encode(b.getvalue()).decode()

def files_in(d, tmp):
    imgs, notes = [], ''
    for f in sorted(os.listdir(d), key=sortkey):
        p = os.path.join(d, f); fl = f.lower()
        if fl in SKIP or f.startswith('.') or not os.path.isfile(p): continue
        if fl.endswith(IMG): imgs.append(p)
        elif fl.endswith('.pdf') and PLAN.search(f): imgs.append(pdf_to_img(p, tmp) + '#plan')
        elif fl in ('notes.txt', 'notes.md', 'description.txt'):
            notes = open(p, encoding='utf-8', errors='ignore').read().strip()
    return imgs, notes

def read_company(d):
    info, logos = {}, []
    if not d: return info, logos
    for f in sorted(os.listdir(d)):
        p = os.path.join(d, f); fl = f.lower()
        if fl.endswith(IMG): logos.append(p)
        elif fl.endswith('.json'): info.update({k.lower(): str(v) for k, v in json.load(open(p)).items()})
        elif fl.endswith(('.txt', '.md')):
            for line in open(p, encoding='utf-8', errors='ignore'):
                if ':' in line:
                    k, v = line.split(':', 1); info[k.strip().lower().lstrip('#- ')] = v.strip()
    logos.sort(key=lambda p: (0 if 'main' in p.lower() or 'primary' in p.lower() else 1, p))
    return info, logos

def collect(root, tmp):
    company, sections = None, []
    for n in sorted(os.listdir(root), key=sortkey):
        p = os.path.join(root, n)
        if not os.path.isdir(p) or n.startswith('.'): continue
        if n.lower() in ('company', 'company details', 'company info'): company = p; continue
        sections.append(p)
    slides = []
    def walk(d, trail):
        imgs, notes = files_in(d, tmp)
        if imgs: slides.append(dict(title=clean(d), parent=' · '.join(trail) or None, trail=trail, imgs=imgs, notes=notes))
        for n in sorted(os.listdir(d), key=sortkey):
            p = os.path.join(d, n)
            if os.path.isdir(p) and not n.startswith('.'): walk(p, trail + [clean(d)])
    groups = []
    for s in sections:
        subs = [clean(n) for n in sorted(os.listdir(s), key=sortkey) if os.path.isdir(os.path.join(s, n)) and not n.startswith('.')]
        start = len(slides); walk(s, [])
        if subs: groups.append(dict(title=clean(s), at=start, rooms=subs, n=len(groups) + 1))
    return company, slides, groups

CSS = '''@page{size:1440px 810px;margin:0}*{box-sizing:border-box;margin:0;padding:0}
body{background:#888;font-family:"Cormorant Garamond",Georgia,serif;color:#2b2925}
.slide{width:1440px;height:810px;background:#fff;display:flex;overflow:hidden;page-break-after:always;margin:0 auto 20px}
@media print{body{background:#fff}.slide{margin:0}}
aside{width:107px;flex:none;background:var(--side);display:flex;flex-direction:column;align-items:center;justify-content:space-between;padding:36px 0 18px}
aside .t{display:flex;flex-direction:column;align-items:center;gap:var(--gap)}aside .w{display:flex;flex-direction:column;align-items:center}
aside span{font-size:var(--fs);line-height:1.6}aside .sl{width:70px;mix-blend-mode:multiply}
main{flex:1;position:relative;padding:50px 60px;height:810px;min-width:0}
figure{overflow:hidden;min-height:0;height:100%}figure img{width:100%;height:100%;object-fit:cover;display:block}
figure.plan{border:1px solid #e3dfd5;background:#fff}figure.plan img{object-fit:contain}
.cover{display:flex;flex-direction:column}.hero{display:grid;gap:14px;height:450px;margin-top:40px}
.kick{text-transform:uppercase;letter-spacing:.35em;font-size:15px;color:#8a8375}
h1{font-weight:400;font-size:68px;letter-spacing:.06em;text-transform:uppercase;line-height:1.1;margin-top:34px}
.sub{font-size:20px;color:#6b665c;font-style:italic}
.tl{position:absolute;top:14px;right:30px;height:80px}.br{position:absolute;bottom:30px;right:50px;display:flex;gap:30px;align-items:center}.br img{height:60px}
.lay{display:grid;gap:44px;height:100%;grid-template-rows:100%}
.col{display:flex;flex-direction:column;min-height:0}.col figure{flex:1;height:auto}
.cap{font-size:14px;letter-spacing:.2em;text-transform:uppercase;color:#8a8375;margin-top:10px}
.grid{display:grid;gap:16px;height:100%;min-height:0}
.notes{align-self:end;border-top:1px solid #c9c3b5;padding-top:22px}
.notes h2{font-weight:400;font-size:34px;text-transform:uppercase;letter-spacing:.06em;margin-bottom:16px}
.crumb{position:absolute;top:20px;left:60px;font-size:13px;letter-spacing:.28em;text-transform:uppercase;color:#8a8375}
.div{display:grid;grid-template-columns:1fr 520px;gap:60px;height:100%;align-items:end}
.div .num{font-size:120px;line-height:1;color:var(--side);font-weight:400}
.div h1{margin-top:6px}.div ul{list-style:none;margin-top:26px;border-top:1px solid #c9c3b5;padding-top:18px;columns:2;column-gap:40px}
.div li{font-size:20px;letter-spacing:.12em;text-transform:uppercase;line-height:2;color:#4a463f}
.notes p{font-size:19px;line-height:1.5;margin-bottom:12px;color:#4a463f;white-space:pre-line}'''

def esc(s): return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def sidebar(title, logo):
    words = title.split()
    letters = sum(len(w) for w in words) + len(words)
    fs = 30 if letters <= 15 else max(16, int(30 * 15 / letters))
    w = ''.join('<div class="w">' + ''.join(f'<span>{esc(c)}</span>' for c in wd) + '</div>' for wd in words)
    lg = f'<img class="sl" src="{logo}">' if logo else ''
    return f'<aside style="--fs:{fs}px;--gap:{int(fs*.8)}px"><div class="t">{w}</div>{lg}</aside>'

def fig(src, plan=False): return f'<figure class="{"plan" if plan else ""}"><img src="{src}"></figure>'

def grid(srcs):
    n = len(srcs); cols = n if n <= 3 else math.ceil(n / 2); rows = math.ceil(n / cols)
    return f'<div class="grid" style="grid-template-columns:repeat({cols},1fr);grid-template-rows:repeat({rows},minmax(0,1fr))">' + ''.join(fig(s) for s in srcs) + '</div>'

def slide_html(s, logo, MAX=6):
    plans = [p[:-5] for p in s['imgs'] if p.endswith('#plan')] + [p for p in s['imgs'] if not p.endswith('#plan') and PLAN.search(os.path.basename(p))]
    refs = [p for p in s['imgs'] if not p.endswith('#plan') and not PLAN.search(os.path.basename(p))]
    if plans and not refs: refs, plans = plans[1:], plans[:1]
    chunks = [refs[i:i + MAX] for i in range(0, len(refs), MAX)] or [[]]
    out = []
    for i, ch in enumerate(chunks):
        title = s['title'] + (f' {i+1}' if len(chunks) > 1 and i else '')
        cols, parts = [], []
        if plans:
            cap = clean(plans[0]) if not plans[0].endswith('.png') or '/tmp' not in plans[0] else 'PLAN'
            cols.append('400px' if ch else '1fr'); parts.append(f'<div class="col">{fig(b64(plans[0]), True)}<p class="cap">{esc(cap)}</p></div>')
        if ch: cols.append('560px' if len(ch) == 1 and not plans else '1fr'); parts.append(grid([b64(p) for p in ch]))
        if s['notes'] and i == 0:
            body = ''.join(f'<p>{esc(l)}</p>' for l in s['notes'].split('\n\n'))
            cols.append('320px'); parts.append(f'<div class="notes"><h2>{esc(s["title"].title())}</h2>{body}</div>')
        crumb = f'<div class="crumb">{esc(s["parent"])}</div>' if s.get('parent') else ''
        out.append(f'<section class="slide">{sidebar(title, logo)}<main>{crumb}<div class="lay" style="grid-template-columns:{" ".join(cols)}">{"".join(parts)}</div></main></section>')
    return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('out'); ap.add_argument('--title'); ap.add_argument('--side', default='#d1cdc1')
    a = ap.parse_args(); tmp = tempfile.mkdtemp()
    company, slides, groups = collect(a.root, tmp)
    info, logos = read_company(company)
    title = (a.title or info.get('project') or info.get('title') or clean(a.root)).upper()
    logo = b64(logos[0], 400) if logos else None
    hero = [s['imgs'][j] for s in slides for j in range(len(s['imgs'])) if not s['imgs'][j].endswith('#plan') and not PLAN.search(os.path.basename(s['imgs'][j]))]
    seen, pick = set(), []
    for s in slides:  # one hero image per slide first
        for p in s['imgs']:
            if p in hero and p not in seen: pick.append(p); seen.add(p); break
    pick = (pick + [p for p in hero if p not in seen])[:4]
    sub = info.get('subtitle') or ' · '.join(g['title'].title() for g in groups) or ' · '.join(s['title'].title() for s in slides[:6])
    kick = info.get('kicker') or info.get('client') or 'Interior Concept Board'
    tl = f'<img class="tl" src="{logo}">' if logo else ''
    br = '<div class="br">' + ''.join(f'<img src="{b64(p, 500)}">' for p in logos[1:3]) + '</div>' if len(logos) > 1 else ''
    heroh = f'<div class="hero" style="grid-template-columns:repeat({max(1,len(pick))},1fr)">' + ''.join(fig(b64(p)) for p in pick) + '</div>'
    cover = f'<section class="slide">{sidebar(title, None)}<main class="cover">{heroh}<h1>{esc(title)}</h1><p class="kick">{esc(kick)}</p><p class="sub">{esc(sub)}</p>{tl}{br}</main></section>'
    def divider(g):
        first = next((p for s in slides[g['at']:] for p in s['imgs'] if not p.endswith('#plan') and not PLAN.search(os.path.basename(p))), None)
        img = fig(b64(first)) if first else '<div></div>'
        rooms = ''.join(f'<li>{esc(r)}</li>' for r in g['rooms'])
        return f'<section class="slide">{sidebar(g["title"], logo)}<main><div class="div"><div><div class="num">{g["n"]:02d}</div><h1>{esc(g["title"])}</h1><ul>{rooms}</ul></div>{img}</div></main></section>'
    starts = {g['at']: g for g in groups}
    body = [cover]
    for i, s in enumerate(slides):
        if i in starts: body.append(divider(starts[i]))
        body += slide_html(s, logo)
    html = f'<!doctype html><html><head><meta charset="utf-8"><title>{esc(title.title())}</title><link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet"><style>:root{{--side:{info.get("color", a.side)}}}{CSS}</style></head><body>{"".join(body)}</body></html>'
    os.makedirs(a.out, exist_ok=True)
    base = os.path.join(a.out, f'{title} PPT'); open(base + '.html', 'w').write(html)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1440, 'height': 810})
        pg.goto('file://' + os.path.abspath(base + '.html')); pg.wait_for_timeout(1500)
        pg.pdf(path=base + '.pdf', width='1440px', height='810px', print_background=True); b.close()
    print(f'{len(body)} slides -> {base}.html / .pdf')
    for s in slides: print(' -', (s["parent"] + ' / ' if s["parent"] else '') + s['title'], len(s['imgs']), 'images', '(notes)' if s['notes'] else '')

if __name__ == '__main__': main()
