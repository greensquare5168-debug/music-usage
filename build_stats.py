#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
產生「音樂使用狀況」資料（廠牌 → 專輯）——**只統計站上已有專輯頁的專輯**。

來源：
  - ../網站音樂索引/all_20261005_full.jsonl   站台全站索引（節目頁曲目）
  - ../網站自動生成/site_nav_20261005.json     站台導覽（圖書館／專輯／曲目頁 名稱與階層）

規則：
  1. 只列站上「已有專輯頁」的專輯（level 4, 圖書館音樂 底下）
  2. 專輯「使用頁數」＝站上節目頁（yoyotv/巧連智/momo親子台/公視/古古食）中，
     有列出該專輯任一曲目的頁數；完全沒用到 → 0
  3. CPM 館內：編號 CAS… → 「CPM Archive Series」、CLASS… → 「CPM Classical Series」（各自一系列）
輸出：stats.json
"""
import json, re, collections, os, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
INDEX = os.path.join(ROOT, '網站音樂索引', 'all_20261005_full.jsonl')
NAV   = os.path.join(ROOT, '網站自動生成', 'site_nav_20261005.json')

PLATFORMS = {'yoyotv', '巧連智', 'momo親子台', '公視', '古古食'}
ROLE_PREFIX = {'標題', '片頭曲', '片尾曲', '簡介', '進廣告', '插曲', '主題曲', '配樂',
               '片頭', '片尾', '開頭', '結尾', '前奏', '尾奏', 'BGM'}

def norm_track(t):
    t = (t or '').strip()
    p = t.split(' ', 1)
    return p[1].strip() if len(p) == 2 and p[0] in ROLE_PREFIX else t

def split_label(s):
    """導覽標籤 → (編號, 名稱)：'CAR176 - Children/Comedy/Shorts 2' → ('CAR176','Children/Comedy/Shorts 2')"""
    s = (s or '').strip()
    m = re.match(r'^(.+?)\s+[-–—]\s+(.+)$', s)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return s, ''

def main():
    # 節目頁 → 曲目集合
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

    nav = json.load(open(NAV, encoding='utf-8'))
    lib_name, albums, tracks = {}, {}, collections.defaultdict(list)
    for e in nav:
        parts = [p for p in e['href'].split('/') if p]
        if len(parts) < 5 or parts[3] != '圖書館音樂':
            continue
        if len(parts) == 5:
            lib_name[parts[4]] = (e.get('label') or parts[4]).strip()
        elif len(parts) == 6 and e.get('level') == 4:
            albums[e['href']] = (parts[4], (e.get('label') or parts[5]).strip())
    for e in nav:
        if e.get('level') != 5:
            continue
        parent = e['href'].rsplit('/', 1)[0]
        if parent in albums:
            t = re.split(r'\s+-\s+', e.get('label', ''))[0].strip()
            if t:
                tracks[parent].append(t)

    # 各專輯使用頁數
    rows = []
    for href, (slug, label) in albums.items():
        used = set()
        for t in tracks.get(href, ()):
            for pg, ts in page_tracks.items():
                if t in ts:
                    used.add(pg)
        code, title = split_label(label)
        brand = lib_name.get(slug, slug)
        if slug == 'cpm':
            c = code.upper()
            if c.startswith('CAS'):
                brand = 'CPM Archive Series'
            elif c.startswith('CLASS'):
                brand = 'CPM Classical Series'
        rows.append({'lib': brand, 'code': code, 'title': title, 'count': len(used)})

    lab = collections.defaultdict(list)
    for r in rows:
        lab[r['lib']].append({'name': (r['code'] + (' ' + r['title'] if r['title'] else '')).strip(),
                              'code': r['code'], 'title': r['title'], 'count': r['count']})
    labels = []
    for name, al in lab.items():
        al.sort(key=lambda a: -(a['count']))
        labels.append({'name': name, 'total': sum(a['count'] for a in al),
                       'n': len(al), 'albums': al})
    labels.sort(key=lambda x: (-x['total'], x['name']))

    data = {
        'generated': datetime.date.today().isoformat(),
        'source_date': '2026-10-05（站台重爬）',
        'summary': {'pages': len(page_tracks), 'labels': len(labels), 'albums': len(rows)},
        'labels': labels,
    }
    with open(os.path.join(BASE, 'stats.json'), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    nz = sum(1 for r in rows if r['count'])
    print('OK 廠牌=%d 專輯=%d（有使用 %d）節目頁=%d'
          % (len(labels), len(rows), nz, len(page_tracks)))

if __name__ == '__main__':
    main()
