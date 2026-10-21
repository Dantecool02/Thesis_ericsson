"""Build the clean version of the thesis presentation on the official KTH template (Dec 2025).

Style: short titles, one idea per slide, a four-part breadcrumb, charts drawn as plain
shapes to scale. Every number comes from deck_data.json. The spoken script (about 25
minutes) is in the speaker notes, with time stamps computed from the word counts.
Writes ../Dante_Wesslund_Thesis_Presentation_v2_clean.pptx and ../Speaker_script_v2_clean.md.
"""
import copy
import json
import re
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE, PP_PLACEHOLDER
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

HERE = Path(__file__).resolve().parent
D = json.load(open(HERE / "deck_data.json"))
OUT = HERE.parent / "Dante_Wesslund_Thesis_Presentation_v2_clean.pptx"
SCRIPT = HERE.parent / "Speaker_script_v2_clean.md"
DATE = "2026-10-22"
FONT = "Figtree"
WPM = 135

NAVY, KTH, SKY, LIGHT, SAND = "000061", "004791", "6298D2", "DEF0FF", "EBE5E0"
GREY, LGREY, DGREY, MID, PALE = "A5A5A5", "E6E6E6", "323232", "595959", "C9CDD6"
GREEN, BRICK, WHITE = "4DA060", "E86A58", "FFFFFF"
TXT2 = "6B7280"
X0, W_FULL = 0.66, 12.02
ACTS = ("The problem", "The method", "The findings", "What it means")
MINUS = "−"

P, CMP, MC, TM = D["policies"], D["cmp"], D["mcnemar"], D["token_means"]
TOK = {k: P[k]["tokens_printed"] for k in P}
mb, tf, an, am, ty = P["modernbert"], P["tfidf"], P["always_naive"], P["always_mix"], P["type_only"]
CL, BT, CAS = D["classes"], D["by_type"], D["cascade"]

def rgb(h):
    return RGBColor.from_string(h)

def fmt_int(x):
    return f"{int(x):,}"

def sgn(x, nd=3):
    return f"{x:+.{nd}f}".replace("-", MINUS)

def pv(p):
    return "p < 0.001" if p < 0.001 else ("p = " + (f"{p:.3f}" if p < 0.2 else f"{p:.2f}"))

def curve_at(router, thr):
    return next(r for r in D["curves"][router] if abs(r["thr"] - thr) < 1e-6)

prs = Presentation(HERE / "kth_template_251203.pptx")
LAYOUT = {l.name.strip(): l for l in prs.slide_masters[0].slide_layouts}
sld = prs.slides._sldIdLst
for s_ in list(sld):
    prs.part.drop_rel(s_.rId)
    sld.remove(s_)

# ------------------------------------------------------------------------------------- helpers
SPOKEN = []  # (slide, title, body) for the main talk; stamped with times at the end

def add_footer(slide, footer_text=DATE, footer=True):
    for ph in slide.slide_layout.placeholders:
        t = ph.placeholder_format.type
        if t == PP_PLACEHOLDER.SLIDE_NUMBER or (footer and t == PP_PLACEHOLDER.FOOTER):
            slide.shapes._spTree.append(copy.deepcopy(ph._element))
    for ph in slide.placeholders:
        if ph.placeholder_format.type == PP_PLACEHOLDER.FOOTER:
            ph.text_frame.text = footer_text

def notes(slide, text, title=None):
    body = text.strip()
    if title:
        SPOKEN.append((slide, title, body))
    else:
        slide.notes_slide.notes_text_frame.text = body

def set_runs(tf_, paras, size=22, color=DGREY, bold=False, align=PP_ALIGN.LEFT, space_after=6, line=1.05):
    tf_.word_wrap = True
    first = True
    for para in paras:
        popt = para if isinstance(para, dict) else {"runs": para}
        runs = popt["runs"]
        if isinstance(runs, str):
            runs = [(runs, {})]
        p = tf_.paragraphs[0] if first else tf_.add_paragraph()
        first = False
        p.alignment = popt.get("align", align)
        p.space_after = Pt(popt.get("space_after", space_after))
        p.line_spacing = popt.get("line", line)
        if popt.get("bullet"):
            pPr = p._p.get_or_add_pPr()
            pPr.set("marL", str(Emu(Inches(0.36)))); pPr.set("indent", str(-Emu(Inches(0.36))))
            bc = etree.SubElement(pPr, qn("a:buClr")); sc = etree.SubElement(bc, qn("a:srgbClr")); sc.set("val", KTH)
            bf = etree.SubElement(pPr, qn("a:buFont")); bf.set("typeface", "Arial")
            bch = etree.SubElement(pPr, qn("a:buChar")); bch.set("char", "■")
        for t, o in runs:
            for k, part in enumerate(t.split("\v")):
                if k:
                    p.add_line_break()
                r = p.add_run(); r.text = part
                f = r.font
                f.name = FONT
                f.size = Pt(o.get("size", popt.get("size", size)))
                f.bold = o.get("bold", popt.get("bold", bold))
                f.italic = o.get("italic", False)
                f.color.rgb = rgb(o.get("color", popt.get("color", color)))
    return tf_

def text(slide, x, y, w, h, paras, anchor=MSO_ANCHOR.TOP, **kw):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf_ = tb.text_frame; tf_.vertical_anchor = anchor
    for side in ("left", "right", "top", "bottom"):
        setattr(tf_, f"margin_{side}", 0)
    set_runs(tf_, paras, **kw)
    return tb

def rect(slide, x, y, w, h, fill, line=None, radius=None, paras=None, anchor=MSO_ANCHOR.MIDDLE, pad=0.12, **kw):
    shape = MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if radius:
        s.adjustments[0] = radius
    if fill:
        s.fill.solid(); s.fill.fore_color.rgb = rgb(fill)
    else:
        s.fill.background()
    if line:
        s.line.color.rgb = rgb(line); s.line.width = Pt(1)
    else:
        s.line.fill.background()
    s.shadow.inherit = False
    tf_ = s.text_frame; tf_.vertical_anchor = anchor
    for side in ("left", "right", "top", "bottom"):
        setattr(tf_, f"margin_{side}", Inches(pad))
    if paras:
        set_runs(tf_, paras, **kw)
    return s

def oval(slide, cx, cy, d, fill, label=None, size=18, color=WHITE):
    s = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx - d / 2), Inches(cy - d / 2), Inches(d), Inches(d))
    s.fill.solid(); s.fill.fore_color.rgb = rgb(fill); s.line.fill.background(); s.shadow.inherit = False
    if label:
        tf_ = s.text_frame
        for side in ("left", "right", "top", "bottom"):
            setattr(tf_, f"margin_{side}", 0)
        tf_.vertical_anchor = MSO_ANCHOR.MIDDLE
        set_runs(tf_, [{"runs": label, "align": PP_ALIGN.CENTER, "size": size, "bold": True, "color": color, "space_after": 0}])
    return s

def line(slide, x1, y1, x2, y2, color=GREY, width=1.5, dash=None, arrow=False):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    c.line.color.rgb = rgb(color); c.line.width = Pt(width)
    ln = c.line._get_or_add_ln()
    if dash:
        pd = etree.SubElement(ln, qn("a:prstDash")); pd.set("val", dash)
    if arrow:
        te = etree.SubElement(ln, qn("a:tailEnd")); te.set("type", "triangle"); te.set("w", "med"); te.set("len", "med")
    return c

def actbar(slide, cur):
    runs = []
    for i, a in enumerate(ACTS):
        runs.append((a, {"bold": i == cur, "color": KTH if i == cur else "98A0AE"}))
        if i < len(ACTS) - 1:
            runs.append(("   ›   ", {"color": "C9CDD6"}))
    text(slide, 1.1, 0.4, 11.0, 0.38, [{"runs": runs, "size": 16}])

def content(title, act, lead=None):
    s = prs.slides.add_slide(LAYOUT["Headline only"])
    s.shapes.title.text_frame.text = title
    if act is not None:
        actbar(s, act)
    if lead:
        text(s, X0, 2.02, W_FULL, 0.5, [{"runs": lead, "size": 22, "color": DGREY}])
    add_footer(s)
    return s

def lead_runs(parts):
    """parts: list of (text, emphasised?)"""
    return [(t, {"bold": True, "color": KTH} if e else {}) for t, e in parts]

