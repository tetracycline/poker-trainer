# B861 — rank128 原始 SB_BB GTO 邊界篩查（0.297410%／手）
B860 原候選完成獨立逐位元重播、完整稽核及正式安全快轉。新一批依 B838 第21順位研究 rank128，排除 B735 已處理 KsQh4d/Tc 整個邊界，不重跑原根或先前負例。

來源為 B1 44666285424 和 B5 44736420272 的六個不同原始 GTO SB_BB 已成功 job；B5 整體曾取消，但所選三個原始個別 job 均成功。鎖定 artifact ID、ZIP SHA256、run/head/job、原始 root/subgame SHA、原始範圍與100bb底池。只做 b33 c 邊界及已有的 x b100 c/x 河牌輸出，逐座實體組合阻擋牌與顯示分類；沒有 export 不當作負例，GTO 單邊不可當 NL2 共同可達。無新 native、無 CERT、無新增鎖頻或去極化。尚未驗收，不能先報 PASS。後續只有可行且未研究的原始來源才另立 native continuation，不重複完成工作。

PR #2 保持 open draft。正式 registry 158/234，模型節點機會加權覆蓋率 84.700987%，不是不重複手牌覆蓋率。
