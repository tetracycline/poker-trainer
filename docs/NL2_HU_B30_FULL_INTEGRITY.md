# NL2 392 MODEL：B30 跨街導航＋具名 GTO／鎖頻／50% 下注完整回歸驗證

分類：**24 CERT-MULTIBOARD／368 APPROX／0 EST**。前 24 個高頻模型均僅在 3–5 張具名牌面取得來源認證。

河牌導航：**2475/2475（100%）**。模型行動線表格：392 張；獨立路徑覆蓋 100%；違規 0。

來源精確配對：**88/88 張具名牌面，99/99 組英雄端局部 lock**。
其中 50% 底池非極化研究候選 35 張、證據不足 53 張。
歷史來源未記錄逐節點統計：30 筆；其數值維持未知，不代入 0 或聲稱觀測。
嚴格可達 combo 少於 10 的牌面：10 張。

來源的 NL2 聚合頻率不等於逐私牌、逐牌面、逐行動歷史的實測行為。
LMP 的 50% 單尺寸限制樹與 169-class 假設起始範圍不等於完整 NL2 GTO。
本次只做完整回歸驗證，不重寫原始 GTO、CERT 規則、排序或其他 APPROX。
PR #2 必須維持 Draft／Open，絕不 merge。

來源檔 SHA-256：

- data/nl2_hu_multiboard_status.json: \`3759426648443381341f8b5aa29c15ec006b1f609115efd23b2bf8037d94ea6c\`
- data/nl2_hu_cert_lock_medium_matrix.json: \`37a9030f944c1208e653d9e9b93068e3e9bbc21853105abd173c94ac5228aaac\`
- data/nl2_hu_cert_ui_completeness_gate.json: \`9c044a4dac3f6679c92a21214554078dd28bfd98f25b7657697ed4954e31fc84\`
