# B896｜既有原生 Jh9s4c 的未研究精確價格邊界

PR #2 保持 open draft，不合併，不 force push。本批不重跑已完成 native。

- 最新正式基線 `14974cf4fd027ff6fca6b35a01e2dda54734709d`；B895 入庫後完整稽核 [45871209601](https://github.com/tetracycline/poker-trainer/actions/runs/45871209601) success。直接讀取完整 current registry Git blob `59d02d3c7b5ed05515ec94bc1753300264598346` 與凍結權重重算：158 CERT / 234 APPROX、84.700987% 模型節點機會加權覆蓋率，30 格達 0.2% 門檻，非實測獨立手牌覆蓋。
- B843、B845、B849、B850、B852、B857、B860、B864、B865、B878、B884 的現有結果仍是各自已測邊界／負例／取消證據；不得把取消或缺來源當零可達。保留 B838 的頻率排序；本批只處理已定位到原始未測精確尺寸來源的末段 rank157、158，先 rank157，不能宣稱其餘高頻格皆耗盡。
- B538 原始已完成雙來源 run 45119866932：Jh9s4c GTO artifact 14793064321、exp_oop artifact 14793179237，均未過期、原 head 相同、SHA256 固定於程式。
- B538 已驗 Qc、4h、Kd 的舊 check/check 子局，非新的 b75 或 b33 turn lead。B887 已研究 Qc 的精確尺寸靜態邊界；本批排除 Qc、6c6d3h 三個已知零 NL2 共同可達、8h8d4c 及 Qh7s3d 的未收斂雙來源。只讀取 Jh9s4c 的 4h、Kd 原始根與舊子局，驗證 650/9750 -> 1300/9425 的籌碼路徑與每一座位的同一實體手牌交集。
- 針對 rank157 (975 cents)、rank158 (433 cents) 的新精確尺寸，掃描全部追蹤 native archives 的實際 job 或結果及命名歷史程式線索；固定原始 archive digest、兩次 byte-identical 重播。僅靜態候選，未通過 code lead 去重與後街雙策略共同可達不得派發或認證。外部過期未歸檔 artifact 不在去重保證內。
- 本批新增正式 CERT、node-lock、非極化均為 0。新 workflow 尚未驗收，不能稱 PASS。
