"""提出用の動画（約3分、字幕のみ）を runs/ の試行動画から作る。

  ../third_party/cap-x/.venv-mac/bin/python scripts/make_video.py <出力先.mp4> [--work <作業フォルダ>]

必要なもの: ffmpeg（PATH 上）、Pillow、runs/（リポジトリには含めていない生の出力）、report/figs/。
字幕はヒラギノ角ゴシック（macOS 標準）で画像にして重ねる。数字はレポート（report/report_draft.md）と同じもの。
"""

from __future__ import annotations

import argparse
import re
import glob
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
W, H, FPS = 1920, 1080, 30
MARGIN = 100
BG = (16, 24, 38)
PANEL = (30, 42, 62)
FG = (240, 243, 248)
SUB = (165, 177, 195)
ACCENT = (255, 196, 70)
OK = (90, 200, 120)
NG = (240, 100, 90)
CODE = (200, 225, 255)
FONT_B = "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc"
FONT_R = "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"
FONT_M = "/System/Library/Fonts/Menlo.ttc"
NO_HEAD = set("、。，．）」』】・：；！？ー")
NO_TAIL = set("（「『【")


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

    def _font(self, size, bold=False, mono=False):
        return font(FONT_M if mono else (FONT_B if bold else FONT_R), size)

    def text(self, xy, s, size=40, fill=FG, bold=False, anchor="la", mono=False):
        self.d.text(xy, s, font=self._font(size, bold, mono), fill=fill, anchor=anchor)

    def wrap(self, s: str, size: int, maxw: int, bold=False) -> list[str]:
        """幅 maxw で折り返す。英数字の並び（API 名など）は途中で切らず、閉じ括弧や句読点は行頭に置かない。"""
        f = self._font(size, bold)
        out = []
        for para in s.split("\n"):
            tokens = re.findall(r"[A-Za-z0-9_.@/+\-=√]+|.", para)
            merged: list[str] = []
            for t in tokens:  # 行頭に来てはいけない文字は前の塊に、開き括弧のあとは次の塊にくっつける
                if merged and (t in NO_HEAD or merged[-1][-1] in NO_TAIL):
                    merged[-1] += t
                else:
                    merged.append(t)
            line = ""
            for t in merged:
                if line and f.getlength(line + t) > maxw:
                    out.append(line.rstrip())
                    line = t.lstrip()
                else:
                    line += t
            out.append(line)
        return out

    def para(self, x, y, s, size=38, fill=FG, bold=False, maxw=W - 2 * MARGIN, gap=1.55) -> int:
        """折り返して書き、次に書ける y を返す。"""
        for i, line in enumerate(self.wrap(s, size, maxw, bold)):
            self.text((x, y + i * size * gap), line, size, fill=fill, bold=bold)
        return int(y + len(self.wrap(s, size, maxw, bold)) * size * gap)

    def header(self, title: str, sub: str = "") -> int:
        self.d.rectangle([0, 0, W, 8], fill=ACCENT)
        self.text((MARGIN, 52), title, 56, bold=True)
        y = 140
        if sub:
            y = self.para(MARGIN, 140, sub, 34, fill=SUB)
        return y + 20

    def bullets(self, x, y, rows, size=38, maxw=W - 2 * MARGIN, gap=1.5, space=0.55) -> int:
        """rows は str か (str, 色, 太字)。行頭に「・」を付けて折り返す。"""
        for r in rows:
            fill, bold = FG, False
            if isinstance(r, tuple):
                r, fill, bold = r
            self.text((x, y), "・", size, fill=fill, bold=bold)
            y = self.para(x + size, y, r, size, fill=fill, bold=bold, maxw=maxw - size, gap=gap)
            y += int(size * space)
        return y

    def box(self, x, y, w, h, fill=PANEL, radius=18):
        self.d.rounded_rectangle([x, y, x + w, y + h], radius, fill=fill)

    def label_box(self, x, y, w, h, label, size=38):
        self.box(x, y, w, h)
        self.text((x + w / 2, y + h / 2), label, size, bold=True, anchor="mm")

    def arrow(self, x0, y, x1, color=SUB):
        self.d.line([x0, y, x1 - 18, y], fill=color, width=6)
        self.d.polygon([(x1, y), (x1 - 26, y - 16), (x1 - 26, y + 16)], fill=color)

    def image(self, path: Path, box, pad=12, bg=(255, 255, 255)):
        x, y, w, h = box
        im = Image.open(path).convert("RGB")
        im.thumbnail((w - 2 * pad, h - 2 * pad), Image.LANCZOS)
        framed = Image.new("RGB", (im.width + 2 * pad, im.height + 2 * pad), bg)
        framed.paste(im, (pad, pad))
        self.im.paste(framed, (int(x + (w - framed.width) / 2), int(y + (h - framed.height) / 2)))

    def table(self, x, y, colw, rows, size=34, rowh=62, head_fill=PANEL, colors=None):
        """rows[0] が見出し。colors は {(行, 列): 色}。"""
        colors = colors or {}
        for r, row in enumerate(rows):
            cx = x
            if r == 0:
                self.box(x, y - 8, sum(colw), rowh, fill=head_fill, radius=10)
            for c, cell in enumerate(row):
                fill = colors.get((r, c), FG if r else SUB)
                anchor = "lm" if c == 0 else "mm"
                tx = cx + 16 if c == 0 else cx + colw[c] / 2
                self.text((tx, y + rowh / 2 - 8), cell, size, fill=fill, bold=(r == 0 or c == 0), anchor=anchor)
                cx += colw[c]
            y += rowh
        return y

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


