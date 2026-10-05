#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
產生「音樂使用狀況」資料（廠牌 → 專輯）。

廠牌/專輯清單：來自 `全站專輯_未建_依使用排序_含平台_*.txt`（PM Wiki 分類＋未建頁面的專輯）
**使用頁數**：改為直接由站台現況計算 ——
  站上節目頁（yoyotv/巧連智/momo親子台/公視/古古食）中，有列出該專輯任一曲目的頁數
  （曲目清單取自 `批次輸出/ALL/站上使用對照.md`；純數字＝解析錯誤已濾除）
輸出：stats.json
"""
import json, re, collections, os, glob, datetime

BASE  = os.path.dirname(os.path.abspath(__file__))
ROOT  = os.path.dirname(BASE)
INDEX = os.path.join(ROOT, '網站音樂索引', 'all_20261005_full.jsonl')
MD    = os.path.join(ROOT, '批次輸出', 'ALL', '站上使用對照.md')
ALBUM = os.path.join(ROOT, '全站專輯_未建_依使用排序_含平台_20261003.txt')

UNKNOWN = '（未標廠牌）'
PLATFORMS = {'yoyotv', '巧連智', 'momo親子台', '公視', '古古食'}
ROLE_PREFIX = {'標題', '片頭曲', '片尾曲', '簡介', '進廣告', '插曲', '主題曲', '配樂',
               '片頭', '片尾', '開頭', '結尾', '前奏', '尾奏', 'BGM'}

ALIAS = {
    'omnimusic': 'Omni',
    'koka media': 'Koka',
    'arcadia': 'Arcadia Cosmos',
}

def norm_track(t):
    t = (t or '').strip()
    p = t.split(' ', 1)
    return p[1].strip() if len(p) == 2 and p[0] in ROLE_PREFIX else t

def norm_album(s):
    s = (s or '').strip()
    n = re.sub(r'\s*[（(]\s*\d*\s*[)）]\s*$', '', s).strip()
    n = re.sub(r'\s+(?:1[89]\d{2}|20\d{2})\s*$', '', n).strip()
    if n != s:
        n = re.sub(r'[\s．.。，,]+$', '', n).strip()
    return n or s

def brand_of(lib):
    """『圖書館』字串 → 廠牌（去掉格式後綴）"""
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
        pmid = p.strip()
        p = re.sub(r'\s+Production Music Library$', '', p, flags=re.I)
        p = re.sub(r'\s+Recorded Music Library$', '', p, flags=re.I)
        p = re.sub(r'\s+Music Sound Stage$', '', p, flags=re.I)
        p = re.sub(r'\s+Music Library$', '', p, flags=re.I)
        p = re.sub(r'\s+AMPS$', '', p, flags=re.I)
        p = re.sub(r'\s+classical music$', '', p, flags=re.I)
        p = re.sub(r'\s+(Music\s+)?classical$', '', p, flags=re.I)
        p = re.sub(r'\s+Music$', '', p, flags=re.I)
        p = re.sub(r'\s+Main Series$', '', p)
        p = p.strip()
        parts = p.split()
        if len(parts) > 1 and parts[0] == 'KPM':
            p = 'KPM'
        if len(p) < 3 or p.lower() in ('the', 'a', 'an'):
            p = pmid
        p = ALIAS.get(p.lower(), p)
        if p:
            out.append(p)
    return out or [UNKNOWN]

def split_album_name(name):
    toks = name.split(' ')
    idx = next((i for i, t in enumerate(toks) if any(c.isdigit() for c in t)), None)
    if idx is None:
        return name, ''
    k = idx
    while k + 1 < len(toks) and re.fullmatch(r'\d{1,4}', toks[k + 1]):
        k += 1
    return ' '.join(toks[:k + 1]), ' '.join(toks[k + 1:]).lstrip('- ').strip()

def load_program_pages():
    pg = collections.defaultdict(set)
    for line in open(INDEX, encoding='utf-8'):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        if r.get('platform') in PLATFORMS:
            t = norm_track(r.get('track'))
            if t:
                pg[r['url_path']].add(t)
    return pg

def load_md_tracks():
    """專輯（原始名）→ 曲目清單；純數字行視為解析錯誤丟棄"""
    d = collections.defaultdict(list); cur = None
    for line in open(MD, encoding='utf-8'):
        if line.startswith('## '):
            cur = line[3:].strip()
        elif line.startswith('- ') and not line.startswith('    -'):
            m = re.match(r'^(.*?)（\d+ 次）$', line[2:].strip())
            if not m or cur is None:
                continue
            body = m.group(1).strip()
            if re.fullmatch(r'[\d\s\.\-–]+', body):
                continue
            parts = [x.strip() for x in re.split(r'\s+-\s+', body)]
            tk = parts[1] if len(parts) >= 2 and parts[0].isdigit() else parts[0]
            if tk:
                d[cur].append(tk)
    return d

def main():
    pg = load_program_pages()
    md = load_md_tracks()

    # 專輯清單（廠牌 + 原始名）
    albums = []
    for line in open(ALBUM, encoding='utf-8'):
        m = re.match(r'^\s*\d+\.\s*(\d+)頁\s+(.+?)\s*｜\s*圖書館：(.*?)\s*｜\s*平台：', line)
        if not m:
            continue
        raw = m.group(2).strip()
        for b in brand_of(m.group(3)):
            albums.append((b, raw))

    # 使用頁數（站台現況）
    rows = []
    for b, raw in albums:
        tracks = md.get(raw)
        if not tracks:
            continue
        used = set()
        for t in tracks:
            for p, ts in pg.items():
                if t in ts:
                    used.add(p)
        if used:
            rows.append((b, norm_album(raw), len(used)))

    lab = collections.defaultdict(lambda: collections.OrderedDict())
    for b, name, cnt in rows:
        d = lab[b]
        d[name] = max(d.get(name, 0), cnt)
    labels = []
    for name, d in lab.items():
        if name == UNKNOWN:
            continue
        al = []
        for k, v in d.items():
            code, title = split_album_name(k)
            al.append({'name': k, 'code': code, 'title': title, 'count': v})
        al.sort(key=lambda a: -a['count'])
        labels.append({'name': name, 'total': sum(a['count'] for a in al),
                       'n': len(al), 'albums': al})
    labels.sort(key=lambda x: -x['total'])

    data = {
        'generated': datetime.date.today().isoformat(),
        'source_date': '2026-10-05（站台重爬）',
        'summary': {'pages': len(pg), 'labels': len(labels), 'albums': len(rows)},
        'labels': labels,
    }
    with open(os.path.join(BASE, 'stats.json'), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('OK 廠牌=%d 專輯=%d 節目頁=%d' % (len(labels), len(rows), len(pg)))

if __name__ == '__main__':
    main()
