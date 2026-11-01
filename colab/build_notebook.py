"""colab/pai_planA.ipynb を作る（ノートブックはこのスクリプトから生成する。直すときはここを直して再生成）。

  python3 colab/build_notebook.py

セルは素の Python で書く（! や % の魔法は使わない）。Colab 以外（GPU なしのコンテナ）でも、
環境変数 PLANA_DRY_RUN=1 を付けると vLLM の代わりにダミーのモデルで最後まで動かせる（試運転用）。
"""

from __future__ import annotations

import json
from pathlib import Path

CELLS: list[tuple[str, str]] = []


def md(text: str) -> None:
    CELLS.append(("markdown", text.strip("\n")))


def code(text: str) -> None:
    CELLS.append(("code", text.strip("\n")))


def code_in_repo(text: str) -> None:
    """リポジトリの中で動かすセル。@title の次の行で REPO_DIR に移る
    （Colab CLI の `colab exec` は実行のたびに作業ディレクトリを /content に戻すため）。"""
    title, _, body = text.strip("\n").partition("\n")
    code(f"{title}\nos.chdir(REPO_DIR)\n{body}")


md("""
# 案A: Qwen3.5-9B を Colab の GPU で CaP-X にかける

小さいオープンモデル `Qwen/Qwen3.5-9B` を vLLM で立て、同じランタイムの中で CaP-X（特権情報あり）を回す。
- タスク: stack・nut・handover
- 条件: base／skill（他タスクの成功コードの見本つき）／base_mt（複数ターン）／skill_mt（両方）
- 各10回、合計120試行

**押す順番**: 上から順に1つずつ実行する。詳しくは `colab/README.md`。
- ランタイムは「ランタイムのタイプを変更」で **A100**（実際に回したのは A100。L4 は文脈の長さが足りない恐れがある。README）。
- 途中でランタイムが切れたら、もう一度上から実行する。Google Drive に逃がした途中経過を戻し、終わったセルは飛ばして続きから回る。
""")

code(r'''
# @title 0. 設定とヘルパー（ふつうは変えなくてよい）
import ast, json, os, re, shutil, signal, subprocess, sys, time
from pathlib import Path

IN_COLAB = "google.colab" in sys.modules
# 試運転用（Colab では使わない）: PLANA_DRY_RUN=1 なら vLLM の代わりにダミーのモデル（proxy/dummy_llm.py）を使う
DRY_RUN = os.environ.get("PLANA_DRY_RUN") == "1"

GITHUB_REPO = ""          # @param {type:"string"}
# ↑ "<アカウント名>/pai-final-cap"。Colab のシークレット GITHUB_REPO があればそちらを使う（ここは空のままでよい）
BRANCH = "main"    # @param {type:"string"}
VIDEO_TRIALS = 2          # @param {type:"integer"}
# ↑ 動画を残すのは各セルの最初の N 試行だけ（CPU 描画だと動画の分だけ遅くなるため）
GL_BACKEND = "auto"       # @param ["auto", "egl", "osmesa"]
VLLM_VERSION = "auto"     # @param ["auto", "0.31.0", "0.19.1"]
# ↑ auto: ドライバーが CUDA 13 以上なら 0.31.0（PyPI の既定、CUDA 13 版）、それ未満なら 0.19.1（CUDA 12.8 版）
MAX_MODEL_LEN = 65536     # @param {type:"integer"}
# ↑ 立ち上がらなければ自動で 32768 に下げて試す（下げると長い複数ターンの試行が落ちる。セル6の説明）

# CaP-X が LLM に送る値（CaP-X の既定、capx/envs/launch.py。run_grid.py は変えない）
CAPX_TEMPERATURE = 1.0
CAPX_MAX_TOKENS = 20480
# プロンプト（入力）＋ CAPX_MAX_TOKENS が max-model-len を超えると vLLM は 400 を返し、CaP-X はその試行を記録から落とす。
# 案A の本番（A100、65536）でのプロンプトの最大は 23029 トークン。これを下回る上限では試行が抜ける恐れがある
SAFE_MODEL_LEN = CAPX_MAX_TOKENS + 24000

MODEL_ID = "Qwen/Qwen3.5-9B"
SERVED_NAME = "dummy" if DRY_RUN else "qwen3.5-9b"   # CaP-X の --model = vLLM の served-model-name
TAG = os.environ.get("PLANA_TAG", "planA")
TASKS = ["stack", "nut", "handover"]
CONDS = ["base", "skill", "base_mt", "skill_mt"]       # 1回で答える2条件を先に回す
TRIALS = int(os.environ.get("PLANA_TRIALS", "10"))
GPU_MEM_UTIL = 0.92
SYNC_SEC = 300                                          # Drive に逃がす間隔（秒）

WORK = Path("/content") if IN_COLAB else Path(os.environ.get("PLANA_WORK", os.getcwd()))
REPO_DIR = Path(os.environ.get("PLANA_REPO_DIR", str(WORK / "pai-final-cap")))
CAPX_DIR = Path(os.environ.get("PLANA_CAPX_DIR", str(WORK / "third_party" / "cap-x")))
CAPX_PY = CAPX_DIR / ".venv" / "bin" / "python"
VLLM_VENV = WORK / "vllm-venv"
DRIVE_DIR = Path("/content/drive/MyDrive/pai_planA") if IN_COLAB else WORK / "fake_drive" / "pai_planA"
ENV_JSON = WORK / "planA_env.json"      # 環境メモの材料（セルごとに書き足す）
LLM_URL = "http://127.0.0.1:8120/chat/completions"   # CaP-X が呼ぶ口（proxy/log_proxy.py → vLLM :8000）
SKILL_MARK = "Reference examples (skill library):"


def run(cmd, check=True, env=None, cwd=None):
    """コマンドを実行し、出力をそのまま表示する。"""
    shown = cmd if isinstance(cmd, str) else " ".join(map(str, cmd))
    print("$", shown[:300], flush=True)
    p = subprocess.Popen(cmd if isinstance(cmd, str) else list(map(str, cmd)), shell=isinstance(cmd, str),
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env, cwd=cwd, bufsize=1)
    for line in p.stdout:
        print(line, end="", flush=True)
    rc = p.wait()
    if check and rc != 0:
        raise RuntimeError(f"exit code {rc}: {shown[:200]}")
    return rc


def load_env() -> dict:
    return json.loads(ENV_JSON.read_text()) if ENV_JSON.exists() else {}


def save_env(**kw) -> None:
    d = load_env()
    d.update(kw)
    ENV_JSON.parent.mkdir(parents=True, exist_ok=True)
    ENV_JSON.write_text(json.dumps(d, indent=2, ensure_ascii=False))


def capx_env() -> dict:
    """CaP-X を動かすときの環境変数（カーネルを再起動しても ENV_JSON から戻せるように）。"""
    gl = load_env().get("gl", {}).get("backend") or os.environ.get("MUJOCO_GL") or "osmesa"
    return dict(os.environ, CAPX_DIR=str(CAPX_DIR), CAPX_PYTHON=str(CAPX_PY), MUJOCO_GL=gl, PYOPENGL_PLATFORM=gl)


def http_ok(url: str, timeout: float = 5) -> bool:
    import urllib.request
    try:
        return urllib.request.urlopen(url, timeout=timeout).status == 200
    except Exception:
        return False


def pid_alive(pid_file: Path) -> bool:
    """pid ファイルのプロセスが動いているか。終わったのに回収されていない子（ゾンビ）は止まったとみなす。"""
    try:
        pid = int(pid_file.read_text())
        os.kill(pid, 0)
    except (FileNotFoundError, ValueError, ProcessLookupError, PermissionError):
        return False
    try:
        state = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[0]
    except (FileNotFoundError, IndexError):
        return True
    if state == "Z":
        try:
            os.waitpid(pid, os.WNOHANG)   # このカーネルの子なら回収する
        except ChildProcessError:
            pass
        return False
    return True


def kill_port(port: int) -> None:
    out = subprocess.run(["lsof", "-t", f"-i:{port}", "-sTCP:LISTEN"], capture_output=True, text=True).stdout.split()
    for pid in out:
        try:
            os.killpg(os.getpgid(int(pid)), signal.SIGTERM)
        except Exception:
            subprocess.run(["kill", "-9", pid])


def tail(path: Path, n: int = 15) -> str:
    return "\n".join(path.read_text(errors="replace").splitlines()[-n:]) if path.exists() else "(no file)"


WORK.mkdir(parents=True, exist_ok=True)
print(f"IN_COLAB={IN_COLAB} DRY_RUN={DRY_RUN} WORK={WORK}\nREPO_DIR={REPO_DIR}\nCAPX_DIR={CAPX_DIR}\nTAG={TAG} TRIALS={TRIALS}")
''')

