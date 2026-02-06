from __future__ import annotations

from io import BytesIO
from datetime import datetime
from typing import Dict, Any

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def render_receipt_pdf(receipt: Dict[str, Any]) -> bytes:
    """Render a simple, investor-friendly PDF for a receipt dict."""
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    y = height - 60

    def line(txt: str, size: int = 12, bold: bool = False, dy: int = 18):
        nonlocal y
        if bold:
            c.setFont("Helvetica-Bold", size)
        else:
            c.setFont("Helvetica", size)
        c.drawString(60, y, txt)
        y -= dy

    line("FlipTrybe Receipt", 20, True, 26)
    line(f"Generated: {datetime.utcnow().isoformat()}Z", 10, False, 18)

    line("", 12, False, 10)
    line(f"Receipt ID: {receipt.get('id','')}", 12, True)
    line(f"Kind: {receipt.get('kind','')}", 12)
    line(f"Reference: {receipt.get('reference','')}", 12)

    line("", 12, False, 10)
    line(f"Amount: ₦{receipt.get('amount',0)}", 14, True, 20)
    line(f"Fee: ₦{receipt.get('fee',0)}", 12)
    line(f"Total: ₦{receipt.get('total',0)}", 12)

    desc = (receipt.get("description") or "").strip()
    if desc:
        line("", 12, False, 10)
        line("Description", 12, True)
        # wrap rudimentary
        max_len = 85
        while desc:
            line(desc[:max_len], 11, False, 15)
            desc = desc[max_len:]

    line("", 12, False, 14)
    line("Thank you for using FlipTrybe.", 12, True)

    c.showPage()
    c.save()
    return buf.getvalue()
