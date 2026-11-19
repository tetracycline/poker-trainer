# NL2 HU 河牌覆蓋與解算來源審核 — 2026-11-19

> 分支：`fix/nl2-hu-lines-audit-20261118`，PR #2 僅保留 Draft，**不可合併**。下列「覆蓋率」是網頁主連結能走到河牌的既有稽核數，不是 GTO CERT 認證覆蓋率。

## 一、既有網頁路徑缺口（獨立 GitHub Actions）

- `link_audit.js` 的逐格證據已從只列 107 個粗略缺口聚合，改為 1,312 個獨立 cell ID，附來源表、六牌面列、手牌欄、動作、可點主連結、斷鏈位置、代表的中文行動歷史。資料輸出於 `link.json.unresolvedCells`。
- `hu_gap_plan.py` 按底池、翻前位置與完整可見歷史分為 **135 組**，每組有 cell IDs；任何缺 node-size/SPR/實際逐 combo range 者，`node_spr=null`，不假填。解算排程由 `nl2-hu-gap-plan.yml` 產生稽核檔。
- **網頁路徑 338 / 1,650＝20.5%；待補 1,312**，包括 865 個沒有主連結及 447 個轉牌繼續卻未抵達河牌。
- 底池分布：**SRP 534、3BP 387、ISO 232、limped 159**，合計 1,312。
- 已有可重現的精確翻前 CFR range／根底池／起始籌碼規格 **921 格**；尚未有來源證明 **391 格**，全部在 ISO 232 與 LMP 159，故這 391 格不可用現有 SRP/3BP 策略替代。
- UTG 開池 → CO 跟注：根底池 6.5bb，有效餘額 97.5bb，根 SPR 15.0；CO 開池 → BTN 3-bet → CO 跟注：開池 2.5bb，IP 3-bet 7.5bb，底池 16.5bb，有效餘額 92.5bb，根 SPR 約 5.606。這兩個新增位置所需的 169 手牌權重來自 `poker-solver/v8_build/build/pf_data.json` 的真實翻前動作鏈，而不是人工估算。根 SPR **不可代替** 翻／轉／河行動後的節點 SPR。

## 二、原始解算檔驗證

