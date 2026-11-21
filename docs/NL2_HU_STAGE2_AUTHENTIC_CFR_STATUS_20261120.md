# NL2 HU 第二階段｜真實 CFR、嚴格組合可達性及剝削研究交接（2026-11-20）

專案：`tetracycline/poker-trainer`，**PR #2 維持 Draft，絕對不合併**。主線：`fix/nl2-hu-lines-audit-20261118`。

## 摘要與認證邊界

| 指標 | 真實驗證成果 |
| --- | ---: |
| 導航到河牌 | **2,475 / 2,475（100%）** |
| SRP／3BP 五批真實 Rust CFR 翻牌→轉牌→河牌子局 | **644** |
| 指定公牌＋精確 action／SPR 的 GTO 來源 CERT | **219** |
| 同樣具來源的 NL2 部分頻率鎖定剝削子局（研究中） | **425** |
| 具獨立完整翻牌→轉牌→河牌逐 combo「最高頻／近混頻」門檻交集稽核的子局 | **297** |
| ISO／LMP 額外假設 100bb + NL2 實測邊際頻率鎖定試算 | **16**（與上面 644 分開） |
| 通用六牌面／五手牌分類 MODEL 表節點 | **392** |
| 通用 MODEL 真正升級的 CERT／EST | **0／0** |

**不能混淆：** 「原始 CFR 真實求解了某個具體公牌」不等於「相同抽象牌面類別／行動線的全部 NL2 策略格獲得 GTO 認證」。原始 392 張 MODEL 表沒有完整翻牌、轉牌、河牌的具體卡片，也沒有精確的歷史下注尺寸／經前街條件化後的 combo range，因此不能依法則直接用近似 SPR 或牌面紋理貼 CERT／EST。

## 經 GitHub Actions 真實求解、來源與收斂驗證的五批

