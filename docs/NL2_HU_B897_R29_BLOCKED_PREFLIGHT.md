# B897｜B896 已驗收；最高頻 rank29 未執行原根的工程修復

- PR #2 open draft；基線 058555083b0473acfbfca621fc28968375bae6fd。不 merge、不 force push。
- B896 authenticated boundary [45879893776](https://github.com/tetracycline/poker-trainer/actions/runs/45879893776) 與完整稽核 [45879893560](https://github.com/tetracycline/poker-trainer/actions/runs/45879893560) 均 success。兩次重播各四個相同結果：rank157/158 的 Jh9s4c 4h（541 共同前街實體組合）與 Kd（505），皆 NO_STATIC_CHECK_WITNESS、0 候選河牌、0 exact raw hits。不是已求解的 turn/river 零可達結果；不再派發這四個邊界。Artifact 15145804448 SHA256 707a79f3c6e9181cbaa0dbdb9b4b45852b41a80c15e6a1642a894fc15c369c49；原始 bytes 仍在 Actions，尚未永久入庫。
- 回到 B838 頻率第一 rank29（1.378548%／手）：B882 Jd9d3c job 139691797892 確認只在人工選取的靜態 witness 失敗，native step skipped。原定四個 turn 2d/4d/5d/7d 不變。用原假設範圍、現行 UI 與實體牌組做 deterministic static enumeration；沒有使用任何 native outcome 選 witness。若找不到 witness、來源去重有疑慮、或價格/範圍檢查未過，禁止 native dispatch。B882 的 KcTc6h、Qh8h4s 已成功且歸檔，完全不重跑。
- 新 workflow 僅單一未執行原根，29 分鐘上限、完整 batch audit 仍適用。不把靜態合法性、成功啟動或單側可達當 CERT。即使成功仍需要獨立同一雙方實體牌組 GTO+NL2、來源/收斂/SPR/50% 評估等完整證據。
- B896 直接重算基線：158 CERT / 234 APPROX、84.700987% 模型節點機會加權覆蓋率（非獨立手牌覆蓋），30 高頻 APPROX；當前 registry blob 59d02d3c7b5ed05515ec94bc1753300264598346 未變。本批新增正式認證、節點鎖、非極化皆 0。B897 尚未驗收。