def vbars(s, x, y, w, h, items, vmax, ticks, tick_fmt, ylabel=None, chance=None, bar_w=1.35):
    """Vertical bar chart drawn with shapes. items: (label, value, color, ci or None, value_text)."""
    px0, px1 = x + 1.0, x + w
    base, top = y + h - 0.55, y + 0.45
    def vy(v):
        return base - (base - top) * v / vmax
    for t in ticks:
        line(s, px0, vy(t), px1, vy(t), "EEF0F3", 1)
        text(s, x, vy(t) - 0.16, 0.85, 0.32, [{"runs": tick_fmt(t), "size": 14, "color": "9AA3B2", "align": PP_ALIGN.RIGHT}])
    line(s, px0, base, px1, base, PALE, 1.25)
    if ylabel:
        tb = text(s, x - 0.9, y + h / 2 - 0.2, 2.0, 0.35, [{"runs": ylabel, "size": 15, "color": TXT2, "align": PP_ALIGN.CENTER}])
        tb.rotation = -90
    n = len(items)
    slot = (px1 - px0) / n
    for i, (lab, v, col, ci, vt) in enumerate(items):
        cx = px0 + slot * (i + 0.5)
        rect(s, cx - bar_w / 2, vy(v), bar_w, base - vy(v), col)
        ytop = vy(v)
        if ci:
            lo, hi = ci
            line(s, cx, vy(hi), cx, vy(lo), "1F2A44", 2)
            line(s, cx - 0.12, vy(hi), cx + 0.12, vy(hi), "1F2A44", 2)
            line(s, cx - 0.12, vy(lo), cx + 0.12, vy(lo), "1F2A44", 2)
            ytop = vy(hi)
        text(s, cx - 1.0, ytop - 0.45, 2.0, 0.4, [{"runs": vt, "size": 20, "bold": True, "color": "1F2A44", "align": PP_ALIGN.CENTER}])
        text(s, cx - 1.3, base + 0.1, 2.6, 0.4, [{"runs": lab, "size": 18, "color": "000000", "align": PP_ALIGN.CENTER}])
    if chance is not None:
        cv, clab = chance
        line(s, px0, vy(cv), px1, vy(cv), BRICK, 2, dash="dash")
        text(s, px1 - 1.6, vy(cv) - 0.38, 1.6, 0.32, [{"runs": clab, "size": 15, "color": BRICK, "align": PP_ALIGN.RIGHT}])
    return vy

def hpanel(s, x, y, w, title, note, rows, vmax, fmt, row_h=0.72, sig=None):
    text(s, x, y, w, 0.42, [{"runs": title, "size": 22, "bold": True, "color": KTH}])
    text(s, x, y + 0.42, w, 0.32, [{"runs": note, "size": 15, "color": TXT2}])
    yy = y + 0.95
    bar_max = w - 1.6
    for lab, v, col in rows:
        text(s, x, yy, w, 0.3, [{"runs": lab, "size": 17, "color": "333333"}])
        bw = max(0.06, bar_max * v / vmax)
        rect(s, x, yy + 0.32, bw, 0.28, col, radius=0.15)
        text(s, x + bw + 0.12, yy + 0.28, 1.5, 0.34, [{"runs": fmt(v), "size": 17, "bold": True, "color": "1F2A44"}])
        yy += row_h
    if sig:
        stxt, strong = sig
        text(s, x, yy + 0.05, w, 0.35, [{"runs": stxt, "size": 16, "bold": strong, "color": KTH if strong else TXT2}])

def bullets(s, items, y=2.3, size=24):
    paras = []
    for head, body in items:
        paras.append({"runs": [(head + "  ", {"bold": True, "color": KTH}), (body, {})], "size": size, "bullet": True, "space_after": 26, "line": 1.1})
    text(s, X0, y, W_FULL, 4.4, paras)

def cards(s, items, y=2.15, ch=2.05, body_size=19):
    cw = 5.86
    for i, (h_, b_) in enumerate(items):
        r_, c_ = divmod(i, 2)
        rect(s, X0 + c_ * (cw + 0.3), y + r_ * (ch + 0.3), cw, ch, LIGHT, radius=0.05, anchor=MSO_ANCHOR.TOP, pad=0.28,
             paras=[{"runs": h_, "size": 24, "bold": True, "color": KTH, "space_after": 8}, {"runs": b_, "size": body_size, "color": "333333", "line": 1.1}])

def table(slide, x, y, w, h, data, col_w, size=16, hl_rows=()):
    rows_n, cols_n = len(data), len(data[0])
    gt = slide.shapes.add_table(rows_n, cols_n, Inches(x), Inches(y), Inches(w), Inches(h))
    tbl = gt.table
    sid = tbl._tbl.tblPr.find(qn("a:tableStyleId"))
    if sid is not None:
        sid.text = "{5940675A-B579-460E-94D1-54222C63F5DA}"
    for i, cw in enumerate(col_w):
        tbl.columns[i].width = Inches(cw)
    for r in range(rows_n):
        tbl.rows[r].height = Inches(h / rows_n)
        for c in range(cols_n):
            cell = tbl.cell(r, c)
            cell.margin_left, cell.margin_right = Inches(0.15), Inches(0.1)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            cell.fill.fore_color.rgb = rgb(KTH if r == 0 else (LIGHT if r in hl_rows else WHITE))
            p = cell.text_frame.paragraphs[0]; p.text = ""
            run = p.add_run(); run.text = str(data[r][c])
            run.font.name = FONT
            run.font.size = Pt(size); run.font.bold = r == 0 or r in hl_rows
            run.font.color.rgb = rgb(WHITE if r == 0 else DGREY)
            p.alignment = PP_ALIGN.LEFT if c == 0 else PP_ALIGN.CENTER
            cell.text_frame.word_wrap = True

def roadmap(s, cy, sq=0.5, size=19):
    cx0, cx1 = X0 + 1.3, X0 + W_FULL - 1.3
    line(s, cx0, cy, cx1, cy, "D7DBE2", 2)
    for i, lab in enumerate(ACTS):
        cx = cx0 + (cx1 - cx0) * i / 3
        rect(s, cx - sq / 2, cy - sq / 2, sq, sq, KTH, radius=0.12, paras=[{"runs": str(i + 1), "align": PP_ALIGN.CENTER, "size": 20, "bold": True, "color": WHITE, "space_after": 0}], pad=0)
        text(s, cx - 1.4, cy + sq / 2 + 0.12, 2.8, 0.4, [{"runs": lab, "size": size, "align": PP_ALIGN.CENTER, "color": "000000"}])

# ============================================================================== 1 title
s = prs.slides.add_slide(LAYOUT["Title, KTH blue"])
t = s.shapes.title
t.text_frame.text = "Adaptive Hybrid\vRetrieval-Augmented Generation"
t.left, t.top, t.width, t.height = Inches(1.85), Inches(3.15), Inches(9.62), Inches(1.85)
for ph in s.placeholders:
    if ph.placeholder_format.idx == 1:
        ph.text_frame.text = f"Dante Wesslund  ·  {DATE}"
        ph.left, ph.top, ph.width, ph.height = Inches(2.33), Inches(6.12), Inches(8.67), Inches(0.51)
text(s, 2.4, 5.2, 8.53, 0.78, [{"runs": "Optimizing the computational cost-performance trade-off", "align": PP_ALIGN.CENTER, "size": 20, "color": WHITE, "space_after": 0},
                               {"runs": "via learned query routing", "align": PP_ALIGN.CENTER, "size": 20, "color": WHITE}])
text(s, 2.4, 6.72, 8.53, 0.6, [{"runs": "Examiner: Pawel Herman  ·  Supervisors: Arvid Eriksson (KTH), Peng Zhang (Ericsson)", "align": PP_ALIGN.CENTER, "size": 14, "color": "DEF0FF", "space_after": 0},
                               {"runs": "DA233X Degree Project, Machine Learning  ·  In collaboration with Ericsson", "align": PP_ALIGN.CENTER, "size": 14, "color": "DEF0FF"}])
notes(s, """
Hello everyone, and thank you for coming.
My name is Dante Wesslund, and this is my master's thesis, Adaptive Hybrid Retrieval-Augmented Generation, which I did in collaboration with Ericsson. I would like to begin by thanking my supervisors, Arvid Eriksson at KTH and Peng Zhang at Ericsson, and my examiner, Pawel Herman.
This thesis is about optimizing cost in a Hybrid RAG system. I train a classifier that, based on the question text alone, predicts which RAG method should be used.
""", "Title")

# ============================================================================== 2 in short
s = prs.slides.add_slide(LAYOUT["Headline only"])
s.shapes.title.text_frame.text = "In short"
add_footer(s)
text(s, X0, 2.15, 11.4, 1.2, [{"runs": [("Route before you retrieve. ", {"bold": True, "color": KTH}),
                                        ("The question alone often tells you whether the expensive retrieval is needed.", {"color": "1F2A44"})], "size": 32, "line": 1.1}])
stats = ((f"{mb['time_saving']*100:.0f}%", "less time than always using Mix"),
         (f"{mb['token_saving']*100:.0f}%", "fewer tokens"),
         (f"{mb['retention']*100:.0f}%", "of correct answers kept"))
for i, (num, lab) in enumerate(stats):
    x = X0 + i * 4.05
    text(s, x, 3.6, 3.85, 0.75, [{"runs": num, "size": 48, "bold": True, "color": KTH, "space_after": 0}])
    text(s, x, 4.38, 3.85, 0.4, [{"runs": lab, "size": 18, "color": TXT2}])
