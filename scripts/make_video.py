"""提出用の短い動画（約1分40秒、字幕のみ）を runs/ の試行動画から作る。

  ../third_party/cap-x/.venv-mac/bin/python scripts/make_video.py <出力先.mp4> [--work <作業フォルダ>]

必要なもの: ffmpeg（PATH 上）、Pillow、runs/（リポジトリには含めていない生の出力）、report/figs/。
字幕はヒラギノ角ゴシック（macOS 標準）で画像にして重ねる。
"""

from __future__ import annotations

import argparse
import glob
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
W, H, FPS = 1920, 1080, 30
BG = (16, 24, 38)
FG = (240, 243, 248)
SUB = (160, 172, 190)
ACCENT = (255, 196, 70)
OK = (90, 200, 120)
NG = (240, 100, 90)
FONT_B = "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc"
FONT_R = "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"
FONT_M = "/System/Library/Fonts/Menlo.ttc"


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def trial(pattern: str) -> Path:
    """runs/ 以下のパターンに合う試行フォルダの video_combined.mp4（1つだけ）。"""
    hits = sorted(glob.glob(str(ROOT / "runs" / pattern / "video_combined.mp4")))
    if len(hits) != 1:
        raise SystemExit(f"clip not unique: {pattern} -> {hits}")
    return Path(hits[0])


# ---------------------------------------------------------------- 画像（背景と字幕）
class Card:
    def __init__(self) -> None:
        self.im = Image.new("RGB", (W, H), BG)
        self.d = ImageDraw.Draw(self.im)

    def text(self, xy, s, size=44, fill=FG, bold=False, anchor="la", mono=False):
        f = font(FONT_M if mono else (FONT_B if bold else FONT_R), size)
        self.d.text(xy, s, font=f, fill=fill, anchor=anchor)

    def header(self, title: str, sub: str = "") -> None:
        self.d.rectangle([0, 0, W, 8], fill=ACCENT)
        self.text((80, 60), title, 60, bold=True)
        if sub:
            self.text((80, 150), sub, 38, fill=SUB)

    def lines(self, x, y, rows, size=44, gap=1.75):
        for i, r in enumerate(rows):
            fill, bold = FG, False
            if isinstance(r, tuple):
                r, fill, bold = r
            self.text((x, y + i * size * gap), r, size, fill=fill, bold=bold)

    def box(self, x, y, w, h, label, fill=(36, 50, 74)):
        self.d.rounded_rectangle([x, y, x + w, y + h], 18, fill=fill)
        self.text((x + w / 2, y + h / 2), label, 40, bold=True, anchor="mm")

    def arrow(self, x0, y, x1):
        self.d.line([x0, y, x1 - 18, y], fill=SUB, width=6)
        self.d.polygon([(x1, y), (x1 - 26, y - 16), (x1 - 26, y + 16)], fill=SUB)

    def image(self, path: Path, box):
        x, y, w, h = box
        im = Image.open(path).convert("RGB")
        im.thumbnail((w, h), Image.LANCZOS)
        pad = Image.new("RGB", (im.width + 24, im.height + 24), (255, 255, 255))
        pad.paste(im, (12, 12))
        self.im.paste(pad, (int(x + (w - pad.width) / 2), int(y + (h - pad.height) / 2)))

    def save(self, path: Path) -> Path:
        self.im.save(path)
        return path


# ---------------------------------------------------------------- ffmpeg
def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS)]


def still(png: Path, dur: float, out: Path) -> Path:
    run(["ffmpeg", "-loglevel", "error", "-y", "-loop", "1", "-t", str(dur), "-i", str(png), *ENC, str(out)])
    return out


def panels(png: Path, clips: list[tuple[Path, float, int, int, int]], dur: float, out: Path) -> Path:
    """背景 png の上に動画を並べる。clips は (動画, 再生速度, x, y, 一辺)。短い動画は最後のコマで止める。"""
    args = ["ffmpeg", "-loglevel", "error", "-y", "-loop", "1", "-t", str(dur), "-i", str(png)]
    chains, last = [], "0:v"
    for i, (path, speed, x, y, size) in enumerate(clips, start=1):
        args += ["-i", str(path)]
        chains.append(f"[{i}:v]setpts=PTS/{speed},fps={FPS},scale={size}:{size},"
                      f"tpad=stop_mode=clone:stop_duration={dur}[c{i}]")
        chains.append(f"[{last}][c{i}]overlay={x}:{y}:eof_action=repeat[o{i}]")
        last = f"o{i}"
    args += ["-filter_complex", ";".join(chains), "-map", f"[{last}]", "-t", str(dur), *ENC, str(out)]
    run(args)
    return out


