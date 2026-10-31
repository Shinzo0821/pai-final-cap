# クラウドでの実行環境（Fable の複数ターン）

Fable（`claude-fable-5-1`）は手元の Mac から呼べないため、複数ターンの4セル
（base_mt の restack・handover、noisy_mt の stack・nut）をクラウドのコンテナで回した。
1回で答える条件の回答（`replay/claude-fable-5-1@medium/`）も同じコンテナで作った。

## マシン
- OS: Ubuntu 24.04.5 LTS（Linux 6.18、x86_64）
- CPU: 4 コア（Intel Xeon @ 2.80GHz）、メモリ 15 GB、GPU なし
- 描画: `MUJOCO_GL=osmesa`、`PYOPENGL_PLATFORM=osmesa`（apt の libosmesa6 25.1.7）。
  GPU が無いため EGL は初期化できなかった。

## Claude CLI
- `claude --version`: 2.1.314 (Claude Code)
- 呼び方は `proxy/cli_proxy.py` の `_call_claude` のまま（`--model claude-fable-5-1 --effort medium
  --tools "" --strict-mcp-config --setting-sources "" --no-session-persistence --system-prompt <SYSTEM_PROMPT>
  --output-format json`）。
- コンテナには `CLAUDE_EFFORT=high` という環境変数が入っていたが、これは Claude Code が
  Bash やフックに今の effort を知らせるための出力用で、CLI は読まない（effort を上書きするのは
  `CLAUDE_CODE_EFFORT_LEVEL` で、こちらは未設定）。なので `--effort medium` がそのまま効く。

## CaP-X
- github.com/capgym/cap-x の `53e9966`（`patches/CAPX_COMMIT`）を `../third_party/cap-x` にクローンし、
  `git submodule update --init`。robosuite は `9729273`。
- `patches/capx.patch` をそのまま適用。
- venv: Python 3.12.3（`/usr/bin/python3.12`）を uv で。
  `uv pip install -e capx/third_party/robosuite` → `uv pip install --no-deps -e .` → 下の依存を個別に入れた。
- site-packages に `.pth` を置き、このリポジトリのルートを通した（`pai_ext` の import 用）。

### 主なパッケージの版
| パッケージ | 版 |
|---|---|
| mujoco | 3.5.0 |
| numpy | 1.26.4 |
| scipy | 1.14.1 |
| transformers | 4.57.6 |
| robosuite | 1.5.1（サブモジュール） |
| pyroki | git `388e43e` |
| jax / jaxlib | 0.4.29 |
| open3d | 0.20.0 |
| pyrender | 0.1.45 |
| PyOpenGL | 3.1.6 |
| openai | 3.42.0 |
| gymnasium | 1.4.0 |
| cloudpickle | 3.1.2 |
| opencv-python-headless | 4.12.0.88 |
| viser | 1.1.1 |
| yourdfpy | 0.0.60 |
| trimesh | 5.2.0 |
| robot-descriptions | 3.3.0 |

入れたもの（pyproject の依存のうち）: gymnasium, tyro, pydantic, rich, matplotlib, imageio[ffmpeg],
requests, tqdm, h5py, einops, pyyaml, omegaconf, pyroki, robot_descriptions, yourdfpy, viser, trimesh,
msgpack_numpy, mediapy, uvicorn, fastapi, openai, pyrender, opencv-python-headless, pillow, cloudpickle,
open3d。torch・torchvision・sam3・decord・ray は入れていない（特権情報ありのタスクでは import されなかった）。

中継サーバー（`proxy/cli_proxy.py`）は別の Python 3.12 venv（fastapi 0.162.0、uvicorn 0.54.0、pydantic 2.14.2）で起動。

## 手元の手順から変えた点
- `MUJOCO_GL` を `cgl` から `osmesa` に（`PYOPENGL_PLATFORM=osmesa` も設定）。
- `run_grid.py` の `CAPX_DIR`・`CAPX_PYTHON` を環境変数で Linux の場所に向けた。
  コードの変更はなし（`lsof` がコンテナにあったので、IK サーバーの再起動もそのまま動いた）。
- apt で libosmesa6・libegl1・libgl1 などを追加。

## 確認と結果
（本番は実行中。終わったら追記する）