roadmap(s, 5.6)
notes(s, f"""
Here is the whole talk in one line: route before you retrieve. For many questions, the question itself tells you whether the expensive retrieval is needed.
In my experiments, routing with a fine-tuned classifier cut the mean time per question by {mb['time_saving']*100:.0f} percent, and the token usage by {mb['token_saving']*100:.0f} percent, compared with always using the expensive mode. And it kept about {mb['retention']*100:.0f} percent of the correct answers.
For the rest of the talk, we will go through the following four parts: the problem, the method, the findings, and what they mean.
""", "In short")

# ============================================================================== 3 RAG
s = content("Retrieval-augmented generation", 0)
boxes = (("question", LIGHT, "000000", 2.0), ("search the documents", "1F2A44", WHITE, 3.0), ("language model", LIGHT, "000000", 2.6), ("answer", LIGHT, "000000", 1.8))
gap = 0.55
total = sum(b[3] for b in boxes) + gap * 3
xx = X0 + (W_FULL - total) / 2
for i, (lab, fill, col, w) in enumerate(boxes):
    rect(s, xx, 3.0, w, 1.1, fill, line=None if fill == "1F2A44" else "D7DBE2", radius=0.1,
         paras=[{"runs": lab, "align": PP_ALIGN.CENTER, "size": 24, "bold": fill == "1F2A44", "color": col, "space_after": 0}])
    if i < 3:
        line(s, xx + w + 0.08, 3.55, xx + w + gap - 0.08, 3.55, "9AA3B2", 2, arrow=True)
    xx += w + gap
text(s, X0, 4.85, W_FULL, 0.7, [{"runs": lead_runs([("The answer is only as good as ", False), ("what the search finds", True), (".", False)]), "size": 32, "align": PP_ALIGN.CENTER, "color": "1F2A44"}])
notes(s, """
So, let us get started on the details. First of all, the setting. Retrieval-augmented generation, RAG for short, is a standard way to build question answering over private documents. Instead of trusting what a language model memorised during training, you first search a document collection for context that looks relevant, and the model answers based on that context.
This matters for a company like Ericsson, whose internal technical documentation cannot be assumed to be in any public model's training data.
The key point for this talk is the following: the answer can only be as good as the context the retrieval system provides to the language model. Hence, what method you use to provide that context matters, and different ways of searching cost very different amounts of compute.
""", "Retrieval-augmented generation")

# ============================================================================== 4 two modes
s = content("Two ways to search", 0)
for j, (name, sub, mode) in enumerate((("Naive", "vector search only", "naive"), ("Mix", "vector search + knowledge graph", "mix"))):
    x = X0 + j * 6.2
    text(s, x, 2.15, 5.6, 0.5, [{"runs": name, "size": 30, "bold": True, "color": KTH if j == 0 else NAVY, "space_after": 0}])
    text(s, x, 2.7, 5.6, 0.4, [{"runs": sub, "size": 18, "color": TXT2}])
    qx, qy = x + 0.45, 4.15
    oval(s, qx, qy, 0.62, KTH, "Q", 18)
    if mode == "naive":
        for k, yy in enumerate((3.35, 3.95, 4.55)):
            line(s, qx + 0.31, qy, x + 2.2, yy + 0.25, "9AA3B2", 1.75)
            rect(s, x + 2.2, yy, 2.6, 0.5, LIGHT, line="D7DBE2", radius=0.15, paras=[{"runs": "similar text", "align": PP_ALIGN.CENTER, "size": 15, "color": MID, "space_after": 0}], pad=0.02)
    else:
        for yy in (3.4, 4.4):
            line(s, qx + 0.31, qy, x + 1.6, yy + 0.25, "9AA3B2", 1.75)
            rect(s, x + 1.6, yy, 1.5, 0.5, LIGHT, line="D7DBE2", radius=0.15, paras=[{"runs": "text", "align": PP_ALIGN.CENTER, "size": 15, "color": MID, "space_after": 0}], pad=0.02)
        n1, n2, n3 = (x + 3.6, 3.65), (x + 4.55, 4.15), (x + 3.6, 4.65)
        for a_, b_ in ((n1, n2), (n2, n3), (n1, n3)):
            line(s, a_[0], a_[1], b_[0], b_[1], NAVY, 2.25)
        line(s, x + 3.1, 3.65, n1[0], n1[1], NAVY, 2.25)
        line(s, x + 3.1, 4.65, n3[0], n3[1], NAVY, 2.25)
        for nx, ny in (n1, n2, n3):
            oval(s, nx, ny, 0.3, NAVY)
        text(s, x + 4.8, 4.0, 1.2, 0.35, [{"runs": "graph", "size": 15, "color": NAVY}])
    cost_t = an["mean_time"] if j == 0 else am["mean_time"]
    cost_k = TM["naive"] if j == 0 else TM["mix"]
    text(s, x, 5.3, 5.8, 0.5, [{"runs": [(f"{cost_t:.1f} s", {"bold": True, "color": "1F2A44"}), (" per question   ·   ", {"color": MID}),
                                         (f"≈{fmt_int(round(cost_k, -2))}", {"bold": True, "color": "1F2A44"}), (" tokens", {"color": MID})], "size": 22}])
text(s, X0, 6.15, W_FULL, 0.5, [{"runs": lead_runs([("Mix can connect facts across documents, at ", False), (f"{am['mean_time']/an['mean_time']:.1f}× the time", True),
                                                   (" and ", False), (f"{TM['mix']/TM['naive']:.0f}× the tokens", True), (".", False)]), "size": 22}])
notes(s, f"""
In this thesis I worked with LightRAG, an open-source RAG framework that offers two kinds of search over the same documents.
Naive mode is plain vector search: it turns the question into a vector and returns the chunks of text most similar to it. It is fast and cheap, and works well when a few chunks of context hold the entire answer. However, it works badly on multi-hop questions, where the answer has to be pieced together from several documents that each may not look much like the question on their own.
Mix mode enhances Naive search by also using a knowledge graph of entities and their relations, built from the documents in advance. That lets it connect facts that sit in different documents, which is exactly what multi-hop questions need.
The price is cost. On the test questions, Mix took {am['mean_time']:.1f} seconds per question against {an['mean_time']:.1f} for Naive, about {am['mean_time']/an['mean_time']:.1f} times longer. And it used about {TM['mix']/TM['naive']:.0f} times as many tokens, which is the main measurement for cost in this setting. Building the graph is also a one-off cost up front, which is significantly more expensive compared to creating the vector database required for vector search. My thesis is about the cost paid on every single question.
[pause] So the obvious move, always using Mix to be safe, is expensive.
""", "Two ways to search")

# ============================================================================== 5 examples
s = content("Some questions need Mix", 0)
text(s, X0, 2.02, W_FULL, 0.5, [{"runs": lead_runs([(f"Of {fmt_int(D['n_judged'])} judged questions, Mix was needed on only ", False), (str(CL['mix_required']), True), (".", False)]), "size": 22}])
OK_, BAD_ = "2E7D45", "C0392B"
rows_ = (("Which film came out first,\vThe Love Route or Engal Aasan?", (("Naive correct", OK_), ("Mix correct", OK_)), "Naive is enough", False),
         ("When was the director of the film\vPrivate Hell 36 born?", (("Naive not enough", BAD_), ("Mix correct", OK_)), "needs Mix", True))
yy = 2.85
for q, pills, verdict, strong in rows_:
    line(s, X0, yy - 0.12, X0 + W_FULL, yy - 0.12, "EBEDF1", 1)
    text(s, X0, yy + 0.08, 5.65, 1.0, [{"runs": q, "size": 22, "color": "000000", "line": 1.1}])
    px = 5.95
    for lab, col in pills:
        rect(s, px, yy + 0.16, 2.15, 0.5, col, radius=0.5, paras=[{"runs": lab, "align": PP_ALIGN.CENTER, "size": 15, "bold": True, "color": WHITE, "space_after": 0}], pad=0.02)
        px += 2.3
    text(s, 10.55, yy + 0.2, 2.13, 0.45, [{"runs": verdict, "size": 19, "bold": strong, "color": NAVY if strong else MID}])
    yy += 1.35
text(s, X0, 5.7, W_FULL, 0.8, [{"runs": "Naive found the director, Don Siegel, but not his birth date. Mix answered: October 26, 1912.", "size": 19, "color": MID}])
notes(s, f"""
Here are two real questions from my runs that show the difference between the modes.
The first one compares two films that are both named in the question. Each film has its own document with its release date, and thus plain vector search finds both and answers correctly.
The second one is a two-hop question: you first have to find who directed the film, and then when that director was born. Naive search found the film's page and even the director's name, but the birth date sits in a different document that does not look like the question. So Naive could not answer, while Mix got both the director and the birth date right. This example motivates the need for Mix retrieval for some questions.
And here is the motivating number: of the {fmt_int(D['n_judged'])} benchmark questions I ran through both modes, Mix was actually needed on only {CL['mix_required']}, about one in six. I will show how those were labelled in a moment, but the important takeaway is that always paying for Mix leads to a lot of wasted compute.
""", "Some questions need Mix")

