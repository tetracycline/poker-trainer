# B859：B858 逾時隔離及下一順位 LMP 原根預檢

B858 原始兩個工作 Jh6d3c/2s、Th4d3c/7s 均在 native 步驟取消，編譯與預檢成功；不可視為 GTO 零可達，也不可升級。兩份 844-byte Actions artifact 的 API digest、job ID、run/head 已凍結。ZIP 內容雜湊待新 Actions 驗收。B858 全批靜態稽核 45608758792 已成功。rank114 仍僅有 B857 歸檔的 Th5d2c 正向來源。

依 B838 凍結順位（rank115、116、118 同為 0.328858%/手）利用 B724 已完成、具雜湊的三個原始 flop 的 12 個 BB b33/CO call 邊界，對三格共 36 個 rank × boundary 做真實兩座、實體牌組及三街顯示格預檢。原先 B718/B729 的已完成負例不重解。B732 的同一原根讀取器驗證原始 source receipt、job、root、SPR 和 boundary SHA；新預檢不是 turn 策略或 CERT。任何候選須再用未解的精確尺寸、雙策略與共同實體牌組驗收。若沒有候選則依頻率移往 rank122/123，不重刷相同根。

本提交僅入庫已查核的取消狀態及新的可重現工作；新 Actions 尚未驗收。158 CERT / 234 APPROX、84.700987% 模型節點機會加權覆蓋率不變。PR2 保持 open draft，禁止 merge/force push。
