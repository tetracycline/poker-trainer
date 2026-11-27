# B902｜rank75 原始篩選歸檔、rank80 既有根未測轉牌前置檢查

B901 [來源及篩選](https://github.com/tetracycline/poker-trainer/actions/runs/45913269104) 與 [完整稽核](https://github.com/tetracycline/poker-trainer/actions/runs/45913269073) 均 success。rank57 四原生根與16固定轉牌負例7檔已由 ba6371304736541dbb510f927f2773c695b72d30 入庫。rank75 Td8d5d 原始轉牌 2d/3d/4d held-out binary64 遮罩重播成功；七個未測同花 turn 6d/7d/9d/Jd/Qd/Kd/Ad 無弱聽牌合法 witness，不派原生。B902 重新獨立重播、驗證 ZIP SHA、完整稽核後產生 detached archive candidate。

依 B838 順序，rank76 既有 B705 鎖頻精確尺寸有結構性衝突。下一 rank80 (0.560271%/手) 使用 B843 已入庫兩個 B841 原生根 6c6d3h、KdJd5c。辨識 flop b33/c 嚴格可達是否為零；若 root 非零，驗證 held-out 遮罩重播，僅篩選其45個未測固定 turn。靜態 lead 不算解算，不直接派原生，下一批仍須全歷史去重與完整 job 位元組重播及雙策略同一實體牌組可達。原先已解的固定轉牌不重跑。

B901 runner 重算 registry：158 CERT / 234 APPROX，模型節點機會加權覆蓋率 84.700987%，30 高頻 APPROX。B902 不改 registry 或 UI，不升 CERT，不宣告任何高頻格全域耗盡。B902 尚未驗收。PR #2 永遠 open draft、不合併、不 force push、不輪詢。
