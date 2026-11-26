# B901｜rank57 原始來源歸檔；rank75 既有根未測轉牌預檢

B900 [診斷與來源稽核](https://github.com/tetracycline/poker-trainer/actions/runs/45907839357) 與 [完整稽核](https://github.com/tetracycline/poker-trainer/actions/runs/45907839252) 均已成功。兩個 rank29 原生負例／8 個固定轉牌已於 475cf16ab21bcaae9132ab424a2eb66ddb3101df 歸檔。rank57 四個原生翻牌、16 個固定轉牌均為 GTO_DISPLAYED_ACTION_ZERO，不再重解已成功原根；B901 驗證 B900 原診斷 artifact 與四個原生 ZIP，建立通過完整稽核的 detached archive candidate，待 expected_sha 快轉。未測牌面不宣告耗盡。

依 B838 下一頻率 rank75（0.613597%/手）處理既有 B846 Td8d5d 原根（B849 已入庫；原先三個固定轉牌無正向證據）。只重播 raw chance 邊界並靜態檢查其他同花 turn，不重解原根、不重跑已測子局。任何新 native dispatch 仍須獨立全歷史去重與 pinned full-job byte replay。若無弱聽牌合法 witness，不派作業。B837 原根與已測 turn 不重試。

本批不改 registry 或 UI，不升 CERT；B900 實際重算 158 CERT / 234 APPROX，模型節點機會加權覆蓋率 84.700987%，不是獨立手牌覆蓋率。B901 尚未驗收。PR #2 保持 open draft，不合併、不 force push、不輪詢 Actions。
