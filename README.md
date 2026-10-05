# 音樂使用狀況｜知識平台網

統計知識平台網「罐頭音樂研究所」的音樂使用狀況：**廠牌 → 專輯**。

- 🌐 線上：https://greensquare5168-debug.github.io/music-usage/
  - `index.html`：全部廠牌（點列 → 進入該廠牌）
  - `label.html?b=廠牌名`：該廠牌的專輯清單（編號／名稱／使用頁數，可用 A–Z 或使用頁數排序）

## 使用頁數怎麼算（2026-10-05 起）

**直接照站台現況**：站上節目頁（yoyotv／巧連智／momo親子台／公視／古古食）中，
有列出該專輯任一曲目的頁數（不含館藏／專輯頁自己）。

## 更新資料

```bash
# 1) 重爬站台（需要站台頁面清單）
python3 ../網站音樂索引/scrape_site.py  <urls.txt>  ../網站音樂索引/all_YYYYMMDD_full.jsonl
# 2) 產出統計
python3 build_stats.py      # → stats.json
git add -A && git commit -m "update stats" && git push
```

## 資料來源

| 檔案 | 用途 |
|---|---|
| `網站音樂索引/all_20261005_full.jsonl` | 站台全站索引（節目頁曲目、館藏頁）＝使用頁數來源 |
| `網站自動生成/site_nav_20261005.json` | 站台導覽（library／專輯／曲目頁 名稱） |
| `批次輸出/ALL/站上使用對照.md` | 專輯 → 曲目（PM Wiki 對照；純數字行視為解析錯已丟） |
| `全站專輯_未建_依使用排序_含平台_20261003.txt` | 廠牌／專輯清單 |

> 原始資料位於 `~/clawd/projects/罐頭音樂/`。
> 廠牌名稱正規化：去格式後綴（CD／vinyl／digital／年份）、去結尾 Music、
> 去 Production/Recorded Music Library・Music Sound Stage・Music Library・AMPS 尾巴、
> 古典分類；CPM Main→CPM、CPM Archive Series（CAS）、CPM Classical Series（CLASS）各自一系列、KPM 併為單一；
> 別名表 `ALIAS`（Omnimusic→Omni、Koka Media→Koka、Arcadia→Arcadia Cosmos）。