# ============================================================================== 6 idea
s = content("Query routing", 0)
rect(s, X0 + 0.3, 3.3, 2.1, 0.9, LIGHT, line="D7DBE2", radius=0.1, paras=[{"runs": "question", "align": PP_ALIGN.CENTER, "size": 24, "color": "000000", "space_after": 0}])
line(s, X0 + 2.5, 3.75, X0 + 3.4, 3.75, "9AA3B2", 2, arrow=True)
rect(s, X0 + 3.5, 3.05, 3.0, 1.4, "1F2A44", radius=0.1, paras=[{"runs": "router", "align": PP_ALIGN.CENTER, "size": 30, "bold": True, "color": WHITE, "space_after": 2},
                                                               {"runs": "small classifier", "align": PP_ALIGN.CENTER, "size": 16, "color": "C9D3E6", "space_after": 0},
                                                               {"runs": "no LLM call", "align": PP_ALIGN.CENTER, "size": 16, "color": "C9D3E6", "space_after": 0}])
line(s, X0 + 6.6, 3.45, X0 + 7.9, 2.75, "9AA3B2", 2, arrow=True)
line(s, X0 + 6.6, 4.05, X0 + 7.9, 4.75, "9AA3B2", 2, arrow=True)
rect(s, X0 + 8.0, 2.3, 2.9, 0.95, LIGHT, line="D7DBE2", radius=0.1, paras=[{"runs": [("Naive", {"bold": True, "color": KTH}), ("   cheap", {"color": MID, "size": 18})], "align": PP_ALIGN.CENTER, "size": 26, "space_after": 0}])
rect(s, X0 + 8.0, 4.3, 2.9, 0.95, LIGHT, line="D7DBE2", radius=0.1, paras=[{"runs": [("Mix", {"bold": True, "color": NAVY}), ("   expensive", {"color": MID, "size": 18})], "align": PP_ALIGN.CENTER, "size": 26, "space_after": 0}])
text(s, X0, 5.6, W_FULL, 0.7, [{"runs": lead_runs([("Decide from the ", False), ("question alone", True), (", before paying for retrieval.", False)]), "size": 32, "align": PP_ALIGN.CENTER, "color": "1F2A44"}])
text(s, X0, 6.5, W_FULL, 0.35, [{"runs": "Related: Adaptive-RAG (Jeong et al., 2024), RouterBench (Hu et al., 2024)", "size": 15, "color": TXT2, "align": PP_ALIGN.CENTER}])
notes(s, """
So the idea of this thesis is to put a router in front of retrieval. This router is a small text classifier which reads only the question text as input to its routing decision. It then sends the question to either Naive or Mix depending on the router's prediction.
Why only the question? Because the point is to decide before any retrieval cost is paid.
This has relatives in the literature. Adaptive-RAG is a paper which uses a small classifier to decide how much retrieval a question needs, and RouterBench is another paper which looks at routing between cheap and expensive language models. What I had not seen is routing between a vector mode and a graph mode inside one framework, based on the question alone.
[pause] So the open question becomes: is the need for Mix visible in how a question is phrased?
""", "Query routing")

# ============================================================================== 7 RQ
s = content("Research question", 0)
text(s, X0, 2.2, 11.6, 2.0, [{"runs": [("Within one Hybrid RAG system, how well can a ", {}), ("lightweight classifier", {"bold": True, "color": KTH}),
                                       (" predict from the question alone whether the cheap retrieval mode is enough, and how much ", {}),
                                       ("cost", {"bold": True, "color": KTH}), (" does routing with it save?", {})], "size": 26, "color": "1F2A44", "line": 1.15}])
for i, (lab, body) in enumerate((("Prediction.", "ModernBERT vs a TF-IDF baseline and a question-type rule"),
                                 ("Cost.", "Time and tokens saved vs always using Mix"))):
    yy = 4.45 + i * 0.85
    rect(s, X0, yy, 0.52, 0.52, KTH, radius=0.12, paras=[{"runs": str(i + 1), "align": PP_ALIGN.CENTER, "size": 20, "bold": True, "color": WHITE, "space_after": 0}], pad=0)
    text(s, X0 + 0.75, yy + 0.04, 11.0, 0.5, [{"runs": [(lab + " ", {"bold": True, "color": KTH}), (body, {"color": "333333"})], "size": 22}])
notes(s, """
Now onto the research question, which is the following: within one Hybrid RAG system, how well can a lightweight classifier predict from the question alone whether the cheap retrieval mode is enough, and how much cost does routing with it save? [pause, 2 s]
It then splits into two parts. First, about the prediction: how does a fine-tuned ModernBERT classifier compare with a simple TF-IDF baseline, and with a simple rule that uses the question-type label each benchmark question comes with? Secondly, about the cost: how much time and how many tokens does routing save compared with always using Mix? And here I also estimate what it risks in answer quality.
So, I evaluate the routers both as classifiers and as routing policies.
""", "Research question")

# ============================================================================== 8 labels
s = content("Building the labels", 1)
steps = ((f"{fmt_int(D['n_judged'])} questions", LIGHT, "000000", 2.75), ("run Naive and Mix", LIGHT, "000000", 2.8), ("LLM judge", "1F2A44", WHITE, 2.2), ("label", LIGHT, "000000", 1.5))
gap = 0.55
total = sum(b[3] for b in steps) + gap * 3
xx = X0 + (W_FULL - total) / 2
for i, (lab, fill, col, w) in enumerate(steps):
    rect(s, xx, 2.2, w, 0.8, fill, line=None if fill == "1F2A44" else "D7DBE2", radius=0.1,
         paras=[{"runs": lab, "align": PP_ALIGN.CENTER, "size": 21, "bold": fill == "1F2A44", "color": col, "space_after": 0}])
    if i < 3:
        line(s, xx + w + 0.08, 2.6, xx + w + gap - 0.08, 2.6, "9AA3B2", 2, arrow=True)
    xx += w + gap
tot = D["n_judged"]
xx = X0
for n_, fill, col, lab in ((CL["naive_enough"], LIGHT, "1F2A44", "Naive enough"), (CL["mix_required"], NAVY, WHITE, "Mix"), (CL["none_enough"], LGREY, DGREY, "neither correct")):
    w = W_FULL * n_ / tot
    rect(s, xx, 3.6, w - 0.04, 1.0, fill, line="C9D3E6" if fill == LIGHT else None,
         paras=[{"runs": [(f"{n_}  ", {"bold": True, "size": 24}), (lab, {"size": 19})], "color": col, "space_after": 0}], pad=0.18)
    xx += w
text(s, X0, 5.0, W_FULL, 1.0, [{"runs": lead_runs([("Label = the ", False), ("cheapest mode that was enough", True), (f". The {fmt_int(D['n_binary'])} questions where at least one mode worked are used.", False)]), "size": 22}])
notes(s, f"""
Let us now talk about the labels. In order to train a router, I need labels for the classification training, so this is how I made them.
I took {fmt_int(tot)} questions from 2WikiMultihopQA, a public benchmark where answering usually requires combining several documents. I indexed their documents in LightRAG and ran every question through both Naive and Mix.
Then a language model acting as a judge, Gemini 3 Flash in this case, looked at each question, the benchmark's correct answer, and the two candidate answers, and decided which mode was enough. Giving the judge the correct answer turns it into a comparison against a reference, which is much more reliable than open-ended grading. And when both answers are right, it is told to pick Naive, so the label is the cheapest mode that was enough.
The result: {CL['naive_enough']} questions were labelled as Naive enough, {CL['mix_required']} as Mix, and {CL['none_enough']} as neither correct. Those last ones are excluded, because when both modes fail, choosing between them cannot help. That leaves {fmt_int(D['n_binary'])} labelled questions.
One caveat, which I will return to under the limitations segment, is that these are judged labels, not ground truth.
""", "Building the labels")

# ============================================================================== 9 setup
s = content("The setup", 1)
cards(s, (("Data", f"{fmt_int(D['n_binary'])} labelled questions from 2WikiMultihopQA, split {D['split_n']['train']} / {D['split_n']['validation']} / {D['split_n']['test']} for training, validation and test."),
          ("Retrieval", "LightRAG: Naive and Mix on one index. Gemini writes and judges the answers."),
          ("Routers", "TF-IDF with logistic regression as the baseline, and a fine-tuned ModernBERT: three training runs, scores averaged."),
          ("Evaluation", f"On the {D['n_test']} test questions: prediction quality and routing cost. Paired bootstrap and permutation tests, Holm-corrected.")))
