import os, re, glob
from fpdf import FPDF
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD = os.path.join(HERE, "report_sim_v6.md"); FIG = os.path.join(HERE, "figures")
FONT = "/usr/share/fonts/google-droid/DroidSansFallback.ttf"
pdf = FPDF("P", "mm", "A4"); pdf.add_font("Droid", "", FONT, uni=True)
pdf.set_auto_page_break(True, margin=15); pdf.add_page(); pdf.set_font("Droid", size=9)
W = pdf.w - 2 * pdf.l_margin
for ln in open(MD, encoding="utf-8"):
    s = ln.rstrip()
    if not s: pdf.ln(3); continue
    if s.startswith("# "): pdf.ln(2); pdf.set_font("Droid", size=15); pdf.multi_cell(W, 8, s[2:]); pdf.set_font("Droid", size=9)
    elif s.startswith("## "): pdf.ln(2); pdf.set_font("Droid", size=12); pdf.multi_cell(W, 6, s[3:]); pdf.set_font("Droid", size=9)
    elif s.startswith("### "): pdf.ln(1); pdf.set_font("Droid", size=10); pdf.multi_cell(W, 5, s[4:]); pdf.set_font("Droid", size=9)
    elif s.startswith("> "): pdf.set_text_color(80,80,80); pdf.multi_cell(W, 5, s); pdf.set_text_color(0,0,0)
    elif s.startswith("|"): pdf.set_font("Droid", size=7); pdf.multi_cell(W, 4, s); pdf.set_font("Droid", size=9)
    else:
        c = re.sub(r"\*\*(.+?)\*\*", r"\1", s); c = re.sub(r"`([^`]+)`", r"\1", c)
        pdf.multi_cell(W, 5, c)
pdf.add_page(); pdf.set_font("Droid", size=14); pdf.cell(0, 10, "附录：关键图表", ln=1); pdf.ln(2); pdf.set_font("Droid", size=9)
for fig in sorted(glob.glob(os.path.join(FIG, "*.png"))):
    pdf.multi_cell(W, 5, os.path.basename(fig)); pdf.ln(1)
    try: pdf.image(fig, w=W * 0.82)
    except Exception as e: pdf.cell(0, 5, f"[err: {e}]", ln=1)
    pdf.ln(3)
out = os.path.join(HERE, "report_sim_v6.pdf"); pdf.output(out)
print("PDF:", out, os.path.getsize(out), "bytes")
