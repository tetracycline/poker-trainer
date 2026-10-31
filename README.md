# poker-trainer

撲克練習 v8（6-max NL2）。所有翻前範圍表、題目、答題後表格與課程數字都來自同一份解算器資料 `pf_data.js`。

- `index.html` + `app.js`：練習（預設穩健剝削 NL2 池版，可切 GTO）、翻前表、我的弱點、說明
- `solver.html`：解算器分頁（河牌練習、自己解河牌），`river/`、`data/river_v8.js`
- `learn.html` + `learn.js`：剝削打法四分頁（3-bet / Iso / 行動線 / 讀牌），資料唯一來源 `learn_data.js`、`reads_data.js`（由 poker-solver `gto_check/apply_gto.py` 產生，每條附 GTO 理論值 vs 玩家池）
- `sw.js`：service worker（cache `poker-v8-1031j`）

## 全站結構（1031j 整理）
`nav.js` 在每頁最上方放同一條主選單（大按鈕），每區下面是自己的分頁：
- ⌂ 首頁 `index.html#home`（5 個大按鈕；底下「更多」：我的弱點・我的實戰手牌・自己解河牌・說明）
- 翻前 `index.html#prac`：練習｜範圍表｜我的弱點｜說明
- 翻後 `postflop/index.html`：練習｜翻後表｜河牌解算器（`solver.html`）｜說明
- 剝削 `learn.html#tb`：3-bet｜Iso 跛入｜行動線｜讀牌（＋GTO 對照）
- 對手範圍 `learn.html#eq`：查表｜測驗（`eq.js`、`eq_data.js`）
- 覆盤 `review/`
舊網址都保留：`?p=…`、`index.html#<練習>`、`#charts`→範圍表、`#solver`/`#river`/`?p=solver`→`solver.html`。