notes(s, f"""
The setup for this thesis, in four parts, is the following.
Data: the {fmt_int(D['n_binary'])} labelled questions, split into {D['split_n']['train']} for training, {D['split_n']['validation']} for validation and {D['split_n']['test']} for the test, with the same stratification of question types and labels in every split.
Retrieval is as before: LightRAG's two modes, with Gemini writing and judging the answers.
The routers both see only the question text. The baseline is TF-IDF with logistic regression, which looks at which words and word pairs appear. It tells us how much of the signal is plain vocabulary. The main model is ModernBERT, a modern pretrained text encoder. I fine-tuned it three times with different random seeds and averaged their scores into one router, so the result does not hang on one lucky run.
Each router outputs a score and sends the question to Mix above a decided threshold. For both, I chose that threshold by the same rule on the validation set, best F1 score, a score that balances catching Mix-needing questions against false alarms, and froze it before touching the test set. So the test compares the two routers as they would actually be deployed.
For the evaluation, I used the {D['n_test']} test questions and looked at how well each router predicts the label, and what routing with it would have cost.
""", "The setup")

# ============================================================================== 10 AUPRC
s = content("Can the question predict it?", 2)
text(s, X0, 2.02, W_FULL, 0.5, [{"runs": lead_runs([("Yes, partly. Both routers find the Mix-needing questions ", False), ("far above chance", True), (".", False)]), "size": 22}])
text(s, X0, 2.55, 11.5, 0.32, [{"runs": f"Test set: {D['n_test']} questions, {D['n_pos']} need Mix. Whiskers: 95% bootstrap intervals.", "size": 15, "color": TXT2, "align": PP_ALIGN.RIGHT}])
mg = D["marginal"]
vbars(s, X0 + 0.9, 2.65, 10.6, 4.2,
      (("TF-IDF", CMP["auprc"]["tfidf"], SKY, (mg["tfidf_baseline"]["auprc"]["lo"], mg["tfidf_baseline"]["auprc"]["hi"]), f"{CMP['auprc']['tfidf']:.3f}"),
       ("ModernBERT", CMP["auprc"]["modernbert"], KTH, (mg["modernbert_ensemble"]["auprc"]["lo"], mg["modernbert_ensemble"]["auprc"]["hi"]), f"{CMP['auprc']['modernbert']:.3f}")),
      1.0, (0, 0.25, 0.5, 0.75, 1.0), lambda t: f"{t:.2f}", ylabel="AUPRC", chance=(0.254, "chance 0.254"), bar_w=1.6)
ad = CMP["auprc"]
notes(s, f"""
Now the findings, starting with prediction. Two terms first. Precision: which is, when a router says Mix, how often it is right. And recall, which measures, of the questions that need Mix, how many it actually catches.
The main metric is AUPRC, the area under the precision-recall curve for the Mix-needing class. In plain words: if you sort the questions by the router's score, how high up do the Mix-needing ones end up? I use it rather than accuracy because only a quarter of the questions need Mix, so a router that always says Naive already gets 75 percent accuracy and is useless.
Guessing at random gives 0.254 AUPRC, the share of Mix-needing questions. That is the red dashed line in this figure. TF-IDF reaches {ad['tfidf']:.2f} and ModernBERT {ad['modernbert']:.2f}, roughly three times chance, and the 95 percent bootstrap intervals sit far above the line. AUROC, the other standard ranking metric, tells the same story, at about 0.9 for both. [pause, 2 s]
So the first answer is: yes, partly. Whether a question needs Mix is visible in how it is phrased. ModernBERT is ahead here, but the paired interval for the difference still includes zero, so that gap is not resolved. Where the two routers really differ is on the next slide.
""", "Can the question predict it?")

# ============================================================================== 11 precision vs recall
s = content("More selective", 2)
text(s, X0, 2.02, W_FULL, 0.8, [{"runs": lead_runs([("ModernBERT is ", False), ("significantly more precise and more accurate", True), (". Recall, F1 and the ranking metrics are not resolved.", False)]), "size": 22, "line": 1.1}])
base, top = 6.05, 3.15
def vy(v):
    return base - (base - top) * v
line(s, X0 + 1.5, base, X0 + 10.5, base, PALE, 1.25)
for g, (name, k, sig) in enumerate((("Precision", "precision_mix", True), ("Recall", "recall_mix", False))):
    gx = X0 + 2.4 + g * 4.4
    for j, (lab, col) in enumerate((("tfidf", SKY), ("modernbert", KTH))):
        v = CMP[k][lab]
        bx = gx + j * 1.45
        rect(s, bx, vy(v), 1.25, base - vy(v), col)
        text(s, bx - 0.3, vy(v) - 0.45, 1.85, 0.4, [{"runs": f"{v:.2f}", "size": 20, "bold": True, "color": "1F2A44", "align": PP_ALIGN.CENTER}])
    text(s, gx - 0.5, base + 0.08, 3.7, 0.4, [{"runs": name, "size": 20, "color": "000000", "align": PP_ALIGN.CENTER}])
    hp = CMP[k]["perm_p_holm"]
    lab_ = f"significant, Holm {pv(hp)}" if sig else f"not significant, Holm {pv(hp)}"
    text(s, gx - 0.5, base + 0.45, 3.7, 0.35, [{"runs": lab_, "size": 16, "bold": sig, "color": KTH if sig else TXT2, "align": PP_ALIGN.CENTER}])
lx = X0 + 9.75
rect(s, lx, 3.3, 0.28, 0.28, SKY); text(s, lx + 0.4, 3.26, 1.8, 0.35, [{"runs": "TF-IDF", "size": 17, "color": "333333"}])
rect(s, lx, 3.8, 0.28, 0.28, KTH); text(s, lx + 0.4, 3.76, 2.0, 0.35, [{"runs": "ModernBERT", "size": 17, "color": "333333"}])
text(s, lx, 4.45, 2.27, 1.6, [{"runs": f"Paired tests on the same {D['n_test']} questions, Holm-corrected over 7 metrics.", "size": 15, "color": TXT2, "line": 1.1}])
cp, cr, ca = CMP["precision_mix"], CMP["recall_mix"], CMP["accuracy"]
notes(s, f"""
Both routers are scored on the same {D['n_test']} questions, so I compare them with paired bootstrapping and permutation tests, with a Holm correction because I test seven metrics at once. A difference counts as significant only if it is too large to be explained by chance, that is, by which questions happened to end up in the test set.
The clear difference is precision. When ModernBERT says Mix, it is right {cp['modernbert']*100:.0f} percent of the time, against {cp['tfidf']*100:.0f} for TF-IDF. That gap of {cp['diff']:.2f} is significant, with a corrected p below 0.001. Overall accuracy is also significantly higher, {ca['modernbert']:.2f} against {ca['tfidf']:.2f}.
On the other side, TF-IDF has the higher recall: it catches {cr['tfidf']*100:.0f} percent of the Mix-needing questions against {cr['modernbert']*100:.0f} for ModernBERT, because it sends more questions to Mix. That difference is not significant, and neither are the differences in AUPRC, AUROC and F1. With only {D['n_pos']} Mix-needing test questions, gaps this small could come from chance alone. So I read them as undecided, not as equal.
One caveat: precision depends on where the threshold sits. Both thresholds were set by the same rule on validation, so this compares the routers as they would be deployed.
[pause] In short: ModernBERT is the more selective router. I cannot claim it is better overall. So what is it actually picking up from the question?
""", "More selective")

# ============================================================================== 12 signal
s = content("Where the signal comes from", 2)
text(s, X0, 2.02, W_FULL, 0.5, [{"runs": lead_runs([("Largely ", False), ("question structure", True), (", recognised from the wording.", False)]), "size": 22}])
tn = (("comparison", "comparison"), ("compositional", "compositional"), ("bridge_comparison", "bridge-comparison"), ("inference", "inference"))
base, top = 5.75, 3.75
x_start = X0 + 0.2
text(s, x_start, 2.62, 8.2, 0.35, [{"runs": f"Share of the {fmt_int(D['n_binary'])} labelled questions that needed Mix, by type", "size": 17, "color": TXT2}])
line(s, x_start, base, x_start + 8.0, base, PALE, 1.25)
for i, (k, lab) in enumerate(tn):
    v = BT[k]["mix"] / BT[k]["n"]
    bx = x_start + 0.35 + i * 2.0
    h_ = (base - top) * v / 0.62
    rect(s, bx, base - h_, 1.2, h_, NAVY if k == "compositional" else PALE)
    text(s, bx - 0.4, base - h_ - 0.72, 2.0, 0.4, [{"runs": f"{v*100:.0f}%", "size": 20, "bold": True, "color": "1F2A44", "align": PP_ALIGN.CENTER, "space_after": 0},
                                                 {"runs": f"{BT[k]['mix']} of {BT[k]['n']}", "size": 14, "color": TXT2, "align": PP_ALIGN.CENTER}])
    text(s, bx - 0.5, base + 0.1, 2.2, 0.4, [{"runs": lab, "size": 17, "color": "000000", "align": PP_ALIGN.CENTER}])
