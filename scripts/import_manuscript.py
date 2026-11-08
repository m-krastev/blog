#!/usr/bin/env python3
"""Turn a sermon manuscript (.md or .docx) into a Hugo post body.

Cleans the author's working notes out of the manuscript and marks up Scripture:
  - drops <!-- comments --> (old versions) and the <!-- side --> note that follows the marker
  - "(Изход 31:1-6)" before a quote, or at the start of one, becomes a small caption
  - verse numbers at the start of quoted verses become <sup class="v">
  - the bold refrain paragraph gets {.refrain}; prayers ("> Боже, ...") are wrapped in .prayer
  - .docx (via pandoc): paragraphs that are a quotation („...“) become blockquotes,
    escaped markdown ("\\## ...") is restored, stray footnote asterisks and bidi marks removed

Usage: import_manuscript.py SOURCE > body.md   (front matter is written by hand)
"""
import re
import subprocess
import sys
from pathlib import Path

REF = r"[1-3]?\s?[А-Яа-я][А-Яа-я. ]{1,20}\s\d{1,3}(?::[\d,\-–а-я ]+)?"


def from_docx(path: Path) -> str:
    md = subprocess.run(["pandoc", "-f", "docx", "-t", "markdown-smart", "--wrap=none", str(path)],
                        capture_output=True, text=True, check=True).stdout
    md = md.replace("‬", "").replace("‪", "").replace("\\*", "")
    md = re.sub(r"^\\(#+) ", r"\1 ", md, flags=re.M)          # "\## Heading" typed in Word
    md = re.sub(r"\\\n", "\n", md)                              # pandoc hard breaks
    paras = [p.strip() for p in re.split(r"\n\s*\n", md)]
    out = []
    for p in paras:
        if not p:
            continue
        # A paragraph that is a quotation („…“ optionally followed by a reference) -> blockquote.
        if p.startswith("„") and re.search(r"“\s*(\(" + REF + r"\))?\.?$", p) and not p.startswith(">"):
            p = "> " + p
        # Paragraph broken in two by Word (previous ends without punctuation, this starts lowercase).
        if out and p[:1].islower() and not re.search(r"[.!?:;“”\"…)]$", out[-1]):
            out[-1] = out[-1] + " " + p
            continue
        out.append(p)
    return "\n\n".join(out) + "\n"


def clean(md: str) -> str:
    md = re.sub(r"<!--\s*side\s*-->\s*\n(?:>.*\n)+", "", md)   # note for the preacher
    md = re.sub(r"<!--.*?-->\n?", "", md, flags=re.S)
    lines = []
    for line in md.split("\n"):
        s = line.strip()
        if s.startswith("# ") or re.fullmatch(r"\*\*[^*]+\*\*", s) and not lines:
            continue                                            # title is in front matter
        lines.append(line.rstrip() if s else "")
    md = "\n".join(lines)

    # "(Ref)" on its own line right before a quote -> caption inside the quote.
    md = re.sub(r"^\((" + REF + r")\)\s*\n+>\s?", r'> <span class="ref">\1</span>\n>\n> ', md, flags=re.M)
    # "> (Ref) 2 text" -> caption + text.
    md = re.sub(r"^>\s*\((" + REF + r")\)\s+", r'> <span class="ref">\1</span>\n>\n> ', md, flags=re.M)

    out = []
    for line in md.split("\n"):
        if line.startswith(">"):
            # verse numbers: at line start and inline before a capital/lowercase word
            line = re.sub(r"^(>\s*)(\d{1,3}) (?=\S)", r'\1<sup class="v">\2</sup>', line)
            line = re.sub(r"(?<=[.;:,!?…“”\"]) (\d{1,3}) (?=[А-Яа-я„\"])", r' <sup class="v">\1</sup>', line)
            if out and not out[-1].startswith(">") and out[-1].strip():
                out.append("")
        out.append(line)
    md = "\n".join(out)

    # Keep each quoted verse line on its own line (hard break) inside multi-line quotes.
    qlines = md.split("\n")
    for i in range(len(qlines) - 1):
        a, b = qlines[i], qlines[i + 1]
        if a.startswith(">") and b.startswith(">") and a.strip() != ">" and b.strip() != ">" \
                and '<span class="ref">' not in a:
            qlines[i] = a + "\\"
    md = "\n".join(qlines)

    # Refrain: a paragraph that is entirely bold and starts with the thesis.
    md = re.sub(r"^\*\*(„Когато не знаеш.*?)\*\*$", r"\1\n{.refrain}", md, flags=re.M)
    # Prayers.
    md = re.sub(r"^(> Боже,.*(?:\n>.*)*)", r'<div class="prayer">\n\n\1\n\n</div>', md, flags=re.M)
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip() + "\n"


def main():
    src = Path(sys.argv[1])
    md = from_docx(src) if src.suffix.lower() == ".docx" else src.read_text(encoding="utf-8")
    sys.stdout.write(clean(md))


if __name__ == "__main__":
    main()