def first_frame(video: Path, out: Path, at: float = 0.0) -> Path:
    run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(at), "-i", str(video), "-frames:v", "1", str(out)])
    return out


# ---------------------------------------------------------------- 構成
def build(out_mp4: Path, work: Path) -> None:
    segs: list[Path] = []
    n = 0

    def seg(name: str) -> Path:
        nonlocal n
        n += 1
        return work / f"{n:02d}_{name}"

    # 使う試行（フォルダ名の taskcompleted_1/0 が成否）
    sol_ho = trial("clean/base/codex-cli__gpt-6.1-sol@medium/*/handover/trial_01_*taskcompleted_1")
    terra_ho = trial("clean/base/codex-cli__gpt-6.1-terra@medium/*/handover/trial_01_*taskcompleted_0")
    sol_rs = trial("clean/base/codex-cli__gpt-6.1-sol@medium/*/restack/trial_01_*taskcompleted_0")
    argon_rs = trial("main/base_mt/agy-cli__gemini-4-argon-medium/*/restack/trial_01_*taskcompleted_1")
    haiku_st = trial("main/base/claude-cli__claude-haiku-5-5@medium/*/stack/trial_01_*taskcompleted_1")
    haiku_nst = trial("main/noisy/claude-cli__claude-haiku-5-5@medium/*/stack/trial_04_*taskcompleted_0")
    flash_nut = trial("main/base/agy-cli__gemini-3.8-flash-medium/*/nut/trial_01_*taskcompleted_1")
    qwen_base = trial("planA/base/qwen3.5-9b/*/stack/trial_02_*taskcompleted_0")
    qwen_skill = trial("planA/skill/qwen3.5-9b/*/stack/trial_01_*taskcompleted_1")

    # 1. タイトル
    c = Card()
    c.d.rectangle([0, 0, W, 8], fill=ACCENT)
    c.text((W / 2, 400), "LLM にロボット制御コードを書かせる", 80, bold=True, anchor="mm")
    c.text((W / 2, 520), "CaP-X での 9 モデルの比較と、小型オープンモデルの底上げ", 50, fill=SUB, anchor="mm")
    c.text((W / 2, 760), "PAI 応用編1 最終課題", 40, fill=ACCENT, anchor="mm")
    segs.append(still(c.save(seg("title.png")), 4, seg("title.mp4")))

    # 2. 全体像
    c = Card()
    y = c.header("この課題の全体像",
                 "Code-as-Policy: LLM が API（物体の位置を調べる・掴む姿勢を求める・手先を動かす関数）を組み合わせた "
                 "Python コードを書き、それを実行してロボットを動かす方式。GENIAC-PRIZE 2026 の本コンテストの題材。")
    bw, bh, top = 780, 560, y + 40
    for i, (title, rows) in enumerate([
        ("実験1: 大規模 LLM の比較", [
            "Claude・GPT・Gemini・GPT-OSS の計 9 モデル",
            "4 タスク × 4 条件（シングルターン／複数ターン／位置ノイズ／ノイズ＋複数ターン）",
            "計 900 試行。どのモデルが、どんな作業で、どこまでできるか",
        ]),
        ("実験2: 小型オープンモデルの底上げ", [
            "Qwen3.5-9B（Colab の GPU で推論）",
            "① 複数ターン ② スキルライブラリ（実験1 の成功コードを見本に追加）",
            "計 120 試行。仕組みを足すと、大規模モデルにどこまで近づくか",
        ]),
    ]):
        x = MARGIN + i * (bw + 160)
        c.box(x, top, bw, bh)
        c.text((x + 40, top + 40), title, 44, fill=ACCENT, bold=True)
        c.bullets(x + 40, top + 130, rows, 36, maxw=bw - 80)
    c.arrow(MARGIN + bw + 20, top + bh / 2, MARGIN + bw + 140, color=ACCENT)
    c.text((MARGIN + bw + 80, top + bh / 2 + 50), "成功コード", 26, fill=ACCENT, anchor="mm")
    segs.append(still(c.save(seg("overview.png")), 13, seg("overview.mp4")))

    # 3. CaP-X
    c = Card()
    y = c.header("ベンチマーク CaP-X",
                 "Code-as-Policy のベンチマーク。robosuite（物理エンジン MuJoCo）上のロボットを、LLM が書いたコードで動かす")
    top = y + 30
    c.label_box(MARGIN, top, 460, 150, "プロンプト")
    c.arrow(MARGIN + 480, top + 75, MARGIN + 600)
    c.label_box(MARGIN + 620, top, 460, 150, "LLM が Python を生成")
    c.arrow(MARGIN + 1100, top + 75, MARGIN + 1220)
    c.label_box(MARGIN + 1240, top, 480, 150, "シミュレータで実行")
    c.para(MARGIN + 10, top + 165, "タスクの目標 ＋ 使える API の説明", 30, fill=SUB, maxw=560)
    c.para(MARGIN + 1250, top + 165, "終了時に、環境が目標を満たしたかを判定（成否）", 30, fill=SUB, maxw=470)
    c.bullets(MARGIN, top + 300, [
        "API の例: get_object_pose（物体の位置と姿勢）、sample_grasp_pose（掴む位置と向き）、goto_pose（手先を動かす）",
        "今回はすべて「特権情報あり」の設定: 物体の位置はシミュレータの真の値が返る（画像認識は使わない）",
        "人が書いた正解コードは、使った 4 タスクで各 3 回とも成功する → 失敗は LLM のコードの問題",
    ], 36)
    segs.append(still(c.save(seg("capx.png")), 11, seg("capx.mp4")))

    # 4. タスク
    c = Card()
    c.header("使った 4 タスク（実験2 は積み替えを除く 3 タスク）")
    thumbs = [
        (first_frame(haiku_st, work / "t_stack.png"), ("積む", "cube_stack"),
         "赤いキューブを掴み、緑のキューブの上に積む。基本の確認"),
        (first_frame(flash_nut, work / "t_nut.png"), ("ナット", "nut_assembly"),
         "四角いナットの取っ手を掴み、四角い柱に通す。ナットの向きを柱に合わせる必要がある"),
        (first_frame(sol_rs, work / "t_restack.png"), ("積み替え", "cube_restack"),
         "初期状態では緑が赤の上に載っている。赤を緑の上に積むには、まず緑を下ろす必要がある"),
        (first_frame(sol_ho, work / "t_handover.png"), ("受け渡し", "two_arm_handover"),
         "腕 0 が持ち上げたハンマーの柄を、腕 1 が掴んで受け取る。2 本の腕の位置と向きの協調"),
    ]
    tw = 400
    for i, (png, name, desc) in enumerate(thumbs):
        x = MARGIN + i * (tw + 40)
        c.image(png, (x, 170, tw, tw), pad=0)
        c.text((x, 600), name[0], 36, fill=ACCENT, bold=True)
        c.text((x, 652), name[1], 28, fill=SUB, mono=True)
        c.para(x, 710, desc, 30, maxw=tw, gap=1.5)
    segs.append(still(c.save(seg("tasks.png")), 13, seg("tasks.mp4")))

    # 5. 実験1 の設定
    c = Card()
    y = c.header("実験1: 大規模 LLM 9 モデルの比較 — 設定")
    y = c.para(MARGIN, y + 10,
               "モデル: Claude（Haiku 5.5・Opus 5.5・Fable 5.1）、GPT（gpt-6.1-terra・gpt-6.1-sol・gpt-6-astra）、"
               "Gemini（3.8 Flash・4 Argon）、GPT-OSS 120B の計 9 モデル。各社の CLI 経由、推論の深さ（effort）は medium", 36)
    y = c.bullets(MARGIN, y + 30, [
        ("シングルターン: LLM はコードを 1 回だけ書く（CaP-X の公式設定）", FG, False),
        ("複数ターン: 実行したコードと標準出力・エラーを LLM に返し、REGENERATE（書き直す）か FINISH（完了）かを選ばせる（CaP-X 公式のプロンプト）", FG, False),
        ("位置ノイズ: 位置を返す API の戻り値に、呼ぶたびに独立なガウス誤差（標準偏差 1 cm）を加える。画像認識の誤差の代わり", FG, False),
    ], 36)
    c.para(MARGIN, y + 10, "モデル × タスク × 条件の組み合わせ（セル）ごとに 10 試行。9 モデル × 10 セル = 900 試行", 36, fill=ACCENT, bold=True)
    segs.append(still(c.save(seg("exp1_setup.png")), 14, seg("exp1_setup.mp4")))

    # 6. 全体の表
    c = Card()
    y = c.header("実験1 の結果（成功数 / 10 と、10 セルの合計 / 100）",
                 "左 4 列: シングルターン、中 2 列: 複数ターン、右 4 列: 位置ノイズあり（シングル・複数ターン）。"
                 "合計は難しさの違うセルの和なので、近い値どうし（例: Argon 56 と Flash 55）の順位には意味がない")
    c.image(ROOT / "report/figs/fig0_heatmap.png", (MARGIN, y, W - 2 * MARGIN, H - y - 30))
    segs.append(still(c.save(seg("heatmap.png")), 10, seg("heatmap.mp4")))

    # 7. 受け渡し
    c = Card()
    c.header("差が最も大きいのは両腕の受け渡し",
             "シングルターン（4 倍速）。sol・astra は 10/10、terra は 1/10、Fable・GPT-OSS は 0/10（Fisher の正確検定で p ≦ 0.0001）")
    c.text((520, 1005), "gpt-6.1-sol: 成功（10/10）", 42, fill=OK, bold=True, anchor="mm")
    c.text((1400, 1005), "gpt-6.1-terra: ハンマーを落とす（1/10）", 42, fill=NG, bold=True, anchor="mm")
    segs.append(panels(c.save(seg("handover.png")),
                       [(sol_ho, 4, 160, 250, 700), (terra_ho, 4, 1050, 250, 700)], 14, seg("handover.mp4")))

    # 8. 積み替え
    c = Card()
    c.header("積み替え: シングルターンでは 9 モデルすべて 0/10",
             "緑が赤の上に載っていることを確かめずに掴みにいく。複数ターンで上がったのは Gemini 4 Argon（5/10）だけで、"
             "その 5 回はすべて書き直した試行。Flash・sol は書き直さずに FINISH と答えた（1/3 速）")
    c.text((520, 985), "シングルターン（gpt-6.1-sol）: 失敗", 38, fill=NG, bold=True, anchor="mm")
    c.text((1400, 975), "複数ターン（Gemini 4 Argon）: 成功", 38, fill=OK, bold=True, anchor="mm")
    c.text((1400, 1035), "1 回目は失敗 → 位置を確かめて再試行するコードに REGENERATE", 28, fill=SUB, anchor="mm")
    segs.append(panels(c.save(seg("restack.png")),
                       [(sol_rs, 1 / 3, 190, 280, 660), (argon_rs, 1 / 3, 1070, 280, 660)], 14, seg("restack.mp4")))

    # 9. 位置ノイズ（見て分かる「積む」で見せ、ナットは数字で出す）
    c = Card()
    c.header("位置ノイズ（標準偏差 1 cm）で成功率が下がる",
             "Claude Haiku 5.5 の積む（1/3 速）。9 モデル合計で 積む 87/90 → 64/90（p < 0.0001）、"
             "ナット 56/90 → 37/90（p = 0.007）。ナットは Flash 9 → 1、Haiku 6 → 0")
    c.text((520, 1000), "ノイズなし: 成功（10/10）", 40, fill=OK, bold=True, anchor="mm")
    c.text((1400, 1000), "ノイズあり: 赤が緑の上に載らない（7/10）", 40, fill=NG, bold=True, anchor="mm")
    segs.append(panels(c.save(seg("noisy.png")),
                       [(haiku_st, 1 / 3, 210, 270, 680), (haiku_nst, 1 / 3, 1060, 270, 680)], 12, seg("noisy.mp4")))

    # 10. 平均化
    code = (ROOT / "runs/main/noisy/claude-cli__claude-opus-5-5@medium/claude-cli_claude-opus-5-5@medium/stack"
            / "trial_04_sandboxrc_0_reward_1.000_taskcompleted_1/code.py").read_text().splitlines()[3:10]
    c = Card()
    y = c.header("ノイズに備えるコードを書くモデルもある",
                 "ノイズは呼ぶたびに独立なので、n 回読んで平均すれば誤差の標準偏差は 1/√n になる（Claude Opus 5.5 が書いたコード）")
    c.box(MARGIN, y + 10, W - 2 * MARGIN, 400, fill=(26, 34, 50))
    for i, line in enumerate(code):
        c.text((MARGIN + 50, y + 50 + i * 48), line, 34, fill=CODE, mono=True)
    c.bullets(MARGIN, y + 450, [
        ("ノイズありの積む: Opus 9/10、Argon 10/10。どちらも 10 試行すべてで平均化していた", OK, True),
        "Haiku と GPT-OSS は一度も平均化しなかった",
        "ナットは平均化しても成功するとは限らない（位置だけでなく向きも合わせる必要がある）",
    ], 36)
    segs.append(still(c.save(seg("avg.png")), 10, seg("avg.mp4")))

    # 11. 実験2 のねらいと設定
    c = Card()
    y = c.header("実験2: 小型オープンモデルの底上げ",
                 "ねらい: 本コンテストでは大規模モデルを API で使えない場面がある。9B 規模のオープンモデルに仕組みを足すと、どこまで近づくか")
    y = c.para(MARGIN, y + 10,
               "モデル: Qwen3.5-9B（bf16）。Colab の A100 上で vLLM により推論し、CaP-X も同じ VM で実行"
               "（thinking はオフ、temperature 1.0）。積む・ナット・受け渡し × 4 条件 × 各 10 回 = 120 試行", 34)
    top = y + 30
    cw, ch = 840, 400
    for i, (title, desc) in enumerate([
        ("① 複数ターン", "実験1 と同じ。実行結果（標準出力・エラー）を見せ、REGENERATE か FINISH を選ばせる"),
        ("② スキルライブラリ", "実験1 で大規模モデル（主に gpt-6.1-sol）が成功したコードを、見本（few-shot 例）としてプロンプトに追加。"
                            "答えの持ち込みを防ぐため、同じタスクの成功コードは入れない（例: 積むには、ナットと受け渡しのコードを見せる）"),
    ]):
        x = MARGIN + i * (cw + 40)
        c.box(x, top, cw, ch)
        c.text((x + 36, top + 30), title, 40, fill=ACCENT, bold=True)
        c.para(x + 36, top + 100, desc, 32, maxw=cw - 72, gap=1.5)
    c.para(MARGIN, top + ch + 30, "条件: そのまま ／ ① ／ ② ／ ①＋② の 4 つ", 36, fill=ACCENT, bold=True)
    segs.append(still(c.save(seg("exp2_setup.png")), 16, seg("exp2_setup.mp4")))

    # 12. 実験2 の結果（表）
    c = Card()
    y = c.header("実験2 の結果（成功数 / 10 と、3 タスクの合計 / 30）",
                 "参考の行は、大規模 9 モデルのシングルターンの中央値。合計の 19 は、各モデルの 3 タスク合計の中央値（範囲 12〜29）")
    rows = [
        ["条件", "積む", "ナット", "受け渡し", "合計 / 30"],
        ["そのまま", "1", "0", "0", "1"],
        ["① 複数ターン", "5", "0", "0", "5"],
        ["② スキルライブラリ", "5", "1", "0", "6"],
        ["①＋②", "6", "0", "0", "6"],
        ["参考: 大規模 9 モデルの中央値", "10", "6", "5", "19"],
    ]
    colors = {(r, 1): OK for r in (2, 3, 4)}
    colors.update({(5, c_): SUB for c_ in range(5)})
    colors.update({(r, 4): ACCENT for r in range(1, 5)})
    y = c.table(MARGIN, y + 20, [700, 240, 240, 260, 280], rows, size=38, rowh=78, colors=colors)
    c.bullets(MARGIN, y + 40, [
        "積むは 1/10 から 5〜6/10 に上がった。3 条件まとめると 16/30 対 1/10 で Fisher の p = 0.026"
        "（ただし、まとめ方は結果を見てから決めた。①と②のどちらが効いたかは区別できない）",
        ("ナットと受け渡しは、①②を足してもほぼ 0（60 試行で成功 1 回）", NG, True),
    ], 34)
    segs.append(still(c.save(seg("exp2_table.png")), 12, seg("exp2_table.mp4")))

    # 13. 実験2 の動画
    c = Card()
    c.header("実験2: Qwen3.5-9B の積む", "シングルターン（1/3 速）")
    c.text((520, 1000), "そのまま: 失敗（1/10）", 42, fill=NG, bold=True, anchor="mm")
    c.text((1400, 1000), "② スキルライブラリ: 成功（5/10）", 42, fill=OK, bold=True, anchor="mm")
    segs.append(panels(c.save(seg("exp2_clip.png")),
                       [(qwen_base, 1 / 3, 210, 230, 700), (qwen_skill, 1 / 3, 1060, 230, 700)], 9, seg("exp2_clip.mp4")))

    # 14. 実験2 で分かったこと
    c = Card()
    y = c.header("実験2 で分かったこと")
    c.bullets(MARGIN, y + 10, [
        ("① はコードが例外で止まる試行を減らした（そのまま 16/30 → ① 2/30）。ただしナット・受け渡しでは、止まらなくなっても成功に届かなかった", FG, True),
        "小型モデルは「最後まで動くコード」の手前でつまずく。大規模モデルの失敗は、ほとんどが段取りや向き・位置の誤りだった",
        ("② には副作用もあった", FG, True),
        "積むで 4 試行が、見本（ナット）にしかない関数 goto_home_joint_position を写して NameError で止まった",
        ("示唆: 9B 規模をそのまま使うのは難しい。成功コードでの学習（ファインチューニング）か、"
         "高レベルの関数を増やして LLM が書く部分を減らす方向が要る", ACCENT, True),
    ], 36)
    segs.append(still(c.save(seg("exp2_findings.png")), 13, seg("exp2_findings.mp4")))

    # 15. まとめ
    c = Card()
    y = c.header("まとめ")
    c.text((MARGIN, y + 10), "実験1: 大規模 LLM 9 モデルの比較", 42, fill=ACCENT, bold=True)
    y = c.bullets(MARGIN, y + 80, [
        "差が出るのは両腕の協調（受け渡し）。積むだけなら、ほぼ全モデルが満点",
        "複数ターンは、モデルが自分で確かめて書き直すときだけ効く",
        "位置ノイズに弱い。平均化などで備えるかはモデル次第",
    ], 36, space=0.35)
    c.text((MARGIN, y + 20), "実験2: 小型オープンモデルの底上げ", 42, fill=ACCENT, bold=True)
    y = c.bullets(MARGIN, y + 90, [
        "①②で積むは 1/10 → 5〜6/10 に上がったが、ナット・受け渡しはほぼ 0 のまま。大規模モデルとの差は大きい",
    ], 36)
    c.text((MARGIN, y + 40), "コード・設定・結果: github.com/Shinzo0821/pai-final-cap", 40, fill=SUB)
    segs.append(still(c.save(seg("summary.png")), 12, seg("summary.mp4")))

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
