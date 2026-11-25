# B862 — B861 checkout 環境修復

B861 run 45639569303 / job 139294125539 在第一個 checkout 步驟失敗：Node24 拒絕全 job 的 `NODE_OPTIONS: --max-old-space-size:1536`。來源稽核腳本未執行，無負例、無 native、無 artifact。相同 commit 的 full batch audit 45639569114 已成功。

移除全 job 的 NODE_OPTIONS，僅在 Python 稽核程式（其子程序為系統 node）啟用記憶體上限。保留原 B861 來源、牌面、SHA 與 gate，不重解任何 native。新 run 尚未驗收，維持 158 CERT / 234 APPROX、84.700987% 模型節點機會加權覆蓋率，新增認證、鎖頻、半池及非極化皆 0。