md("## 1. マシンを確かめる（GPU・メモリ・CPU）")

code(r'''
# @title 1. GPU の種類・メモリ・CPU コア数
info = {"checked_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "python_system": sys.version.split()[0], "cpu_count": os.cpu_count()}
try:
    info["cpu_model"] = next(l.split(":", 1)[1].strip() for l in open("/proc/cpuinfo") if l.startswith("model name"))
    info["ram_gb"] = round(int(next(l.split()[1] for l in open("/proc/meminfo") if l.startswith("MemTotal"))) / 1024**2, 1)
except Exception:
    pass
info["disk_free_gb"] = round(shutil.disk_usage(WORK).free / 1024**3, 1)
if shutil.which("nvidia-smi"):
    q = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
                       capture_output=True, text=True).stdout.strip().splitlines()
    name, mem, drv = [x.strip() for x in q[0].split(",")]
    cuda = re.search(r"CUDA Version:\s*([\d.]+)", subprocess.run(["nvidia-smi"], capture_output=True, text=True).stdout)
    info.update(gpu_name=name, gpu_memory=mem, gpu_count=len(q), nvidia_driver=drv,
                cuda_driver=cuda.group(1) if cuda else None)
else:
    info.update(gpu_name=None)
    print("GPU が見つからない。" + ("「ランタイム」→「ランタイムのタイプを変更」で A100 を選ぶ。" if IN_COLAB else "（試運転なので問題ない）"))
# CaP-X の並列数: IK サーバーと vLLM と描画に CPU を残し、最大 5（10試行を2巡）
WORKERS = max(1, min(5, (os.cpu_count() or 2) - 2))
info["workers"] = WORKERS
save_env(machine=info)
for k, v in info.items():
    print(f"{k:16s} {v}")
if info.get("gpu_memory") and int(re.sub(r"\D", "", info["gpu_memory"]) or 0) < 22000 and not DRY_RUN:
    print("\n注意: GPU のメモリが 22GB 未満。Qwen3.5-9B（bf16 で約19GB）は載らない。L4・G4・A100 に替える。")
''')

md("""
## 2. リポジトリを取ってくる
非公開リポジトリなので、次のどちらか。
- **おすすめ**: Colab の左の鍵マーク（シークレット）に `GITHUB_TOKEN`（読み取りだけの Fine-grained トークン）と
  `GITHUB_REPO`（`<アカウント名>/pai-final-cap`）を登録し、「ノートブックからのアクセス」をオンにする。
- 無ければ、GitHub の「Code → Download ZIP」（ブランチ `main`）で落とした zip をアップロードする。

トークンは表示も保存もしない（git の設定ファイルにも残らない）。
""")

