# 音樂使用狀況｜知識平台網

互動式網頁，統計知識平台網「罐頭音樂研究所」的音樂使用狀況。

- 🌐 線上：https://greensquare5168-debug.github.io/music-usage/
- 分頁
  - `index.html`：全部廠牌（點列 → 進入該廠牌）
  - `label.html?b=廠牌名`：該廠牌的專輯清單
  - `tracks.html`：全部曲目（含所屬專輯、可搜尋）
  - `programs.html`：節目分布
  - `platforms.html`：平台分布

## 更新資料

```bash
python3 build_stats.py   # 重新產生 stats.json + tracks.json
git add -A && git commit -m "update stats" && git push
```

## 資料來源

| 檔案 | 用途 |
|---|---|
| `網站音樂索引/all_20260925_full.jsonl` | 全站索引（頁面 × 曲目 × 平台 × 節目） |
| `站上使用最多_排行_20261003.txt` | TOP 曲目（歷史檔，已改用全站索引重建）|
| `全站專輯_未建_依使用排序_含平台_20261003.txt` | 專輯 × 使用頁數 × 廠牌 |

> 原始資料位於 `~/clawd/projects/罐頭音樂/`。
> 廠牌由「圖書館」欄位正規化（去掉 CD / vinyl / digital / 年份等格式後綴）。
> 有部分專輯在來源資料未標廠牌 → 以「（未標廠牌）」列示。
> 節目分布只列節目名稱（排除圖書館分類／廠牌，並把集數名併回節目）；**不含作者**。
> 曲目分布＝全部曲目（`tracks.json`），段落前綴（片頭曲／片尾曲／標題／簡介…）會去掉；查無專輯者標「（專輯待補）」。
