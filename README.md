# 音樂使用狀況｜知識平台網

統計知識平台網「罐頭音樂研究所」的音樂使用狀況：**廠牌 → 專輯**。

- 🌐 線上：https://greensquare5168-debug.github.io/music-usage/
  - `index.html`：全部廠牌（點列 → 進入該廠牌）
  - `label.html?b=廠牌名`：該廠牌的專輯清單（依使用頁數）

## 更新資料

```bash
python3 build_stats.py   # 重新產生 stats.json
git add -A && git commit -m "update stats" && git push
```

## 資料來源

| 檔案 | 用途 |
|---|---|
| `全站專輯_未建_依使用排序_含平台_20261003.txt` | 專輯 × 使用頁數 × 廠牌 |
| `網站音樂索引/all_20260925_full.jsonl` | 全站索引（頁面統計） |
| `網站自動生成/網站頁面清單_快取.json` | 站上已建專輯頁（曲目→專輯對照備用） |
| `批次輸出/ALL/站上使用對照.md`、`批次輸出/{Bruton,Parry}/*曲目-作者*.txt` | 曲目→專輯對照備用 |

> 原始資料位於 `~/clawd/projects/罐頭音樂/`。
> 廠牌由「圖書館」欄位正規化：去格式後綴（CD / vinyl / digital / 年份）、去結尾 Music、
> 去 Production/Recorded Music Library・Music Sound Stage・Music Library・AMPS 等尾巴、
> 古典分類、CPM/KPM 各系列併為單一廠牌；別名表 `ALIAS`（例：Omnimusic → Omni）。
> 有部分專輯在來源資料未標廠牌 → 以「（未標廠牌）」列示。
