"""Valuation Memo PDF builder using reportlab. Pure, no I/O."""
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, PageBreak)

INK = colors.HexColor("#0A0A0A")
INK2 = colors.HexColor("#4B5563")
MUTED = colors.HexColor("#9CA3AF")
LINE = colors.HexColor("#E5E5E0")
BG2 = colors.HexColor("#F7F7F4")
SUCCESS = colors.HexColor("#16A34A")


def _fmt_inr(n):
    if n is None: return "—"
    if n >= 1e7: return f"₹{n/1e7:.2f} Cr"
    if n >= 1e5: return f"₹{n/1e5:.1f} L"
    return f"₹{int(n):,}"


def build_valuation_memo(subject: dict, comps: list, developments: list,
                         user: dict) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=18*mm, bottomMargin=18*mm,
                            leftMargin=18*mm, rightMargin=18*mm,
                            title="PlaceHolder Valuation Memo")
    ss = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=ss["Heading1"], fontName="Helvetica-Bold",
                        fontSize=22, textColor=INK, spaceAfter=4, leading=26)
    h2 = ParagraphStyle("h2", parent=ss["Heading2"], fontName="Helvetica-Bold",
                        fontSize=12, textColor=INK, spaceBefore=14, spaceAfter=6)
    tiny = ParagraphStyle("tiny", parent=ss["Normal"], fontName="Helvetica-Bold",
                          fontSize=8, textColor=MUTED, leading=10)
    body = ParagraphStyle("body", parent=ss["Normal"], fontName="Helvetica",
                          fontSize=10, textColor=INK2, leading=14)
    big = ParagraphStyle("big", parent=ss["Normal"], fontName="Helvetica-Bold",
                         fontSize=28, textColor=INK, leading=32)

    story = []
    # Logo monogram + brand block
    logo = Table([["PH", Paragraph("<b>PlaceHolder</b><br/><font size=7 color='#9CA3AF'>India PropTech Intelligence</font>", body)]],
                 colWidths=[14*mm, 60*mm], rowHeights=[14*mm])
    logo.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (0,0), INK),
        ("TEXTCOLOR", (0,0), (0,0), colors.white),
        ("FONT", (0,0), (0,0), "Helvetica-Bold", 14),
        ("ALIGN", (0,0), (0,0), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (1,0), (1,0), 8),
    ]))
    story.append(logo)
    story.append(Spacer(1, 8))
    story.append(Paragraph("PLACEHOLDER · VALUATION MEMO", tiny))
    story.append(Paragraph(f"{subject.get('submarket','—')}, {subject.get('city','—')}", h1))
    story.append(Paragraph(
        f"{subject.get('property_type','Property')} · {subject.get('size_sqft','—')} sqft · "
        f"Generated {datetime.now().strftime('%d %b %Y')} by {user.get('name','')} ({user.get('email','')})",
        body))    # Valuation summary
    if comps:
        psfs = [c["price_per_sqft"] for c in comps if c.get("price_per_sqft")]
        avg_psf = sum(psfs) / len(psfs) if psfs else 0
        low_psf = min(psfs) if psfs else 0
        high_psf = max(psfs) if psfs else 0
        size = subject.get("size_sqft") or 0
        est = avg_psf * size
        story.append(Paragraph("Indicative valuation", h2))
        story.append(Paragraph(_fmt_inr(est), big))
        story.append(Paragraph(
            f"Range: {_fmt_inr(low_psf * size)} – {_fmt_inr(high_psf * size)} · "
            f"Avg ₹{int(avg_psf):,}/sqft based on {len(comps)} comparable transactions.",
            body))
    else:
        story.append(Paragraph("Indicative valuation", h2))
        story.append(Paragraph("Insufficient comparable data for this submarket.", body))

    # Comps table
    story.append(Paragraph(f"Comparable transactions ({len(comps)})", h2))
    if comps:
        rows = [["Confidence", "Address", "Type", "TX", "Sqft", "Sold (₹)", "₹/sqft", "Date"]]
        for c in comps[:25]:
            src = c.get("source", "")
            conf = "VERIFIED" if src.startswith(("NHAI", "Sub-Registrar")) else "OPEN"
            rows.append([conf,
                        Paragraph(f"<font size=8>{c.get('address','—')[:46]}<br/>"
                                  f"<font color='#9CA3AF'>{c.get('submarket','')}</font></font>", body),
                        c.get("property_type",""), c.get("transaction_type",""),
                        f"{int(c.get('size_sqft',0)):,}",
                        _fmt_inr(c.get("sold_price_inr")),
                        f"₹{int(c.get('price_per_sqft',0)):,}",
                        c.get("transaction_date","")])
        t = Table(rows, colWidths=[18*mm, 52*mm, 18*mm, 12*mm, 14*mm, 22*mm, 18*mm, 20*mm])
        t.setStyle(TableStyle([
            ("FONT", (0,0), (-1,0), "Helvetica-Bold", 8),
            ("FONT", (0,1), (-1,-1), "Helvetica", 8),
            ("TEXTCOLOR", (0,0), (-1,0), MUTED),
            ("BACKGROUND", (0,0), (-1,0), BG2),
            ("LINEBELOW", (0,0), (-1,0), 0.5, LINE),
            ("LINEBELOW", (0,1), (-1,-1), 0.25, LINE),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("LEFTPADDING", (0,0), (-1,-1), 4),
            ("RIGHTPADDING", (0,0), (-1,-1), 4),
            ("TOPPADDING", (0,0), (-1,-1), 5),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ]))
        # Color verified rows
        for i, c in enumerate(comps[:200], start=1):
            if c.get("source","").startswith(("NHAI","Sub-Registrar")):
                t.setStyle(TableStyle([("TEXTCOLOR", (0,i), (0,i), SUCCESS)]))
        story.append(t)
    else:
        story.append(Paragraph("No comparable transactions matched the filter criteria.", body))

    # Nearby developments
    story.append(Paragraph(f"Nearby developments ({len(developments)})", h2))
    if developments:
        drows = [["Type", "Project", "Status", "Investment", "Year"]]
        for d in developments[:50]:
            drows.append([d.get("type",""),
                          Paragraph(f"<font size=8>{d.get('name','')[:48]}</font>", body),
                          d.get("status",""),
                          _fmt_inr((d.get("investment_inr_cr") or 0) * 1e7),
                          str(d.get("completion_year",""))])
        dt = Table(drows, colWidths=[22*mm, 78*mm, 30*mm, 28*mm, 16*mm], repeatRows=1)
        dt.setStyle(TableStyle([
            ("FONT", (0,0), (-1,0), "Helvetica-Bold", 8),
            ("FONT", (0,1), (-1,-1), "Helvetica", 8),
            ("TEXTCOLOR", (0,0), (-1,0), MUTED),
            ("BACKGROUND", (0,0), (-1,0), BG2),
            ("LINEBELOW", (0,0), (-1,-1), 0.25, LINE),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("LEFTPADDING", (0,0), (-1,-1), 4),
            ("TOPPADDING", (0,0), (-1,-1), 5),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ]))
        story.append(dt)

    # Source attribution
    story.append(Spacer(1, 14))
    sources = sorted({c.get("source","Unknown") for c in comps} |
                     {d.get("source","Unknown") for d in developments if d.get("source")})
    story.append(Paragraph("Sources", tiny))
    story.append(Paragraph(" · ".join(sources) or "Mixed (see line items)", body))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "Generated by PlaceHolder PropTech Intelligence · "
        "Indicative only, not a certified valuation. "
        "Verify with on-site inspection and registered valuer before transacting.", tiny))

    doc.build(story)
    return buf.getvalue()
