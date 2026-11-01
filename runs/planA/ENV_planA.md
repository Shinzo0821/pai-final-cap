# 案A の実行環境（planA）

Colab で自動生成（colab/pai_planA.ipynb の 13）。

## マシン
- checked_at_utc: 2026-11-01T01:10:14Z
- python_system: 3.13.16
- cpu_count: 12
- cpu_model: Intel(R) Xeon(R) CPU @ 2.20GHz
- ram_gb: 83.5
- disk_free_gb: 235.6
- gpu_name: NVIDIA A100-SXM4-40GB
- gpu_memory: 40960 MiB
- gpu_count: 1
- nvidia_driver: 580.82.07
- cuda_driver: 13.0
- workers: 5

## 描画
- MUJOCO_GL / PYOPENGL_PLATFORM: egl
- GL_RENDERER: NVIDIA A100-SXM4-40GB/PCIe/SSE2
- 確認の結果: `{"egl": {"ok": true, "fps": 1098.8, "mean_pixel": 125.70019639756944, "gl_renderer": "NVIDIA A100-SXM4-40GB/PCIe/SSE2", "gl_vendor": "NVIDIA Corporation", "mujoco": "3.5.0", "pyopengl": "3.1.6"}, "osmesa": {"ok": true, "fps": 71.0, "mean_pixel": 125.734013671875, "gl_renderer": "llvmpipe (LLVM 20.1.2, 256 bits)", "gl_vendor": "Mesa", "mujoco": "3.5.0", "pyopengl": "3.1.6"}}`

## LLM
- モデル: Qwen/Qwen3.5-9B（served-model-name qwen3.5-9b）
- vLLM: {"version": "0.31.0", "torch": "2.13.0+cu130", "torch_cuda": "13.0", "gpu": "NVIDIA A100-SXM4-40GB"}
- 起動コマンド: `/content/vllm-venv/bin/vllm serve Qwen/Qwen3.5-9B --served-model-name qwen3.5-9b --host 127.0.0.1 --port 8000 --dtype bfloat16 --max-model-len 65536 --gpu-memory-utilization 0.92 --max-num-seqs 8 --language-model-only --default-chat-template-kwargs {"enable_thinking": false}`
- 立ち上がりまで: 390 秒
- 試しの呼び出し: {"seconds": 5.0, "usage": {"prompt_tokens": 775, "total_tokens": 1139, "completion_tokens": 364, "prompt_tokens_details": null, "completion_tokens_details": null}, "tokens_per_s": 72.4, "think_tag": false, "force_no_think": false}
- 中継で enable_thinking=false を足したか: False
- CaP-X が送るのは model・messages・temperature・max_tokens だけ。値は CaP-X の既定（`capx/envs/launch.py`）の
  **temperature 1.0・max_tokens 20480**（本番の 289 回すべて。logs/llm_calls.jsonl で確認）。
  ノートブックが自動で書いた「temperature 0.2・max_tokens 4096」は誤りで、それはセル 6b の試しの呼び出しの値
- 全呼び出しは logs/llm_calls.jsonl（リポジトリには入れていない）

## CaP-X
- {"dir": "/content/third_party/cap-x", "commit": "53e9966", "python": "3.12.3", "install_s": 226}
- リポジトリ: {'commit': '8fce6df', 'branch': 'plana-colab', 'source': 'git archive zip'}
```
gymnasium                 1.4.0
jax                       0.4.29
jaxlib                    0.4.29
mujoco                    3.5.0
numpy                     1.26.4
open3d                    0.20.0
openai                    3.42.0
pyrender                  0.1.45
pyroki                    0.0.0
robosuite                 1.5.1       /content/third_party/cap-x/capx/third_party/robosuite
scipy                     1.14.1
```

## 実行
- oracle（3回ずつ）: {'stack': '3/3', 'nut': '3/3', 'handover': '2/3'}。handover だけ回し直すと 3/3（下の補足）
- 本番: `/usr/bin/python3 scripts/run_grid.py --tag planA --models qwen3.5-9b --conds base skill base_mt skill_mt --tasks stack nut handover --trials 10 --workers 5 --video-trials 2`
- 並列数: 5、動画は各セルの最初の 2 試行

