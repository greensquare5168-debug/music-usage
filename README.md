# 音樂使用狀況｜知識平台網

互動式條形圖儀表板，統計知識平台網「罐頭音樂研究所」的音樂使用狀況。

- 🌐 線上：https://greensquare5168-debug.github.io/music-usage/
- 圖表：使用最多的曲目 TOP 30／作曲者 TOP 20／專輯 TOP 30／平台分布／節目分布

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
| `全站專輯_未建_依使用排序_20261003.txt` | TOP 專輯（依使用頁數） |

> 原始資料位於 `~/clawd/projects/罐頭音樂/`。
