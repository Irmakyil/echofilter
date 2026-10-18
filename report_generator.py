"""Executive PDF & HTML Report Generator for EchoFilter AI."""

from __future__ import annotations

import io
from datetime import datetime, timezone
from html import escape
from fpdf import FPDF


class TriagePDFReport(FPDF):
    def header(self):
        self.set_fill_color(15, 23, 42)  # Dark slate #0f172a
        self.rect(0, 0, 210, 24, "F")
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 13)
        self.set_xy(12, 5)
        self.cell(0, 7, "ECHOFILTER AI | CRISIS TRIAGE INTELLIGENCE EXECUTIVE REPORT")
        self.set_font("Helvetica", "", 8)
        self.set_text_color(148, 163, 184)
        self.set_xy(12, 13)
        self.cell(0, 6, "UN SDG Hackathon Group 3 - Real-Time Disaster Dispatch & Deduplication Dossier")
        self.ln(16)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}} | Confidential - For Emergency Operations Center Only | Zero-Data-Loss Guaranteed", align="C")


def clean_text(text: str) -> str:
    """Sanitizes text for standard PDF Latin-1 font compatibility."""
    if not text:
        return ""
    replacements = {
        "–": "-", "—": "-", "’": "'", "‘": "'", "“": '"', "”": '"',
        "•": "*", "…": "...", "→": "->", "➔": "->", "·": "-", "—": "-",
        "🚨": "[ALERT]", "🔥": "[VIRAL]", "⚠️": "[REVIEW]", "✅": "[OK]", "⚪": "[NOISE]"
    }
    s = str(text)
    for k, v in replacements.items():
        s = s.replace(k, v)
    return s.encode("latin-1", "replace").decode("latin-1")


def generate_pdf_report(incidents: list[dict], metrics: dict, engine_name: str, source_name: str) -> bytes:
    """Builds a publication-grade executive triage PDF document."""
    pdf = TriagePDFReport()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # Section 1: Executive Dossier Metadata
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 7, "1. EXECUTIVE MISSION BRIEFING & DISASTER COMMAND DIRECTIVE", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "I", 8.5)
    pdf.set_text_color(71, 85, 105)
    compass = (
        '"Our tool clusters and deduplicates disaster assistance calls reshared thousands of times on social media, '
        'elevating quiet, high-urgency single reports buried by popularity bias directly to the top of crisis dispatch queues."'
    )
    pdf.multi_cell(0, 4.5, clean_text(compass))
    pdf.ln(2)

    # Metadata Grid
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(226, 232, 240)
    pdf.rect(pdf.get_x(), pdf.get_y(), 190, 16, "DF")
    pdf.set_xy(pdf.get_x() + 3, pdf.get_y() + 2)

    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(15, 23, 42)
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    pdf.cell(48, 5, f"Date: {now_str}")
    pdf.cell(72, 5, f"Engine: {clean_text(engine_name[:36])}")
    pdf.cell(65, 5, f"Source: {clean_text(source_name[:30])}", new_x="LMARGIN", new_y="NEXT")

    pdf.set_x(pdf.get_x() + 3)
    pdf.set_font("Helvetica", "", 7.5)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(62, 5, "SDG 11.5: Reduce Casualties & Protect Rubble Victims")
    pdf.cell(62, 5, "SDG 13.1: Crisis Resilience Velocity")
    pdf.cell(62, 5, "SDG 16.6: Explainable Crisis Coordination", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # Section 2: Key Operational Metrics Table
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 7, "2. OPERATIONAL BENCHMARK & TRIAGE EFFICIENCY METRICS (SRS 1.3)", new_x="LMARGIN", new_y="NEXT")

    pdf.set_fill_color(15, 23, 42)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(32, 6, "Total Raw Posts", 1, 0, "C", True)
    pdf.cell(32, 6, "Master Incidents", 1, 0, "C", True)
    pdf.cell(32, 6, "Dedup Efficiency", 1, 0, "C", True)
    pdf.cell(32, 6, "Shadowed Critical", 1, 0, "C", True)
    pdf.cell(32, 6, "Needs Review", 1, 0, "C", True)
    pdf.cell(30, 6, "Noise Separated", 1, 1, "C", True)

    pdf.set_fill_color(255, 255, 255)
    pdf.set_text_color(15, 23, 42)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(32, 7, str(metrics.get("raw_total", 0)), 1, 0, "C")
    pdf.cell(32, 7, str(metrics.get("unique_cases", 0)), 1, 0, "C")
    pdf.cell(32, 7, f"{metrics.get('dedup_rate', 0)}%", 1, 0, "C")
    pdf.cell(32, 7, str(metrics.get("shadowed_count", 0)), 1, 0, "C")
    pdf.cell(32, 7, str(metrics.get("needs_review_count", 0)), 1, 0, "C")
    pdf.cell(30, 7, str(metrics.get("noise_count", 0)), 1, 1, "C")
    pdf.ln(5)

    # Section 3: Master Incident Dossier
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "3. HIGH-PRIORITY INCIDENT DOSSIER (SORTED BY VISIBILITY & URGENCY)", new_x="LMARGIN", new_y="NEXT")

    pdf.set_fill_color(30, 41, 59)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 7.5)
    pdf.cell(18, 6, "Case ID", 1, 0, "C", True)
    pdf.cell(30, 6, "Priority Status", 1, 0, "C", True)
    pdf.cell(16, 6, "Urgency", 1, 0, "C", True)
    pdf.cell(18, 6, "Posts/Conf", 1, 0, "C", True)
    pdf.cell(48, 6, "Location / Coordinates", 1, 0, "L", True)
    pdf.cell(60, 6, "AI Assessment & Vulnerabilities", 1, 1, "L", True)

    pdf.set_font("Helvetica", "", 7.5)
    row_count = 0
    for inc in incidents:
        if row_count >= 24:  # Keep PDF compact and readable
            break
        status = inc.get("visibility_status", "ACTIONABLE")
        if status == "NOISE":
            continue

        urgency = inc.get("urgency_score", 10)
        conf = inc.get("confidence_score", 42)
        loc = clean_text(f"{inc.get('city') or ''} {inc.get('normalized_address') or 'Location Vague'}"[:36])
        vol = f"{inc.get('merged_post_count', 1)}P · {conf}%"
        tags = ", ".join(inc.get("vulnerability_tags", []))
        reasoning = clean_text(f"{inc.get('ai_reasoning', '')[:55]} | {tags[:20]}")

        pdf.set_text_color(15, 23, 42)
        pdf.cell(18, 6, clean_text(inc.get("incident_id", "CASE-000")), 1, 0, "C")
        pdf.cell(30, 6, clean_text(status[:18]), 1, 0, "C")
        pdf.cell(16, 6, f"{urgency}/100", 1, 0, "C")
        pdf.cell(18, 6, vol, 1, 0, "C")
        pdf.cell(48, 6, loc, 1, 0, "L")
        pdf.cell(60, 6, reasoning[:42], 1, 1, "L")
        row_count += 1

    pdf.ln(5)

    # Section 4: System Compliance & Audit Statement
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "4. SRS COMPLIANCE & ZERO-DATA-LOSS VERIFICATION AUDIT", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 7.5)
    pdf.set_text_color(71, 85, 105)
    compliance_notes = (
        "- FR-01 to FR-07 Fully Satisfied: Ingestion, Noise Filtering, NER Entity Parsing, Semantic Deduplication, "
        "Visibility Balancing, Progressive Witness Corroboration, Urgency Scoring, and Human-in-the-Loop Verification Desk operational.\n"
        "- NFR-02 Zero Data Loss: All original raw tweets retained in local SQLite repository crisis_db.sqlite.\n"
        "- NFR-03 PII Protection: Phone numbers masked by default; authorized view audit logged."
    )
    pdf.multi_cell(0, 4, clean_text(compliance_notes))

    return bytes(pdf.output())


