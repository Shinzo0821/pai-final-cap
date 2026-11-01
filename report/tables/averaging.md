| モデル | 条件 | タスク | 平均化した試行 | 成功（平均化あり） | 成功（平均化なし） | 出どころ |
|---|---|---|---|---|---|---|
| Claude Fable 5.1 | 誤差あり・複数ターン | 積む | 0/10 | 0/0 | 7/10 | cloud_runs/cloud/noisy_mt/stack |
| Claude Fable 5.1 | 誤差あり・複数ターン | ナット | 6/10 | 0/6 | 1/4 | cloud_runs/cloud/noisy_mt/nut |
| Claude Fable 5.1 | 誤差あり・1回 | 積む | 0/10 | （対応なし） | （対応なし） | replay/claude-fable-5-1@medium/9239b5ad50ecd964 |
| Claude Fable 5.1 | 誤差あり・1回 | ナット | 3/10 | （対応なし） | （対応なし） | replay/claude-fable-5-1@medium/0a305999e24273c1 |

scripts/scan_averaging.py と同じ判定（np.mean/median/average と range(...) があり、位置を読む関数を呼ぶ）。正規表現による目安で、取りこぼしがありうる。 このリポジトリには runs/ が無いので、Fable（cloud_runs/ と replay/）だけを数えた。ほかの8モデルは runs/ のある手元で `python3 scripts/make_report.py` を流し直すと埋まる。
