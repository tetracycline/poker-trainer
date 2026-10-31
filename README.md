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

## 部署前必跑：全站 QA（`tools/qa_all.py`）

```
python3 tools/qa_all.py            # 每個練習 500 題，約 30–40 分鐘；有任何失敗 exit 1
python3 tools/qa_all.py -n 30 --only ln,eq   # 快速檢查部分練習
python3 tools/qa_all.py --shots 50 --shotdir /tmp/qashots   # 另存 50 張截圖人工看
```

需要 playwright + Chrome、node。逐題檢查 7 類：
1. 範圍：發給你的牌是 HW 實際會玩的（`hwrange.js` 核心範圍，頻率 ≥50%，再依 HW 實際頻率收緊）；翻後/河牌只發會走到這條線的牌（到達率 ≥50%）。
2. 行動線：翻前到當前街每一條街的動作都要顯示，下注/加注都有尺寸。
3. 統計範圍：每個池統計都寫位置、整條線、合併或分牌面、n／攤牌 n、GTO vs 池和顯著性；信賴區間和「顯著」字樣要一致。
4. 快捷鍵：每個按鈕都有鍵。
5. 版面：1280×800 題目不用捲動、答案（對錯＋按鈕）在 800px 內；手機字比桌機大（≥15px）。
6. 剝削規則：池顯著偏離 **且** 每手多賺 >0.25bb 才剝削，否則照 GTO。
7. 牌：手牌兩張、不重複。

資料重建工具：
- `tools/build_hwrange.py` → `hwrange.js`（HW 實際範圍，來源 `hw_stats_cumulative.json` ＋ 網站核心範圍）。
- `lines_v1/apply_hw.py`（工作區）→ `learn_data.js`：行動線例牌、GTO vs 池文字、0.25bb 規則。
- `read_tx/add_gto.py`（工作區）→ `reads_data.js`：讀牌每題的 GTO 動作與顯著性。

## 整手模式（翻後 → 整手）

一手牌從**翻前**打到開牌。兩個入口（翻後分頁列，或整手頁上方切換、**V** 鍵切換）：

- **剝削整手** `postflop/index.html#handx`：對手照 NL2 池頻率；你每一步用剝削解評分（翻前 pf_data v8-1031x 剝削節點、翻後／河牌站上的剝削解），但只有在池顯著偏離 GTO **且** 剝削多賺 > 0.25bb 時才偏離 GTO，否則照 GTO 評分。每步寫：依剝削或 GTO 評分＋原因、你選的頻率、剝削模型下每個動作的 EV（照 GTO 評時也列 GTO EV）、你這個動作之後對手的池統計 vs GTO（n、95% 區間、顯著/不顯著）。只發剝削解會走到的手；你偏離剝削線之後剝削解走不到的點標示「剝削解裡這手不會走到這裡 → 照 GTO 評分」。
- **GTO 整手** `postflop/index.html#handg`：全部照 GTO 解評分。

細節：

- 翻前：隨機情境（你開池 UTG/HJ/CO/BTN/SB、你在 BB 面對開池、你在 SB 面對 BTN 開），你的牌只從 HW 在那個位置會玩的範圍發（hwrange.js）；你的翻前動作用 v8 翻前解評分（剝削版只在多賺 > 0.25bb 時才偏離 GTO）。
- 對手翻前／翻後動作：NL2 池頻率（n≥500 且 GTO 在 95% 區間外）→ 照池抽；否則照 GTO。每個動作的依據都列在「對手動作依據」。
- 翻後：跟注後進入對應的 HU 翻後解（X_BB、SB_BB、BB3_BTN、SB3_BTN）；沒解的翻前線（例：非 BTN 的 3-bet 底池、4-bet 底池）直接發完到開牌，標示「不評分」。
- 每個決策當場顯示：對錯、EV 少多少、最佳動作與頻率、你的勝率（對他走到這裡的範圍）、跟注需要的勝率、每個動作的 EV。
- 一手結束：整手回顧（每個決策、每步少多少 EV、依剝削或 GTO、整手 EV 共少多少、對手的牌——依他的範圍＋每個動作的 GTO 機率抽樣）。
- 解只存主要的線：離開解的線之後自動過牌/跟注到開牌（標示「不評分」）。
- 快捷鍵：F 棄、C 跟/過、R 開池/加注/下注、B/N 第二/第三個下注尺寸、A 全下、空白 繼續、V 切換剝削整手/GTO 整手。
- QA（tools/qa_all.py）跑 `postflop:handx` 和 `postflop:handg`：剝削整手沒偏離剝削線時不能出剝削解走不到的手、不能頻率 0% 判對、每步要寫依據與原因、剝削評分要列剝削模型 EV 與池統計（n）。