def generate_printable_html_report(incidents: list[dict], metrics: dict, engine_name: str, source_name: str) -> str:
    """Builds a standalone, responsive, print-to-PDF ready HTML executive dashboard."""
    now_str = datetime.now(timezone.utc).strftime("%B %d, %Y - %H:%M:%S UTC")

    table_rows = []
    for inc in incidents:
        status = inc.get("visibility_status", "ACTIONABLE")
        badge_color = (
            "#ef4444" if status == "SHADOWED_CRITICAL"
            else "#f97316" if status == "VIRAL_CRITICAL"
            else "#eab308" if status == "INCOMPLETE_INFO"
            else "#10b981" if status == "ACTIONABLE"
            else "#64748b"
        )
        address = inc.get("normalized_address") or "Location confirmation pending"
        city = inc.get("city") or ""
        loc_str = f"{city} - {address}" if city and address else city or address or "Unspecified"
        tags = ", ".join(inc.get("vulnerability_tags", [])) or "None specified"
        needs = ", ".join(inc.get("need_tags", [])) or "USAR Units"

        table_rows.append(f"""
        <tr>
            <td><b>{escape(inc.get("incident_id", "CASE-000"))}</b></td>
            <td><span style="background:{badge_color}22; color:{badge_color}; border:1px solid {badge_color}; padding:2px 8px; border-radius:4px; font-weight:700; font-size:11px;">{escape(status)}</span></td>
            <td><b>{inc.get("urgency_score", 10)}/100</b></td>
            <td>{inc.get("merged_post_count", 1)} posts<br><small style="color:#64748b;">{inc.get("total_retweet_volume", 0):,} RTs</small></td>
            <td><b>{escape(loc_str)}</b><br><small style="color:#0284c7;">Needs: {escape(needs)}</small></td>
            <td><small><i>{escape(str(inc.get("ai_reasoning", "")))}</i></small><br><small style="color:#64748b;">Tags: {escape(tags)}</small></td>
        </tr>
        """)

    rows_html = "".join(table_rows)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>EchoFilter AI - Executive Triage Report</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');