code(r'''
# @title 2. リポジトリの取得（トークン → 無ければ zip のアップロード）
import base64, zipfile

def _secret(name):
    if not IN_COLAB:
        return os.environ.get(name) or None
    from google.colab import userdata
    try:
        return userdata.get(name) or None
    except Exception:   # 未登録・アクセス未許可
        return None

if (REPO_DIR / "scripts" / "run_grid.py").exists():
    print("取得済み:", REPO_DIR)
else:
    token, repo = _secret("GITHUB_TOKEN"), (_secret("GITHUB_REPO") or GITHUB_REPO.strip())
    if token and repo:
        print(f"トークンで clone します（ブランチ {BRANCH}）")
        hdr = "Authorization: Basic " + base64.b64encode(f"x-access-token:{token}".encode()).decode()
        # 認証のヘッダーは環境変数で一時的に渡す（URL・引数・.git/config に残さない）
        env = dict(os.environ, GIT_CONFIG_COUNT="1", GIT_CONFIG_KEY_0="http.https://github.com/.extraheader",
                   GIT_CONFIG_VALUE_0=hdr, GIT_TERMINAL_PROMPT="0")
        r = subprocess.run(["git", "clone", "-q", "--branch", BRANCH, f"https://github.com/{repo}.git", str(REPO_DIR)],
                           env=env, capture_output=True, text=True)
        msg = (r.stdout + r.stderr).replace(token, "***")
        del token, hdr, env
        if r.returncode != 0:
            raise RuntimeError("clone に失敗:\n" + msg + "\nトークンの権限（Contents: Read）と GITHUB_REPO を確かめる")
    else:
        if not IN_COLAB:
            raise RuntimeError(f"{REPO_DIR} が無い（試運転では PLANA_REPO_DIR でリポジトリを指す）")
        from google.colab import files
        print("シークレットが無いので zip をアップロードしてください（GitHub の Download ZIP）")
        up = files.upload()
        zpath = WORK / next(iter(up))
        tmp = WORK / "_upload"
        shutil.rmtree(tmp, ignore_errors=True)
        zipfile.ZipFile(zpath).extractall(tmp)
        root = next(p.parent.parent for p in tmp.rglob("scripts/run_grid.py"))
        shutil.move(str(root), str(REPO_DIR))
        shutil.rmtree(tmp, ignore_errors=True)
os.chdir(REPO_DIR)
(REPO_DIR / "logs").mkdir(exist_ok=True)
commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip() or "zip"
save_env(repo={"commit": commit, "branch": BRANCH})
print("commit:", commit)
''')

md("""
## 3. CaP-X を入れる
`colab/setup_capx.sh`（`cloud_runs/ENV.md` と同じ手順）。CaP-X は Python 3.10〜3.12 しか対応しないので、
Colab の Python とは別に uv で Python 3.12 の venv を作る（`third_party/cap-x/.venv`）。初回は数分かかる。
""")

code_in_repo(r'''
# @title 3. CaP-X の導入（apt の描画ライブラリ・CaP-X・パッチ・venv）
t0 = time.time()
run(["bash", str(REPO_DIR / "colab" / "setup_capx.sh")], env=dict(os.environ, CAPX_DIR=str(CAPX_DIR)))
capx_commit = subprocess.run(["git", "-C", str(CAPX_DIR), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
capx_pyver = subprocess.run([str(CAPX_PY), "-c", "import sys; print(sys.version.split()[0])"], capture_output=True, text=True).stdout.strip()
save_env(capx={"dir": str(CAPX_DIR), "commit": capx_commit, "python": capx_pyver, "install_s": round(time.time() - t0)})
print(f"CaP-X {capx_commit}, Python {capx_pyver}, {time.time() - t0:.0f} 秒")
''')

md("""
## 4. 描画の方式を決める（EGL → だめなら OSMesa）
受け渡し（handover）の遅さは CPU 描画が原因だったので、まず GPU の EGL を試す。
`GL_RENDERER` に NVIDIA と出れば GPU で描いている。llvmpipe ならソフトウェア描画（OSMesa と同じ速さ）。
設定の `GL_BACKEND` で固定もできる。
""")

code_in_repo(r'''
# @title 4. 描画の確認（結果は環境メモに残す）
if IN_COLAB and shutil.which("nvidia-smi"):
    # Colab では NVIDIA の EGL が登録されていないことがあるので、MuJoCo の公式 Colab と同じく登録する
    icd = Path("/usr/share/glvnd/egl_vendor.d/10_nvidia.json")
    if not icd.exists():
        icd.parent.mkdir(parents=True, exist_ok=True)
        icd.write_text('{"file_format_version" : "1.0.0", "ICD" : {"library_path" : "libEGL_nvidia.so.0"}}\n')
        print("NVIDIA の EGL を登録した:", icd)
check = {}
if GL_BACKEND == "auto":
    r = subprocess.run([str(CAPX_PY), "colab/check_gl.py", "--out", "logs/gl_check.json"], capture_output=True, text=True)
    print(r.stdout[-3000:], r.stderr[-1500:])
    m = re.search(r"CHOSEN=(\w+)", r.stdout)
    gl = m.group(1) if m else "osmesa"
    check = json.loads(Path("logs/gl_check.json").read_text()) if Path("logs/gl_check.json").exists() else {}
else:
    gl = GL_BACKEND
os.environ["MUJOCO_GL"] = os.environ["PYOPENGL_PLATFORM"] = gl
renderer = check.get("results", {}).get(gl, {}).get("gl_renderer", "?")
save_env(gl={"backend": gl, "renderer": renderer, "check": check})
print(f"\n使う描画: MUJOCO_GL={gl}（GL_RENDERER: {renderer}）")
''')

md("""
## 5. vLLM を入れる
別の venv（`/content/vllm-venv`）に入れる（Colab の torch などを壊さないため）。
- vLLM 0.31.0（PyPI の既定は CUDA 13 版の torch 2.13）: ドライバーが CUDA 13 以上のとき。
- vLLM 0.19.1（torch 2.10、CUDA 12.8）: それより古いドライバーのとき。
どちらも `Qwen3_5ForConditionalGeneration`・`--language-model-only`・`--default-chat-template-kwargs` があることを
ソースと引数の解釈で確かめてある（`colab/README.md`）。
""")

