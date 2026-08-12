"""Replace the plain-text objectives in Appendix A with native Word equations.

    python scripts/insert_equations.py

The brief asks for equations set with Word's equation editor or LaTeX, numbered,
with every symbol defined. python-docx has no equation API, but a Word equation
is just OMML (Office Math Markup Language) inside the paragraph, so the markup
can be built directly. The result is a real equation object that Word will
render, re-style, and let me edit by hand afterwards.

Run once. Running it again is safe - it looks for the plain-text lines and
skips any that have already been converted.
"""
from __future__ import annotations

import pathlib
import sys

from docx import Document
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn

ROOT = pathlib.Path(__file__).resolve().parent.parent
TARGET = ROOT / "report" / "report.docx"

M = "http://schemas.openxmlformats.org/officeDocument/2006/math"
NS = f'xmlns:m="{M}" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'


def run(text: str, italic: bool = True, bold: bool = False) -> str:
    """One math run. Variables are italic and operators are not, as in print."""
    props = ""
    if not italic or bold:
        sty = []
        if bold:
            sty.append('<m:sty m:val="b"/>')
        if not italic:
            sty.append('<m:nor/>')
        props = f"<m:rPr>{''.join(sty)}</m:rPr>"
    return f"<m:r>{props}<m:t xml:space=\"preserve\">{text}</m:t></m:r>"


def upright(text: str) -> str:
    return run(text, italic=False)


def sub(base: str, s: str) -> str:
    return f"<m:sSub><m:e>{base}</m:e><m:sub>{s}</m:sub></m:sSub>"


def sup(base: str, s: str) -> str:
    return f"<m:sSup><m:e>{base}</m:e><m:sup>{s}</m:sup></m:sSup>"


def frac(num: str, den: str) -> str:
    return f"<m:f><m:num>{num}</m:num><m:den>{den}</m:den></m:f>"


def rad(inner: str) -> str:
    return (f'<m:rad><m:radPr><m:degHide m:val="1"/></m:radPr>'
            f"<m:deg/><m:e>{inner}</m:e></m:rad>")


def paren(inner: str) -> str:
    return (f'<m:d><m:dPr><m:begChr m:val="("/><m:endChr m:val=")"/></m:dPr>'
            f"<m:e>{inner}</m:e></m:d>")


def oMath(body: str) -> str:
    return f"<m:oMathPara {NS}><m:oMath>{body}</m:oMath></m:oMathPara>"


# --- the four objectives ---------------------------------------------------

w, Sig, mu, one = run("w", bold=True), run("Σ", bold=True), run("μ", bold=True), run("1", bold=True)
wT = sup(w, upright("T"))
oneT = sup(one, upright("T"))
quad = f"{wT}{Sig}{w}"                                   # wᵀΣw
budget = f"{oneT}{w}{upright(" = 1")}"                   # 1ᵀw = 1
nonneg = f"{w}{upright(" ≥ ")}{run('0')}"                 # w ≥ 0
subject = f"{upright('   subject to   ')}{budget}{upright(', ')}{nonneg}"

EQUATIONS = {
    "(1)  Equal weight": oMath(
        f"{sub(run('w'), run('i'))}{upright(' = ')}{frac(run('1'), run('N'))}"
        f"{upright('   for every asset ')}{run('i')}"),
    "(2)  Minimum variance": oMath(
        f"{sub(upright('min'), w)}{upright(' ')}{quad}{subject}"),
    "(3)  Maximum Sharpe": oMath(
        f"{sub(upright('max'), w)}{upright(' ')}"
        f"{frac(f'{wT}{mu}{upright(' − ')}{sub(run('r'), upright('f'))}', rad(quad))}"
        f"{subject}"),
    "(4)  Risk parity": oMath(
        f"{sub(upright('RC'), run('i'))}{upright(' = ')}"
        f"{frac(f'{sub(run('w'), run('i'))}{sub(paren(f'{Sig}{w}'), run('i'))}', quad)}"
        f"{upright(' = ')}{frac(run('1'), run('N'))}"
        f"{upright('   for all ')}{run('i')}"),
}


def main() -> None:
    doc = Document(str(TARGET))
    converted = 0
    for para in doc.paragraphs:
        for label, omml in EQUATIONS.items():
            if not para.text.startswith(label):
                continue
            if para._p.findall(qn("m:oMathPara")):
                print(f"  已是公式，跳过: {label}")
                break
            # keep the numbered label as text, replace the formula that follows
            for r in para.runs:
                r.text = ""
            para.runs[0].text = f"{label}:"
            para._p.append(parse_xml(omml))
            converted += 1
            print(f"  转换: {label}")
            break
    doc.save(str(TARGET))
    print(f"{converted} 条公式已改为 Word 原生公式对象")
    if converted:
        print("在 Word 中打开可直接编辑；样式随文档主题渲染")


if __name__ == "__main__":
    sys.exit(main())