vt, tp = D["vs_type_mb"], D["type_only_point"]
bx0, by0, bw0, bh0 = X0 + 8.6, 2.7, 3.42, 4.05
rect(s, bx0, by0, bw0, bh0, LIGHT, radius=0.05)
ix, iw = bx0 + 0.25, bw0 - 0.5
text(s, ix, by0 + 0.22, iw, 0.4, [{"runs": "Precision (test set)", "size": 18, "bold": True, "color": KTH}])
yy = by0 + 0.78
for lab, v, col in (("Question-type rule", tp["precision_mix"], GREY), ("TF-IDF", CMP["precision_mix"]["tfidf"], SKY), ("ModernBERT", CMP["precision_mix"]["modernbert"], KTH)):
    text(s, ix, yy, iw, 0.3, [{"runs": lab, "size": 16, "color": "333333"}])
    bw = (iw - 0.75) * v
    rect(s, ix, yy + 0.32, bw, 0.24, col, radius=0.15)
    text(s, ix + bw + 0.1, yy + 0.27, 0.7, 0.32, [{"runs": f"{v:.2f}", "size": 16, "bold": True, "color": "1F2A44"}])
    yy += 0.68
text(s, ix, yy + 0.08, iw, 1.0, [{"runs": "The rule needs a type label that real questions lack. Only ModernBERT is significantly above it.", "size": 14, "color": TXT2, "line": 1.1}])
notes(s, f"""
This chart shows how often each question type needed Mix. Comparison questions, like the film example, almost never did: {BT['comparison']['mix']} of {BT['comparison']['n']}. Compositional questions, like the director example, needed it {BT['compositional']['mix']/BT['compositional']['n']*100:.0f} percent of the time.
So a simple rule, use Mix if the question is compositional, already does well, but it uses a label the benchmark provides and real questions do not have. Its precision is {tp['precision_mix']:.2f}. TF-IDF, at {CMP['precision_mix']['tfidf']:.2f}, is not significantly different from that rule on any metric: from the vocabulary it essentially recovers the question type. ModernBERT, from the wording alone, is significantly more precise than the rule, at {CMP['precision_mix']['modernbert']:.2f}. Its F1 is not significantly higher than the rule's, and its recall is lower, also not significantly.
So the signal is largely question structure, plus some precision on top.
Now, what does that precision mean for the actual routing decisions?
""", "Where the signal comes from")

# ============================================================================== 13 errors
s = content("Routing errors", 2)
text(s, X0, 2.02, W_FULL, 0.5, [{"runs": "Far less wasted compute, for a small and unresolved increase in risk.", "size": 22}])
mo, mu = MC["mb_vs_tfidf_naive_rows(over_routing)"], MC["mb_vs_tfidf_mix_rows(recall)"]
hpanel(s, X0, 2.6, 5.6, "Unnecessary Mix calls", f"of {D['n_neg']} questions where Naive was enough",
       (("TF-IDF", tf["fp"], SKY), ("ModernBERT", mb["fp"], KTH)), 34, lambda v: str(int(v)), sig=(f"significant, McNemar {pv(mo['p_value'])}", True))
hpanel(s, X0 + 6.4, 2.6, 5.6, "Missed Mix calls", f"of {D['n_pos']} questions that needed Mix",
       (("TF-IDF", tf["fn"], SKY), ("ModernBERT", mb["fn"], KTH)), 34, lambda v: str(int(v)), sig=(f"not significant, McNemar {pv(mu['p_value'])}", False))
notes(s, f"""
Precision shows up directly in the routing decisions. There are two kinds of mistakes, and they matter differently.
On the left, we see unnecessary Mix calls, where Naive was enough but the router chose Mix anyway, which is a waste of compute. TF-IDF makes {tf['fp']} of these, while ModernBERT only makes {mb['fp']}. ModernBERT also avoids {mo['a_right_b_wrong']} of TF-IDF's mistakes while not making any new ones. A McNemar test, which looks only at the questions where the two routers disagree, here {mo['a_right_b_wrong']} against {mo['a_wrong_b_right']}, gives p below 0.001.
On the right, we see missed Mix calls, which is where the question needed Mix but went to Naive instead. Those are the dangerous ones, because the answer suffers. ModernBERT misses {mb['fn']} here, while TF-IDF only misses {tf['fn']}. The gap comes from just {mu['n_discordant']} questions where the routers disagree, and using McNemar we get a p-value of {mu['p_value']:.3f}, so it is not significant.
[pause] So overall, ModernBERT wastes much less compute, at the price of a small increase in risk that we cannot statistically confirm. Which of the two you would prefer depends on what a wasted Mix call costs, compared with a worse answer.
Now, what does this mean for cost?
""", "Routing errors")

# ============================================================================== 14 cost
s = content("Cost", 2)
text(s, X0, 2.02, W_FULL, 0.5, [{"runs": lead_runs([("ModernBERT routing: ", False), (f"{mb['time_saving']*100:.0f}% less time", True), (" and ", False),
                                                   (f"{mb['token_saving']*100:.0f}% fewer tokens", True), (" than always-Mix.", False)]), "size": 22}])
rt = D["routed_time_test"]
hpanel(s, X0, 2.6, 5.6, "Mean time per question", "measured on every test question",
       (("Always Mix", am["mean_time"], PALE), ("TF-IDF routing", tf["mean_time"], SKY), ("ModernBERT routing", mb["mean_time"], KTH), ("Always Naive", an["mean_time"], PALE)),
       27, lambda v: f"{v:.1f} s", row_h=0.74,
       sig=(f"ModernBERT vs TF-IDF: {abs(rt['diff_mean_seconds']):.1f} s faster, {pv(rt['perm_p'])}", True))
hpanel(s, X0 + 6.4, 2.6, 5.6, "Model tokens per question", f"estimated from {TM['n']} instrumented questions",
       (("Always Mix", TOK["always_mix"], PALE), ("TF-IDF routing", TOK["tfidf"], SKY), ("ModernBERT routing", TOK["modernbert"], KTH), ("Always Naive", TOK["always_naive"], PALE)),
       19800, lambda v: fmt_int(v), row_h=0.74)
notes(s, f"""
On the left, we see the mean time per question, measured on every test question. Always using Mix takes {am['mean_time']:.1f} seconds, while always using Naive takes {an['mean_time']:.1f} seconds. Routing with TF-IDF takes {tf['mean_time']:.0f} seconds, and routing with ModernBERT takes {mb['mean_time']:.1f} seconds, which is {mb['time_saving']*100:.0f} percent less than always using Mix. ModernBERT's routing is also significantly faster than TF-IDF's, by about {abs(rt['diff_mean_seconds']):.1f} seconds per question, which is because it makes far fewer unnecessary Mix calls.
On the right, we see tokens per question. ModernBERT routing uses under 7,000 tokens per question, compared to almost 18,000 for always-Mix, which is {mb['token_saving']*100:.0f} percent fewer tokens.
In other words: ModernBERT saves the most time and tokens out of the relevant routers.
""", "Cost")

# ============================================================================== 15 answers kept
s = content("Answers kept", 2)
text(s, X0, 2.02, W_FULL, 0.5, [{"runs": lead_runs([("About ", False), (f"{mb['retention']*100:.0f}% of the correct answers", True),
                                                   (f", at {TOK['modernbert']/TOK['always_mix']*100:.0f}% of the token cost.", False)]), "size": 22}])
hpanel(s, X0, 2.6, 8.2, "Share of always-Mix's correct answers kept", "assuming Mix is correct wherever Naive was",
       (("Always Mix", 100.0, PALE), ("TF-IDF routing", tf["retention"] * 100, SKY), ("ModernBERT routing", mb["retention"] * 100, KTH), ("Always Naive", an["retention"] * 100, PALE)),
       108, lambda v: f"{v:.1f}%", row_h=0.74)
notes(s, f"""
So, what do those savings cost in answer quality?
I did not re-judge the answers each routing policy would produce, so this relies on one explicit assumption: that Mix answers correctly whenever Naive does. Under that assumption, the only way routing loses an answer is by sending a Mix-needing question to Naive.
Then always-Mix keeps all its correct answers by definition, and always-Naive keeps {an['retention']*100:.1f} percent. ModernBERT routing keeps {mb['retention']*100:.1f} percent, at {TOK['modernbert']/TOK['always_mix']*100:.0f} percent of always-Mix's token cost. TF-IDF keeps a little more, {tf['retention']*100:.1f} percent, at about half the cost.
These shares cover the questions where at least one mode was right, about {D['n_binary']/D['n_judged']*100:.0f} percent of all judged questions. When both fail, routing only changes the cost, not the answer.
So roughly: you give up about eight percentage points of answers to save almost two thirds of the cost. [pause, 2 s] Whether that is worth it depends on the deployment.
""", "Answers kept")

