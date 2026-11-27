# B906｜B905 單次收據恢復、rank104/105 保存根篩選

PR #2 head af5e067d61a1b2a1344aaa87fdd89545c30c3fff，open draft。直接重讀 6,533,310 bytes registry blob 59d02d3c7b5ed05515ec94bc1753300264598346 與凍結 392 格權重：158 CERT / 234 APPROX、加權模型節點機會 84.70098741122534%、30 高頻；並非獨立手牌覆蓋率。

本批控制器的 commit workflow 查詢僅含 pull_request 觸發，對 B905 返回空；不得因此假定 B905 失敗或 PASS。B906 一次讀 B905 已派發來源、核 SHA 和 archive job 收據；驗證原 detached candidate 的 13 檔內容後，完整稽核才允許在當前 B906 head 建立新 detached archive candidate，絕不自行動 ref。B905 plan 仍需逐案歷史去重；不派新 native。增加一條 PR 技術收據（僅 run ID 和 job 結果，不更動 PR 狀態）讓下一輪可直接定位來源。

按頻率並行研究下一組 rank104/105（各 0.383122%/手），B524 原始 7d5c4c、5h4h3s、8h7h5c 的 GTO / exp_ip 均有已完成成功 job 和未過期 ZIP。排除 B720 已知轉牌、6s5h4d/Kd 的 B847/B850 負例以及 exp_ip job cancelled 的 6d4c3h。不重跑任何原生解算。僅驗原 manifest 中兩策略共有的固定轉牌、實際 actor/價格及相同實體雙方牌組的前街 gate。rank104 之 b75 不在此原 turn menu，不能將原 b50 代替或宣告全域不可達；rank105 的正向線索仍需實際 river 動作和獨立完整來源重播。完整祖先與 artifact metadata 盤點不是 native 去重 clearance。無新 CERT、lock 或非極化，未驗收不得稱 PASS。
