# B900｜最高頻 rank29 原生負例歸檔；次高頻 rank57 現有來源診斷

B899 [原生雙 job PASS](https://github.com/tetracycline/poker-trainer/actions/runs/45901243318)，[完整稽核 PASS](https://github.com/tetracycline/poker-trainer/actions/runs/45901243266)。兩份 job log 均顯示原根完成、4 固定 turn 均未進入 GTO turn subgame，無正向翻牌。Ac3c2h 與 Ac3h2c 不再重解原根。B900 依 ZIP SHA、native file/job SHA、root pot/stack、原始固定 turn、前街雙方行動與 UI gate 重新驗證負例；待獨立完整稽核後才允許歸檔候選 expected_sha 快轉。尚不宣稱已歸檔。

並行研究下一頻率 rank57（0.767868%/手）：B840/B877 已完成四個原生翻牌、16 固定 turn；四份原始 job log 均為 0 正向。使用這四份仍可取得的原 ZIP，不重跑 root 或 subgame，分辨 GTO 顯示動作零、NL2 顯示動作零與兩策略英雄牌組交集零的障礙，避免盲目新解負例。這是來源診斷，不是新增解算或同一雙方實體手牌證據；未測 turn 或其他翻牌並未宣告耗盡。若找不到新可行機制，依 B838 下一個仍高於門檻的 rank75 前進。

本批不改 registry、UI、認證、節點鎖或 50% pot 非極化。B899 preflight 實際重算 158 CERT/234 APPROX，模型節點機會加權覆蓋率 84.700987%，30 高頻 APPROX；不是實測獨立手牌覆蓋率。B900 尚未驗收。PR #2 保持 open draft；不得 merge、force push、輪詢 Actions。