code_in_repo(r'''
# @title 5. vLLM の導入
def _vllm_check():
    r = subprocess.run([str(VLLM_VENV / "bin" / "python"), "-c",
                        "import vllm, torch; print(vllm.__version__, torch.__version__, torch.version.cuda, "
                        "torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else '-')"],
                       capture_output=True, text=True)
    return r.stdout.strip().split(" ", 4) if r.returncode == 0 else None

if DRY_RUN:
    print("試運転なので vLLM は入れない（ダミーのモデルを使う）")
else:
    cuda = float(load_env().get("machine", {}).get("cuda_driver") or 0)
    want = VLLM_VERSION if VLLM_VERSION != "auto" else ("0.31.0" if cuda >= 13.0 else "0.19.1")
    for ver in [want] + (["0.19.1"] if want == "0.31.0" and VLLM_VERSION == "auto" else []):
        st = _vllm_check() if (VLLM_VENV / "bin" / "python").exists() else None
        if not st or st[0] != ver:
            t0 = time.time()
            shutil.rmtree(VLLM_VENV, ignore_errors=True)
            run(["uv", "venv", "-q", "--python", "3.12", str(VLLM_VENV)])
            run(["uv", "pip", "install", "-q", "--python", str(VLLM_VENV / "bin" / "python"), f"vllm=={ver}"])
            print(f"入れた: vllm=={ver}（{time.time() - t0:.0f} 秒）")
        st = _vllm_check()
        print("vllm / torch / CUDA / GPU が使えるか / GPU:", st)
        if st and st[3] == "True":
            save_env(vllm={"version": st[0], "torch": st[1], "torch_cuda": st[2], "gpu": st[4]})
            break
        print(f"vllm=={ver} では GPU が使えない（ドライバーが古い？）。次の版を試す")
    else:
        raise RuntimeError("vLLM から GPU が使えない。GPU のランタイムか、VLLM_VERSION を確かめる")
''')

md("""
## 6. vLLM で Qwen3.5-9B を立てる
- thinking を切る: CaP-X は `chat_template_kwargs` を送らないので、vLLM 側の既定を
  `--default-chat-template-kwargs '{"enable_thinking": false}'` にする。
- `--language-model-only`: 画像の部分（ビジョンエンコーダ）を読み込まず、文字だけで使う（メモリの節約）。
- `--max-model-len`: 既定 65536。CaP-X は毎回 `max_tokens` 20480 を送るので、プロンプト＋20480 が上限を超えると
  vLLM が 400 を返し、CaP-X はその試行を記録から落とす（複数ターンではプロンプトが 2 万トークンを超える）。
  立ち上がらなければ `--enforce-eager`、次に 32768 を自動で試す（32768 で立ち上がったら警告を出す）。
  20480 より小さい上限では全部の呼び出しが断られるので、それより下げない。
- vLLM の venv の `bin` を PATH に足して起動する。FlashInfer のサンプラーが初回に JIT でコンパイルするとき `ninja` を探すため
  （無いと CUDA グラフのウォームアップで落ちる）。初回の JIT で数分余計にかかる。
- 前に立てた CaP-X との間に記録用の中継（`proxy/log_proxy.py`、ポート 8120）を置き、全呼び出しを `logs/llm_calls.jsonl` に残す。
初回はモデルのダウンロード（約19GB）があるので 5〜15 分（A100 では 6.5 分）。
""")

code_in_repo(r'''
# @title 6. vLLM と記録用の中継を起動
VLLM_LOG = REPO_DIR / "logs" / "vllm.log"
FORCE_NO_THINK = load_env().get("force_no_think", False)

def start_proxy():
    kill_port(8120)
    cmd = [sys.executable, "proxy/log_proxy.py", "--port", "8120",
           "--upstream", "http://127.0.0.1:8000/v1/chat/completions", "--log", "logs/llm_calls.jsonl"]
    if FORCE_NO_THINK:
        cmd.append("--force-no-think")
    subprocess.Popen(cmd, stdout=open("logs/log_proxy.log", "a"), stderr=subprocess.STDOUT, start_new_session=True)
    for _ in range(20):
        if http_ok("http://127.0.0.1:8120/health"):
            return
        time.sleep(0.5)
    raise RuntimeError("log proxy did not start")

def vllm_cmd(max_len, eager):
    cmd = [str(VLLM_VENV / "bin" / "vllm"), "serve", MODEL_ID, "--served-model-name", SERVED_NAME,
           "--host", "127.0.0.1", "--port", "8000", "--dtype", "bfloat16",
           "--max-model-len", str(max_len), "--gpu-memory-utilization", str(GPU_MEM_UTIL), "--max-num-seqs", "8",
           "--language-model-only", "--default-chat-template-kwargs", '{"enable_thinking": false}']
    return cmd + (["--enforce-eager"] if eager else [])

if http_ok("http://127.0.0.1:8000/v1/models"):
    print("モデルのサーバーはもう動いている")
elif DRY_RUN:
    subprocess.Popen([sys.executable, "proxy/dummy_llm.py", "--port", "8000", "--model", SERVED_NAME],
                     stdout=open("logs/dummy_llm.log", "a"), stderr=subprocess.STDOUT, start_new_session=True)
    for _ in range(20):
        if http_ok("http://127.0.0.1:8000/v1/models"):
            break
        time.sleep(0.5)
    save_env(vllm_server={"cmd": "proxy/dummy_llm.py (dry run)"})
else:
    env = dict(os.environ)
    # FlashInfer の JIT が ninja（vLLM の venv に入っている）を PATH から探すので、venv を有効にしたのと同じにする
    env["PATH"] = f"{VLLM_VENV / 'bin'}:{env.get('PATH', '')}"
    hf = _secret("HF_TOKEN")   # 無くてよい（Qwen3.5-9B は公開モデル）。あればダウンロードの制限が緩む
    if hf:
        env["HF_TOKEN"] = hf
    tries = []
    for t in [(MAX_MODEL_LEN, False), (MAX_MODEL_LEN, True), (32768, False), (32768, True)]:
        if t not in tries:
            tries.append(t)
    started = None
    for max_len, eager in tries:
        cmd = vllm_cmd(max_len, eager)
        print("起動:", " ".join(cmd))
        with open(VLLM_LOG, "a") as lf:
            lf.write(f"\n===== {time.ctime()} {' '.join(cmd)}\n")
        t0 = time.time()
        proc = subprocess.Popen(cmd, stdout=open(VLLM_LOG, "a"), stderr=subprocess.STDOUT, env=env, start_new_session=True)
        while time.time() - t0 < 1800:
            if http_ok("http://127.0.0.1:8000/v1/models"):
                started = (max_len, eager, round(time.time() - t0))
                break
            if proc.poll() is not None:
                break
            time.sleep(15)
            print(f"  {time.time() - t0:5.0f}s  {tail(VLLM_LOG, 1)[:160]}", flush=True)
        if started:
            break
        print("立ち上がらなかった。ログの最後:\n" + tail(VLLM_LOG, 25))
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except Exception:
            pass
        time.sleep(10)
    del hf, env
    if not started:
        raise RuntimeError("vLLM が立ち上がらない。メモリ不足なら G4 か A100 に替える（README）")
    max_len, eager, secs = started
    save_env(vllm_server={"cmd": " ".join(vllm_cmd(max_len, eager)), "max_model_len": max_len,
                          "enforce_eager": eager, "startup_s": secs, "path_has_venv_bin": True})
    print(f"\n立ち上がった（max-model-len {max_len}、enforce-eager {eager}、{secs} 秒）")
    if max_len < SAFE_MODEL_LEN:
        print(f"\n警告: max-model-len {max_len} は {SAFE_MODEL_LEN} 未満。CaP-X は max_tokens {CAPX_MAX_TOKENS} を送るので、"
              f"プロンプトが {max_len - CAPX_MAX_TOKENS} トークンを超えた呼び出しは 400 で断られ、その試行が記録から落ちる。"
              "複数ターンの条件で起きやすい。メモリの大きい GPU（A100・G4）に替えることをすすめる")
start_proxy()
print("記録用の中継: http://127.0.0.1:8120 → :8000（logs/llm_calls.jsonl）")
''')

