# NL2 HU 河牌路徑 100%：導航驗收與「假設模型」邊界

- 專案：`tetracycline/poker-trainer`
- 分支：`fix/nl2-hu-lines-audit-20261118`
- PR：[#2](https://github.com/tetracycline/poker-trainer/pull/2) — **Draft，禁止合併**
- 日期：2026-11-19

## 驗收結果：100% 是可到達「河牌表」的導航，不等於 100% GTO 解算

GitHub Actions [44508555478](https://github.com/tetracycline/poker-trainer/actions/runs/44508555478) 的 `nl2-hu-audit` 原始 artifact 經確認：

| 指標 | 結果 |
| --- | ---: |
| 應連往下一街的合法翻／轉牌格（擴展模型後新分母） | **2,475** |
| 有下一街主連結並可走到河牌的格 | **2,475** |
| 路徑覆蓋率 | **100.0%** |
| 缺河牌路徑 | **0** |
| 真正棄牌終點 | **355** |
| 真正全下終點 | **12** |
| 原有 HU 表節點 | **224** |
| 新增明示假設的模型節點（轉／河） | **392** |
| 全部可見頁面節點 | **616** |
| 指向模型節點的主連結 | **2,092** |
| 已檢查同街次要錨點 | **1,410** |
| class × texture 的路徑不合法 | **0** |
| 「五欄、六牌面」合約錯誤 | **0** |
| 獨立原有 Combo 可達性稽核違反 | **0** |

**重要**：舊版 338/1,650＝20.5%（缺 1,312）是新增模型前的導航分母，不是已經確認有完整 solver 的 338 格。本版含實際生成的 392 張 MODEL 表及其新增可繼續的動作，因此分母改成 2,475；不能聲稱「1,312 格全部變 CERT／EST」，也不能把導航成功等同解算成功。

原始表有解算或來源證據的策略保留；現有證據到不了的合法行動新增獨立 MODEL 續街表，以可點選主連結連到下一街，缺資料處不再偽裝成牌局結束。網頁表頂、行動格與本文件標明 `MODEL／待真實 CFR`；MODEL 表**不是 GTO、不是 CERT／EST**。獨立 `tools/hu_model_path_audit.js` 逐行動、逐紋理、逐牌型欄核對 next-street 與 river，檢查主連結與 secondary anchors；`tools/link_audit.js` 作不同實作的交叉驗證並維持 100% PR 閘門。

## 固定共同假設（均為有效籌碼起始 100bb）

起始大小僅用於沒有可用真實牌局範圍／SPR 的模型路徑，**並非以代表翻牌直接映射到不同底池**。百分比為*先驗假設*，不是 NL2 玩家池直接測量頻率。

| 類型與對局 | 翻前行動假設 | 翻牌底池 | 有效剩餘籌碼 | 根 SPR | 範圍來源 |
| --- | --- | ---: | ---: | ---: | --- |
| SRP BTN vs BB | BTN 開池 2.5bb，BB 跟注 | 5.5bb | 97.5bb | 17.727 | 既有 `poker-solver` 翻前 169 類加權 CFR |
| SRP CO vs BB | CO 開池 2.5bb，BB 跟注 | 5.5bb | 97.5bb | 17.727 | 同上 |
| SRP SB vs BB | SB 開池 3bb，BB 跟注 | 6bb | 97bb | 16.167 | 同上 |
| SRP UTG vs CO | UTG 開池 2.5bb，CO 跟注 | 6.5bb | 97.5bb | 15.000 | 翻前 169 類動作鏈（原始碼有紀錄） |
| 3BP BB vs BTN | BTN 開池 2.5bb，BB 3-bet 10bb，BTN 跟 | 20.5bb | 90bb | 4.390 | 既有翻前 CFR |
| 3BP SB vs BTN | BTN 開池 2.5bb，SB 3-bet 10bb，BTN 跟 | 21bb | 90bb | 4.286 | 既有翻前 CFR |
| 3BP CO vs BTN | CO 開池 2.5bb，BTN 3-bet 7.5bb，CO 跟 | 16.5bb | 92.5bb | 5.606 | 翻前 CFR 動作鏈 |
| ISO BTN vs CO limper | CO limp 1bb，BTN 隔離至 4bb，CO 跟 | 9.5bb | 96bb | 10.105 | **假設：BTN 約 22% 隔離範圍、CO 約 28% limp-call 範圍** |
| ISO SB 隔離 | SB 隔離至 4bb | 9bb | 96bb | 10.667 | **假設**（需單獨實際解算） |
| LMP CO vs BB | CO limp 1bb，BB check，SB 0.5bb | 2.5bb | 99bb | 39.600 | **假設：limper 約 35%，BB 在無加注時可 check 的廣範圍** |

`tools/solve_hu_assumed_pots.py` 把 ISO／LMP 的各 169 類起始權重逐一寫死，嘗試使用真實 Rust CFR solver，原始 job、flop、turn/river、hash、SPR 由對應 Actions 輸出保存。即使解算完成，**只能在完全同位置、同 pot、同下注歷史、同公牌及逐 combo 範圍驗證之後**發布 CERT，不能直接替代目前網頁模型。

## 續街近似大小與牌面限制

對未完全解算節點：翻牌預設下注 ⅓ pot，轉牌 ½ pot，河牌 ¾ pot，常見加注 3 倍；模型依下注、跟注及加注重算當街剩餘有效籌碼與 pot，並於每一 MODEL 表列出使用的 **估計節點 SPR**。MODEL 的頂對好、頂對弱、中小對、強聽、弱聽僅按原表已可達的**顯示手牌分類**展開，未把它當作精確逐 combo CFR range，也**沒有**用不同 pot 家族的現有 90 翻牌資料直接跨家族 EST。

目前擴展時沿用來源牌面六分類的相同（brick-like）續街。真實發出的轉牌、河牌可能導致 A-high、paired、mono 或成牌類型升級，**需要按實際牌面重新分類，不能把此模型當可用於特定真實 runout 的 CERT**。若某個來源格的主動作是全下，或是棄牌，當作真終點，絕不要求後續河牌連結。

行動混合的真實過濾門檻只對已求解且有 combo 頻率的節點適用：每手牌必走最高頻動作；只有第二動作頻率 `f(a) ≥ 40%` 且 `f(a) ≥ 70% × f_max` 才保留另一條。**MODEL 階段沒有逐 combo 頻率，不能宣稱已通過這一驗證**。原表的獨立可達性審核與新增模型的導航審核是分開執行的。

## 真實解算／剝削／去極化的驗證狀態

- 既有原始解算 [44447817452](https://github.com/tetracycline/poker-trainer/actions/runs/44447817452)、[44481771702](https://github.com/tetracycline/poker-trainer/actions/runs/44481771702)；證據來源存檔完整性經 [44499274720](https://github.com/tetracycline/poker-trainer/actions/runs/44499274720) PASS；但 **90 代表翻牌不能自動覆蓋 ISO、3BP 等不同 pot/SPRs**。
- 新多街 CFR [44498509066](https://github.com/tetracycline/poker-trainer/actions/runs/44498509066) 與 [44499874094](https://github.com/tetracycline/poker-trainer/actions/runs/44499874094)：共 24 個真實 turn–river CFR 子局，來源／SPR／可達性驗證 [44500729006](https://github.com/tetracycline/poker-trainer/actions/runs/44500729006) 和 [44500957474](https://github.com/tetracycline/poker-trainer/actions/runs/44500957474) 均 PASS。
- 真實 50% pot 去極化配對 [44493984447](https://github.com/tetracycline/poker-trainer/actions/runs/44493984447)：經驗證尚無可直接發布到英雄策略格的 50% pot 決策；不能把對手的 50% pot 頻率錯標為英雄最佳下注。
- 新 assumed ISO/LMP pilot 工作流程 `[nl2-hu-assumed-iso-lmp.yml](../.github/workflows/nl2-hu-assumed-iso-lmp.yml)`（本文件建立時進行中），產物仍以原始資料為主，不自動將 392 個 MODEL 表格改為 CERT／EST。

## 距離『解算內容 100%』仍需完成

1. 對每個 MODEL 節點建立**真正可達**的翻前 169 類/1326 combo 範圍、精確下注歷史、起始與轉／河 SPR、真實牌面 runout；ISO/LMP 的假設需明示並與實際 NL2 池區別。
2. 以相同底池/SPR、位置、下注尺寸、完整行動歷史在 solver 中做多街求解；真實輸出應附原始 JSON SHA、收斂指標、node lock 資料來源和相同手牌分類映射。
3. 依 combo 的最高頻／雙門檻規則刪去不會經過的支線，按翻／轉／河牌真實紋理變化顯示對應策略格；重算導航分母，不用「刪掉難解格」製造 100%。
4. 把經逐格驗證的結果標 **CERT**，只有來源底池家族、節點 SPR、位置和行動歷史都相容才允許明示 **EST**；來源不足保留 MODEL 而不是自稱 GTO。
5. 多街鎖定剝削與去極化下注需更多盤面與合法 combo 頻率才能填為已驗證建議。未完成前 PR 保持 **Draft、不可合併**。