# 覆盤頁產生器（tools/build_review.py）

把一場的分析結果做成網站上的覆盤頁：`review/<日期>.html`，並更新 `review/data/index.js`（覆盤列表，最新在上）。
翻前「我的弱點」分頁和最上面的「覆盤」按鈕都會讀這份列表。

## 每場流程
1. 用 analyze.py 解析手牌，得到 `hands.json`。**原始手牌和 hands.json 放在 repo 外面，不要 commit。**
2. 寫一份當天的 `review_config.json`，也放在 repo 外面（格式見下）。
3. 執行：
   ```
   python3 tools/build_review.py --hands /path/<日期>/hands.json --config /path/review_config.json
   ```
   會寫出 `review/data/<日期>.js`、`review/<日期>.html`，並更新 `review/data/index.js`，也會更新 `review/index.html` 和根目錄 `index.html` 裡列表的 `?v=`。
4. 用瀏覽器開來檢查，然後 commit、push 到 main（GitHub Pages）。

## 題目怎麼來
- **翻前錯題練習**：Hero 每個能對到 v8 樹的翻前決定（RFI、面對單一開池、開池後面對 3-bet、3-bet 後面對 4-bet；limp 底池和多人底池跳過）。用網站同一套評分規則：最高頻率的動作或頻率 ≥25% 的動作都算對；這裡挑剝削版判錯的，依 EV 損失排序。答案在網頁上即時從 `pf_data.js` 讀出，所以跟翻前表、練習題不會矛盾，切換 GTO 也會跟著改。
- **最貴的手**：在 config 的 `costly` 裡手動挑。
  - `"dec": "pre"`：翻前題，答案來自 solver。預設用這手第一個判錯的翻前決定；要指定第幾個就加 `"pre_n"`。
  - `"dec": {"st": "flop|turn|river", "k": 0}`：Hero 在那條街的第 k 個動作。要附 `opts`（[key, 顯示文字]）和 `ok`（正確的 key）。這種題目標成「非 solver，依原則判斷」。
  - `why`：揭曉時顯示的原因。

## 隱私
- 對手只顯示位置（UTG/HJ/CO/BTN/SB/BB），不會出現暱稱。如果輸出裡還留有任何暱稱，腳本會直接停下來。
- 只顯示 Hero 的手牌，以及攤牌時真的亮出來的牌。
- 金額都換成 bb，不輸出桌名、檔名或原始手牌文字。

## review_config.json 欄位
`date`、`title`、`session`、`result{net_bb,bb100,se_bb100,rake_bb,allin_ev_bb,luck_bb,adj_bb100}`、`conclusion[]`（可用 `<b>`）、
`stats[[項目,今天,累計,目標,"bad"|""]]`、`stats_note`、`leaks[{t,p,fix,go:[[練習id,名稱]]}]`、`post_notes[]`、`costly[]`。
範例：/workspace/poker_mb/review_20261030/review_config.json（在 box 上，不在 repo 裡）。

練習 id 跟 ../index.html#<id> 一樣，例如 sb、3bet、vs3b、rfi-sb、rfi-co、bb-co、bb-btn。

## Cumulative leak stats (leaks page)
`review/data/hw_stats.js` sets `window.HWS` (hands, span, prev, and per-stat k/n/pct/Wilson lo–hi/prev).
The leaks page (`app.js` renderLeaks) reads it; regenerate it after each review from the
de-duplicated cumulative hand set (raw hands stay outside the repo; only counts are published).
