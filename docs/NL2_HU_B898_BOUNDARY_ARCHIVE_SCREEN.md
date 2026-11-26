# B898｜B897 明確靜態阻礙；新原根先做有限候選篩選

- PR #2 基線 a5a9ec9b5ee15a5c73734011ad5a083686731a11，open draft，僅指定分支；無 merge／force push。
- B897 原始 [45886968636](https://github.com/tetracycline/poker-trainer/actions/runs/45886968636) failure；job 140139967714 在 deterministic static enumeration 報 `NO_STATIC_RANGE_UI_WITNESS: no native dispatch`。Rust build 與 native/replay steps 均 skipped。Jd9d3c 的固定 2d/4d/5d/7d 研究結束，保留 APPROX；不把它當 native zero reach。不再修同一固定候選。 [完整批次稽核 45886968547](https://github.com/tetracycline/poker-trainer/actions/runs/45886968547) success。
- 本批分開處理兩件事：(1) 將 B896 已通過雙重重播的 4 個精確價格靜態負例、B897 未執行原根收據與原始 ZIP 保存至經完整稽核的 detached candidate，待 expected_sha 安全入庫；(2) rank29 仍為最高頻 1.378548%/手，先用不含原生結果的固定 A/K/Q-high two-tone suit-class universe，掃描留存資料及現行程式引用，保守排除已見 suit class；每 stratum 最多 4 個未見代表 flop，凍結後才檢查所有同花 turn 的合法實體牌組與現行 UI，避免再盲派無靜態 witness 的 root。兩件事獨立，不等 Actions。沒有新增原生派發，不能把靜態正向當作 CERT；下次須再對歷史 job/receipt 去重及來源可達性審核才考慮新 root，過期未歸檔來源仍是限制。此有界 cohort 不代表 rank29 已窮盡。
- Registry blob 59d02d3c7b5ed05515ec94bc1753300264598346 未變；前次完整資料驗收 158 CERT / 234 APPROX / 0 EST，84.700987% 模型節點機會覆蓋率（非實測獨立手牌），30 高頻 APPROX。本批程式從完整 registry 與凍結 weights 直接再計算。新正式 CERT/節點鎖/非極化均 0。B898 尚未驗收。
