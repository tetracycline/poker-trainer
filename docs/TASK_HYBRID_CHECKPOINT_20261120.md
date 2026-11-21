# TASK-HYBRID｜即時交付與凍結範圍（2026-11-20）

**Repository:** `tetracycline/poker-trainer`  
**PR:** [#2](https://github.com/tetracycline/poker-trainer/pull/2)  
**Branch:** `fix/nl2-hu-lines-audit-20261118`  
**狀態:** Draft、Open、**禁止 merge**。

本檔案是經已完成 GitHub Actions 原始來源檢查後的有限 checkpoint。已停止擴大策略範圍；不把尚未完成的 GTO / EXP 或無法匹配的牌面當成已驗證。

## 已交付的 392 格分類

| 分類 | 數量 | 實際含義 |
|---|---:|---|
| **CERT-MULTIBOARD** | **12** | 限同底池、位置、具體行動線和 SPR 的 3–5 個**具名公牌**真實 GTO；**不宣稱整格所有紋理為 GTO** |
| **APPROX** | **380** | 近似模型，介面明確標示，並附無法驗證的原因 |
| **EST** | **0** | 不以跨家族／跨 SPR 的近似標記為已解算 |
| **已分類** | **392 / 392** | 高頻排名先前固定前 24 格，其中 12 已獲多公牌來源，另 12 高頻與 368 低頻暫為 APPROX |

分類來源：[`data/nl2_hu_multiboard_status.json`](../data/nl2_hu_multiboard_status.json)。  
詳細各認證格之 3–5 翻牌、實際轉牌、公牌、下注歷史、SPR、combo reach、source SHA 和 EXP 對照：[多公牌來源對照](NL2_HU_MULTIBOARD_STATUS.md)。

## 真實 CFR 已完成與封存

| Source | GitHub Actions 結果 | 真實多街 CFR 子局 | GTO 指定公牌 | NL2 局部 node-lock 試驗 | 認證處理 |
|---|---|---:|---:|---:|---|
| 既有 Stage 2 五批 | 各次來源驗證通過 | 644 | 219 | 425 | 已是原始來源 |
| [B1 Run 44666285424](https://github.com/tetracycline/poker-trainer/actions/runs/44666285424) | **PASS**；18 個 solver jobs + 獨立驗證 | 247 | 88 | 159 | 已納入新 392 格分類 |
| [B3 Run 44666294821](https://github.com/tetracycline/poker-trainer/actions/runs/44666294821) | **PASS**；9 個 solver jobs + 獨立驗證 | 133 | 43 | 90 | 已納入新 392 格分類 |
| [B2 Run 44666290556](https://github.com/tetracycline/poker-trainer/actions/runs/44666290556) | **FAIL**；17/18 個 solver jobs 成功，`SB3_BTN / 8s8h3d / GTO` 失敗，verify-and-commit skipped | 不入帳 | 不入帳 | 不入帳 | 隔離，不得標 CERT |

已來源驗證並分類的 B1+B3 新增 **380 個真實子局**（GTO 131、局部鎖頻試驗 249）。連同既有正式來源，現在可追溯的指定公牌真實子局 **1,024**（GTO 350、局部鎖頻試驗 674）。這些「指定公牌子局」與「392 個抽象 MODEL 節點」不是同一統計單位；對照後僅 12 格獲得多公牌認證。

B1 完整索引：[`data/solver_evidence/NL2_MULTIBOARD_B1.index.json`](../data/solver_evidence/NL2_MULTIBOARD_B1.index.json)；
B3 完整索引：[`data/solver_evidence/NL2_MULTIBOARD_B3.index.json`](../data/solver_evidence/NL2_MULTIBOARD_B3.index.json)。
原始證據 `.json.gz` 與驗證資訊同目錄。

## 逐 combo 可達性、節點鎖及中尺度下注

- GTO 與 EXP 源由真實 Rust CFR 產生，保存公牌、完整 action、根 pot/stack 及 node SPR。
- 每個組合只走最高頻動作；另一動作只有同時 `f(a)≥40%`、`f(a)≥70%×fmax` 才能保留。來源保存逐街可達性與卡片 blocker 檢查。
- B1/B3 的 **249** 個 EXP 子局採用 NL2 實測的聚合頻率；沒有精確 action-history 資料時，以**已註明的預設**補上，不能宣稱所有對手或私有手牌均已實測／鎖定。
- 已完成的 Stage 2 去極化分析，**847** 個 GTO/英雄的精確牌面 b50 研究候選，當中 **769** 個符合既有最優 EV 比例門檻。它們是具體牌面研究候選，不是所有 MODEL 中等下注的泛用最優策略。
- 訓練頁 `nl2.html` 與 `nl2_hu_multiboard_ui.js` 明確顯示 **CERT-MULTIBOARD**、各公牌範圍及 **APPROX 近似**，`nl2-multiboard.html` 可查看具體來源的牌面、hole-card combo 與局部鎖頻實驗。

**NL2 頻率來源：** 2,334,487 手牌，SRP 61.7%、limped pot 24.5%、3-bet 11.9%。高頻事前截斷為 24 / 392。ISO 未另行實測精確 postflop 比率，採 limped 家族 25% ISO / 75% LMP 代理假設；未觀測過牌後下注率預設 45%，下注尺寸 33/50/75/100% 比例 35/35/20/10。**這些都是已揭露假設，不是真實 NL2 逐節點／逐私牌觀察。**

## 河牌路徑

[Run 44722773687](https://github.com/tetracycline/poker-trainer/actions/runs/44722773687) 的獨立 HU navigation / link audit **PASS**：

- **2,475 / 2,475＝100%** 合法延續可到達河牌。
- 392 個 MODEL 表，0 條缺河牌鏈；367 個合法棄牌／全下終點。
- 此數字**不是 100% GTO／CERT**；後續只改分類來源、文件與標籤，沒有新增或刪除 HU 導航線。

## 暫停擴大後的剩餘清單（之後每個批次上限 30 分鐘）

1. **B2 分離修復**：僅處理 GTO `SB3_BTN 8s8h3d` 失敗，或將其餘成功來源分離獨立驗證；未驗證前不計入證書。
2. **剩餘 12 個前 24 高頻節點**：按同一底池、位置、實際行動歷史、SPR，補齊各自 3–5 個具名公牌的 GTO 與英雄 node-lock；每批只做可在 30 分鐘內完成並驗證的有限工作，未完成保持 APPROX。
3. **證據與前端每批校驗**：逐 combo reach、node-lock 來源與預設、b50 equity/EV、100% 導航 CI；驗證通過才 commit 並 push，未達門檻不冒充 CERT。
4. **368 個低頻格** 按事前截斷繼續保持 APPROX；不再擴大研究工作量，也不因已看到 GTO 結果反向調整高頻排序。

此 checkpoint 已直接推上 PR #2，沒有合併。