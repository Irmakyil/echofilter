from __future__ import annotations

import os
import math
import json
from html import escape
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

from crisis_triage import (
    MAX_BATCH_SIZE,
    analyze_posts,
    ensure_schema,
    load_posts,
    load_synthetic_english,
    mask_phones,
    save_incidents,
)
from icons import render_icon
from report_generator import generate_pdf_report, generate_printable_html_report

st.set_page_config(
    page_title="EchoFilter AI | Disaster Triage Intelligence Command",
    page_icon="https://cdn-icons-png.flaticon.com/512/9442/9442436.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# High-Tech Cyber Command Center CSS (100% Vector SVG Icons, Zero Emojis)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700;800&display=swap');

:root {
    --bg-space: #070a12;
    --card-surface: #0f172a;
    --card-surface-elevated: #162036;
    --border-subtle: rgba(255, 255, 255, 0.08);
    --border-bright: rgba(56, 189, 248, 0.3);
    --text-high: #f8fafc;
    --text-muted: #94a3b8;
    --cyan-glow: #38bdf8;
    --crimson-glow: #ff2a55;
    --amber-glow: #fb923c;
    --emerald-glow: #10b981;
}

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    color: var(--text-high);
}

.stApp {
    background-color: var(--bg-space);
    background-image: 
        radial-gradient(at 0% 0%, rgba(56, 189, 248, 0.06) 0px, transparent 45%),
        radial-gradient(at 100% 0%, rgba(255, 42, 85, 0.05) 0px, transparent 45%),
        radial-gradient(at 50% 100%, rgba(16, 185, 129, 0.04) 0px, transparent 50%);
}

/* Command Header HUD */
.command-hud {
    background: linear-gradient(135deg, #0b1324 0%, #111e38 100%);
    border: 1px solid var(--border-subtle);
    border-radius: 18px;
    padding: 1.5rem 1.8rem;
    margin-bottom: 1.25rem;
    position: relative;
    overflow: hidden;
    box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.5);
}

.command-hud::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, #38bdf8, #818cf8, #ff2a55, #38bdf8);
    background-size: 300% 100%;
    animation: hud-shimmer 8s linear infinite;
}

@keyframes hud-shimmer {
    0% { background-position: 0% 50%; }
    100% { background-position: 300% 50%; }
}

.hud-top-meta {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin-bottom: 0.5rem;
}

.hud-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: rgba(56, 189, 248, 0.12);
    border: 1px solid rgba(56, 189, 248, 0.25);
    color: #38bdf8;
    padding: 0.2rem 0.65rem;
    border-radius: 9999px;
    font-size: 0.73rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

.hud-title {
    font-size: 1.95rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    color: #ffffff;
    margin: 0 0 0.45rem 0;
    display: flex;
    align-items: center;
    gap: 0.65rem;
}

.hud-compass {
    font-size: 0.95rem;
    line-height: 1.55;
    color: #cbd5e1;
    margin: 0;
    max-width: 980px;
    border-left: 3px solid #38bdf8;
    padding-left: 0.9rem;
}

.sdg-tag-group {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 0.9rem;
}

