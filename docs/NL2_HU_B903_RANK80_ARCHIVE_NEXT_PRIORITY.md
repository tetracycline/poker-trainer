# B903｜rank80 原始根不可達歸檔、rank83 與 rank92–94 前置檢查

B902 [來源診斷](https://github.com/tetracycline/poker-trainer/actions/runs/45919151213) 及 [完整稽核](https://github.com/tetracycline/poker-trainer/actions/runs/45919151153) 均 success。rank75 7 未測同花轉牌負例 3 檔已以 7188a7ff388c5dec75e332edc309e6b20fcb0777 安全快轉歸檔。rank80 B841 6c6d3h 嚴格 BB b33 62、CO c 0；KdJd5c 兩邊均 0；因此這兩個既有根的 90 個未測固定轉牌不能修復前街零可達，禁止重跑原根。不代表整個 rank80 耗盡。

B903 重播 B902 原始 SHA 及報告 byte equality，通過完整稽核後才產生 detached archive candidate。另依 B838 順序重新確認 rank83 (0.507599%/手) 的既有 primary ingress 5% SPR 衝突，再檢視 rank92/93/94 (各 0.446055%/手) 的實際渲染路徑、既有 references、crosswalk、歷史 source 提示。這是供下一批去重與正確價格原生候選篩選用的 inventory，不能當作完整歷史去重、合法雙策略 witness 或 CERT。無新 native，無重跑，無價格或 registry 改動。

B902 runner 重新計算 158 CERT / 234 APPROX，模型節點機會加權覆蓋率 84.700987%，30 高頻 APPROX。B903 尚未驗收。PR #2 永遠 open draft，禁止 merge/force push，不等、不輪詢 Actions。
