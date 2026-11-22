"""Render a project Markdown file (headings, tables, lists, paragraphs) to a styled HTML page.

    python tools/md_to_html.py Reference_materials/extracted/OTHERS_FINANCIAL_REVIEW.md
"""
import html
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def inline(s):
    s = html.escape(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)
    return re.sub(r"(?<![*\w])\*([^*]+)\*(?!\w)", r"<i>\1</i>", s)


def render(src, title):
    css = (ROOT / "tools" / "backtest_gold.py").read_text().split('css = """', 1)[1].split('"""', 1)[0]
    out, lines, i = [], src.split("\n"), 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            hdr, body = rows[0], [r for r in rows[1:] if not re.match(r"^-+$", r[0].replace(":", ""))]
            out.append("<div class='wrap'><table><thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in hdr) + "</tr></thead><tbody>"
                       + "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in body) + "</tbody></table></div>")
            continue
        m = re.match(r"^(#+) (.*)", line)
        if m:
            out.append(f"<h{len(m.group(1))}>{inline(m.group(2))}</h{len(m.group(1))}>")
            i += 1
            continue
        if re.match(r"^\s*(- |\d+\. )", line):
            tag = "ol" if re.match(r"^\d+\.", line.strip()) else "ul"
            items = []
            while i < len(lines) and (re.match(r"^\s*(- |\d+\. )", lines[i]) or (lines[i].startswith("   ") and lines[i].strip())):
                if re.match(r"^\s*(- |\d+\. )", lines[i]):
                    items.append(re.sub(r"^\s*(- |\d+\. )", "", lines[i]))
                else:
                    items[-1] += " " + lines[i].strip()
                i += 1
            out.append(f"<{tag}>" + "".join(f"<li>{inline(x)}</li>" for x in items) + f"</{tag}>")
            continue
        if line.strip():
            out.append(f"<p>{inline(line)}</p>")
        i += 1
    return (f"<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>{html.escape(title)}</title><style>{css} code{{font-size:12px}}</style></head><body>" + "\n".join(out) + "</body></html>")


if __name__ == "__main__":
    p = pathlib.Path(sys.argv[1])
    p.with_suffix(".html").write_text(render(p.read_text(), sys.argv[2] if len(sys.argv) > 2 else "Others Financial Review"), encoding="utf-8")
