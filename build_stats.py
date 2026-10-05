#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
產生「音樂使用狀況」儀表板資料 (stats.json)
資料來源：
  - ../網站音樂索引/all_20260925_full.jsonl   全站索引（頁面 × 曲目 × 平台 × 節目）
  - ../站上使用最多_排行_20261003.txt          TOP 曲目 / TOP 作曲者
  - ../全站專輯_未建_依使用排序_20261003.txt   TOP 專輯（依站上使用頁數）
輸出：stats.json（與 index.html 同目錄）
"""
import json, re, collections, os, sys, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
IDX  = os.path.join(ROOT, '網站音樂索引', 'all_20260925_full.jsonl')
RANK = os.path.join(ROOT, '站上使用最多_排行_20261003.txt')
ALB  = os.path.join(ROOT, '全站專輯_未建_依使用排序_20261003.txt')

def parse_rank(path):
    tracks, composers = [], []
    mode = None
    with open(path, encoding='utf-8') as f:
        for line in f:
            if 'TOP 60 曲目' in line: mode = 't'; continue
            if 'TOP 30 作曲者' in line: mode = 'c'; continue
            s = line.rstrip('\n')
            if not s.strip(): continue
            if mode == 't':
                m = re.match(r'^\s*(\d+)\s+(.+?)\s+—\s*(.*?)\s*\[.*\]\s*$', s)
                if m:
                    cnt = int(m.group(1)); name = m.group(2).strip()
                    comp = m.group(3).strip()
                    tracks.append({'name': name, 'composer': comp, 'count': cnt})
            elif mode == 'c':
                m = re.match(r'^\s*(\d+)\s+(.+?)\s*$', s)
                if m:
                    composers.append({'name': m.group(2).strip(), 'count': int(m.group(1))})
    return tracks, composers

def parse_albums(path, topn=30):
    out = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            m = re.match(r'^\s*(\d+)\.\s*(\d+)頁\s+(.+?)\s*｜\s*圖書館：(.*?)\s*$', line.rstrip('\n'))
            if not m: continue
            out.append({'name': m.group(3).strip(), 'count': int(m.group(2)),
                        'lib': m.group(4).strip() or '—'})
            if len(out) >= topn: break
    return out

def main():
    tracks, composers = parse_rank(RANK)
    albums = parse_albums(ALB)

    pl_pages = collections.defaultdict(set)
    pr_pages = collections.defaultdict(set)
    all_pages = set()
    records = 0
    with open(IDX, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            d = json.loads(line); records += 1
            p = d.get('url_path') or d.get('page_title')
            all_pages.add(p)
            pl_pages[d.get('platform', '')].add(p)
            pr_pages[d.get('program', '')].add(p)

    usage_plat = [(k, len(v)) for k, v in pl_pages.items()
                  if k and k not in ('圖書館音樂', 'view')]
    usage_plat.sort(key=lambda x: -x[1])
    programs = [(k, len(v)) for k, v in pr_pages.items() if k]
    programs.sort(key=lambda x: -x[1])
    programs = [p for p in programs if not p[0].startswith('arcadia')][:20]

    data = {
        'generated': datetime.date.today().isoformat(),
        'source_date': '2026-09-25',
        'summary': {
            'pages': len(all_pages),
            'records': records,
            'tracks': len(tracks),
            'albums': len(albums),
        },
        'topTracks': tracks[:30],
        'topComposers': composers[:20],
        'topAlbums': albums,
        'platforms': [{'name': k, 'count': v} for k, v in usage_plat],
        'programs': [{'name': k, 'count': v} for k, v in programs],
    }
    with open(os.path.join(BASE, 'stats.json'), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print('OK pages=%d records=%d tracks=%d albums=%d platforms=%d programs=%d'
          % (data['summary']['pages'], records, len(data['topTracks']),
             len(data['topAlbums']), len(data['platforms']), len(data['programs'])))

if __name__ == '__main__':
    main()
