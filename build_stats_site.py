#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
產生「音樂使用狀況」資料（廠牌 → 專輯），**以站台現況為準**。

來源：
  - ../網站音樂索引/all_20261005_full.jsonl   站台全站索引（節目頁 / 館藏頁的曲目）
  - ../網站頁面清單_快取.json                  站台導覽（library / 專輯 / 曲目頁 名稱）
  - ../網站音樂索引/site_urls_20261005.txt     站台頁面清單（結構）

計算：
  專輯「使用頁數」＝站上節目頁面（yoyotv/巧連智/momo親子台/公視/古古食）中，
  有列出該專輯任一曲目的頁數（不含館藏頁自己）。
輸出：stats.json（與 index.html 同目錄）
"""
import json, re, collections, os, datetime

BASE  = os.path.dirname(os.path.abspath(__file__))
ROOT  = os.path.dirname(BASE)
INDEX = os.path.join(ROOT, '網站音樂索引', 'all_20261005_full.jsonl')
NAV   = os.path.join(ROOT, '網站自動生成', 'site_nav_20261005.json')
URLS  = os.path.join(ROOT, '網站音樂索引', 'site_urls_20261005.txt')

PLATFORMS = {'yoyotv', '巧連智', 'momo親子台', '公視', '古古食'}
ROLE_PREFIX = {'標題', '片頭曲', '片尾曲', '簡介', '進廣告', '插曲', '主題曲', '配樂',
               '片頭', '片尾', '開頭', '結尾', '前奏', '尾奏', 'BGM'}

def norm_track(t):
    t = (t or '').strip()
    p = t.split(' ', 1)
    return p[1].strip() if len(p) == 2 and p[0] in ROLE_PREFIX else t

def clean_album_label(s):
    """導覽標籤 → (編號, 名稱)。例：PH15 - Child's Play → ('PH15', "Child's Play")"""
    s = (s or '').strip()
    m = re.match(r'^([A-Za-z][A-Za-z0-9]*(?:[-–][A-Za-z0-9]+)*(?:\s+\d{1,4})*)\s*[-–—:]\s*(.+)$', s)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    toks = s.split(' ')
    idx = next((i for i, t in enumerate(toks) if any(c.isdigit() for c in t)), None)
    if idx is None:
        return s, ''
    k = idx
    while k + 1 < len(toks) and re.fullmatch(r'\d{1,4}', toks[k + 1]):
        k += 1
    return ' '.join(toks[:k + 1]), ' '.join(toks[k + 1:]).lstrip('- ').strip()

def main():
    # 1) 節目頁：每頁的曲目集合
    page_tracks = collections.defaultdict(set)
    for line in open(INDEX, encoding='utf-8'):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        if r.get('platform') in PLATFORMS:
            t = norm_track(r.get('track'))
            if t:
                page_tracks[r['url_path']].add(t)

    # 2) 導覽：library slug → 名稱；專輯頁 → (廠牌, 專輯)；曲目頁 → 專輯
    lib_name, alb_lib, alb_label, alb_tracks = {}, {}, {}, collections.defaultdict(list)
    data = json.load(open(NAV, encoding='utf-8'))
    for e in data:
        parts = [p for p in e['href'].split('/') if p]
        if len(parts) >= 5 and parts[3] == '圖書館音樂':
            slug = parts[4]
            if len(parts) == 5 and e.get('label'):
                lib_name[slug] = e['label'].strip()
            elif len(parts) == 6:
                alb_lib[e['href']] = slug
                alb_label[e['href']] = e.get('label', '').strip()
    for e in data:
        if e.get('level') == 5:
            parent = e['href'].rsplit('/', 1)[0]
            if parent in alb_lib:
                t = re.split(r'\s+-\s+', e.get('label', ''))[0].strip()
                if t:
                    alb_tracks[parent].append(t)

    # 3) 各專輯使用頁數（站上節目頁有列到該專輯任一曲目）
    rows = []
    for href, slug in alb_lib.items():
        tracks = alb_tracks.get(href)
        if not tracks:
            continue
        used = set()
        for t in tracks:
            for pg, ts in page_tracks.items():
                if t in ts:
                    used.add(pg)
        if not used:
            continue
        code, title = clean_album_label(alb_label.get(href, href.rsplit('/', 1)[-1]))
        rows.append({'lib': lib_name.get(slug, slug), 'slug': slug,
                     'code': code, 'title': title, 'count': len(used)})

    # 4) CPM 系列拆分（CAS＝Archive、CLASS＝Classical 各成一系列）
    for r in rows:
        if r['lib'] == 'CPM' or r['slug'] == 'cpm':
            c = r['code'].upper()
            if c.startswith('CAS'):
                r['lib'] = 'CPM Archive Series'
            elif c.startswith('CLASS'):
                r['lib'] = 'CPM Classical Series'

    # 5) 廠牌 → 專輯
    lab = collections.defaultdict(list)
    for r in rows:
        lab[r['lib']].append({'name': (r['code'] + (' ' + r['title'] if r['title'] else '')).strip(),
                              'code': r['code'], 'title': r['title'], 'count': r['count']})
    labels = []
    for name, albums in lab.items():
        albums.sort(key=lambda a: -a['count'])
        labels.append({'name': name, 'total': sum(a['count'] for a in albums),
                       'n': len(albums), 'albums': albums})
    labels.sort(key=lambda x: -x['total'])

    data_out = {
        'generated': datetime.date.today().isoformat(),
        'source_date': '2026-10-05',
        'summary': {'pages': len(page_tracks), 'labels': len(labels),
                    'albums': len(rows)},
        'labels': labels,
    }
    with open(os.path.join(BASE, 'stats.json'), 'w', encoding='utf-8') as f:
        json.dump(data_out, f, ensure_ascii=False, indent=1)
    print('OK 廠牌=%d 專輯=%d 節目頁=%d' % (len(labels), len(rows), len(page_tracks)))

if __name__ == '__main__':
    main()