.sdg-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.25rem 0.7rem;
    border-radius: 8px;
    font-size: 0.76rem;
    font-weight: 600;
    letter-spacing: 0.02em;
}
.sdg-11 { background: rgba(253, 157, 36, 0.15); border: 1px solid rgba(253, 157, 36, 0.4); color: #fba738; }
.sdg-13 { background: rgba(63, 126, 68, 0.2); border: 1px solid rgba(63, 126, 68, 0.5); color: #4ade80; }
.sdg-16 { background: rgba(0, 104, 157, 0.2); border: 1px solid rgba(0, 104, 157, 0.5); color: #60a5fa; }

/* Balanced Responsive KPI Grid */
.kpi-row {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 0.75rem;
    margin-bottom: 1.4rem;
}

@media (max-width: 1450px) {
    .kpi-row {
        grid-template-columns: repeat(3, 1fr);
    }
}

@media (max-width: 768px) {
    .kpi-row {
        grid-template-columns: repeat(2, 1fr);
    }
}

.kpi-box {
    background: var(--card-surface);
    border: 1px solid var(--border-subtle);
    border-radius: 14px;
    padding: 1.05rem 1.15rem;
    position: relative;
    overflow: hidden;
    transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}

.kpi-box:hover {
    transform: translateY(-3px);
    border-color: rgba(255, 255, 255, 0.2);
    box-shadow: 0 8px 24px -4px rgba(0, 0, 0, 0.4);
}

.kpi-box-crimson {
    background: linear-gradient(180deg, rgba(239, 68, 68, 0.09) 0%, #0f172a 100%);
    border-color: rgba(239, 68, 68, 0.4);
}

.kpi-box-cyan {
    background: linear-gradient(180deg, rgba(56, 189, 248, 0.09) 0%, #0f172a 100%);
    border-color: rgba(56, 189, 248, 0.4);
}

.kpi-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: var(--text-muted);
    font-size: 0.74rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.35rem;
}

.kpi-val {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.95rem;
    font-weight: 800;
    line-height: 1.1;
    color: #ffffff;
}

.kpi-note {
    font-size: 0.72rem;
    color: var(--text-muted);
    margin-top: 0.3rem;
    display: flex;
    align-items: center;
    gap: 0.35rem;
}

/* Incident Alert Cards */
.card-incident {
    background: var(--card-surface);
    border: 1px solid var(--border-subtle);
    border-radius: 14px;
    padding: 1.25rem 1.35rem;
    margin-bottom: 0.95rem;
    transition: all 0.2s ease;
    position: relative;
}

.card-incident:hover {
    border-color: rgba(255, 255, 255, 0.22);
    box-shadow: 0 6px 20px -2px rgba(0, 0, 0, 0.35);
}

.border-shadowed {
    border-left: 5px solid #ef4444 !important;
    background: linear-gradient(90deg, rgba(239, 68, 68, 0.07) 0%, #0f172a 100%);
    box-shadow: 0 0 15px -4px rgba(239, 68, 68, 0.2);
}

.border-viral {
    border-left: 5px solid #f97316 !important;
    background: linear-gradient(90deg, rgba(249, 115, 22, 0.05) 0%, #0f172a 100%);
}

.border-incomplete {
    border-left: 5px solid #eab308 !important;
    background: linear-gradient(90deg, rgba(234, 179, 8, 0.05) 0%, #0f172a 100%);
}

.border-actionable {
    border-left: 5px solid #10b981 !important;
    background: linear-gradient(90deg, rgba(16, 185, 129, 0.05) 0%, #0f172a 100%);
}

.card-meta-row {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 0.6rem;
    margin-bottom: 0.7rem;
}

.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    font-size: 0.74rem;
    font-weight: 700;
    padding: 0.3rem 0.75rem;
    border-radius: 9999px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

.status-shadowed {
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid rgba(239, 68, 68, 0.5);
    color: #fca5a5;
    animation: pulse-border 2.5s infinite;
}

@keyframes pulse-border {
    0%, 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); }
    50% { box-shadow: 0 0 0 6px rgba(239, 68, 68, 0.12); }
}

.status-viral { background: rgba(249, 115, 22, 0.15); border: 1px solid rgba(249, 115, 22, 0.5); color: #fdba74; }
.status-incomplete { background: rgba(234, 179, 8, 0.15); border: 1px solid rgba(234, 179, 8, 0.5); color: #fde047; }
.status-actionable { background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.5); color: #86efac; }
.status-noise { background: rgba(100, 116, 139, 0.15); border: 1px solid rgba(100, 116, 139, 0.4); color: #cbd5e1; }

.pill-metric {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid var(--border-subtle);
    color: #e2e8f0;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.74rem;
    padding: 0.25rem 0.6rem;
    border-radius: 6px;
}

.pill-urgency {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    background: #020617;
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: #ffffff;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    font-weight: 800;
    padding: 0.28rem 0.7rem;
    border-radius: 6px;
}

.incident-headline {
    font-size: 1.2rem;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 0.4rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.incident-quote {
    font-size: 0.88rem;
    line-height: 1.5;
    color: #94a3b8;
    background: rgba(0, 0, 0, 0.25);
    border-left: 3px solid #38bdf8;
    padding: 0.55rem 0.8rem;
    border-radius: 0 8px 8px 0;
    margin: 0.55rem 0;
}

.incident-ai-box {
    background: rgba(15, 23, 42, 0.85);
    border: 1px solid rgba(56, 189, 248, 0.25);
    border-left: 3px solid #38bdf8;
    border-radius: 8px;
    padding: 0.7rem 0.9rem;
    margin: 0.65rem 0 0.75rem 0;
}

.incident-ai-hdr {
    display: flex;
    align-items: center;
    gap: 0.45rem;
    font-size: 0.74rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #38bdf8;
    margin-bottom: 0.3rem;
}

.incident-ai-text {
    font-size: 0.88rem;
    line-height: 1.5;
    color: #e2e8f0;
}

.incident-update-alert {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: rgba(16, 185, 129, 0.12);
    border: 1px solid rgba(16, 185, 129, 0.4);
    border-radius: 6px;
    padding: 0.45rem 0.75rem;
    font-size: 0.8rem;
    color: #86efac;
    margin: 0.5rem 0 0.65rem 0;
}

.badge-tag {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: #e2e8f0;
    border-radius: 9999px;
    padding: 0.22rem 0.65rem;
    font-size: 0.74rem;
    font-weight: 600;
    margin-right: 0.4rem;
    margin-top: 0.35rem;
}

.badge-vuln {
    background: rgba(239, 68, 68, 0.14) !important;
    border: 1px solid rgba(239, 68, 68, 0.4) !important;
    color: #fca5a5 !important;
}

.badge-need {
    background: rgba(56, 189, 248, 0.12) !important;
    border: 1px solid rgba(56, 189, 248, 0.35) !important;
    color: #7dd3fc !important;
}

.raw-evidence-box {
    background: rgba(0, 0, 0, 0.35);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 10px;
    padding: 0.8rem 0.95rem;
    margin-bottom: 0.55rem;
}

.raw-evidence-meta {
    display: flex;
    justify-content: space-between;
    font-size: 0.74rem;
    color: #64748b;
    margin-bottom: 0.3rem;
}

.raw-evidence-text {
    font-size: 0.87rem;
    line-height: 1.45;
    color: #e2e8f0;
}

/* Sidebar Elements */
section[data-testid="stSidebar"] {
    background-color: #0b1120;
    border-right: 1px solid var(--border-subtle);
}

.sidebar-brand-box {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    border: 1px solid rgba(56, 189, 248, 0.25);
    border-radius: 14px;
    padding: 1.15rem;
    margin-bottom: 1.25rem;
}

.sidebar-hdr {
    display: flex;
    align-items: center;
    gap: 0.45rem;
    font-size: 0.78rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #38bdf8;
    margin: 1.15rem 0 0.4rem 0;
}

.ethical-guard-box {
    background: rgba(16, 185, 129, 0.07);
    border: 1px solid rgba(16, 185, 129, 0.25);
    border-radius: 10px;
    padding: 0.85rem;
    margin-top: 0.6rem;
    font-size: 0.74rem;
    color: #cbd5e1;
}

.ethical-guard-item {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    margin-bottom: 0.3rem;
    color: #86efac;
    font-weight: 600;
}

/* Export Cards */
.export-card-panel {
    background: #0f172a;
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-radius: 14px;
    padding: 1.4rem;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
    border-bottom: 1px solid var(--border-subtle);
    padding-bottom: 0.3rem;
}

.stTabs [data-baseweb="tab"] {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid var(--border-subtle);
    border-radius: 8px 8px 0 0;
    color: #94a3b8;
    font-weight: 700;
    font-size: 0.86rem;
    padding: 0.65rem 1.2rem;
    border-bottom: none;
    transition: all 0.15s ease;
}

.stTabs [aria-selected="true"] {
    background: rgba(56, 189, 248, 0.1) !important;
    color: #38bdf8 !important;
    border-top: 2px solid #38bdf8 !important;
    border-color: rgba(56, 189, 248, 0.3) !important;
}

div.stButton > button {
    border-radius: 8px;
    font-weight: 700;
    transition: transform 0.1s ease;
}
div.stButton > button:hover {
    transform: scale(1.01);
}
</style>
""", unsafe_allow_html=True)


# Safe HTML Renderer (prevents Markdown 4-space code block bug)
def render_html_block(html_content: str) -> None:
    """Render HTML safely without triggering Markdown's 4-space indented code block rule."""
    cleaned = " ".join(line.strip() for line in html_content.strip().splitlines() if line.strip())
    st.markdown(cleaned, unsafe_allow_html=True)


# Status Badge with Vector SVG Icon
def get_status_badge_html(status: str) -> str:
    if status == "SHADOWED_CRITICAL":
        return f'<span class="status-pill status-shadowed">{render_icon("siren", 14, "#ff2a55")} SHADOWED CRITICAL (LOW VISIBILITY · URGENT)</span>'
    elif status == "VIRAL_CRITICAL":
        return f'<span class="status-pill status-viral">{render_icon("flame", 14, "#fb923c")} VIRAL CRITICAL (HIGH REPOST VOLUME)</span>'
    elif status == "INCOMPLETE_INFO":
        return f'<span class="status-pill status-incomplete">{render_icon("alert-triangle", 14, "#facc15")} NEEDS VERIFICATION (MISSING DETAILS)</span>'
    elif status == "ACTIONABLE":
        return f'<span class="status-pill status-actionable">{render_icon("check-circle", 14, "#4ade80")} ACTIONABLE DISPATCH</span>'
    else:
        return f'<span class="status-pill status-noise">{render_icon("filter", 14, "#94a3b8")} FILTERED NOISE</span>'


# Incident Card Component
def render_incident_card(incident: dict, authorized: bool, key_prefix: str = "main") -> None:
    status = incident["visibility_status"]
    border_class = (
        "border-shadowed" if status == "SHADOWED_CRITICAL"
        else "border-viral" if status == "VIRAL_CRITICAL"
        else "border-incomplete" if status == "INCOMPLETE_INFO"
        else "border-actionable"
    )

    address = incident.get("normalized_address") or "Exact location pending operator verification"
    city = incident.get("city") or ""
    district = incident.get("district") or ""
    loc_display = f"{city}, {district}" if city and district else city or district or "Region Unspecified"
    full_title = f"{loc_display} · {address}" if address else loc_display

    merged_count = incident.get("merged_post_count", 1)
    total_rt = incident.get("total_retweet_volume", 0)
    urgency = incident.get("urgency_score", 10)
    reasoning = escape(str(incident.get("ai_reasoning", "")))
    victims = incident.get("victim_count_est")

    v_tags_html = "".join([f'<span class="badge-tag badge-vuln">{render_icon("alert-circle", 12, "#fca5a5")} {escape(t)}</span>' for t in incident.get("vulnerability_tags", [])])
    n_tags_html = "".join([f'<span class="badge-tag badge-need">{render_icon("box", 12, "#38bdf8")} {escape(n)}</span>' for n in incident.get("need_tags", [])])

    victim_pill = f'<span class="pill-metric">{render_icon("users", 13, "#38bdf8")} ~{victims} Persons</span>' if victims else ''

    # Urgency pill with color coding
    if urgency >= 85:
        urgency_bg = "background: rgba(239, 68, 68, 0.2); border: 1px solid #ef4444; color: #ff6b81;"
        urg_icon = render_icon("siren", 13, "#ff2a55")
    elif urgency >= 60:
        urgency_bg = "background: rgba(249, 115, 22, 0.2); border: 1px solid #f97316; color: #fdba74;"
        urg_icon = render_icon("alert-triangle", 13, "#fb923c")
    else:
        urgency_bg = "background: rgba(148, 163, 184, 0.15); border: 1px solid #64748b; color: #cbd5e1;"
        urg_icon = render_icon("target", 13, "#94a3b8")

    # Corroboration Confidence Level (SRS FR-04/FR-07)
    conf_score = incident.get("confidence_score", 42)
    if conf_score >= 85:
        conf_pill = f'<span class="pill-metric" style="background:rgba(16,185,129,0.12); border-color:rgba(16,185,129,0.4); color:#34d399;">{render_icon("check-circle", 12, "#34d399")} Multi-Confirmed · {conf_score}% Confidence</span>'
    elif conf_score >= 65:
        conf_pill = f'<span class="pill-metric" style="background:rgba(56,189,248,0.12); border-color:rgba(56,189,248,0.4); color:#7dd3fc;">{render_icon("users", 12, "#38bdf8")} Corroborated · {conf_score}% Confidence</span>'
    else:
        conf_pill = f'<span class="pill-metric" style="background:rgba(148,163,184,0.1); border-color:rgba(148,163,184,0.3); color:#cbd5e1;">{render_icon("info", 12, "#94a3b8")} Single Witness · {conf_score}% Confidence</span>'

    update_banner = ""
    if incident.get("recent_update_note"):
        update_banner = f"""
        <div class="incident-update-alert">
            {render_icon("radio", 13, "#34d399")}
            <span><b>Progressive Corroboration:</b> {escape(incident['recent_update_note'])}</span>
        </div>
        """

    tags_block = f'<div style="margin-top:0.4rem;">{v_tags_html}{n_tags_html}</div>' if (v_tags_html or n_tags_html) else ''

    card_html = f"""
    <div class="card-incident {border_class}">
        <div class="card-meta-row">
            <div style="display:flex; align-items:center; flex-wrap:wrap; gap:0.45rem;">
                {get_status_badge_html(status)}
                {conf_pill}
                <span class="pill-metric">{render_icon("repeat", 13, "#94a3b8")} {merged_count} Merged Posts</span>
                <span class="pill-metric">{render_icon("activity", 13, "#94a3b8")} {total_rt:,} Total RTs</span>
                {victim_pill}
            </div>
            <div>
                <span class="pill-urgency" style="{urgency_bg}">{urg_icon} Urgency: {urgency}/100</span>
            </div>
        </div>
        {update_banner}
        <div class="incident-headline">
            {render_icon("map-pin", 20, "#38bdf8")} <span>{escape(full_title)}</span>
        </div>
        <div class="incident-ai-box">
            <div class="incident-ai-hdr">
                {render_icon("sparkles", 13, "#38bdf8")}
                <span>Triage Assessment</span>
            </div>
            <div class="incident-ai-text">{reasoning}</div>
        </div>
        {tags_block}
    </div>
    """
    render_html_block(card_html)

    # Source-post evidence remains linked to each incident for review.
    with st.expander(f"Inspect Retained Evidence & Source Posts ({merged_count} records · {incident['incident_id']})"):
        for post in incident.get("posts", []):
            raw_text = post["raw_text"]
            disp_text = raw_text if authorized else mask_phones(raw_text)
            rt_disp = f"{post.get('retweet_count'):,} RT" if pd.notna(post.get("retweet_count")) else "RT count unavailable"
            user = post.get("username", "anonymous")
            time_str = post.get("created_at") or "Time unavailable"

            post_html = f"""
            <div class="raw-evidence-box">
                <div class="raw-evidence-meta">
                    <span><b>@{escape(str(user))}</b> ({escape(str(post.get('post_id')))})</span>
                    <span>{render_icon("repeat", 12, "#64748b")} {rt_disp} &nbsp;·&nbsp; {render_icon("clock", 12, "#64748b")} {escape(str(time_str))}</span>
                </div>
                <div class="raw-evidence-text">{escape(disp_text)}</div>
            </div>
            """
            render_html_block(post_html)

    # Operator Action Center
    col_act1, col_act2, col_act3 = st.columns([1.5, 1.5, 3])
    with col_act1:
        if st.button("Dispatch USAR Units", key=f"{key_prefix}_disp_{incident['incident_id']}"):
            st.toast(f"Urban Search & Rescue units dispatched to {incident['incident_id']}!", icon=":material/send:")
    with col_act2:
        if st.button("Mark Resolved", key=f"{key_prefix}_res_{incident['incident_id']}"):
            st.toast(f"Incident {incident['incident_id']} marked resolved.", icon=":material/check_circle:")
    st.write("")


# Session State Management
if "source_frame" not in st.session_state:
    st.session_state.source_frame = load_synthetic_english()
    st.session_state.source_name = "Global Disaster Reference Gold Dataset (60 Posts)"
if "incidents" not in st.session_state:
    incidents, engine, metrics = analyze_posts(st.session_state.source_frame)
    save_incidents(incidents, st.session_state.source_name)
    st.session_state.incidents = incidents
    st.session_state.engine = engine
    st.session_state.metrics = metrics
if "live_results" not in st.session_state:
    st.session_state.live_results = []

incidents = st.session_state.get("incidents", [])
metrics = st.session_state.get("metrics", {})

# ----------------- REVISED ETHICAL SIDEBAR COMMAND CENTER -----------------
with st.sidebar:
    # 1. Clean Vector Brand Card (Rendered via clean HTML)
    render_html_block(f"""
    <div class="sidebar-brand-box">
        <div style="display:flex; align-items:center; gap:0.65rem; margin-bottom:0.4rem;">
            <div style="background:rgba(56,189,248,0.15); border-radius:10px; padding:7px; display:flex; align-items:center; justify-content:center; border:1px solid rgba(56,189,248,0.3);">
                {render_icon("siren", 22, "#38bdf8")}
            </div>
            <div>
                <div style="font-weight:800; font-size:1.15rem; color:#ffffff; letter-spacing:-0.02em; line-height:1.2;">EchoFilter AI</div>
                <div style="font-size:0.68rem; color:#38bdf8; font-weight:700; text-transform:uppercase; letter-spacing:0.06em;">Crisis Triage Command</div>
            </div>
        </div>
        <div style="display:flex; align-items:center; gap:0.45rem; font-size:0.73rem; color:#94a3b8; padding-top:0.35rem; border-top:1px solid rgba(255,255,255,0.06);">
            <span style="display:inline-block; width:7px; height:7px; background:#10b981; border-radius:50%; box-shadow:0 0 6px #10b981;"></span>
            <span>Local Rules Default · Provider Choice Available</span>
        </div>
    </div>
    """)

    # 2. Ingestion Data Stream
    render_html_block(f"""
    <div class="sidebar-hdr">{render_icon("inbox", 14, "#38bdf8")} 1. Ingestion Data Stream</div>
    """)

    data_mode = st.radio(
        "Select Disaster Stream",
        [
            "Disaster Gold Benchmark (60 Posts)",
            "Upload Custom Social Stream (.csv / .json)"
        ],
        index=0,
        label_visibility="collapsed"
    )

    if data_mode == "Disaster Gold Benchmark (60 Posts)":
        if st.session_state.source_name != "Global Disaster Reference Gold Dataset (60 Posts)":
            st.session_state.source_frame = load_synthetic_english()
            st.session_state.source_name = "Global Disaster Reference Gold Dataset (60 Posts)"
            incidents, engine, metrics = analyze_posts(st.session_state.source_frame)
            st.session_state.incidents = incidents
            st.session_state.engine = engine
            st.session_state.metrics = metrics
            st.rerun()
    else:
        uploaded_file = st.file_uploader("Upload Crisis Stream File", type=["csv", "json"], label_visibility="collapsed")
        if uploaded_file is not None:
            try:
                loaded = load_posts(uploaded_file.getvalue(), uploaded_file.name)
                st.session_state.source_frame = loaded.iloc[:MAX_BATCH_SIZE].copy()
                st.session_state.source_name = f"Upload: {uploaded_file.name}"
                st.success(f"{len(st.session_state.source_frame)} records successfully staged.")
            except Exception as e:
                st.error(f"Ingestion failed: {e}")

    # 3. Analysis engine and external-provider disclosure
    render_html_block(f"""
    <div class="sidebar-hdr">{render_icon("cpu", 14, "#38bdf8")} 2. Ethical Disaster AI Architecture</div>
    """)

    engine_choice = st.selectbox(
        "Analysis engine",
        [
            "Local NLP Rule Engine (Offline)",
            "Google Gemini 2.5 Flash (External API)",
            "OpenAI gpt-4o-mini (External API)",
        ],
        index=0,
        help="The local rule engine works offline. Gemini and OpenAI use their provider APIs and require the matching API key in the server environment."
    )
    external_model = "External API" in engine_choice
    external_consent = False
    if external_model:
        st.warning(
            "Selected message text (with detected phone numbers masked) will be sent to the selected provider for analysis. "
            "Review the provider's data terms and use synthetic or otherwise approved data for demos."
        )
        external_consent = st.checkbox(
            "I understand and approve sending the selected messages to this external AI provider.",
            key="external_ai_data_consent",
        )

    # Ethical AI Guardrails Status Box
    render_html_block(f"""
    <div class="ethical-guard-box">
        <div class="ethical-guard-item">{render_icon("shield", 13, "#86efac")} Local-First Analysis Available</div>
        <div class="ethical-guard-item">{render_icon("lock", 13, "#86efac")} Low-Visibility Priority Rule Enabled</div>
        <div class="ethical-guard-item">{render_icon("check-circle", 13, "#86efac")} Human Review Required</div>
    </div>
    """)

    # 4. Zero-Trust Privacy & PII
    render_html_block(f"""
    <div class="sidebar-hdr">{render_icon("lock", 14, "#38bdf8")} 3. Phone Number Masking</div>
    """)
    authorized = st.toggle(
        "Authorized Command View",
        value=False,
        help="When OFF, phone numbers are masked (+1 (555) ***-**78). Toggle ON to view authorized PII."
    )

    # 5. Pipeline Trigger
    st.markdown("<div style='margin-top:0.75rem;'></div>", unsafe_allow_html=True)
    if st.button("Execute Stream Triage Pipeline", type="primary", use_container_width=True):
        if external_model and not external_consent:
            st.error("Confirm external data sharing before running this provider.")
            st.stop()
        try:
            with st.spinner("Extracting entities, clustering duplicate incidents, and computing visibility weights..."):
                incidents, engine, metrics = analyze_posts(
                    st.session_state.source_frame,
                    engine_choice=engine_choice,
                    api_key=""  # Secure sovereign mode
                )
                save_incidents(incidents, st.session_state.source_name)
                st.session_state.incidents = incidents
                st.session_state.engine = engine
                st.session_state.metrics = metrics
            st.success(f"Triage Pipeline Completed · {engine}")
            st.rerun()
        except Exception as e:
            st.error(f"Analysis Pipeline Error: {e}")

    # 6. Direct Executive Export in Sidebar
    st.markdown("---")
    render_html_block(f"""
    <div class="sidebar-hdr">{render_icon("file-text", 14, "#38bdf8")} 4. SITREP & Dossier Export</div>
    """)

    try:
        pdf_bytes = generate_pdf_report(incidents, metrics, st.session_state.engine, st.session_state.source_name)
        st.download_button(
            label="Download Official Executive PDF",
            data=pdf_bytes,
            file_name=f"EchoFilter_SITREP_Executive_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    except Exception as pdf_err:
        st.caption(f"PDF compiler note: {pdf_err}")


# ----------------- MAIN COMMAND CENTER HUD -----------------
render_html_block(f"""
<div class="command-hud">
    <div class="hud-top-meta">
        <span class="hud-chip">{render_icon("shield", 12, "#38bdf8")} Generative AI for SDGs Hackathon · Group 3</span>
        <span class="hud-chip" style="background:rgba(16,185,129,0.12); border-color:rgba(16,185,129,0.3); color:#34d399;">
            {render_icon("radio", 12, "#34d399")} Local-First Triage · Human Review
        </span>
    </div>
    <div class="hud-title">
        {render_icon("siren", 32, "#38bdf8")} EchoFilter AI · Crisis Triage Intelligence Command
    </div>
    <p class="hud-compass">
        "Our tool clusters and deduplicates disaster assistance calls reshared thousands of times on social media, elevating quiet, high-urgency single reports buried by popularity bias directly to the top of crisis dispatch queues."
    </p>
    <div class="sdg-tag-group">
        <span class="sdg-chip sdg-11">{render_icon("globe", 13, "#fba738")} SDG 11.5: Reduce Casualties & Protect Rubble Victims</span>
        <span class="sdg-chip sdg-13">{render_icon("globe", 13, "#4ade80")} SDG 13.1: Strengthen Climate & Hazard Resilience</span>
        <span class="sdg-chip sdg-16">{render_icon("globe", 13, "#60a5fa")} SDG 16.6: Transparent & Accountable Crisis Coordination</span>
    </div>
</div>
""")


# ----------------- BALANCED RESPONSIVE KPI ROW -----------------
raw_total = metrics.get("raw_total", len(st.session_state.source_frame))
unique_cases = metrics.get("unique_cases", sum(1 for i in incidents if i["is_emergency_call"]))
dedup_rate = metrics.get("dedup_rate", 0.0)
shadowed_count = metrics.get("shadowed_count", sum(1 for i in incidents if i["visibility_status"] == "SHADOWED_CRITICAL"))
review_count = metrics.get("needs_review_count", sum(1 for i in incidents if i["needs_review"]))
noise_count = metrics.get("noise_count", sum(1 for i in incidents if not i["is_emergency_call"]))

render_html_block(f"""
<div class="kpi-row">
    <div class="kpi-box">
        <div class="kpi-header"><span>Raw Social Posts</span>{render_icon("inbox", 16, "#94a3b8")}</div>
        <div class="kpi-val">{raw_total}</div>
        <div class="kpi-note">{render_icon("shield", 12, "#94a3b8")} Zero data loss archive</div>
    </div>
    <div class="kpi-box">
        <div class="kpi-header"><span>Master Incidents</span>{render_icon("target", 16, "#94a3b8")}</div>
        <div class="kpi-val">{unique_cases}</div>
        <div class="kpi-note">{render_icon("map-pin", 12, "#94a3b8")} Clustered unique coordinates</div>
    </div>
    <div class="kpi-box kpi-box-cyan">
        <div class="kpi-header" style="color:#7dd3fc;"><span>Dedup Efficiency</span>{render_icon("zap", 16, "#38bdf8")}</div>
        <div class="kpi-val" style="color:#38bdf8;">{dedup_rate}%</div>
        <div class="kpi-note" style="color:#7dd3fc;">{render_icon("repeat", 12, "#38bdf8")} Cognitive noise saved</div>
    </div>
    <div class="kpi-box kpi-box-crimson">
        <div class="kpi-header" style="color:#fca5a5;"><span>Shadowed Critical</span>{render_icon("siren", 16, "#ef4444")}</div>
        <div class="kpi-val" style="color:#ff2a55;">{shadowed_count}</div>
        <div class="kpi-note" style="color:#fca5a5;">{render_icon("activity", 12, "#ef4444")} &lt;15 RTs · Urgent Alert</div>
    </div>
    <div class="kpi-box" style="border-color:rgba(234, 179, 8, 0.4);">
        <div class="kpi-header" style="color:#fde047;"><span>Needs Review</span>{render_icon("alert-triangle", 16, "#eab308")}</div>
        <div class="kpi-val" style="color:#fde047;">{review_count}</div>
        <div class="kpi-note">{render_icon("info", 12, "#94a3b8")} Incomplete address / vague</div>
    </div>
    <div class="kpi-box">
        <div class="kpi-header"><span>Noise Separated</span>{render_icon("filter", 16, "#94a3b8")}</div>
        <div class="kpi-val">{noise_count}</div>
        <div class="kpi-note">{render_icon("check-circle", 12, "#94a3b8")} Condolences & broadcasts</div>
    </div>
</div>
""")


# ----------------- DYNAMIC NAVIGATION TABS -----------------
active_queue = [i for i in incidents if i["is_emergency_call"] and not i["needs_review"]]
review_list = [i for i in incidents if i["needs_review"]]
noise_list = [i for i in incidents if not i["is_emergency_call"]]

tab_queue, tab_review, tab_simulation, tab_noise, tab_srs = st.tabs([
    f"Priority Incident Queue ({len(active_queue)})",
    f"Human Verification Desk ({len(review_list)})",
    "Live Simulation Radar",
    f"Filtered Noise Vault ({len(noise_list)})",
    "Executive SITREP & Export Center"
])

# 1. TAB: Priority Incident Queue
with tab_queue:
    st.markdown("#### High-Priority Emergency Queue (Visibility Balanced)")
    st.caption("Compass Directive: High-urgency reports buried by low engagement (<15 RTs) are prioritized over viral repost storms.")

    if not active_queue:
        st.info("No active verified distress calls in queue.")
    else:
        filter_c1, filter_c2, filter_c3 = st.columns([2.5, 2.5, 3])
        with filter_c1:
            only_shadowed = st.checkbox("Only Shadowed Critical Incidents", value=False)
        with filter_c2:
            only_infants = st.checkbox("Infants / Children Involved", value=False)

        filtered = active_queue
        if only_shadowed:
            filtered = [i for i in filtered if i["visibility_status"] == "SHADOWED_CRITICAL"]
        if only_infants:
            filtered = [i for i in filtered if "Infant / Child" in i.get("vulnerability_tags", [])]

        for inc in filtered:
            render_incident_card(inc, authorized, key_prefix=f"queue_{inc['incident_id']}")

# 2. TAB: Human Verification Desk (FR-07)
with tab_review:
    st.markdown("#### Human-in-the-Loop Verification Desk")
    st.caption("Distress calls lacking street coordinates or conflicting details are retained here for operator geocoding.")

    if not review_list:
        st.success("Verification desk clear. All active reports contain complete coordinates.")
    else:
        for idx, inc in enumerate(review_list):
            render_incident_card(inc, authorized, key_prefix=f"rev_{inc['incident_id']}_{idx}")
            with st.container():
                edit_c1, edit_c2, edit_c3 = st.columns([3, 3, 2])
                with edit_c1:
                    fixed_city = st.text_input("Verified Region / City", value=inc.get("city") or "", key=f"fc_{inc['incident_id']}_{idx}")
                with edit_c2:
                    fixed_addr = st.text_input("Exact Street / Building Coordinate", value=inc.get("normalized_address") or "", key=f"fa_{inc['incident_id']}_{idx}")
                with edit_c3:
                    st.write("")
                    if st.button("Confirm & Promote to Queue", key=f"btn_promote_{inc['incident_id']}_{idx}", type="primary"):
                        inc["city"] = fixed_city
                        inc["normalized_address"] = fixed_addr
                        inc["needs_review"] = False
                        inc["visibility_status"] = "SHADOWED_CRITICAL" if inc.get("total_retweet_volume", 0) < 15 else "ACTIONABLE"
                        st.toast(f"Incident {inc['incident_id']} promoted to active dispatch queue!", icon=":material/check:")
                        st.rerun()
            st.divider()

# 3. TAB: Live Simulation Radar
with tab_simulation:
    st.markdown("#### Interactive Live Post Simulation Radar")
    st.caption("Simulate incoming emergency calls or test system response to popular cascades vs. quiet single calls.")

    preset_choice = st.selectbox(
        "Load Demonstration Preset",
        [
            "Custom Input (Write Your Own)",
            "Preset 1: Quiet Critical - Trapped Newborn & Oxygen Support (0 RT)",
            "Preset 2: Viral Repost Cascade - Downtown Building (3,500 RT)",
            "Preset 3: Missing Location - Screaming for Help (No Address)",
            "Preset 4: Community Condolences & Broadcast News (Noise)",
            "Preset 5: Progressive Corroboration - Add Trapped Infant to Lantern Street (Dynamic Update)"
        ]
    )

    default_text = "Urgent help needed at Fictional Brookside, Elm Court 3. A newborn and two adults are trapped under rubble; urgent rescue needed. Contact: +1 (555) 234-5678"
    default_rt = 0

    if "Preset 1" in preset_choice:
        default_text = "Please help at Fictional Maplewood, Pine Street 14. A 6-month-old infant and an elder needing insulin are trapped under collapsed roof. Emergency Tel: +1 (555) 432-8901"
        default_rt = 2
    elif "Preset 2" in preset_choice:
        default_text = "Fictional Cedar Bay, Lantern Street 4: Building collapsed, multiple people inside need crane and rescue teams immediately!"
        default_rt = 3500
    elif "Preset 3" in preset_choice:
        default_text = "People are screaming under the collapsed building, please send an ambulance and help now!!"
        default_rt = 14
    elif "Preset 4" in preset_choice:
        default_text = "Sending heartfelt thoughts and prayers to everyone affected by the earthquake. Stay safe! Official news link attached."
        default_rt = 850
    elif "Preset 5" in preset_choice:
        default_text = "Update for Fictional Cedar Bay, Lantern Street 4: An infant is trapped under the rear stairs with high fever! Crane and pediatric rescue team urgently required! Tel: +1 (555) 789-0123"
        default_rt = 8

    sim_c1, sim_c2 = st.columns([3, 2])
    with sim_c1:
        sim_text = st.text_area("Simulated Social Post Text", value=default_text, height=120)
    with sim_c2:
        sim_rt = st.slider("Retweet (RT) Engagement Volume", min_value=0, max_value=6000, value=default_rt, step=1)
        sim_author = st.text_input("Handle / Author", value="@corroborating_witness")
        trigger_sim = st.button("Preview Live Signal", type="secondary", use_container_width=True)
        trigger_enrich = st.button("Inject & Stream-Enrich Active Queue", type="primary", use_container_width=True)

    if trigger_sim and sim_text.strip():
        new_row = pd.DataFrame([{
            "post_id": f"SIM_{len(st.session_state.live_results) + 1:03d}",
            "username": sim_author,
            "created_at": pd.Timestamp.now("UTC").strftime("%Y-%m-%d %H:%M:%SZ"),
            "raw_text": sim_text.strip(),
            "retweet_count": sim_rt,
            "incident_hint": ""
        }])
        sim_incidents, sim_eng, _ = analyze_posts(new_row)
        st.session_state.live_results = sim_incidents
        st.success(f"Live post previewed via {sim_eng}")

    if trigger_enrich and sim_text.strip():
        new_post_dict = {
            "post_id": f"LIVE_{pd.Timestamp.now('UTC').strftime('%H%M%S')}",
            "username": sim_author,
            "created_at": pd.Timestamp.now("UTC").strftime("%Y-%m-%d %H:%M:%SZ"),
            "raw_text": sim_text.strip(),
            "retweet_count": sim_rt,
            "incident_hint": ""
        }
        from crisis_triage import enrich_or_append_post
        action, target_inc, summary = enrich_or_append_post(
            st.session_state.incidents,
            new_post_dict,
            engine_choice=engine_choice
        )
        save_incidents(st.session_state.incidents, st.session_state.source_name)
        if action == "UPDATED":
            st.success(f"Incident {target_inc['incident_id']} Corroborated & Enriched! {summary}")
            st.toast(f"Corroborated {target_inc['incident_id']}: Confidence elevated!", icon=":material/sync:")
        else:
            st.info(f"New Master Incident {target_inc['incident_id']} created! {summary}")
            st.toast(f"New Incident {target_inc['incident_id']} Registered", icon=":material/add_alert:")
        st.rerun()

    if st.session_state.live_results:
        st.markdown("##### Real-Time Analysis Result:")
        for res_inc in st.session_state.live_results:
            render_incident_card(res_inc, authorized, key_prefix=f"sim_{res_inc['incident_id']}")

# 4. TAB: Filtered Noise Vault
with tab_noise:
    st.markdown("#### Filtered Noise Archive")
    st.caption("Non-actionable posts (thoughts, prayers, news broadcasts, traffic updates) are archived here without cluttering first-responder queues.")

    if not noise_list:
        st.info("No noise records in current dataset batch.")
    else:
        for inc in noise_list:
            render_incident_card(inc, authorized, key_prefix=f"noise_{inc['incident_id']}")

# 5. TAB: Executive SITREP & Export Center
with tab_srs:
    st.markdown("#### Executive Disaster SITREP & CAD Interoperability Export")
    st.caption("Official Situation Report (SITREP #01) and Computer-Aided Dispatch (CAD) structured data exports.")

    # High-Priority Export Actions (Clean HTML layout with zero unrendered tags)
    exp_col1, exp_col2 = st.columns(2)
    with exp_col1:
        render_html_block(f"""
        <div style="display:flex; align-items:center; gap:0.55rem; font-weight:700; font-size:1.05rem; color:#ffffff; margin-bottom:0.4rem;">
            {render_icon('file-text', 18, '#38bdf8')}
            <span>Official Executive SITREP PDF Report</span>
        </div>
        """)
        st.write("Generate a formal, publication-ready emergency triage PDF containing the executive summary, operational metrics table, and prioritized dispatch list.")
        try:
            pdf_data = generate_pdf_report(incidents, metrics, st.session_state.engine, st.session_state.source_name)
            st.download_button(
                label="Download Official Executive PDF Report",
                data=pdf_data,
                file_name=f"EchoFilter_SITREP_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"PDF creation error: {e}")

    with exp_col2:
        render_html_block(f"""
        <div style="display:flex; align-items:center; gap:0.55rem; font-weight:700; font-size:1.05rem; color:#ffffff; margin-bottom:0.4rem;">
            {render_icon('globe', 18, '#38bdf8')}
            <span>Printable HTML Dashboard Dossier</span>
        </div>
        """)
        st.write("Generate a standalone HTML dashboard suitable for full-screen presentation or direct browser print-to-PDF (`Ctrl+P` / `Cmd+P`).")
        try:
            html_data = generate_printable_html_report(incidents, metrics, st.session_state.engine, st.session_state.source_name)
            st.download_button(
                label="Download Printable HTML Dossier",
                data=html_data.encode("utf-8"),
                file_name=f"EchoFilter_AI_Dossier_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
                mime="text/html",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"HTML creation error: {e}")

    # CAD Interoperability Export Row
    st.markdown("<div style='margin-top:0.8rem;'></div>", unsafe_allow_html=True)
    cad_col1, cad_col2 = st.columns(2)
    with cad_col1:
        # Export structured master incidents CSV for CAD
        export_df = pd.DataFrame([{
            "incident_id": i["incident_id"],
            "visibility_status": i["visibility_status"],
            "urgency_score": i["urgency_score"],
            "city": i.get("city") or "",
            "normalized_address": i.get("normalized_address") or "",
            "victim_count_est": i.get("victim_count_est") or 0,
            "vulnerability_tags": ";".join(i.get("vulnerability_tags", [])),
            "need_tags": ";".join(i.get("need_tags", [])),
            "merged_post_count": i.get("merged_post_count", 1),
            "total_retweet_volume": i.get("total_retweet_volume", 0),
            "ai_reasoning": i.get("ai_reasoning", "")
        } for i in incidents if i["is_emergency_call"]])
        st.download_button(
            label="Export CAD Dispatch CSV Dataset (.csv)",
            data=export_df.to_csv(index=False).encode("utf-8"),
            file_name=f"EchoFilter_CAD_Incidents_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    with cad_col2:
        # Export JSON
        st.download_button(
            label="Export Structured Geo-Incident JSON (.json)",
            data=json.dumps(incidents, indent=2, ensure_ascii=False).encode("utf-8"),
            file_name=f"EchoFilter_GeoIncidents_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True
        )

    st.divider()

    # Metrics Audit
    r_c1, r_c2 = st.columns(2)
    with r_c1:
        st.markdown("##### Core Benchmark Metrics (SRS 1.3)")
        st.metric("1. Deduplication Efficiency Rate", f"{dedup_rate}%", help="Percentage of redundant reports compressed into single master incidents")
        st.metric("2. Low-Visibility Critical Cases", metrics.get("shadowed_count", 0), help="Count flagged by the configured low-repost and urgency rule; this is not a recall measurement")
        st.metric("3. Total Raw Posts Processed", f"{raw_total} Posts")
        st.metric("4. Clustered Unique Incidents", f"{raw_total} -> {unique_cases} Master Cases")

    with r_c2:
        st.markdown("##### Sustainable Development Goals (SDG) Alignment")
        st.markdown("""
        - **SDG 11 (Target 11.5):** Substantially reduce the number of deaths and people affected by disasters, with a focus on protecting vulnerable groups under rubble (infants, elderly, chronic illness).
        - **SDG 13 (Target 13.1):** Strengthen resilience and adaptive capacity to climate-related hazards and natural disasters.
        - **SDG 16 (Target 16.6):** Develop effective, accountable and transparent institutions at all levels through explainable, auditable disaster triage.
        """)

    st.divider()
    st.markdown("##### Ethical AI & Humanitarian Data Governance (SRS Section 7)")
    st.markdown("""
    - **Analysis modes:** The local deterministic rule engine works offline. Optional Gemini and OpenAI modes send selected, phone-masked messages to the configured provider after operator consent.
    - **Low-visibility priority rule:** High-urgency cases with low repost volume are elevated by a configured rule. Its thresholds and performance require validation on labeled data.
    - **Source traceability:** Raw posts are retained in the local SQLite database. Restrict database access and define retention controls before real-world use.
    - **PII masking limit:** Phone-like strings are masked by pattern matching, which can miss personal data. Human review is required before any action.
    """)