| 批次 | 原始真實 CFR 解算 run | 真實子局 | 指定公牌 GTO | NL2 部分鎖定 |
| --- | --- | ---: | ---: | ---: |
| 01 | [44521980749](https://github.com/tetracycline/poker-trainer/actions/runs/44521980749) | 118 | 38 | 80 |
| 02 | [44522421850](https://github.com/tetracycline/poker-trainer/actions/runs/44522421850) | 148 | 48 | 100 |
| 03 | [44525865923](https://github.com/tetracycline/poker-trainer/actions/runs/44525865923) | 81 | 28 | 53 |
| 04 | [44653774402](https://github.com/tetracycline/poker-trainer/actions/runs/44653774402) | 158 | 55 | 103 |
| 05 | [44654973894](https://github.com/tetracycline/poker-trainer/actions/runs/44654973894) | 139 | 50 | 89 |
| **合計** | | **644** | **219** | **425** |

原始證據 `data/solver_evidence/STAGE2_BATCH01.json` 至 `STAGE2_BATCH05.json`：對照真實 Rust solver 輸出、flop/turn/river、原始 SHA-256、逐節點籌碼／SPR、收斂及逐 combo 可達性。獨立批次 04 source promotion [44656568523](https://github.com/tetracycline/poker-trainer/actions/runs/44656568523) **PASS**、批次 05 [44657606848](https://github.com/tetracycline/poker-trainer/actions/runs/44657606848) **PASS**。精確公牌資料以 GTO／剝削分開標記及 gzip 保存於 `data/nl2_hu_exact_boards*.json.gz`。

已加入網頁：`nl2-cfr.html` 顯示每一個真實 solver 公牌與 action line、玩家 OOP/IP、有效 SPR、GTO 頻率、合法 combo、各行動之 EV 證據與來源；原 `nl2.html` 中的 MODEL 表提供「同位置、同底池／SPR 類似」真實公牌**研究範例連結**，不宣稱原 MODEL 已獲 CERT。

## 跨街組合可達性

實際保留：每個 combo **最高頻動作**；另外只有頻率 `f(a) ≥ 40%` 且 `f(a) ≥ 70% × fmax` 的第二動作可以保留。沿翻、轉、河依序交集，並剔除卡牌相撞、原始 solver 零 reach 的組合。**沒有依結果反轉或額外猜測沒有可達權重的牌。**

- [44657949680](https://github.com/tetracycline/poker-trainer/actions/runs/44657949680)／[44658130952](https://github.com/tetracycline/poker-trainer/actions/runs/44658130952)：批次 04 全街嚴格可達性驗證 PASS。
- 批次 05 `nl2_hu_sequential_reach_official_b05.json.gz` 的逐街組合及原始來源亦已由 CI 輸出。
- [44658483176](https://github.com/tetracycline/poker-trainer/actions/runs/44658483176)：跨街 297 真實子局獨立重核 PASS；19,744 個 node，原始 1,775,300 個可達 combo×node，在逐街最高頻／近混頻檢查後剩 508,138 個（28.62%），1,267,162 個被排除。**這是依既有 solver 決策做合法路徑篩選，不等於重解最佳回應。**

驗證文件：`data/nl2_hu_stage2_sequential_status.json`，可追溯到真實 Actions、SHA、board 與 action line。

## NL2 玩家池多街鎖定剝削、EV 與中下注尺寸

- 實際參照 NL2 玩家池 `poker-solver/inputs/pool_stats.json` 的已觀察聚合動作頻率及 n；只有符合來源規則的節點才鎖，其餘敵手節點未鎖。單靠 aggregate fold/raise/bet 或下注分布**不能**推知對手各個 hole-card combo 真實機率。
- 425 個真實部分鎖頻 solver 子局，鎖頻後英雄「相對模型 EV 增益」（單位 bb）已輸出至 `data/nl2_hu_exploit_depol_report.json`，但這不是實測 NL2 淨贏率。若需要真正「每個節點」的 NL2 最佳回應，仍必須提供各下注歷史、下注尺寸及真實行動頻率的細分原始玩家池資料，不可臆測。
- 以真實 CFR 公牌與 combo 選擇門檻篩出 **847 個 GTO 或英雄**（明確排除已鎖敵手自己的下注）的 50% pot 中下注尺寸、非極化相對 equity 研究候選節點；其中 **769 個**在至少 40% 的合格 combo 上，50% 尺寸同時是源 solver EV 最高行動。這仍不是對所有類似牌面都建議下注 50% 的證明。來源還有 1,181 個包括敵手在內的候選節點，不可把後者混當英雄建議。
- 額外 ISO／LMP 100bb 明示假設 + 觀測 NL2 邊際頻率實際多街 Rust CFR：[44654142656](https://github.com/tetracycline/poker-trainer/actions/runs/44654142656)，16 子局；[44655987659](https://github.com/tetracycline/poker-trainer/actions/runs/44655987659) 獨立驗證 PASS。**ISO 玩家池來源僅用同街 SRP 統計作明確標註的 proxy，非 ISO 逐手牌真實頻率；不算作通用模型 CERT。**
- 新頁面 `nl2-exploit.html` 提供真實部分鎖頻 EV、來源 run、有效樣本比、各公牌最優行動的可達 combo、50% pot 去極化候選及逐 combo EV 第一名的占比，未自動改動原 392 MODEL 動作。

## 392 張通用 MODEL：嚴格來源對照，不能虛構

獨立驗證 [44658073328](https://github.com/tetracycline/poker-trainer/actions/runs/44658073328) **PASS**，`data/nl2_hu_model_history_crosswalk.json` 以五批、644 子局逐表核對：
- **100**：同家族／位置與抽象下注歷史，來源節點 SPR 誤差 ≤1%（**仍缺 MODEL 的具體公牌，不能 CERT／EST**）。
- **140**：有相同抽象行動線，但 SPR 不符，禁止轉用。
- **152**：尚無相應精確 CFR source line；含 ISO／LMP 共 98 格。
- **認證 MODEL = 0／392**；導航 2,475/2,475＝100% 維持。既有抽象手牌類列為教材上的假設，不冒充各 combo 的 GTO 決策。

## 真正仍待完成／合併禁止條件

1. 讓每張通用 MODEL 定義**具體公牌**及完整行動線（包含下注／加注尺寸）、準確的當街 pot／剩餘籌碼／SPR，將各 combo 的真實牌面分類升級和合法到達範圍逐一映射，才能談逐格 CERT。保留現在六牌面分類的泛化教材時，只能維持 MODEL。
2. NL2 玩家池的逐 action-history × position × pot/SPR × size 頻率沒有足夠原始資料；不可宣稱「所有對手節點」已被真實頻率鎖住，亦不可把模型英雄 EV 差視為實盤最佳贏率。
3. 中等尺寸／去極化建議需以多盤面、同模型尺寸集合比較 EV 和穩定性；目前是來源明確、但非可泛用的研究候選。
4. **PR #2 必須繼續 Draft；不 merge、不自動標 Ready。** 「導航 100%」與「原始精確公牌 GTO 子局 219」和「模型 CERT 0/392」三個數字不得混淆。

## 程式入口與可下載來源

- `tools/solve_hu_missing_branches.py`：100bb 真實 CFR、位置、下注尺寸及 multi-street parent ranges；外部 Rust CFR 引擎 pinned SHA。
- `tools/hu_action_reach.py` 和 `tools/hu_sequential_cfr_reach.py`：逐 combo、跨街 max／near-mix、物理卡牌排除與來源 SHA 稽核。
- `tools/verify_hu_solver_bundle.py`：雙面來源檔案／pot／SPR／range／收斂／鎖頻來源驗證。
- `tools/hu_incremental_batch.py`、`tools/hu_stage2_combine_sources.py`、`tools/hu_exploit_depol_report.py`：批次索引、總量稽核、局部剝削與中尺寸研究。
- `data/nl2_hu_stage2_status.json`、`data/nl2_hu_stage2_sequential_status.json`、`data/nl2_hu_exploit_depol_report.json`、`data/nl2_hu_model_history_crosswalk.json`。

此文件記錄已驗證結果及最難的**語意阻礙**：沒有實際發牌組合就不存在能跨同類紋理通用的 combo 級 CERT。不得靠填寫 EST 或刪除合法模型格子完成假的「100% GTO」。