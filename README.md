# 音樂使用狀況｜知識平台網

互動式條形圖，統計知識平台網「罐頭音樂研究所」的音樂使用狀況。

- 🌐 線上：https://greensquare5168-debug.github.io/music-usage/
- 結構：**廠牌 → 專輯**（兩層）
  - `index.html`：廠牌使用排行（點條形／列 → 進入該廠牌）
  - `label.html?b=廠牌名`：該廠牌的專輯使用排行

## 更新資料

```bash
python3 build_stats.py   # 重新產生 stats.json
git add -A && git commit -m "update stats" && git push
```

## 資料來源

| 檔案 | 用途 |
|---|---|
| `網站音樂索引/all_20260925_full.jsonl` | 全站索引（頁面 × 曲目 × 平台 × 節目） |
| `站上使用最多_排行_20261003.txt` | TOP 曲目／TOP 作曲者 |
| `全站專輯_未建_依使用排序_含平台_20261003.txt` | 專輯 × 使用頁數 × 廠牌 |

> 原始資料位於 `~/clawd/projects/罐頭音樂/`。
> 廠牌由「圖書館」欄位正規化（去掉 CD / vinyl / digital / 年份等格式後綴）。
> 有部分專輯在來源資料未標廠牌 → 以「（未標廠牌）」列示。