code_in_repo(r'''
# @title 6b. 1回試す（短い返事と、CaP-X と同じ stack のプロンプト）
import urllib.request

def chat(messages, max_tokens=CAPX_MAX_TOKENS):
    # 温度と上限は CaP-X が本番で送る値と同じにする（上限の不足もここで分かる）
    body = json.dumps({"model": SERVED_NAME, "messages": messages, "temperature": CAPX_TEMPERATURE,
                       "max_tokens": max_tokens}).encode()
    t0 = time.time()
    r = urllib.request.urlopen(urllib.request.Request(LLM_URL, data=body, headers={"Content-Type": "application/json"}), timeout=900)
    resp = json.loads(r.read())
    return resp["choices"][0]["message"].get("content") or "", resp.get("usage") or {}, time.time() - t0

def has_think(text):
    return "<think>" in text or "</think>" in text

c1, u1, s1 = chat([{"role": "user", "content": "Reply with exactly: OK"}], 16)
print(f"短い返事: {c1!r}（{s1:.1f} 秒）")
msgs = ast.literal_eval((REPO_DIR / "skill_src" / "prompts" / "base_stack.txt").read_text())
c2, u2, s2 = chat(msgs)
print(f"\nstack のプロンプト: {s2:.1f} 秒、usage {u2}")
print("\n".join(c2.splitlines()[:40]))
if (has_think(c1) or has_think(c2)) and not FORCE_NO_THINK:
    print("\n<think> が出た。vLLM の既定で切れていないので、中継で enable_thinking=false を足す設定に切り替える")
    FORCE_NO_THINK = True
    save_env(force_no_think=True)
    start_proxy()
    c2, u2, s2 = chat(msgs)
    print("切り替え後の <think>:", has_think(c2))
tok_s = (u2.get("completion_tokens") or 0) / s2 if s2 else 0
save_env(test_call={"seconds": round(s2, 1), "usage": u2, "tokens_per_s": round(tok_s, 1),
                    "temperature": CAPX_TEMPERATURE, "max_tokens": CAPX_MAX_TOKENS,
                    "think_tag": has_think(c2), "force_no_think": FORCE_NO_THINK})
print(f"\n出力の速さ: 約 {tok_s:.1f} トークン/秒、<think>: {has_think(c2)}")
''')

md("""
## 7. Google Drive に途中経過を逃がす
Drive をマウントし、`runs/`・`logs/`・`results/` を5分ごとに `マイドライブ/pai_planA/` へ写す（裏で動き続ける）。
ランタイムが切れて最初からやり直すときは、このセルが Drive の途中経過を手元に戻すので、続きから回る。
""")

