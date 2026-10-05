# 音樂使用狀況｜知識平台網

統計知識平台網「罐頭音樂研究所」的音樂使用狀況：**廠牌 → 專輯**。

- 🌐 線上：https://greensquare5168-debug.github.io/music-usage/
  - `index.html`：全部廠牌（點列 → 進入該廠牌）
  - `label.html?b=廠牌名`：該廠牌的專輯清單（編號／名稱／使用頁數；可用 A–Z 或使用頁數排序）

## 規則（2026-10-05 定案）

1. **只列站上「已有專輯頁」的專輯**（未建頁的不列）
2. **使用頁數**＝站上節目頁（yoyotv／巧連智／momo親子台／公視／古古食）中，
   有列出該專輯任一曲目的頁數；完全沒用到 → 0
3. **廠牌**＝站上《圖書館音樂》的分館；CPM 館內編號 `CAS…` → 「CPM Archive Series」、
   `CLASS…` → 「CPM Classical Series」（各自一系列）

## 更新資料

```bash
# 1) 重爬站台（頁面清單由站台導覽取得）
python3 ../網站音樂索引/scrape_site.py <urls.txt> ../網站音樂索引/all_YYYYMMDD_full.jsonl
# 2) 導覽快照 → site_nav_YYYYMMDD.json（見 ../網站自動生成/）
# 3) 產出統計
python3 build_stats.py      # → stats.json
git add -A && git commit -m "update stats" && git push
```

## 資料來源

| 檔案 | 用途 |
|---|---|
| `網站音樂索引/all_20261005_full.jsonl` | 站台全站索引（節目頁曲目）＝使用頁數來源 |
| `網站自動生成/site_nav_20261005.json` | 站台導覽（圖書館／專輯／曲目頁 名稱與階層） |

> 原始資料位於 `~/clawd/projects/罐頭音樂/`。
