#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
產生「音樂使用狀況」儀表板資料 (stats.json)
結構：廠牌(圖書館) → 專輯（依站上使用頁數）

資料來源：
  - ../網站音樂索引/all_20260925_full.jsonl   全站索引（頁面 × 曲目 × 平台 × 節目）
  - ../站上使用最多_排行_20261003.txt          TOP 曲目 / TOP 作曲者
  - ../全站專輯_未建_依使用排序_含平台_20261003.txt  專輯 × 使用頁數 × 廠牌
輸出：stats.json（與 index.html 同目錄）
"""
import json, re, collections, os, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
IDX   = os.path.join(ROOT, '網站音樂索引', 'all_20260925_full.jsonl')
RANK  = os.path.join(ROOT, '站上使用最多_排行_20261003.txt')
ALBUM = os.path.join(ROOT, '全站專輯_未建_依使用排序_含平台_20261003.txt')

UNKNOWN = '（未標廠牌）'

def brand_of(lib):
    """把『圖書館』字串正規化成廠牌清單（去掉 CD/vinyl/digital/年份 等格式後綴）。"""
    if not lib.strip():
        return [UNKNOWN]
    out = []
    for p in re.split(r'\s+/\s+', lib):
        p = p.strip()
        p = re.sub(r'^miscellaneous\s+', '', p)
        p = re.sub(r'\s+\(.*\)\s*$', '', p)
        p = re.sub(r'\s+(pre|post)-\d{4}.*$', '', p)
        p = re.sub(r'\s+albums?\b.*$', '', p)
        p = re.sub(r'\s*CD/digital.*$', '', p)
        p = re.sub(r'\s*vinyl/CD.*$', '', p)
        p = re.sub(r'\s+CD$', '', p)
        p = re.sub(r'\s+vinyl$', '', p)
        p = re.sub(r'\s+digital$', '', p)
        p = re.sub(r'\s+records/$', '', p)
        p = re.sub(r'\s+classical music$', '', p)
        p = re.sub(r'\s+Main Series$', '', p)
        p = p.strip()
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

def parse_albums(path):
    """回傳 [(廠牌, 專輯名, 使用頁數)]"""
    rows = []
    for line in open(path, encoding='utf-8'):
        m = re.match(r'^\s*\d+\.\s*(\d+)頁\s+(.+?)\s*｜\s*圖書館：(.*?)\s*｜\s*平台：', line)
        if not m: continue
        cnt = int(m.group(1)); name = m.group(2).strip()
        for b in brand_of(m.group(3)):
            rows.append((b, name, cnt))
    return rows

def norm_program(s):
    """節目名正規化：去掉集數後綴（例：古古食-ep-01什麼… → 古古食）"""
    s = (s or '').strip()
    s = re.sub(r'[-_ ]?ep[-_ ]?\d+.*$', '', s, flags=re.I)
    s = re.sub(r'[-_ .]+$', '', s).strip()
    return s

def main():
    tracks, composers = parse_rank(RANK)
    rows = parse_albums(ALBUM)

    # 廠牌 → 專輯
    lab = collections.defaultdict(lambda: {'total': 0, 'albums': []})
    seen = set()
    for b, name, cnt in rows:
        if (b, name) in seen: continue
        seen.add((b, name))
        lab[b]['total'] += cnt
        lab[b]['albums'].append({'name': name, 'count': cnt})
    labels = []
    for name, d in lab.items():
        d['albums'].sort(key=lambda a: -a['count'])
        labels.append({'name': name, 'total': d['total'],
                       'n': len(d['albums']), 'albums': d['albums']})
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
        'topTracks': tracks[:30],
        'topComposers': composers[:20],
        'platforms': [{'name': k, 'count': v} for k, v in usage_plat],
        'programs': [{'name': k, 'count': v} for k, v in programs],
    }
    with open(os.path.join(BASE, 'stats.json'), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('OK labels=%d albums=%d pages=%d records=%d'
          % (len(labels), len(best), len(all_pages), records))

if __name__ == '__main__':
    main()