# ============================================================================== 16 in practice
s = content("In practice", 3)
cards(s, (("Prior work", "Extends Adaptive-RAG to vector vs graph retrieval. As in RouterBench: most of the quality, a fraction of the cost."),
          ("Deployment", "No language-model call per question. The set-up cost is the labels. Needs a small labelled set from the target workload first."),
          ("A cost dial", "The threshold trades wasted Mix calls against missed ones. Each deployment sets its own."),
          ("Sustainability and ethics", "Fewer Mix calls should save energy (not measured). Monitor quality per question type, not just on average.")))
notes(s, f"""
So what does this mean in practice? Four points.
First, prior work. Adaptive-RAG showed that a small classifier can choose a retrieval strategy from the question, and my results show the idea carries over to choosing between a vector mode and a graph mode in one framework. As RouterBench found for language models, a simple router keeps most of the quality at a fraction of the cost.
Second, deployment. The router makes no language-model call per question. The real set-up cost is the labels, which need both modes and the judge once per training question. For Ericsson, real workloads probably contain more simple look-up questions than this multi-hop benchmark, so the savings could be larger. But their documents have no gold answers, so a small human-labelled set, or a judge that does not need gold answers, comes first.
Third, the threshold is a cost dial. Where a weak answer is expensive, you lower it and send more to Mix. Where compute is the constraint, you raise it.
Fourth, sustainability and ethics. Fewer Mix calls should mean less energy, which ties to the UN goal on responsible consumption, though I did not measure energy. And a router can serve some question types worse, like bridge-comparison here, so quality should be monitored per question type, not only on average.
""", "In practice")

# ============================================================================== 17 limitations
s = content("Limitations", 3)
bullets(s, (("Labels.", "An LLM judge decided which mode was enough, using the same Gemini model that wrote the answers, without a human check."),
            ("Estimates.", f"Tokens come from {TM['n']} instrumented questions, answers kept assume Mix is right wherever Naive was, and router time was not measured."),
            ("Scope.", f"One benchmark and one framework, a random split that can share question templates, and only {D['n_test']} test questions.")), y=2.3, size=24)
notes(s, f"""
I want to be clear about the limits.
Labels: they come from a language-model judge, and the same Gemini model both wrote and judged the answers, with no human checking a sample. Giving the judge the correct answer reduces the risk, but shared bias is possible.
Estimates: the token savings rest on {TM['n']} instrumented questions, the {mb['retention']*100:.0f} percent rests on the assumption I stated, and the router's own running time was not measured. The time saving, though, is measured on every test question.
Scope: one benchmark and one framework, chosen partly because, of the three benchmarks I piloted, it gave the least skewed labels, which may flatter the classifier, and only {D['n_test']} test questions, {D['n_pos']} of them needing Mix. That is enough to establish the precision difference, but not to resolve small differences in the ranking metrics. And because the split is random by row, similar question templates can appear in both training and test, so part of the predictability may be template recognition.
These do not change the main findings on this data, but they limit how far the numbers transfer, especially to a company setting.
""", "Limitations")

# ============================================================================== 18 future work
s = content("Future work", 3)
bullets(s, (("Check the labels.", "Validate a sample of judge decisions by hand, and judge again with a model from another family."),
            ("Measure everything.", "Log tokens for every question, time the router itself, and re-judge the answers each routing policy picks."),
            ("Go further.", "Other benchmarks and frameworks, a larger test set, and a second stage that escalates to Mix when Naive's retrieval looks weak.")), y=2.3, size=24)
notes(s, """
Each limitation has a matching next step.
First, check the labels: validate a sample of the judge's decisions by hand, and repeat the judging with a model from a different family, to measure how much the labels depend on the judge.
Second, measure everything: log tokens for every question instead of a sample, time the router itself, and re-judge the answers each routing policy actually picks, so the answer-quality estimate no longer needs an assumption.
Third, go further: other benchmarks and frameworks, a larger test set, and a second stage that runs only the cheap vector search, checks whether the retrieved text covers the question's entities, and escalates to Mix if not. That could recover answers the router misses.
The first two come first, because they strengthen the numbers I already have.
Before I conclude, one disclosure, as in Section 5.7 of the thesis: I used Codex and Claude Code as assistants, for wording and for drafting and debugging code, including analysis code and the scripts that build these slides. I reviewed and ran everything myself, every number comes from my own runs, and the research question, design and conclusions are mine. Let me close with the conclusions.
""", "Future work")

# ============================================================================== 19 conclusions
s = content("Conclusions", 3)
text(s, X0, 2.05, 11.6, 1.1, [{"runs": [("Route before you retrieve. ", {"bold": True, "color": KTH}),
                                        ("The question alone often tells you whether the expensive retrieval is needed.", {"color": "1F2A44"})], "size": 28, "line": 1.1}])
paras = []
for head, body in (("Prediction.", "Both routers find Mix-needing questions far above chance. At its chosen threshold, ModernBERT is significantly more precise than TF-IDF and the type rule."),
                   ("Cost.", f"{mb['time_saving']*100:.0f}% less time and an estimated {mb['token_saving']*100:.0f}% fewer tokens than always using Mix, keeping about {mb['retention']*100:.0f}% of correct answers, under an assumption."),
                   ("Scope.", "One benchmark and judged labels. Validate on real queries before deploying.")):
    paras.append({"runs": [(head + "  ", {"bold": True, "color": KTH}), (body, {})], "size": 22, "bullet": True, "space_after": 14, "line": 1.1})
text(s, X0, 3.4, W_FULL, 3.4, paras)
notes(s, f"""
To conclude, the two parts of the research question.
Prediction: yes, partly. From the question alone, both routers find the Mix-needing questions far above chance, and at the thresholds chosen on validation, ModernBERT is significantly more precise than both the TF-IDF baseline and the question-type rule. Whether it ranks questions better overall is not resolved at this test size.
Cost: routing with ModernBERT cuts the mean time per question by {mb['time_saving']*100:.0f} percent and the estimated tokens by {mb['token_saving']*100:.0f} percent compared with always using Mix, while keeping about {mb['retention']*100:.0f} percent of the correct answers, under the assumption I stated.
The scope is one benchmark with judged labels, so the router should be validated on real questions before it is deployed.
My contributions are three: a statistically tested study of query-only routing between a vector mode and a graph mode, an open and reproducible pipeline and judge-labelled dataset, and the finding that the encoder's advantage lies in precision, and so in cost, rather than in a demonstrably better ranking.
[pause] So, in one line: route before you retrieve. The question alone often tells you whether the expensive retrieval is needed.
""", "Conclusions")

# ============================================================================== 20 thank you
s = prs.slides.add_slide(LAYOUT["Title, navy blue"])
s.shapes.title.text_frame.text = "Thank you"
for ph in s.placeholders:
    if ph.placeholder_format.idx == 1:
        ph.text_frame.text = "Questions?"
text(s, 2.4, 6.78, 8.53, 0.4, [{"runs": "github.com/Dantecool02/Thesis_ericsson", "align": PP_ALIGN.CENTER, "size": 18, "color": "DEF0FF"}])
add_footer(s, footer=False)
notes(s, "Thank you for listening. I am happy to take your questions.", "Thank you")
THANKS = s
N_MAIN = len(prs.slides)

# ============================================================================== backups
s = content("Backup: statistics", None)
rows = [["Metric", "TF-IDF", "ModernBERT", "Difference [95% paired CI]", "Holm p"]]
for name, k in (("AUPRC", "auprc"), ("AUROC", "auroc"), ("Balanced accuracy", "balanced_accuracy"), ("Precision", "precision_mix"),
                ("Recall", "recall_mix"), ("F1", "f1_mix"), ("Accuracy", "accuracy")):
    c = CMP[k]; hp = c["perm_p_holm"]
    rows.append([name, f"{c['tfidf']:.3f}", f"{c['modernbert']:.3f}", f"{sgn(c['diff'])} [{sgn(c['diff_ci95'][0])}, {sgn(c['diff_ci95'][1])}]", "<0.001" if hp < 0.001 else f"{hp:.3f}"])
table(s, X0, 2.1, W_FULL, 3.8, rows, (2.8, 1.7, 1.9, 3.8, 1.82), size=17, hl_rows=(4, 7))
text(s, X0, 6.1, W_FULL, 0.6, [{"runs": f"{D['n_test']} test questions ({D['n_pos']} need Mix). Paired bootstrap (10,000 resamples), paired permutation tests, Holm correction over 7 metrics. Precision and accuracy are significant.", "size": 15, "color": TXT2}])
notes(s, f"Use for: 'Is ModernBERT actually better?' Precision and accuracy significant after Holm correction; the rest not resolved with {D['n_pos']} positives.")

