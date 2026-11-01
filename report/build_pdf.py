"""report/report_draft.md を A4 の PDF にする（Chrome のヘッドレス印刷）。

  uv run --with markdown python report/build_pdf.py <出力先.pdf>

PDF 用の手直しは2つだけ: 先頭の生成元コメントを消す、表の「出どころ」列（長いパス）を消す。
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

import markdown

HERE = Path(__file__).resolve().parent
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

CSS = """
@page { size: A4; margin: 16mm 15mm 16mm 15mm; }
body { font-family: "Hiragino Sans", "Hiragino Kaku Gothic ProN", sans-serif;
       font-size: 9.6pt; line-height: 1.6; color: #1a1a1a; }
h1 { font-size: 17pt; line-height: 1.35; margin: 0 0 4pt; }
h1 + p { color: #555; margin-top: 0; }
h2 { font-size: 13pt; border-bottom: 1.5px solid #333; padding-bottom: 2pt; margin-top: 18pt;
     break-after: avoid; }
h3 { font-size: 11pt; margin-top: 12pt; break-after: avoid; }
p, li { orphans: 3; widows: 3; }
table { border-collapse: collapse; margin: 6pt 0 8pt; font-size: 8.4pt; break-inside: auto; width: 100%; }
th, td { border: 1px solid #bbb; padding: 2pt 5pt; }
th { background: #eef1f5; }
tr { break-inside: avoid; }
td { text-align: center; }
td:first-child, th:first-child { text-align: left; white-space: nowrap; }
thead { display: table-header-group; }
img { max-width: 100%; max-height: 100mm; display: block; margin: 6pt auto 2pt; break-inside: avoid; }
code { font-family: Menlo, monospace; font-size: 8.4pt; background: #f3f3f3; padding: 0 2px; }
hr { border: 0; border-top: 1px solid #ccc; margin: 10pt 0; }
"""


def drop_source_column(md: str) -> str:
    """ヘッダーの最後の列が「出どころ」の表から、その列を消す。"""
    out, in_table = [], False
    for line in md.splitlines():
        if line.startswith("|") and line.rstrip().endswith("| 出どころ |"):
            in_table = True
        if in_table and line.startswith("|"):
            cells = line.rstrip().rstrip("|").split("|")
            line = "|".join(cells[:-1]) + "|"
        elif in_table:
            in_table = False
        out.append(line)
    return "\n".join(out)


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    out_pdf = Path(sys.argv[1]).resolve()
    md = (HERE / "report_draft.md").read_text()
    md = re.sub(r"\A<!--.*?-->\n", "", md, flags=re.S)
    md = drop_source_column(md)
    body = markdown.markdown(md, extensions=["tables", "sane_lists"])
    html = (f'<!doctype html><html lang="ja"><head><meta charset="utf-8">'
            f'<title>LLM にロボット制御コードを書かせて比べる</title>'
            f'<base href="{HERE.as_uri()}/"><style>{CSS}</style></head><body>{body}</body></html>')
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "report.html"
        page.write_text(html)
        subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                        "--allow-file-access-from-files", f"--print-to-pdf={out_pdf}", page.as_uri()],
                       check=True, capture_output=True)
    print(f"wrote {out_pdf}")


if __name__ == "__main__":
    main()