code_in_repo(r'''
# @title 7. Drive のマウント・途中経過の復元・定期コピーの開始
if IN_COLAB:
    from google.colab import drive
    drive.mount("/content/drive")
DRIVE_DIR.mkdir(parents=True, exist_ok=True)
# 復元: Drive にあって手元に無いものを戻す（DONE のあるセルは run_grid が飛ばす）
for sub in ["runs", "logs", "results"]:
    src = DRIVE_DIR / sub
    if not src.exists():
        continue
    for item in src.iterdir():
        dst = REPO_DIR / sub / item.name
        if not dst.exists():
            (shutil.copytree if item.is_dir() else shutil.copy2)(item, dst)
            print("復元:", dst.relative_to(REPO_DIR))
SYNC_PID = WORK / "drive_sync.pid"
if pid_alive(SYNC_PID):
    print("定期コピーはもう動いている")
else:
    script = f"""
while true; do
  for d in runs logs results; do
    [ -d "{REPO_DIR}/$d" ] || continue
    mkdir -p "{DRIVE_DIR}/$d"
    if command -v rsync >/dev/null; then rsync -a "{REPO_DIR}/$d/" "{DRIVE_DIR}/$d/"; else cp -ru "{REPO_DIR}/$d/." "{DRIVE_DIR}/$d/"; fi
  done
  cp -f "{ENV_JSON}" "{DRIVE_DIR}/" 2>/dev/null
  date -u +%Y-%m-%dT%H:%M:%SZ > "{DRIVE_DIR}/last_sync.txt"
  sleep {SYNC_SEC}
done
"""
    p = subprocess.Popen(["bash", "-c", script], stdout=subprocess.DEVNULL, stderr=open("logs/drive_sync.log", "a"),
                         start_new_session=True)
    SYNC_PID.write_text(str(p.pid))
    time.sleep(3)
    print(f"定期コピーを開始（{SYNC_SEC} 秒ごと、{DRIVE_DIR}）。最終コピー:", (DRIVE_DIR / "last_sync.txt").read_text().strip()
          if (DRIVE_DIR / "last_sync.txt").exists() else "まだ")
''')

md("""
## 8. シミュレータの確認（正解コード、3タスク×3回）
人が書いた正解コード（oracle）を流す。Mac とクラウドでは3タスクとも 3/3。ここが 3/3 でなければ描画や環境を疑う。
""")

code_in_repo(r'''
# @title 8. oracle を3タスク×3回
run([sys.executable, "scripts/run_grid.py", "--tag", f"{TAG}_oracle", "--models", "oracle", "--conds", "base",
     "--tasks", *TASKS, "--trials", "3", "--workers", str(min(3, WORKERS)), "--video-trials", "1"], env=capx_env())
rows = [l.split(",") for l in (REPO_DIR / "runs" / f"{TAG}_oracle" / "summary.csv").read_text().splitlines()[1:]]
res = {r[2]: f"{r[3]}/{r[4]}" for r in rows}
save_env(oracle=res)
ok = len(res) == 3 and all(v == "3/3" for v in res.values())
print("\noracle:", res, "→", "Mac と同じ 3/3" if ok else
      "3/3 でないものがある。nut の1回落ちは負荷による揺れでも起きた（試運転で一度）。2回以上落ちる・stack や handover が落ちるなら描画や環境を疑う")
''')

md("## 9. Qwen で1試行だけ通す（skill_mt・stack）")

code_in_repo(r'''
# @title 9. 1試行だけ（見本つき・複数ターン）
run([sys.executable, "scripts/run_grid.py", "--tag", f"{TAG}_try", "--models", SERVED_NAME, "--conds", "skill_mt",
     "--tasks", "stack", "--trials", "1", "--workers", "1", "--video-trials", "1"], env=capx_env())
cell = REPO_DIR / "runs" / f"{TAG}_try" / "skill_mt" / SERVED_NAME
prompt = next(cell.glob("*/stack/initial_prompt.txt"), None)
print("\n送ったプロンプトに見本がある:", bool(prompt) and SKILL_MARK in prompt.read_text())
print(tail(cell / "stack" / "launch.log", 22))
''')

md("""
## 10. 本番（4条件×3タスク×各10回）
裏で動かすので、このセルはすぐ終わる。進み具合は次のセルで見る。
**止まったり切れたりしたら、同じセルをもう一度実行するだけでよい**（`DONE` のあるセルは飛ばし、途中のセルはやり直す）。

止まった試行の見張り（`colab/watchdog.py`）も一緒に起動する。CaP-X の 1000 秒の時間切れが生成コードの
`except` に捕まって効かず、試行が終わらないことがあるため。作業プロセスが 20 分続けて CPU を使い切っていたら
時間切れの合図を送り直す（記録は `logs/watchdog.log`。合図が 0 回なら結果に手は入っていない）。
""")

code_in_repo(r'''
# @title 10. 本番を裏で開始（再開も同じセル）
RUN_PID = WORK / f"run_{TAG}.pid"
RUN_LOG = REPO_DIR / "logs" / f"run_{TAG}.log"
start_file = REPO_DIR / "logs" / f"{TAG}_start.txt"
if not start_file.exists():
    start_file.write_text(f"{time.time():.0f}\n")   # 集計で、これより前の呼び出し（試しの分）を除く
if pid_alive(RUN_PID):
    print("本番はもう動いている。進み具合は次のセルで")
else:
    cmd = [sys.executable, "scripts/run_grid.py", "--tag", TAG, "--models", SERVED_NAME, "--conds", *CONDS,
           "--tasks", *TASKS, "--trials", str(TRIALS), "--workers", str(WORKERS), "--video-trials", str(VIDEO_TRIALS)]
    with open(RUN_LOG, "a") as f:
        f.write(f"\n===== {time.ctime()} {' '.join(cmd)}\n")
    p = subprocess.Popen(cmd, stdout=open(RUN_LOG, "a"), stderr=subprocess.STDOUT, cwd=REPO_DIR, env=capx_env(),
                         start_new_session=True)
    RUN_PID.write_text(str(p.pid))
    save_env(main_run={"cmd": " ".join(cmd), "started_at": open(start_file).read().strip()})
    print("開始した:", " ".join(cmd))
WD_PID = WORK / "watchdog.pid"
if pid_alive(WD_PID):
    print("見張りはもう動いている")
else:
    wd = subprocess.Popen([sys.executable, "-u", "colab/watchdog.py"], stdout=open("logs/watchdog.log", "a"),
                          stderr=subprocess.STDOUT, cwd=REPO_DIR, start_new_session=True)
    WD_PID.write_text(str(wd.pid))
    save_env(watchdog={"script": "colab/watchdog.py", "limit_s": 1200, "log": "logs/watchdog.log"})
    print("見張りを開始した（logs/watchdog.log）")
''')