| cond | model | task | success | trials | elapsed_s |
|---|---|---|---|---|---|
| base | qwen3.5-9b | stack | 1 | 10 | 36 |
| base | qwen3.5-9b | nut | 0 | 10 | 137 |
| base | qwen3.5-9b | handover | 0 | 10 | 1041 |
| skill | qwen3.5-9b | stack | 5 | 10 | 46 |
| skill | qwen3.5-9b | nut | 1 | 10 | 81 |
| skill | qwen3.5-9b | handover | 0 | 10 | 182 |
| base_mt | qwen3.5-9b | stack | 5 | 10 | 64 |
| base_mt | qwen3.5-9b | nut | 0 | 10 | 228 |
| base_mt | qwen3.5-9b | handover | 0 | 10 | 898 |
| skill_mt | qwen3.5-9b | stack | 6 | 10 | 120 |
| skill_mt | qwen3.5-9b | nut | 0 | 10 | 246 |
| skill_mt | qwen3.5-9b | handover | 0 | 10 | 2068 |

## 補足（手で書き足した。Colab CLI でノートブックのセルを順に実行したときの記録）

- **実行の方法**: Colab の Web UI ではなく、手元の Colab CLI（`colab exec`）でセルの中身を順に実行した。
  セル 2 の clone の代わりに `git archive`（commit 8fce6df）の zip をアップロードして展開。セル 7（Drive）は実行せず、
  途中経過は `colab download` で手元に回収した。CLI では毎回作業ディレクトリが `/content` に戻るので、各セルの先頭で
  `os.chdir(REPO_DIR)` してから実行した。
- **vLLM の上限を 65536 に**（ノートブックの既定は 32768）: CaP-X は temperature 1.0・max_tokens 20480 を送るので、
  32768 だとプロンプトが 12289 トークンを超えた呼び出しは vLLM が 400 で断り、CaP-X はその試行を記録から落とす。
  前の VM での実行（結果は VM ごと失われた）では、複数ターンの 3 セルで 7 試行がこれで落ちた。この実行の最大は 23029 トークン。
- **PATH に `/content/vllm-venv/bin` を追加**: venv を有効にせず `vllm serve` を起動すると、FlashInfer のサンプラーの
  JIT が `ninja` を見つけられず、CUDA グラフのウォームアップで落ちる（`--enforce-eager` なら起動はするが、ウォームアップを
  飛ばすだけで直らない）。PATH を足すと初回の JIT（数分）のあと 390 秒で立ち上がった。
- **止まった試行の見張り**（この実行では `logs/watchdog.py`。のちに `colab/watchdog.py` としてリポジトリに入れた）:
  CaP-X の 1000 秒の時間切れ（SIGALRM、1 回だけ）で投げられる TimeoutError が生成コード自身の `except Exception` に
  捕まると消え、生成コードが終わらないループに入ると試行が永久に終わらない（前の VM の base・handover で 1 回。
  手で SIGALRM を送り直すと、生成コードの外で TimeoutError になり、その試行は失敗として終わった）。この実行では、
  CaP-X の作業プロセスが 1200 秒続けて CPU 80% 超なら SIGALRM を送る見張りを本番の間だけ動かした。**合図は 0 回**（結果に手は入っていない）。
- **oracle**: 1 回目（`runs/planA_oracle`）は handover 2/3（trial 3 はコードが最後まで動いたが受け渡しに失敗、reward 0.026。
  直前に IK サーバーの立て直しがあった）。同じ VM で handover だけ回し直すと 3/3（`runs/planA_oracle2`）。前の VM でも 3/3。
- **thinking**: `<think>` で始まる返事は 0 回。ただし 289 回中 2 回、返事の途中に `</think>` が1つ紛れ込んだ
  （thinking のモードではなく、記号だけ。analyze の「<think> in reply 2」はこれ）。
- **試行の抜け**: なし（12 セル × 10 試行 = 120 試行、vLLM のエラー 0 回）。