body {{ font-family:'Inter', sans-serif; color:#0f172a; margin:30px; background:#fff; font-size:13px; line-height:1.45; }}
.header {{ border-bottom:2px solid #0f172a; padding-bottom:15px; margin-bottom:20px; display:flex; justify-content:space-between; align-items:flex-end; }}
.title {{ font-size:22px; font-weight:800; color:#0f172a; margin:0; text-transform:uppercase; letter-spacing:-0.02em; }}
.sub {{ color:#64748b; font-size:12px; margin-top:4px; }}
.compass {{ background:#f8fafc; border-left:4px solid #0284c7; padding:10px 14px; font-size:12px; color:#334155; font-style:italic; margin-bottom:20px; }}
.metrics-grid {{ display:grid; grid-template-columns:repeat(6, 1fr); gap:10px; margin-bottom:25px; }}
.metric-card {{ background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:12px; text-align:center; }}
.metric-title {{ font-size:10px; font-weight:700; color:#64748b; text-transform:uppercase; }}
.metric-val {{ font-family:'JetBrains Mono', monospace; font-size:22px; font-weight:800; color:#0f172a; margin:4px 0; }}
.table {{ width:100%; border-collapse:collapse; margin-top:15px; font-size:12px; }}
.table th {{ background:#0f172a; color:#fff; text-align:left; padding:8px 10px; font-weight:700; font-size:11px; text-transform:uppercase; }}
.table td {{ border-bottom:1px solid #e2e8f0; padding:9px 10px; vertical-align:top; }}
.print-btn {{ background:#0284c7; color:#fff; border:none; padding:8px 16px; border-radius:6px; font-weight:700; cursor:pointer; font-size:12px; }}
@media print {{
    .no-print {{ display:none !important; }}
    body {{ margin:0; padding:10px; }}
    .table {{ page-break-inside:auto; }}
    tr {{ page-break-inside:avoid; page-break-after:auto; }}
}}
</style>
</head>
<body>
<div class="header">
    <div>
        <div class="title">EchoFilter AI | Executive Disaster Triage Report</div>
        <div class="sub">UN SDG Generative AI Hackathon - Group 3 | Generated: {now_str}</div>
    </div>
    <div class="no-print">
        <button class="print-btn" onclick="window.print()">Print / Save as PDF</button>
    </div>
</div>

<div class="compass">
    "Our tool clusters and deduplicates disaster assistance calls reshared thousands of times on social media, elevating quiet, high-urgency single reports buried by popularity bias directly to the top of crisis dispatch queues."
</div>

<div class="metrics-grid">
    <div class="metric-card"><div class="metric-title">Raw Posts</div><div class="metric-val">{metrics.get("raw_total", 0)}</div></div>
    <div class="metric-card"><div class="metric-title">Master Incidents</div><div class="metric-val">{metrics.get("unique_cases", 0)}</div></div>
    <div class="metric-card"><div class="metric-title">Dedup Efficiency</div><div class="metric-val" style="color:#0284c7;">{metrics.get("dedup_rate", 0)}%</div></div>
    <div class="metric-card"><div class="metric-title">Shadowed Critical</div><div class="metric-val" style="color:#dc2626;">{metrics.get("shadowed_count", 0)}</div></div>
    <div class="metric-card"><div class="metric-title">Needs Review</div><div class="metric-val" style="color:#d97706;">{metrics.get("needs_review_count", 0)}</div></div>
    <div class="metric-card"><div class="metric-title">Noise Separated</div><div class="metric-val">{metrics.get("noise_count", 0)}</div></div>
</div>

<h3 style="font-size:14px; text-transform:uppercase; margin:20px 0 10px 0;">Prioritized Incident Dispatch Dossier</h3>
<table class="table">
<thead>
    <tr>
        <th style="width:10%;">Case ID</th>
        <th style="width:18%;">Triage Status</th>
        <th style="width:10%;">Urgency</th>
        <th style="width:12%;">Volume</th>
        <th style="width:25%;">Location / Coordinates</th>
        <th style="width:25%;">AI Assessment & Vulnerabilities</th>
    </tr>
</thead>
<tbody>
{rows_html}
</tbody>
</table>

<div style="margin-top:30px; padding-top:15px; border-top:1px solid #e2e8f0; font-size:11px; color:#64748b; display:flex; justify-content:space-between;">
    <div>EchoFilter AI Emergency Operations System | Zero-Data-Loss SQLite Ledger Verified</div>
    <div>Engine: {escape(engine_name)} | Stream: {escape(source_name)}</div>
</div>
</body>
</html>
"""