- 舊原始 Actions：`44447817452`、`44481771702`。
- 驗證／來源目錄 run [44499274720](https://github.com/tetracycline/poker-trainer/actions/runs/44499274720) **PASS**：列出且成功讀取 **137 份 artifacts、1,906 個 raw CFR JSON case 檔、270 個（spot,version,flop）組合**；來源壓縮包下載錯誤 0。已修正從 GitHub API 轉址到保存站時錯誤轉送 Authorization 導致的 401，並讓任何讀取錯誤 fail-closed。
- 舊 pipeline 只選一條大／小 c-bet 主線與 check-check，並非所有行動歷史；原始 1,906 份結果**不能**因翻牌紋理類似就直接 CERT／EST 到不同底池或 SPR。

## 三、這次實際新增的 CFR 解算

| run ID | 嚴格翻前範圍與位置 | 新解出的 turn+river 子局 | 零可達重量而排除 |
|---|---|---:|---:|
| [44498509066](https://github.com/tetracycline/poker-trainer/actions/runs/44498509066) | BTN_BB／BB3_BTN／SB3_BTN，GTO 與 NL2 對手頻率鎖定變體共 7 jobs | 12 | 2 |
| [44499874094](https://github.com/tetracycline/poker-trainer/actions/runs/44499874094) | 新增 UTG_CO／CO3_BTN，GTO、exp_ip、exp_oop 共 6 jobs | 12 | 0 |

共 **24 份真實多街 CFR 子局**，為（位置、版本、代表翻牌、翻牌 raise-call、轉牌）組合數，不代表 24 個已可直接發布的網頁格。兩個 GTO 子局（BB3_BTN 與 SB3_BTN 的 75% c-bet 後加注被跟）因來源行動後雙方 range 之一為零而排除，未創造假節點。

完整證據含 raw CFR、原始 job、sha256、每條後續牌面、投注額、當時底池與正確剩餘籌碼／SPR、GTO exploitability 或 locked hero gap。獨立審核 [44500729006](https://github.com/tetracycline/poker-trainer/actions/runs/44500729006) **PASS**：驗證第一批 7 jobs、12 子局之來源 SHA、全部節點 SPR 及對應牌面與 action lineage；39,357 個有可達權重的 combo×node、2,254 個符合接近混合頻率的 combo×node。新位置由獨立原始資料審核 [44500957474](https://github.com/tetracycline/poker-trainer/actions/runs/44500957474) **PASS**：6 份 artifact、12 個新位置子局，全部 SHA 與逐節點 SPR 核對成功，15,588 個可達 combo×node、1,034 個接近混合 combo×node。兩次來源審核合計 **24 個已驗證新子局、54,945 個可達 combo×node、3,288 個近混合 combo×node**；這些不是獨立手牌數，也仍未跨到 UI 格的 CERT。

**行動到達規則：** 每個 solver node 的每個有權重 combo，只保留最高頻動作；其他動作只有同時達到 `f(a) ≥ 40%` 與 `f(a) ≥ 70% × f_max` 才保留。此處不把強／弱頂對等牌類整體視為必然可達，也不將 pool aggregate 的頻率冒充每個 combo 的已觀測頻率。

## 四、去極化 50% 池下注與多街剝削

- 真實配對解算 run [44493984447](https://github.com/tetracycline/poker-trainer/actions/runs/44493984447)，來源驗證亦由 run **44500729006** PASS。
- BTN_BB，翻牌 `Ks7h2d`，由 IP 面對 OOP check 的節點，加入 50% 池後：**GTO 加權 b50 頻率 11.5369%，符合雙頻率可達門檻的 combo 為 0**；`exp_ip` 英雄 b50 為 **0.1462%，合格 combo 0**。
- `exp_oop` 的 IP 節點 b50 加權頻率 **30.3947%**，257 combos 符合門檻；但 **IP 是被鎖住的對手、OOP 才是英雄**，不能把對手下注尺寸標成英雄的去極化最佳下注。
- 故**尚無合格的 NL2 英雄 50% 池去極化決策格可發布**。`gate_depolarized_cfr.py` 檢查原始 SHA、真實 reach 與英雄位置，刻意關閉 `action_publish_allowed`。
- `exp_ip`／`exp_oop` 的 Rust 引擎確實依 NL2 玩家池 postflop 統計鎖定可對應的對手行動節點，且延續到河牌；然而沒有同底池/SPR、同街道及下注尺寸的完整網頁 crosswalk，不能把結果自動填回策略卡或聲稱每個節點都有足夠 pool 樣本。

## 五、合併閘門與未完成工作

1. **沒有虛構 CERT／EST：新增已認證的網頁河牌格 0、估計格 0；網頁連結覆蓋仍為 338/1,650（20.5%），不是 100%。**
2. 仍需建立 391 個 ISO/LMP 相關缺口的可追溯精確翻前 combo range，並針對 135 組的每個合法下注歷史逐一建模，而不是跨底池複製。
3. 未對應每個網頁格的原始牌面、翻牌→轉牌→河牌轉換、精確下注/加注尺寸、雙方 combo 權重與 node SPR 前，不能聲稱 CERT 或 EST，也不能把 solver 示範節點直接改成網頁連結。
4. 須把 combo 級雙門檻策略分支實際接到網頁渲染／可達性檢查；獨立端到端審核 100% 真正沿主連結到河牌後，才可把所有合格的新原始 GTO／剝削策略及 medium-size 證據發布。
5. 原 `NL2 HU navigation audit` 的 100% 合併 gate **繼續故意 FAIL**；PR #2 必須維持 Draft，不合併。

本文件及 workflows 不改動 `nl2.html` 或策略格；保留缺解算標示是為避免把猜測假裝成完成。