s = content("Backup: cost and errors", None)
rows = [["Policy", "To Mix", "Mean time", "Est. tokens", "Missed Mix", "Unneeded Mix", "Answers kept"]]
PNAME = {"always_naive": "Always Naive", "type_only": "Question-type rule", "tfidf": "TF-IDF", "modernbert": "ModernBERT", "always_mix": "Always Mix"}
for k in ("always_naive", "type_only", "tfidf", "modernbert", "always_mix"):
    p = P[k]
    rows.append([PNAME[k], f"{p['mix_rate']*100:.1f}%", f"{p['mean_time']:.2f} s", fmt_int(TOK[k]), str(p["fn"]), str(p["fp"]), f"{p['retention']*100:.1f}%"])
table(s, X0, 2.1, W_FULL, 3.2, rows, (2.4, 1.2, 1.55, 1.6, 1.5, 1.9, 1.87), size=16, hl_rows=(4,))
text(s, X0, 5.55, W_FULL, 1.0, [{"runs": f"Time measured per question. Tokens from per-mode means over {TM['n']} instrumented questions ({fmt_int(TM['naive'])} Naive, {fmt_int(TM['mix'])} Mix). Answers kept assume Mix is correct wherever Naive was.", "size": 15, "color": TXT2}])
notes(s, "Use for: token-estimate questions, under- and over-routing, the answer-retention assumption.")

s = content("Backup: try Naive first?", None)
rows = [["Policy", "Mean time", "Est. tokens", "Answers kept"],
        ["ModernBERT router (question only)", f"{mb['mean_time']:.1f} s", fmt_int(TOK["modernbert"]), f"{mb['retention']*100:.1f}%"],
        ["Perfect cascade: Naive first, Mix only where needed", f"{CAS['mean_time']:.1f} s", fmt_int(round(CAS["mean_tokens"])), "100.0%"],
        ["Always Mix", f"{am['mean_time']:.1f} s", fmt_int(TOK["always_mix"]), "100.0%"]]
table(s, X0, 2.1, W_FULL, 2.6, rows, (6.2, 1.9, 1.9, 2.02), size=17, hl_rows=(1,))
text(s, X0, 4.95, W_FULL, 1.2, [{"runs": "A cascade pays for Naive on every question, and escalated questions pay for both modes. Estimated from measured times and per-mode token means; not part of the thesis.", "size": 17, "color": TXT2}])
notes(s, f"Use for: 'Why not run Naive first and escalate when it fails?' Even a perfect cascade averages {CAS['mean_time']:.1f} s against {mb['mean_time']:.1f} s, because it pays for Naive on every question and for both modes on escalated ones, and it needs a failure detector that does not exist yet. Say clearly this is a back-of-the-envelope estimate, not part of the thesis.")

s = content("Backup: the judge", None)
paras = [{"runs": [("naive_enough  ", {"bold": True, "color": KTH}), ("if the Naive answer already answers the question correctly.", {})], "size": 22, "bullet": True, "space_after": 10},
         {"runs": [("mix_required  ", {"bold": True, "color": KTH}), ("if Naive is not enough but the Mix answer is correct.", {})], "size": 22, "bullet": True, "space_after": 10},
         {"runs": [("none_enough  ", {"bold": True, "color": KTH}), ("if neither answer is enough.", {})], "size": 22, "bullet": True, "space_after": 22},
         {"runs": f"The judge sees the question, the benchmark's correct answer and both candidate answers. If both are correct it must choose Naive. Admissions of missing information count as not enough. Gemini, temperature 0, one fixed prompt for all {fmt_int(D['n_judged'])} questions.", "size": 19, "color": MID, "line": 1.1}]
text(s, X0, 2.2, W_FULL, 4.3, paras)
notes(s, "Use for: 'Can you trust the labels?' Judged supervision, not ground truth; the reference answer makes it a constrained comparison; same-model bias not measured; next step is a human-checked sample and a second judge family.")

s = content("Backup: threshold and cost", None)
t_tf, t_eq, t_mb = curve_at("tfidf", round(D["thr"]["tfidf"], 2)), curve_at("tfidf", 0.73), curve_at("modernbert", round(D["thr"]["modernbert"], 2))
rows = [["Router and threshold", "Mean time", "Precision", "Recall", "F1"]]
for lab, r in ((f"TF-IDF at {D['thr']['tfidf']:.2f}, chosen on validation", t_tf), ("TF-IDF at 0.73, about ModernBERT's time", t_eq),
               (f"ModernBERT at {D['thr']['modernbert']:.2f}, chosen on validation", t_mb)):
    rows.append([lab, f"{r['time']:.1f} s", f"{r['precision']:.2f}", f"{r['recall']:.2f}", f"{r['f1']:.2f}"])
table(s, X0, 2.1, W_FULL, 2.6, rows, (5.62, 1.6, 1.6, 1.6, 1.6), size=17, hl_rows=(3,))
text(s, X0, 4.95, W_FULL, 1.5, [{"runs": "Test-set threshold sweep: a post-hoc comparison, not a tested result. Both reported thresholds were fixed on validation by the same rule (best F1). Precision depends on the threshold; at equal time, ModernBERT keeps more recall and F1.", "size": 17, "color": TXT2, "line": 1.1}])
notes(s, f"Use for: 'Is the precision gain just where the threshold landed?' Yes, precision depends on the threshold. Both were fixed on validation by the same rule, so the test compares the routers as deployed. If I raise TF-IDF's threshold until it costs what ModernBERT costs, about 14 s, its precision reaches about {t_eq['precision']:.2f}, but it then catches only {t_eq['recall']*100:.0f} percent of Mix-needing questions, and F1 drops to {t_eq['f1']:.2f} against {t_mb['f1']:.2f}. So at equal cost the encoder is ahead on recall and F1, which fits its higher ranking scores, but that is a post-hoc sweep, not a significance test. As the thesis says, the threshold sets the cost as much as the choice of router.")

BACKUPS = [sl.shapes.title.text_frame.text.replace("Backup: ", "") for sl in list(prs.slides)[N_MAIN:]]

# ------------------------------------------------------------------------------------- finish
def stamp_spoken():
    """Prefix each main-talk note with [m:ss to m:ss], from words at WPM plus pauses and slide changes."""
    def mmss(sec):
        sec = int(round(sec / 5.0) * 5)
        return f"{sec // 60}:{sec % 60:02d}"
    t0, rows_ = 0.0, []
    for slide, title, body in SPOKEN:
        words = len(re.sub(r"\[pause[^\]]*\]", "", body).split())
        pauses = sum(int(m) if m else 2 for m in re.findall(r"\[pause(?:, (\d+) s)?\]", body))
        dur = words / WPM * 60 + pauses + 3
        stamp = f"[{mmss(t0)} to {mmss(t0 + dur)}]"
        full = f"{stamp}\n{body}"
        if slide is THANKS:
            jump = ", ".join(f"{N_MAIN + i + 1} {b}" for i, b in enumerate(BACKUPS))
            full += f"\n(Backup slides: {jump}. In Keynote, type the number and press Return to jump; type {N_MAIN} and Return to come back.)"
        slide.notes_slide.notes_text_frame.text = full
        rows_.append((title, stamp, words, dur, body))
        t0 += dur
    return rows_, t0

def force_font(pres):
    """Keynote ignores theme font references, so name Figtree on every run and field."""
    for sl in pres.slides:
        for el in sl._element.iter(qn("a:r"), qn("a:fld")):
            rPr = el.get_or_add_rPr()
            rPr.get_or_add_latin().set("typeface", FONT)

rows_, total = stamp_spoken()
force_font(prs)
prs.save(OUT)

md = ["# Speaker script (clean version): Adaptive Hybrid Retrieval-Augmented Generation", "",
      f"From the speaker notes of `{OUT.name}`. Times assume {WPM} words per minute, plus the marked pauses and about 3 seconds per slide change. "
      f"Main talk: {sum(r[2] for r in rows_):,} words, about {total/60:.1f} minutes.", ""]
for i, (title, stamp, words, dur, body) in enumerate(rows_, 1):
    md += [f"## {i}. {title}", "", f"*{stamp[1:-1]}*  ·  {words} words ≈ {dur:.0f} s", ""]
    md += [para for para in body.split("\n")]
    md += [""]
md += ["## Backup slides", ""]
for i, sl in enumerate(list(prs.slides)[N_MAIN:], N_MAIN + 1):
    md += [f"**{i}. {sl.shapes.title.text_frame.text}.** {sl.notes_slide.notes_text_frame.text}", ""]
SCRIPT.write_text("\n".join(md))
print(f"saved {OUT.name}: {len(prs.slides)} slides ({N_MAIN} main) | {sum(r[2] for r in rows_)} words, about {total/60:.1f} min")
for title, stamp, words, dur, _ in rows_:
    print(f"  {stamp:<18} {words:>4} w  {title}")
