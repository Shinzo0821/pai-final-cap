#!/usr/bin/env bash
# CaP-X を入れる（Linux、cloud_runs/ENV.md と同じ手順）。Colab とクラウドのコンテナの両方で使う。
#   使い方: bash colab/setup_capx.sh            （リポジトリのルートで）
#   置き場所: CAPX_DIR（既定は <リポジトリ>/../third_party/cap-x）、venv は $CAPX_DIR/.venv
# 何度実行してもよい（済んだ手順は飛ばす）。
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CAPX_DIR="${CAPX_DIR:-$REPO/../third_party/cap-x}"
COMMIT="$(cat "$REPO/patches/CAPX_COMMIT")"
PYVER="${CAPX_PYVER:-3.12}"   # CaP-X は Python 3.10〜3.12 のみ（pyproject の requires-python）

echo "== apt（描画用のライブラリ）"
if ldconfig -p 2>/dev/null | grep -q libOSMesa && ldconfig -p | grep -q libEGL.so.1 \
   && command -v lsof >/dev/null && command -v ffmpeg >/dev/null; then
  echo "  入っている（飛ばす）"
elif command -v apt-get >/dev/null && [ "$(id -u)" = 0 ]; then
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -qq || true
  apt-get install -y -qq libosmesa6 libegl1 libgl1 libglib2.0-0 lsof ffmpeg git >/dev/null || \
    echo "  (apt の一部が失敗。既に入っていれば問題ない)"
fi

echo "== uv"
if ! command -v uv >/dev/null; then
  python3 -m pip install -q uv
fi

echo "== CaP-X のソース ($CAPX_DIR @ ${COMMIT:0:7})"
if [ ! -d "$CAPX_DIR/.git" ]; then
  mkdir -p "$(dirname "$CAPX_DIR")"
  git clone -q https://github.com/capgym/cap-x "$CAPX_DIR"
fi
cd "$CAPX_DIR"
if [ "$(git rev-parse HEAD)" != "$COMMIT" ]; then
  git checkout -q "$COMMIT"
fi
git submodule update --init -q
# パッチ: 当たっていなければ当てる（当たっていれば reverse の確認が通る）
if git apply --reverse --check "$REPO/patches/capx.patch" 2>/dev/null; then
  echo "  patch: 適用済み"
elif git apply --check "$REPO/patches/capx.patch" 2>/dev/null; then
  git apply "$REPO/patches/capx.patch"
  echo "  patch: 適用した"
else
  echo "  patch が当たらない（古いパッチが当たったまま？）。$CAPX_DIR で git checkout -- . をしてからやり直す" >&2
  exit 1
fi

echo "== venv（Python $PYVER）"
if [ ! -x .venv/bin/python ]; then
  uv venv -q --python "$PYVER" .venv
fi
export VIRTUAL_ENV="$CAPX_DIR/.venv"
UVP="uv pip install -q --python .venv/bin/python"

if ! .venv/bin/python -c "import capx, robosuite, pyroki" 2>/dev/null; then
  # 版は cloud_runs/ENV.md の表に合わせる（numpy 1.26 系、mujoco 3.5.0、scipy<1.15）
  $UVP "numpy==1.26.4" "scipy==1.14.1" "mujoco==3.5.0"
  $UVP -e capx/third_party/robosuite "numpy==1.26.4" "scipy==1.14.1" "mujoco==3.5.0"
  $UVP --no-deps -e .
  $UVP "numpy==1.26.4" "scipy==1.14.1" "mujoco==3.5.0" \
    "gymnasium==1.4.0" tyro pydantic rich matplotlib "imageio[ffmpeg]" requests tqdm h5py einops \
    pyyaml omegaconf "pyroki @ git+https://github.com/chungmin99/pyroki.git@388e43e" \
    "jax==0.4.29" "jaxlib==0.4.29" "robot_descriptions==3.3.0" "yourdfpy==0.0.60" "viser==1.1.1" \
    "trimesh==5.2.0" msgpack_numpy mediapy uvicorn fastapi openai "pyrender==0.1.45" "PyOpenGL==3.1.6" \
    "opencv-python-headless==4.12.0.88" pillow "cloudpickle==3.1.2" "open3d==0.20.0" "transformers==4.57.6"
fi

# pai_ext を import できるように、このリポジトリのルートを通す
SITE="$(.venv/bin/python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')"
echo "$REPO" > "$SITE/pai_final_repo.pth"

echo "== 確認"
.venv/bin/python - <<'PY'
import importlib, sys
for m in ["numpy", "scipy", "mujoco", "robosuite", "pyroki", "jax", "capx"]:
    try:
        mod = importlib.import_module(m)
        print(f"  {m:10s} {getattr(mod, '__version__', 'ok')}")
    except Exception as e:  # noqa: BLE001
        print(f"  {m:10s} 失敗: {e!r}")
        sys.exit(1)
import capx.integrations  # 最後に pai_ext が読まれる
from capx.integrations.base_api import get_api
get_api("FrankaControlPrivilegedApi_Noisy")
print("  pai_ext    ok（*_Noisy が登録済み）")
print("  python", sys.version.split()[0])
PY
echo "CAPX_DIR=$CAPX_DIR"
echo "CAPX_PYTHON=$CAPX_DIR/.venv/bin/python"