# ---------------------------------------------------------------- 構成
def build(out_mp4: Path, work: Path) -> None:
    segs: list[Path] = []
    n = 0

    def seg(name: str) -> Path:
        nonlocal n
        n += 1
        return work / f"{n:02d}_{name}"

    # 1. タイトル
    c = Card()
    c.d.rectangle([0, 0, W, 8], fill=ACCENT)
    c.text((W / 2, 400), "LLM にロボット制御コードを書かせて比べる", 76, bold=True, anchor="mm")
    c.text((W / 2, 520), "Code-as-Policy ベンチマーク CaP-X で 9 モデル × 900 試行", 46, fill=SUB, anchor="mm")
    c.text((W / 2, 590), "＋ 小さいオープンモデル（Qwen3.5-9B）の底上げ 120 試行", 46, fill=SUB, anchor="mm")
    c.text((W / 2, 760), "PAI 応用編1 最終課題", 40, fill=ACCENT, anchor="mm")
    segs.append(still(c.save(seg("title.png")), 6, seg("title.mp4")))

    # 2. 仕組み
    c = Card()
    c.header("やったこと", "LLM が書いた Python のコードで、シミュレータのロボットを動かす")
    c.box(120, 300, 440, 150, "LLM")
    c.arrow(580, 375, 720)
    c.box(740, 300, 440, 150, "Python のコード")
    c.arrow(1200, 375, 1340)
    c.box(1360, 300, 440, 150, "シミュレータで実行")
    c.text((W / 2, 490), "作業の説明と、使える関数（物体の位置を調べる・掴む位置を決める・手先を動かす）を渡す",
           34, fill=SUB, anchor="mm")
    c.lines(140, 590, [
        ("タスク: 積む ・ ナット ・ 積み替え ・ 両腕の受け渡し", FG, True),
        "条件: 1回で答える ／ 実行結果を見て書き直す（複数ターン） ／ 物体の位置に 1cm の誤差",
        "モデル: Claude 3 ・ OpenAI 3 ・ Gemini 2 ・ GPT-OSS 120B（各セル10回）",
    ], 42, gap=1.9)
    segs.append(still(c.save(seg("how.png")), 9, seg("how.mp4")))

    # 3. 全体の表
    c = Card()
    c.header("結果の全体", "9 モデル × 10 セル × 各10回。数字は成功数/10")
    c.image(ROOT / "report/figs/fig0_heatmap.png", (160, 210, 1600, 760))
    segs.append(still(c.save(seg("heatmap.png")), 9, seg("heatmap.mp4")))

    # 4. 受け渡し
    sol = trial("clean/base/codex-cli__gpt-6.1-sol@medium/*/handover/trial_01_*taskcompleted_1")
    terra = trial("clean/base/codex-cli__gpt-6.1-terra@medium/*/handover/trial_01_*taskcompleted_0")
    c = Card()
    c.header("差が一番出たのは、両腕の受け渡し", "片腕で持った物を、もう片方の腕に持ち替える（1回で答える条件・4倍速）")
    c.text((520, 1000), "gpt-6.1-sol  10/10 成功", 44, fill=OK, bold=True, anchor="mm")
    c.text((1400, 1000), "gpt-6.1-terra  1/10（持ち替えられない）", 44, fill=NG, bold=True, anchor="mm")
    segs.append(panels(c.save(seg("handover.png")),
                       [(sol, 4, 160, 230, 720), (terra, 4, 1040, 230, 720)], 16, seg("handover.mp4")))

    # 5. 積み替え
    fail = trial("clean/base/codex-cli__gpt-6.1-sol@medium/*/restack/trial_01_*taskcompleted_0")
    argon = trial("main/base_mt/agy-cli__gemini-4-argon-medium/*/restack/trial_01_*taskcompleted_1")
    c = Card()
    c.header("積み替え: 1回で答えると全モデル 0/10",
             "最初から緑が赤の上に載っている。確かめずに積もうとして失敗する（1/3 速）")
    c.text((520, 975), "1回で答える（gpt-6.1-sol）: 失敗", 40, fill=NG, bold=True, anchor="mm")
    c.text((1400, 960), "複数ターン（Gemini 4 Argon）: 5/10", 40, fill=OK, bold=True, anchor="mm")
    c.text((1400, 1025), "1回目は失敗 → 位置を確かめるコードに書き直して成功", 32, fill=SUB, anchor="mm")
    segs.append(panels(c.save(seg("restack.png")),
                       [(fail, 1 / 3, 160, 230, 700), (argon, 1 / 3, 1050, 230, 700)], 14, seg("restack.mp4")))

    # 6. 位置の誤差（見て分かりやすい「積む」で見せ、数字はナットも出す）
    clean = trial("main/base/claude-cli__claude-haiku-5-5@medium/*/stack/trial_01_*taskcompleted_1")
    noisy = trial("main/noisy/claude-cli__claude-haiku-5-5@medium/*/stack/trial_04_*taskcompleted_0")
    c = Card()
    c.header("位置に 1cm の誤差を足すと、失敗が増える",
             "画像認識の誤差の代わり。Claude Haiku 5.5 の「積む」（1/3 速）")
    c.text((520, 960), "誤差なし: 成功（10/10）", 42, fill=OK, bold=True, anchor="mm")
    c.text((1400, 960), "誤差あり: 赤が緑の上に載らない（7/10）", 42, fill=NG, bold=True, anchor="mm")
    c.text((W / 2, 1035), "9モデル合計: 積む 87/90 → 64/90、ナット 56/90 → 37/90（Flash のナット 9 → 1、Haiku 6 → 0）",
           34, fill=SUB, anchor="mm")
    segs.append(panels(c.save(seg("noisy.png")),
                       [(clean, 1 / 3, 210, 230, 680), (noisy, 1 / 3, 1060, 230, 680)], 11, seg("noisy.mp4")))

    # 7. 平均化
    code = (ROOT / "runs/main/noisy/claude-cli__claude-opus-5-5@medium/claude-cli_claude-opus-5-5@medium/stack"
            / "trial_04_sandboxrc_0_reward_1.000_taskcompleted_1/code.py").read_text().splitlines()[3:10]
    c = Card()
    c.header("誤差に備えるモデルもある", "位置を何度も読んで平均する（Claude Opus 5.5 が書いたコード）")
    c.d.rounded_rectangle([120, 240, 1800, 640], 16, fill=(28, 36, 52))
    for i, line in enumerate(code):
        c.text((170, 280 + i * 50), line, 36, fill=(200, 225, 255), mono=True)
    c.lines(140, 700, [
        ("誤差ありの「積む」: Opus 9/10、Argon 10/10（10回とも平均化）", OK, True),
        "Haiku と GPT-OSS は一度も平均化しなかった",
        "ナットは平均化しても成功するとは限らない（向きも合わせる必要がある）",
    ], 42, gap=1.8)
    segs.append(still(c.save(seg("avg.png")), 10, seg("avg.mp4")))

    # 8. 案A
    base = trial("planA/base/qwen3.5-9b/*/stack/trial_02_*taskcompleted_0")
    skill = trial("planA/skill/qwen3.5-9b/*/stack/trial_01_*taskcompleted_1")
    c = Card()
    c.header("案A: 小さいモデル Qwen3.5-9B（Colab の A100）",
             "①実行結果を見て書き直す ②大きいモデルの成功コード（ほかのタスク）を見本にする")
    c.text((520, 960), "そのまま: 積む 1/10", 42, fill=NG, bold=True, anchor="mm")
    c.text((1400, 960), "②見本あり: 積む 5/10（①＋② 6/10）", 42, fill=OK, bold=True, anchor="mm")
    c.text((W / 2, 1035), "ナット・受け渡しは ①② を足してもほぼ 0（60 試行で 1 回）", 34, fill=SUB, anchor="mm")
    segs.append(panels(c.save(seg("planA.png")),
                       [(base, 1 / 3, 210, 230, 680), (skill, 1 / 3, 1060, 230, 680)], 13, seg("planA.mp4")))

    # 9. まとめ
    c = Card()
    c.header("分かったこと")
    c.lines(120, 220, [
        ("1. 差が出るのは両腕の協調。積むだけならほぼ全モデル満点", FG, True),
        ("2. 複数ターンは、モデルが自分で確かめて直すときだけ効く", FG, True),
        ("3. 位置の誤差に弱い。平均化などで備えるかはモデル次第", FG, True),
        ("4. 9B のモデルは「動くコード」まで。段取りと向きは直らない", FG, True),
    ], 50, gap=2.0)
    c.text((120, 760), "次: 小さいモデルを成功コードで学習させる ／ 画像認識ありの設定で回す", 40, fill=SUB)
    c.text((120, 900), "コード・結果: github.com/Shinzo0821/pai-final-cap", 42, fill=ACCENT)
    segs.append(still(c.save(seg("summary.png")), 11, seg("summary.mp4")))

    # つなぐ（無音の音声トラックを付ける）
    lst = work / "list.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in segs))
    run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
         "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-map", "0:v", "-map", "1:a",
         "-c:v", "copy", "-c:a", "aac", "-shortest", "-movflags", "+faststart", str(out_mp4)])
    print(f"wrote {out_mp4}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--work")
    a = ap.parse_args()
    out = Path(a.out).resolve()
    if a.work:
        Path(a.work).mkdir(parents=True, exist_ok=True)
        build(out, Path(a.work))
    else:
        with tempfile.TemporaryDirectory() as tmp:
            build(out, Path(tmp))


if __name__ == "__main__":
    main()
