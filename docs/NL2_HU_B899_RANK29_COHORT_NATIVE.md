# B899｜最高頻 rank29 新原根（僅候選）

B898 兩個 job 與 full batch audit 已 PASS：[45894207896](https://github.com/tetracycline/poker-trainer/actions/runs/45894207896)、[45894207828](https://github.com/tetracycline/poker-trainer/actions/runs/45894207828)。B898 正式永久歸檔 5 檔，head 2923d7bbb2da193f6f3b39fdd2543f48cd797a39；原始資料重算 158 CERT／234 APPROX，模型節點機會覆蓋率 84.700987%，30 高頻 APPROX。非實測獨立手牌覆蓋。

B898 靜態 cohort 498 suit classes、排除 58；12/12 靜態正向，不等同 native 可達。依凍結 cohort 原順序取首二個 Ac3c2h、Ac3h2c；rank29 1.378548%/手，維持最高優先。每個先驗證 B898 artifact SHA、兩個完成 run、固定 100bb route/SPR 及靜態合法牌組；搜尋完整父 commit 祖先的 workflow/worker 變更（包含刪除及同構牌面排列），逐頁檢查歷史 artifact 名稱；任一歷史 lead、資料不完整、PR 不符即禁止 native。既有 B898 留存資料篩選之外另查新增五份檔案。每個 root 選原靜態 witness turn 加三個凍結順序的同花 turn，兩個 job 各 29 min。不重解現存 root，不重試 Jd9d3c 負例。過期未列出/未歸檔的來源是限制。

使用已固定 LMP assumed preflop ranges、原生 GTO 與 NL2 街別邊際 partial lock、原始 job/result、50% pot 評估、無 driver 重播。B703 worker 目前僅共同 hero combo 初篩，後續必須獨立核對同一雙方實體牌組、完整 SHA/actor/pot/SPR/前街與鎖頻後才算正向候選；三個互異真翻牌才可正式 CERT。本批不改 registry、節點鎖、非極化或 UI。尚未驗收；不輪詢、不 merge、不 force push。
