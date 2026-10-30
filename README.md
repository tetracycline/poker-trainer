# poker-trainer

撲克練習 v8（6-max NL2）。所有翻前範圍表、題目、答題後表格與課程數字都來自同一份解算器資料 `pf_data.js`。

- `index.html` + `app.js`：練習（預設穩健剝削 NL2 池版，可切 GTO）、翻前表、我的弱點、說明
- `solver.html`：解算器分頁（河牌練習、自己解河牌），`river/`、`data/river_v8.js`
- `sw.js`：service worker（cache `poker-v8-1030b`）