code_in_repo(r'''
# @title 11. 進み具合（止めても本番は続く）
N_CELLS = len(CONDS) * len(TASKS)
try:
    while True:
        summ = REPO_DIR / "runs" / TAG / "summary.csv"
        rows = summ.read_text().splitlines()[1:] if summ.exists() else []
        rows = list({tuple(l.split(",")[:3]): l for l in rows}.values())   # 回し直したセルは後の行だけ
        alive = pid_alive(WORK / f"run_{TAG}.pid")
        wlog = REPO_DIR / "logs" / "watchdog.log"
        fired = sum("SIGALRM" in l for l in wlog.read_text().splitlines()) if wlog.exists() else 0
        print(f"[{time.strftime('%H:%M:%S')}] 終わったセル {len(rows)}/{N_CELLS}  {'実行中' if alive else '停止'}  "
              f"見張りの合図 {fired} 回  最後: {rows[-1] if rows else '-'}", flush=True)
        if not alive:
            print(tail(REPO_DIR / "logs" / f"run_{TAG}.log", 8))
            break
        time.sleep(60)
except KeyboardInterrupt:
    print("監視をやめた（本番は裏で続いている）")
''')

md("## 12. 集計と確認")

code_in_repo(r'''
# @title 12. 集計（results/planA_*）と、見本が入っていたかの確認
since = (REPO_DIR / "logs" / f"{TAG}_start.txt").read_text().strip()
run([sys.executable, "scripts/analyze.py", "--tag", TAG, "--calls", "logs/llm_calls.jsonl", "--since", since], env=capx_env())
run([sys.executable, "scripts/check_skill_prompts.py", "--run", f"runs/{TAG}", "--calls", "logs/llm_calls.jsonl",
     "--since", since], env=capx_env(), check=False)
# 試行の数が足りないセル（CaP-X は呼び出しが失敗した試行を数に入れない）と、断られた呼び出し
rows = [l.split(",") for l in (REPO_DIR / "runs" / TAG / "summary.csv").read_text().splitlines()[1:]]
last = {(r[0], r[1], r[2]): r for r in rows}   # 回し直したセルは後の行が有効
short = [f"{c}/{t}: " + (f"{last[(c, SERVED_NAME, t)][4]} 試行" if (c, SERVED_NAME, t) in last else "行が無い（IK の失敗などで飛ばされた）")
         for c in CONDS for t in TASKS
         if (c, SERVED_NAME, t) not in last or int(last[(c, SERVED_NAME, t)][4]) < TRIALS]
calls = [json.loads(l) for l in open(REPO_DIR / "logs" / "llm_calls.jsonl")] if (REPO_DIR / "logs" / "llm_calls.jsonl").exists() else []
bad = [c for c in calls if c["time"] >= float(since) and c.get("http_status") != 200]
save_env(check={"short_cells": short, "failed_calls": len(bad)})
print(f"\n{TRIALS} 試行に足りないセル: {short or 'なし'}、断られた呼び出し: {len(bad)} 回")
for c in bad[:5]:
    print("  ", c.get("http_status"), str(c.get("error"))[:300])
if short:
    print("足りないセルは runs/<tag>/<cond>/<model>/<task>/DONE を消してセル10をもう一度実行すれば、そのセルだけ最初から回る"
          "（run_grid が前の試行のフォルダを消し、summary.csv に新しい行を足す）。"
          "400 で文脈の長さが原因なら、先に max-model-len を上げて vLLM を立て直す")
''')

code_in_repo(r'''
# @title 13. 環境メモ（runs/planA/ENV_planA.md）
e = load_env()
pk = subprocess.run(["uv", "pip", "list", "--python", str(CAPX_PY)], capture_output=True, text=True).stdout
keep = ("mujoco", "numpy", "scipy", "robosuite", "pyroki", "jax", "jaxlib", "PyOpenGL", "pyrender", "open3d", "openai", "gymnasium")
pk = "\n".join(l for l in pk.splitlines() if l.split(" ")[0] in keep)
summ = REPO_DIR / "runs" / TAG / "summary.csv"
# CaP-X が実際に送った temperature・max_tokens を、本番の呼び出しの記録から数える
from collections import Counter
since = float((REPO_DIR / "logs" / f"{TAG}_start.txt").read_text()) if (REPO_DIR / "logs" / f"{TAG}_start.txt").exists() else 0
sent, max_in = Counter(), 0
if (REPO_DIR / "logs" / "llm_calls.jsonl").exists():
    for l in open(REPO_DIR / "logs" / "llm_calls.jsonl"):
        c = json.loads(l)
        if c["time"] < since:
            continue
        q = json.loads(c["request"]) if isinstance(c.get("request"), str) else (c.get("request") or {})
        sent[f"temperature {q.get('temperature')}・max_tokens {q.get('max_tokens')}"] += 1
        max_in = max(max_in, c.get("input_tokens") or 0)
wlog = REPO_DIR / "logs" / "watchdog.log"
fired = [l for l in wlog.read_text().splitlines() if "SIGALRM" in l] if wlog.exists() else []
lines = [f"# 案A の実行環境（{TAG}）", "",
         "Colab で自動生成（colab/pai_planA.ipynb の 13）。", "",
         "## マシン", *[f"- {k}: {v}" for k, v in e.get("machine", {}).items()], "",
         "## 描画", f"- MUJOCO_GL / PYOPENGL_PLATFORM: {e.get('gl', {}).get('backend')}",
         f"- GL_RENDERER: {e.get('gl', {}).get('renderer')}",
         f"- 確認の結果: `{json.dumps(e.get('gl', {}).get('check', {}).get('results', {}), ensure_ascii=False)}`", "",
         "## LLM", f"- モデル: {MODEL_ID}（served-model-name {SERVED_NAME}）",
         f"- vLLM: {json.dumps(e.get('vllm', {}), ensure_ascii=False)}",
         f"- 起動コマンド: `{e.get('vllm_server', {}).get('cmd')}`",
         f"- 立ち上がりまで: {e.get('vllm_server', {}).get('startup_s')} 秒",
         f"- 試しの呼び出し: {json.dumps(e.get('test_call', {}), ensure_ascii=False)}",
         f"- 中継で enable_thinking=false を足したか: {e.get('force_no_think', False)}",
         f"- CaP-X が送るのは model・messages・temperature・max_tokens だけ（CaP-X の既定 {CAPX_TEMPERATURE}・{CAPX_MAX_TOKENS}）。"
         f"本番の開始以降の全呼び出しで送られた値: {dict(sent) or '記録なし'}、プロンプトの最大 {max_in} トークン"
         "（本番の後にセル6bを回した分も入る）",
         f"- 試行の数が足りないセル・断られた呼び出し: {e.get('check', {})}",
         "- 全呼び出しは logs/llm_calls.jsonl", "",
         "## CaP-X", f"- {json.dumps(e.get('capx', {}), ensure_ascii=False)}", f"- リポジトリ: {e.get('repo')}",
         "```", pk, "```", "",
         "## 実行", f"- oracle（3回ずつ）: {e.get('oracle')}", f"- 本番: `{e.get('main_run', {}).get('cmd')}`",
         f"- 並列数: {e.get('machine', {}).get('workers')}、動画は各セルの最初の {VIDEO_TRIALS} 試行",
         f"- 止まった試行の見張り（colab/watchdog.py）の合図: {len(fired)} 回" + (f"（{'; '.join(fired)}）" if fired else ""), "",
         "| cond | model | task | success | trials | elapsed_s |", "|---|---|---|---|---|---|",
         *[("| " + " | ".join(l.split(",")) + " |") for l in
           {tuple(l.split(",")[:3]): l for l in (summ.read_text().splitlines()[1:] if summ.exists() else [])}.values()]]
# ↑ 回し直したセルは後の行だけ（run_grid.py は回し直すと summary.csv に行を足す）
out = REPO_DIR / "runs" / TAG / f"ENV_{TAG}.md"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text("\n".join(lines) + "\n")
print(out.read_text())
''')

