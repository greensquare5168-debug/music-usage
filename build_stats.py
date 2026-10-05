#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
產生「音樂使用狀況」儀表板資料 (stats.json)
結構：廠牌(圖書館) → 專輯（依站上使用頁數）

資料來源：
  - ../網站音樂索引/all_20260925_full.jsonl   全站索引（頁面 × 曲目 × 平台 × 節目）
  - ../站上使用最多_排行_20261003.txt          TOP 曲目（只取曲名，不取作者）
  - ../全站專輯_未建_依使用排序_含平台_20261003.txt  專輯 × 使用頁數 × 廠牌
輸出：stats.json（與 index.html 同目錄）
"""
import json, re, collections, os, datetime, glob

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
IDX   = os.path.join(ROOT, '網站音樂索引', 'all_20260925_full.jsonl')
RANK  = os.path.join(ROOT, '站上使用最多_排行_20261003.txt')
ALBUM = os.path.join(ROOT, '全站專輯_未建_依使用排序_含平台_20261003.txt')

UNKNOWN = '（未標廠牌）'

# 廠牌別名對照（孝瓏指定寫短的）
ALIAS = {
    'omnimusic': 'Omni',      # 就寫 Omni
}

def brand_of(lib):
    """把『圖書館』字串正規化成廠牌清單（去掉 CD/vinyl/digital/年份 等格式後綴）。"""
    if not lib.strip():
        return [UNKNOWN]
    out = []
    for p in re.split(r'\s+/\s+', lib):
        p = p.strip()
        raw = re.sub(r'^miscellaneous\s+', '', p).strip()
        p = raw
        p = re.sub(r'\s+\(.*\)\s*$', '', p)
        p = re.sub(r'\s+(pre|post)-\d{4}.*$', '', p)
        p = re.sub(r'\s+albums?\b.*$', '', p)
        p = re.sub(r'\s*CD/digital.*$', '', p)
        p = re.sub(r'\s*vinyl/CD.*$', '', p)
        p = re.sub(r'\s+CD$', '', p)
        p = re.sub(r'\s+vinyl$', '', p)
        p = re.sub(r'\s+digital$', '', p)
        p = re.sub(r'\s+records/$', '', p)
        pmid = p.strip()                       # 格式後綴清完的樣子（供後面防呆回退用）
        p = re.sub(r'\s+Production Music Library$', '', p, flags=re.I)   # Sound Ideas Production Music Library → Sound Ideas
        p = re.sub(r'\s+Recorded Music Library$', '', p, flags=re.I)     # Chappell Recorded Music Library → Chappell
        p = re.sub(r'\s+Music Sound Stage$', '', p, flags=re.I)          # Amphonic Music Sound Stage → Amphonic
        p = re.sub(r'\s+Music Library$', '', p, flags=re.I)              # Standard Music Library → Standard
        p = re.sub(r'\s+AMPS$', '', p, flags=re.I)                       # Amphonic Music AMPS → Amphonic
        p = re.sub(r'\s+classical music$', '', p, flags=re.I)             # Cavendish Music classical music → Cavendish
        p = re.sub(r'\s+(Music\s+)?classical$', '', p, flags=re.I)        # Parry Music Classical → Parry
        p = re.sub(r'\s+Music$', '', p, flags=re.I)          # 寫 Bruton 不要 Music
        p = re.sub(r'\s+(Main|Archive) Series$', '', p)
        p = p.strip()
        parts = p.split()
        if len(parts) > 1 and parts[0] in ('CPM', 'KPM'):   # CPM/KPM 各種系列→單一廠牌
            p = parts[0]
        if len(p) < 3 or p.lower() in ('the', 'a', 'an'):
            p = pmid          # 避免去尾後只剩空／『The』這類沒意義的名字
        p = ALIAS.get(p.lower(), p)
        if p:
            out.append(p)
    return out or [UNKNOWN]

def parse_rank(path):
    tracks, composers, mode = [], [], None
    for line in open(path, encoding='utf-8'):
        if 'TOP 60 曲目' in line: mode = 't'; continue
        if 'TOP 30 作曲者' in line: mode = 'c'; continue
        s = line.rstrip('\n')
        if not s.strip(): continue
        if mode == 't':
            m = re.match(r'^\s*(\d+)\s+(.+?)\s+—\s*(.*?)\s*\[.*\]\s*$', s)
            if m:
                tracks.append({'name': m.group(2).strip(), 'composer': m.group(3).strip(),
                                'count': int(m.group(1))})
        elif mode == 'c':
            m = re.match(r'^\s*(\d+)\s+(.+?)\s*$', s)
            if m:
                composers.append({'name': m.group(2).strip(), 'count': int(m.group(1))})
    return tracks, composers

def norm_album(s):
    """專輯名：去掉結尾的年份／編號括號
       例：BRO 21 … Comic Cuts（2001） → … Comic Cuts；SCD 006 1987（2392） → SCD 006"""
    s = (s or '').strip()
    n = re.sub(r'\s*[（(]\s*\d*\s*[)）]\s*$', '', s).strip()   # 去結尾的 （年份）／（編號）／（）
    n = re.sub(r'\s+(?:1[89]\d{2}|20\d{2})\s*$', '', n).strip()  # 去結尾殘留的裸年份
    if n != s:
        n = re.sub(r'[\s．.。，,]+$', '', n).strip()
    return n or s

def parse_albums(path):
    """回傳 [(廠牌, 專輯名, 使用頁數)]"""
    rows = []
    for line in open(path, encoding='utf-8'):
        m = re.match(r'^\s*\d+\.\s*(\d+)頁\s+(.+?)\s*｜\s*圖書館：(.*?)\s*｜\s*平台：', line)
        if not m: continue
        cnt = int(m.group(1)); name = norm_album(m.group(2).strip())
        for b in brand_of(m.group(3)):
            rows.append((b, name, cnt))
    return rows

def load_track_album_map():
    """曲目 → 可能所屬專輯。來源（優先用『已建專輯頁』）：
       ① 網站自動生成/網站頁面清單_快取.json（站上已建的 圖書館音樂 專輯 → 曲目頁）
       ② 批次輸出/站上使用對照.md（ALL 館對照 PM Wiki）
       ③ 批次輸出/{Bruton,Parry}/*曲目-作者*.txt（逐專輯清單）"""
    m = collections.defaultdict(set)          # ②③（ALL 館對照／Bruton・Parry 逐專輯）
    primary = collections.defaultdict(set)    # ① 站上已建專輯頁（優先）

    def add(track, album, pri=False):
        track = (track or '').strip().lower()
        album = norm_album((album or '').strip())
        if track and album:
            (primary if pri else m)[track].add(album)

    # ① 站上已建專輯頁
    cache = os.path.join(ROOT, '網站自動生成', '網站頁面清單_快取.json')
    if os.path.exists(cache):
        data = json.load(open(cache, encoding='utf-8'))
        alb = {e['href']: e['label'] for e in data if e.get('level') == 4}
        for e in data:
            if e.get('level') != 5:
                continue
            parent = e['href'].rsplit('/', 1)[0]
            name = re.split(r'\s+-\s+', e.get('label', ''))[0]
            add(name, alb.get(parent, parent.rsplit('/', 1)[-1]), pri=True)

    # ② ALL 館對照
    md = os.path.join(ROOT, '批次輸出', 'ALL', '站上使用對照.md')
    if os.path.exists(md):
        cur = None
        for line in open(md, encoding='utf-8'):
            if line.startswith('## '):
                cur = re.sub(r'[（(]\s*\d*\s*[)）]\s*$', '', line[3:].strip()).strip()
            elif line.startswith('- ') and not line.startswith('    -'):
                b = re.match(r'^(.*?)（\d+ 次）$', line[2:].strip())
                if not b:
                    continue
                parts = [x.strip() for x in re.split(r'\s+-\s+', b.group(1))]
                tk = parts[1] if len(parts) >= 2 and parts[0].isdigit() else parts[0]
                add(tk, cur)

    # ③ Bruton / Parry 逐專輯
    for lib in ('Bruton', 'Parry'):
        for f in sorted(glob.glob(os.path.join(ROOT, '批次輸出', lib, '*曲目-作者*.txt'))):
            try:
                first = open(f, encoding='utf-8').readline().strip()
            except Exception:
                continue
            am = re.match(r'^《(.*?)》（(.*?)）', first)
            album = '%s %s' % (am.group(2), am.group(1)) if am else \
                os.path.basename(f).split('_曲目')[0]
            for line in open(f, encoding='utf-8'):
                line = line.strip()
                if not line or line.startswith(('《', '來源')) or ' - ' not in line:
                    continue
                add(re.split(r'\s+-\s+', line)[0], album)
    out = {}
    for k in set(primary) | set(m):
        out[k] = sorted(primary[k] or m[k])
    return out

ROLE_PREFIX = {'標題', '片頭曲', '片尾曲', '簡介', '進廣告', '插曲', '主題曲', '配樂',
               '片頭', '片尾', '開頭', '結尾', '前奏', '尾奏', 'BGM'}

def norm_track(t):
    """曲目名：去掉段落前綴（例：片尾曲 擁有 → 擁有；標題 Toccata Singers → Toccata Singers）"""
    t = (t or '').strip()
    parts = t.split(' ', 1)
    if len(parts) == 2 and parts[0] in ROLE_PREFIX:
        return parts[1].strip()
    return t

def build_tracks(t2a):
    """全站曲目（曲名 → 出現頁數＋所屬專輯）"""
    tp = collections.defaultdict(set)
    for line in open(IDX, encoding='utf-8'):
        line = line.strip()
        if not line:
            continue
        d = json.loads(line)
        t = norm_track(d.get('track', ''))
        if not t:
            continue
        tp[t].add(d.get('url_path') or d.get('page_title'))
    out = []
    for name, pages in tp.items():
        item = {'name': name, 'count': len(pages)}
        alb = sorted(t2a.get(name.lower(), []))
        if alb:
            item['albums'] = alb
        out.append(item)
    out.sort(key=lambda x: (-x['count'], x['name']))
    return out

def norm_program(s):
    """節目名正規化：去掉集數後綴（例：古古食-ep-01什麼… → 古古食）"""
    s = (s or '').strip()
    s = re.sub(r'[-_ ]?ep[-_ ]?\d+.*$', '', s, flags=re.I)
    s = re.sub(r'[-_ .]+$', '', s).strip()
    return s

def main():
    tracks, composers = parse_rank(RANK)
    rows = parse_albums(ALBUM)
    t2a = load_track_album_map()

    # 廠牌 → 專輯（同名合併）
    lab = collections.defaultdict(lambda: {'total': 0, 'alb': collections.OrderedDict()})
    for b, name, cnt in rows:
        lab[b]['total'] += cnt
        lab[b]['alb'][name] = lab[b]['alb'].get(name, 0) + cnt
    labels = []
    for name, d in lab.items():
        albums = [{'name': k, 'count': v} for k, v in d['alb'].items()]
        albums.sort(key=lambda a: -a['count'])
        labels.append({'name': name, 'total': d['total'], 'n': len(albums), 'albums': albums})
    labels.sort(key=lambda x: -x['total'])

    # 全站 TOP 專輯（不分廠牌，去重同名取最大）
    best = {}
    for b, name, cnt in rows:
        if name not in best or cnt > best[name]:
            best[name] = cnt
    top_albums = [{'name': k, 'count': v} for k, v in
                  sorted(best.items(), key=lambda x: -x[1])[:30]]

    # 索引：平台 / 節目
    pl_pages, pr_pages, all_pages, records = (collections.defaultdict(set),
        collections.defaultdict(set), set(), 0)
    for line in open(IDX, encoding='utf-8'):
        line = line.strip()
        if not line: continue
        d = json.loads(line); records += 1
        p = d.get('url_path') or d.get('page_title')
        all_pages.add(p)
        pl_pages[d.get('platform', '')].add(p)
        pr_pages[d.get('program', '')].add(p)

    usage_plat = sorted(((k, len(v)) for k, v in pl_pages.items()
                         if k and k not in ('圖書館音樂', 'view')), key=lambda x: -x[1])
    # 節目分布：只列真正的「節目名稱」——限真實電視平台，
    # 排除『圖書館音樂』底下的分類（power-house / point / atmosphere / match / arcadia…＝音樂廠牌，不是節目）
    REAL_PLAT = {'yoyotv', '巧連智', 'momo親子台', '公視', '古古食'}
    prog_pages = collections.defaultdict(set)
    prog_plat = collections.defaultdict(set)
    for line in open(IDX, encoding='utf-8'):
        line = line.strip()
        if not line: continue
        d = json.loads(line)
        k = norm_program(d.get('program', ''))
        if not k: continue
        p = d.get('url_path') or d.get('page_title')
        prog_pages[k].add(p)
        prog_plat[k].add(d.get('platform', ''))
    programs = sorted(((k, len(v)) for k, v in prog_pages.items()
                       if prog_plat[k] and prog_plat[k] <= REAL_PLAT),
                      key=lambda x: -x[1])

    data = {
        'generated': datetime.date.today().isoformat(),
        'source_date': '2026-09-25',
        'summary': {'pages': len(all_pages), 'records': records,
                    'labels': len(labels),
                    'albums': len(best), 'tracks': len(tracks)},
        'labels': labels,
        'topAlbums': top_albums,
        'platforms': [{'name': k, 'count': v} for k, v in usage_plat],
        'programs': [{'name': k, 'count': v} for k, v in programs],
    }
    with open(os.path.join(BASE, 'stats.json'), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    tracks_full = build_tracks(t2a)
    with open(os.path.join(BASE, 'tracks.json'), 'w', encoding='utf-8') as f:
        json.dump({'source_date': data['source_date'], 'count': len(tracks_full),
                   'tracks': tracks_full}, f, ensure_ascii=False, separators=(',', ':'))
    print('OK labels=%d albums=%d pages=%d records=%d tracks=%d'
          % (len(labels), len(best), len(all_pages), records, len(tracks_full)))

if __name__ == '__main__':
    main()
