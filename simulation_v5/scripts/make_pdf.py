#!/usr/bin/env python3
"""Render report_sim_v5.md -> PDF with CJK support via fpdf2 + DroidSansFallback.
Embeds the 14 key figures. Falls back gracefully if a figure is missing."""
import os, re, glob
from fpdf import FPDF

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD = os.path.join(HERE, "report_sim_v5.md")
FIG = os.path.join(HERE, "figures")
FONT = "/usr/share/fonts/google-droid/DroidSansFallback.ttf"

pdf = FPDF(orientation="P", unit="mm", format="A4")
pdf.add_font("Droid", "", FONT, uni=True)
pdf.set_auto_page_break(True, margin=15)


def line_height(s): return 5 if s else 3


with open(MD, encoding="utf-8") as f:
    raw = f.read()

pdf.add_page()
pdf.set_font("Droid", size=9)
W = pdf.w - 2 * pdf.l_margin

for ln in raw.split("\n"):
    s = ln.rstrip()
    if not s:
        pdf.ln(3); continue
    if s.startswith("# "):
        pdf.ln(2); pdf.set_font("Droid", size=15); pdf.multi_cell(W, 8, s[2:]); pdf.set_font("Droid", size=9); pdf.ln(1)
    elif s.startswith("## "):
        pdf.ln(2); pdf.set_font("Droid", size=12); pdf.multi_cell(W, 6, s[3:]); pdf.set_font("Droid", size=9)
    elif s.startswith("### "):
        pdf.ln(1); pdf.set_font("Droid", size=10); pdf.multi_cell(W, 5, s[4:]); pdf.set_font("Droid", size=9)
    elif s.startswith("> "):
        pdf.set_text_color(80, 80, 80); pdf.multi_cell(W, 5, s); pdf.set_text_color(0, 0, 0)
    elif s.startswith("|"):
        pdf.set_font("Droid", size=7.5); pdf.multi_cell(W, 4, s); pdf.set_font("Droid", size=9)
    else:
        # strip markdown bold/italic markers for readability
        clean = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
        clean = re.sub(r"\*(.+?)\*", r"\1", clean)
        clean = re.sub(r"`([^`]+)`", r"\1", clean)
        pdf.multi_cell(W, 5, clean)

# ---- embed figures ----
pdf.add_page()
pdf.set_font("Droid", size=14); pdf.cell(0, 10, "附录：关键图表", ln=1); pdf.ln(2)
pdf.set_font("Droid", size=9)
for fig in sorted(glob.glob(os.path.join(FIG, "*.png"))):
    name = os.path.basename(fig)
    pdf.multi_cell(W, 5, name); pdf.ln(1)
    try:
        pdf.image(fig, w=W * 0.82)
    except Exception as e:
        pdf.cell(0, 5, f"  [image error: {e}]", ln=1)
    pdf.ln(3)

out = os.path.join(HERE, "report_sim_v5.pdf")
pdf.output(out)
print("PDF written:", out, os.path.getsize(out), "bytes")