md("""
## 14. 結果を zip にする
入れるもの: 各セルの launch.log・DONE・CaP-X のセル単位のファイル、各試行の summary.txt・code.py・all_responses.json、
動画（video_combined.mp4。最初の数試行だけ）、`logs/llm_calls.jsonl`（vLLM の呼び出しの記録）、vLLM・本番のログ、
描画の確認、環境メモ、集計（results/planA_*）。zip は Drive にも置く。
""")

code_in_repo(r'''
# @title 14. zip を作る（Drive にも置き、ダウンロードする）
import zipfile
stamp = time.strftime("%Y%m%d_%H%M%S")
zpath = WORK / f"{TAG}_results_{stamp}.zip"
CELL_FILES = {"launch.log", "DONE", "summary.csv", "summary.txt", "code.py", "all_responses.json",
              "initial_prompt.txt", "summaries.txt", "aaa_done_flag", "video_combined.mp4", f"ENV_{TAG}.md"}
n = 0
with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
    for tag in [TAG, f"{TAG}_oracle", f"{TAG}_try"]:
        for f in sorted((REPO_DIR / "runs" / tag).rglob("*")) if (REPO_DIR / "runs" / tag).exists() else []:
            if f.is_file() and f.name in CELL_FILES:
                z.write(f, f.relative_to(REPO_DIR)); n += 1
    for name in ["llm_calls.jsonl", f"run_{TAG}.log", "gl_check.json", "log_proxy.log", "pyroki_server.log", f"{TAG}_start.txt",
                 "watchdog.log"]:
        f = REPO_DIR / "logs" / name
        if f.exists():
            z.write(f, f.relative_to(REPO_DIR)); n += 1
    vlog = REPO_DIR / "logs" / "vllm.log"
    if vlog.exists():   # vLLM のログは長いので最後の 3000 行だけ
        z.writestr("logs/vllm_tail.log", tail(vlog, 3000)); n += 1
    for f in sorted((REPO_DIR / "results").glob(f"{TAG}_*")):
        z.write(f, f.relative_to(REPO_DIR)); n += 1
    if ENV_JSON.exists():
        z.write(ENV_JSON, "planA_env.json"); n += 1
print(f"{zpath}（{n} ファイル、{zpath.stat().st_size / 1e6:.1f} MB）")
try:
    shutil.copy2(zpath, DRIVE_DIR / zpath.name)
    print("Drive にも置いた:", DRIVE_DIR / zpath.name)
except Exception as ex:
    print("Drive へのコピーに失敗:", ex)
if IN_COLAB:
    try:   # Colab CLI（colab exec）から実行したときは効かないので、手元の colab download で取ってくる
        from google.colab import files
        files.download(str(zpath))
    except Exception as ex:
        print("ブラウザへのダウンロードに失敗:", ex)
print("CLI なら: colab download -s <名前>", zpath, "<手元の置き場所>")
''')

md("""
## 終わったら
- zip が手元と Drive にあることを確かめてから、「ランタイム」→「ランタイムを接続解除して削除」（つないでいる間はユニットが減る）。
- zip を展開し、`runs/planA*` をリポジトリの `runs/` に、`results/planA_*` を `results/` に置く。
""")


def build() -> dict:
    cells = []
    for kind, src in CELLS:
        lines = src.splitlines(keepends=True)
        cell = {"cell_type": kind, "metadata": {}, "source": lines}
        if kind == "code":
            cell.update(execution_count=None, outputs=[])
        cells.append(cell)
    return {
        "cells": cells,
        "metadata": {
            "accelerator": "GPU",
            "colab": {"provenance": [], "gpuType": "A100", "machine_shape": "hm"},
            "kernelspec": {"display_name": "Python 3", "name": "python3"},
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 0,
    }


if __name__ == "__main__":
    out = Path(__file__).resolve().parent / "pai_planA.ipynb"
    out.write_text(json.dumps(build(), indent=1, ensure_ascii=False) + "\n")
    print(f"wrote {out} ({len(CELLS)} cells)")
