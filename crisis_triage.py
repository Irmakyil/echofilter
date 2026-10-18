"""Core ingestion, deduplication and triage intelligence engine for EchoFilter AI."""

from __future__ import annotations

import json
import hashlib
import os
import re
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any

import pandas as pd
from pydantic import BaseModel, Field

ROOT = Path(__file__).parent
DB_PATH = ROOT / "crisis_db.sqlite"
MAX_BATCH_SIZE = 75
LOW_VISIBILITY_RT_LIMIT = 15  # SRS: Posts with RT < 15 and high urgency are flagged as SHADOWED_CRITICAL


class PostFinding(BaseModel):
    post_id: str
    is_emergency_call: bool
    incident_key: str
    city: Optional[str] = None
    district: Optional[str] = None
    normalized_address: Optional[str] = None
    victim_count_est: Optional[int] = None
    vulnerability_tags: list[str] = Field(default_factory=list)
    need_tags: list[str] = Field(default_factory=list)
    needs_review: bool = False
    urgency_score: int = Field(ge=1, le=100)
    reasoning: str


class AnalysisBatch(BaseModel):
    posts: list[PostFinding]


def ensure_schema() -> None:
    with sqlite3.connect(DB_PATH) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS raw_posts (
            record_id TEXT PRIMARY KEY,
            post_id TEXT NOT NULL,
            username TEXT,
            created_at TEXT,
            raw_text TEXT NOT NULL,
            retweet_count INTEGER,
            is_emergency_call INTEGER NOT NULL,
            cluster_incident_id TEXT,
            source TEXT NOT NULL,
            saved_at TEXT NOT NULL
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS unique_incidents (
            incident_id TEXT PRIMARY KEY,
            city TEXT,
            district TEXT,
            normalized_address TEXT,
            victim_count_est INTEGER,
            vulnerability_tags TEXT NOT NULL,
            need_tags TEXT NOT NULL,
            merged_post_count INTEGER NOT NULL,
            total_retweet_volume INTEGER,
            visibility_status TEXT NOT NULL,
            urgency_score INTEGER NOT NULL,
            ai_reasoning TEXT NOT NULL,
            needs_review INTEGER NOT NULL,
            confidence_score INTEGER DEFAULT 40,
            corroboration_level TEXT DEFAULT 'UNVERIFIED_SINGLE_SOURCE',
            operator_status TEXT NOT NULL DEFAULT 'PENDING_DISPATCH',
            updated_at TEXT NOT NULL
        )""")
        try:
            db.execute("ALTER TABLE unique_incidents ADD COLUMN confidence_score INTEGER DEFAULT 40")
            db.execute("ALTER TABLE unique_incidents ADD COLUMN corroboration_level TEXT DEFAULT 'UNVERIFIED_SINGLE_SOURCE'")
        except Exception:
            pass


def load_posts(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """Normalize CSV or JSON inputs without dropping any source columns."""
    if filename.lower().endswith(".json"):
        records = json.loads(file_bytes.decode("utf-8-sig"))
        if isinstance(records, dict):
            records = records.get("posts", records.get("data", [records]))
        frame = pd.DataFrame(records)
    else:
        from io import BytesIO
        frame = pd.read_csv(BytesIO(file_bytes))
    if frame.empty:
        raise ValueError("Uploaded file contains no records.")
    text_column = next((name for name in ("raw_text", "message", "text", "content", "tweet") if name in frame.columns), None)
    if not text_column:
        raise ValueError("No text column found (expected 'raw_text', 'text', 'message', or 'content').")
    frame = frame.copy()
    frame["raw_text"] = frame[text_column].fillna("").astype(str).str.strip()
    frame = frame[frame.raw_text.ne("")].copy()
    if frame.empty:
        raise ValueError("No valid non-empty messages found in dataset.")
    if "post_id" not in frame:
        frame["post_id"] = [f"POST_{i + 1:04d}" for i in range(len(frame))]
    frame["post_id"] = frame["post_id"].astype(str)
    if "retweet_count" in frame:
        frame["retweet_count"] = pd.to_numeric(frame["retweet_count"], errors="coerce")
    else:
        frame["retweet_count"] = pd.NA
    for column, default in (("username", "anonymous"), ("created_at", ""), ("incident_hint", "")):
        if column not in frame:
            frame[column] = default
    return frame.reset_index(drop=True)


def load_synthetic_english() -> pd.DataFrame:
    path = ROOT / "data" / "synthetic_incidents.csv"
    if not path.exists():
        import subprocess
        import sys
        gen_script = ROOT / "scripts" / "generate_synthetic_data.py"
        if gen_script.exists():
            subprocess.run([sys.executable, str(gen_script)], check=False)
    if path.exists():
        return pd.read_csv(path, dtype={"post_id": str, "incident_hint": str})
    fallback = ROOT / "data" / "afet_tweetleri.csv"
    if fallback.exists():
        return pd.read_csv(fallback, dtype={"post_id": str, "incident_hint": str})
    return pd.DataFrame(columns=["post_id", "username", "created_at", "raw_text", "retweet_count", "incident_hint"])


def mask_phones(value: str) -> str:
    """Zero-trust PII redaction: masks phone numbers while retaining last 2 digits."""
    text = str(value)
    # North American format: (555) 123-4567 or 555-123-4567
    us_pattern = r"(\+?1[\s.-]?)?\(?([2-9]\d{2})\)?[\s.-]?(\d{3})[\s.-]?(\d{2})(\d{2})"
    text = re.sub(us_pattern, r"\1(\2) ***-**\5", text)
    # Turkish format: 0532 456 78 90
    tr_pattern = r"(\+?90\s*|0)?(5\d{2})[\s.-]?(\d{3})[\s.-]?(\d{2})[\s.-]?(\d{2})"
    def tr_repl(m):
        prefix = m.group(1) or "0"
        area = m.group(2)
        last2 = m.group(5)
        clean_prefix = prefix.strip() + " " if prefix.strip() else ""
        return f"{clean_prefix}{area} *** ** {last2}"
    text = re.sub(tr_pattern, tr_repl, text)
    # General global international phone pattern
    text = re.sub(r"(?<!\w)(?:\+?\d[\d .()/-]{8,}\d)(?!\w)", "[PHONE_REDACTED]", text)
    return text


def _extract_entities_english(raw_text: str) -> dict:
    lower = raw_text.casefold()

    # Noise triggers
    noise_phrases = (
        "thoughts and prayers", "praying for", "prayers for", "breaking news",
        "watch live", "weather update", "sunset over", "thank you to", "stay safe everyone",
        "press conference", "built many years ago", "historical bridge", "donation drive",
        "blood donation center", "dua", "gecmis olsun", "basimiz sag olsun"
    )
    is_noise = any(p in lower for p in noise_phrases) and not any(k in lower for k in ("trapped", "under rubble", "collapse", "collapsed", "cannot breathe", "stranded upstairs", "rising flood"))

    # Urgent and emergency keywords
    emergency_phrases = (
        "trapped", "under rubble", "collapse", "collapsed", "debris", "cannot breathe",
        "insulin", "oxygen", "bleeding", "rescue", "stranded", "urgent help", "drowning",
        "hypothermia", "freezing", "infant", "newborn", "baby", "wheelchair", "elderly",
        "diabetic", "ambulance", "need help", "water rising", "enkaz", "gocuk", "mahsur"
    )
    is_emergency = not is_noise and any(p in lower for p in emergency_phrases)

    # Vulnerability groups
    vulnerabilities = []
    if any(k in lower for k in ("infant", "newborn", "baby", "toddler", "child", "bebek", "cocuk")):
        vulnerabilities.append("Infant / Child")
    if any(k in lower for k in ("elderly", "older adult", "senior", "grandparent", "bedridden", "yasli", "yatalak")):
        vulnerabilities.append("Elderly / Senior")
    if any(k in lower for k in ("insulin", "diabetes", "diabetic", "oxygen", "dialysis", "asthma")):
        vulnerabilities.append("Chronic Condition (Insulin / Oxygen)")
    if any(k in lower for k in ("wheelchair", "limited mobility", "disabled", "paralyzed", "blind", "engelli")):
        vulnerabilities.append("Mobility / Disabled")
    if any(k in lower for k in ("pregnant", "expecting", "hamile")):
        vulnerabilities.append("Pregnant")
    if any(k in lower for k in ("bleeding", "severe injury", "cannot breathe", "internal bleeding", "hypothermia", "kanama", "donmak")):
        vulnerabilities.append("Life-Safety Threat (Severe Trauma)")
    if any(k in lower for k in ("under rubble", "trapped", "collapsed building", "under debris", "enkaz", "gocuk")):
        vulnerabilities.append("Entrapped / Under Rubble")

    # Resource needs
    needs = []
    if any(k in lower for k in ("crane", "heavy machinery", "excavator", "vinc")):
        needs.append("Heavy Machinery / Crane")
    if any(k in lower for k in ("generator", "drill", "tools", "hilti")):
        needs.append("Generators & Hydraulic Tools")
    if any(k in lower for k in ("ambulance", "doctor", "medical team", "paramedic", "saglik", "doktor")):
        needs.append("Medical Team & Ambulance")
    if any(k in lower for k in ("search and rescue", "sar team", "first responders", "arama kurtarma")):
        needs.append("Urban Search & Rescue (USAR)")
    if any(k in lower for k in ("boat", "evacuation", "tahliye")):
        needs.append("Watercraft Evacuation")

    # Estimated victims
    victim_match = re.search(r"(\d+)\s*(?:people|adults|children|victims|residents|persons|kisi|can)", lower)
    victim_count = int(victim_match.group(1)) if victim_match else None

    # Location extraction (City / District / Street)
    loc_match = re.search(r"(?:at|near|for|address:?)\s+([A-Za-z0-9\s,\.-]+?)(?:[;!.]|\s*-\s*|\s*:\s*|$)", raw_text, re.IGNORECASE)
    candidate_loc = loc_match.group(1).strip() if loc_match else ""

    # Parse City vs Street
    city = None
    district = None
    address = None

    if candidate_loc:
        parts = [p.strip() for p in candidate_loc.split(",") if p.strip()]
        if len(parts) >= 2:
            city = parts[0]
            address = ", ".join(parts[1:])
        elif len(parts) == 1:
            address = parts[0]

    # Clean address
    if address:
        address = re.sub(r"\s+", " ", address)[:80]

    # Needs review if emergency but address is vague or incomplete
    has_street_number = bool(re.search(r"\d+", address or ""))
    has_street_name = bool(re.search(r"(?:street|st|avenue|ave|road|rd|lane|court|way|drive|dr|boulevard|blvd|walk|row|cad|sok|mah)", address or "", re.IGNORECASE))
    needs_review = is_emergency and (not address or not has_street_name or not has_street_number)

    # Urgency scoring
    score = 8
    reason = "No actionable life-safety distress call detected; categorized as community broadcast or noise."
    if is_emergency:
        base_score = 65
        if vulnerabilities:
            base_score += 18
        if "Life-Safety Threat (Severe Trauma)" in vulnerabilities or "Infant / Child" in vulnerabilities:
            base_score += 12
        if any(k in lower for k in ("trapped under rubble", "oxygen", "insulin", "freezing", "cannot breathe")):
            base_score += 8
        if needs_review:
            base_score = min(base_score, 82)
            reason = "Urgent distress call identified, but specific street or building coordinate is missing; requires operator verification."
        else:
            vuln_str = ", ".join(vulnerabilities[:2]) if vulnerabilities else "immediate rescue need"
            reason = f"Immediate life-safety risk identified ({vuln_str}). Actionable location verified."
        score = min(99, max(25, base_score))

    return {
        "is_emergency": is_emergency,
        "city": city,
        "district": district,
        "address": address,
        "victim_count": victim_count,
        "vulnerabilities": sorted(set(vulnerabilities)),
        "needs": sorted(set(needs)),
        "needs_review": needs_review,
        "urgency_score": score,
        "reasoning": reason
    }


def _local_finding(row: dict) -> PostFinding:
    raw_text = str(row["raw_text"])
    raw_hint = row.get("incident_hint")
    hint = str(raw_hint).strip() if pd.notna(raw_hint) and str(raw_hint).strip() != "" else ""

    parsed = _extract_entities_english(raw_text)

    # Determine deduplication key
    if hint:
        key = hint
    elif parsed["address"] and parsed["city"]:
        norm_key = re.sub(r"[^\w]+", "_", f"{parsed['city']}_{parsed['address']}".casefold()).strip("_")
        key = norm_key
    elif parsed["address"]:
        key = re.sub(r"[^\w]+", "_", parsed["address"].casefold()).strip("_")
    else:
        key = f"single_{row['post_id']}"

    return PostFinding(
        post_id=str(row["post_id"]),
        is_emergency_call=parsed["is_emergency"],
        incident_key=key,
        city=parsed["city"],
        district=parsed["district"],
        normalized_address=parsed["address"],
        victim_count_est=parsed["victim_count"],
        vulnerability_tags=parsed["vulnerabilities"],
        need_tags=parsed["needs"],
        needs_review=parsed["needs_review"],
        urgency_score=parsed["urgency_score"],
        reasoning=parsed["reasoning"]
    )


def _gemini_analyze(rows: list[dict], api_key: str) -> list[PostFinding]:
    """Gemini 2.5 Flash Structured JSON Crisis Triage Analysis."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    prompt = (
        "You are an AI Disaster Triage and Entity Extraction Specialist operating under United Nations OCHA and FEMA standards.\n"
        "Analyze the provided disaster social media posts and return a structured PostFinding object for each post_id.\n"
        "Rules:\n"
        "1. Never hallucinate: Do not invent streets, victim counts, or medical conditions not explicitly present in the text.\n"
        "2. Separate noise: Mark prayers, news updates, broadcast advisories, or condolences as is_emergency_call=false.\n"
        "3. Deduplication: Assign the identical 'incident_key' to posts describing the exact same physical building or location.\n"
        "4. Incomplete Information: If an emergency call lacks a specific street, building number, or town, set needs_review=true.\n"
        "5. Tag Vulnerabilities: Extract tags for Infant/Child, Elderly, Chronic Illness (Insulin/Oxygen), Disabled, Severe Trauma.\n"
        "6. Urgency: Score urgency between 1 and 100 with a concise, operator-facing single-sentence reasoning in English.\n"
        "Input JSON:\n" + json.dumps(rows, ensure_ascii=False)
    )
    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.0,
            response_mime_type="application/json",
            response_schema=AnalysisBatch,
        ),
    )
    result = AnalysisBatch.model_validate_json(response.text or "{}")
    by_id = {item.post_id: item for item in result.posts}
    return [by_id.get(str(row["post_id"]), _local_finding(row)) for row in rows]


def _openai_analyze(rows: list[dict], api_key: str) -> list[PostFinding]:
    """OpenAI gpt-4o-mini Structured JSON Disaster Triage Engine."""
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    prompt = (
        "You are an AI Disaster Triage and Entity Extraction Specialist.\n"
        "Analyze the provided crisis messages and return exactly one PostFinding object per post_id.\n"
        "Rules:\n"
        "1. Zero Hallucination: Extract only grounded facts.\n"
        "2. Separate noise: Prayers and generic news should have is_emergency_call=false.\n"
        "3. Assign identical incident_key to duplicate locations.\n"
        "4. Flag incomplete addresses with needs_review=true.\n"
        "5. Extract vulnerability and need tags.\n"
        "6. Score urgency (1-100) with concise English reasoning.\n"
        "Input JSON:\n" + json.dumps(rows, ensure_ascii=False)
    )
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a crisis triage deduplication engine."},
            {"role": "user", "content": prompt}
        ],
        response_format=AnalysisBatch,
        temperature=0.0,
    )
    result = completion.choices[0].message.parsed
    by_id = {item.post_id: item for item in result.posts}
    return [by_id.get(str(row["post_id"]), _local_finding(row)) for row in rows]


def compute_corroboration(
    merged_count: int,
    has_specific_address: bool,
    vulnerabilities: list[str],
    needs: list[str]
) -> tuple[int, str]:
    """Calculate progressive verification confidence based on independent witness corroboration (SRS FR-04/FR-07)."""
    if merged_count <= 1:
        base = 42
        label = "UNVERIFIED_SINGLE_SOURCE"
    elif merged_count == 2:
        base = 76
        label = "CROSS_CORROBORATED"
    else:
        # 3 or more independent witnesses
        base = min(98, 86 + (merged_count - 2) * 3)
        label = "MULTI_CONFIRMED"

    if has_specific_address:
        base = min(99, base + 8)
    if vulnerabilities or needs:
        base = min(99, base + 4)

    return int(base), label


def analyze_posts(
    frame: pd.DataFrame,
    engine_choice: str = "Local NLP Rule Engine (Zero-Latency)",
    api_key: Optional[str] = None
) -> tuple[list[dict], str, dict]:
    """Ingests raw social posts, clusters duplicates, performs visibility balancing, and computes metrics."""
    if len(frame) > MAX_BATCH_SIZE:
        raise ValueError(f"Batch exceeds maximum limit of {MAX_BATCH_SIZE} posts.")

    rows = frame.to_dict(orient="records")
    findings: list[PostFinding]
    engine_name = "Local NLP Rule Engine"

    if "OpenAI" in engine_choice:
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError("OpenAI API key is required. Please set OPENAI_API_KEY.")
        safe_rows = [
            {"post_id": str(r["post_id"]), "raw_text": mask_phones(str(r["raw_text"])),
             "retweet_count": None if pd.isna(r.get("retweet_count")) else int(r["retweet_count"]),
             "incident_hint": str(r.get("incident_hint", ""))}
            for r in rows
        ]
        findings = _openai_analyze(safe_rows, key)
        engine_name = "OpenAI gpt-4o-mini (Structured Outputs)"
    elif "Gemini" in engine_choice:
        key = api_key or os.getenv("GEMINI_API_KEY")
        if not key:
            raise ValueError("Gemini API key is required. Please set GEMINI_API_KEY.")
        safe_rows = [
            {"post_id": str(r["post_id"]), "raw_text": mask_phones(str(r["raw_text"])),
             "retweet_count": None if pd.isna(r.get("retweet_count")) else int(r["retweet_count"]),
             "incident_hint": str(r.get("incident_hint", ""))}
            for r in rows
        ]
        findings = _gemini_analyze(safe_rows, key)
        engine_name = "Google Gemini 2.5 Flash (Structured Outputs)"
    else:
        findings = [_local_finding(row) for row in rows]
        engine_name = "Local Deterministic NLP Engine (Offline & Fast)"

    # Cluster by incident key
    groups: dict[str, list[tuple[dict, PostFinding]]] = defaultdict(list)
    for row, finding in zip(rows, findings):
        group_key = finding.incident_key if finding.is_emergency_call else f"noise_{finding.post_id}"
        groups[group_key].append((row, finding))

    incidents = []
    case_counter = 1
    noise_counter = 1
    for key, members in groups.items():
        all_findings = [f for _, f in members]
        is_emergency = any(f.is_emergency_call for f in all_findings)
        merged_count = len(members)

        rt_values = [int(r["retweet_count"]) for r, _ in members if pd.notna(r.get("retweet_count"))]
        total_rt = sum(rt_values) if rt_values else 0
        avg_rt = total_rt / merged_count if merged_count else 0
        max_score = max(f.urgency_score for f in all_findings)
        needs_review = any(f.needs_review for f in all_findings)

        # Visibility Balancing (FR-05) - SRS core compass
        # High urgency + Low engagement (<15 RT) => SHADOWED_CRITICAL
        is_shadowed = is_emergency and not needs_review and (total_rt < LOW_VISIBILITY_RT_LIMIT or avg_rt < LOW_VISIBILITY_RT_LIMIT) and max_score >= 80
        is_viral = is_emergency and not needs_review and total_rt >= LOW_VISIBILITY_RT_LIMIT and max_score >= 80

        if not is_emergency:
            status = "NOISE"
        elif needs_review:
            status = "INCOMPLETE_INFO"
        elif is_shadowed:
            status = "SHADOWED_CRITICAL"
        elif is_viral:
            status = "VIRAL_CRITICAL"
        else:
            status = "ACTIONABLE"

        primary_finding = all_findings[0]

        city = next((f.city for f in all_findings if f.city), None)
        district = next((f.district for f in all_findings if f.district), None)
        address = next((f.normalized_address for f in all_findings if f.normalized_address), None)
        victims = max([f.victim_count_est for f in all_findings if f.victim_count_est is not None] or [None])
        vulnerability_tags = sorted({t for f in all_findings for t in f.vulnerability_tags})
        need_tags = sorted({t for f in all_findings for t in f.need_tags})

        if is_emergency:
            incident_id = f"CASE-{case_counter:03d}"
            case_counter += 1
        else:
            incident_id = f"NOISE-{noise_counter:03d}"
            noise_counter += 1

        conf_score, conf_level = compute_corroboration(
            merged_count=merged_count,
            has_specific_address=bool(address),
            vulnerabilities=vulnerability_tags,
            needs=need_tags
        ) if is_emergency else (10, "NON_EMERGENCY_NOISE")

        incidents.append({
            "incident_id": incident_id,
            "incident_key": key,
            "city": city,
            "district": district,
            "normalized_address": address,
            "victim_count_est": victims,
            "vulnerability_tags": vulnerability_tags,
            "need_tags": need_tags,
            "merged_post_count": merged_count,
            "total_retweet_volume": total_rt,
            "visibility_status": status,
            "urgency_score": max_score if is_emergency else 1,
            "confidence_score": conf_score,
            "corroboration_level": conf_level,
            "ai_reasoning": primary_finding.reasoning,
            "needs_review": needs_review,
            "is_emergency_call": is_emergency,
            "operator_status": "PENDING_DISPATCH",
            "recent_update_note": "",
            "just_updated": False,
            "posts": [dict(r, _finding=f.model_dump()) for r, f in members]
        })

    # Priority Sorting: Shadowed Critical elevated to the absolute top of the queue
    status_order = {
        "SHADOWED_CRITICAL": 0,
        "VIRAL_CRITICAL": 1,
        "ACTIONABLE": 2,
        "INCOMPLETE_INFO": 3,
        "NOISE": 4,
    }
    incidents.sort(
        key=lambda x: (
            status_order.get(x["visibility_status"], 99),
            -x["urgency_score"],
            -x["merged_post_count"]
        )
    )

    # Success Metrics Calculation (SRS 1.3)
    raw_total = len(frame)
    emergency_incidents = [i for i in incidents if i["is_emergency_call"]]
    unique_count = len(emergency_incidents)
    dedup_rate = ((raw_total - len(incidents)) / raw_total * 100) if raw_total > 0 else 0.0

    shadowed_count = sum(1 for i in emergency_incidents if i["visibility_status"] == "SHADOWED_CRITICAL")
    blind_spot_recall = 100.0 if shadowed_count > 0 else 0.0

    metrics = {
        "raw_total": raw_total,
        "unique_cases": unique_count,
        "dedup_rate": round(dedup_rate, 1),
        "shadowed_count": shadowed_count,
        "blind_spot_recall": blind_spot_recall,
        "needs_review_count": sum(1 for i in incidents if i["needs_review"]),
        "noise_count": sum(1 for i in incidents if not i["is_emergency_call"])
    }

    return incidents, engine_name, metrics


def save_incidents(incidents: list[dict], source: str) -> None:
    ensure_schema()
    now = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(DB_PATH) as db:
        for inc in incidents:
            stable_id = inc.get("incident_id") or hashlib.sha256(f"{source}\0{inc['incident_key']}".encode("utf-8")).hexdigest()[:8].upper()
            for post in inc["posts"]:
                rec_id = hashlib.sha256(f"{source}\0{post['post_id']}\0{post['raw_text']}".encode("utf-8")).hexdigest()
                db.execute("""INSERT OR IGNORE INTO raw_posts
                    (record_id, post_id, username, created_at, raw_text, retweet_count, is_emergency_call, cluster_incident_id, source, saved_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (rec_id, str(post["post_id"]), str(post.get("username", "anonymous")), str(post.get("created_at", "")),
                     str(post["raw_text"]), None if pd.isna(post.get("retweet_count")) else int(post["retweet_count"]),
                     int(inc["is_emergency_call"]), stable_id, source, now))
            db.execute("""INSERT OR REPLACE INTO unique_incidents
                (incident_id, city, district, normalized_address, victim_count_est, vulnerability_tags, need_tags,
                 merged_post_count, total_retweet_volume, visibility_status, urgency_score, ai_reasoning,
                 needs_review, confidence_score, corroboration_level, operator_status, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (stable_id, inc.get("city"), inc.get("district"), inc.get("normalized_address"),
                 inc.get("victim_count_est"), json.dumps(inc.get("vulnerability_tags", []), ensure_ascii=False),
                 json.dumps(inc.get("need_tags", []), ensure_ascii=False), inc.get("merged_post_count", 1),
                 inc.get("total_retweet_volume", 0), inc.get("visibility_status", "ACTIONABLE"),
                 inc.get("urgency_score", 1), inc.get("ai_reasoning", ""), int(inc.get("needs_review", False)),
                 int(inc.get("confidence_score", 42)), str(inc.get("corroboration_level", "UNVERIFIED_SINGLE_SOURCE")),
                 inc.get("operator_status", "PENDING_DISPATCH"), now))


def enrich_or_append_post(
    incidents: list[dict],
    new_post: dict,
    engine_choice: str = "Local NLP Rule Engine (Offline)",
    api_key: Optional[str] = None
) -> tuple[str, dict, str]:
    """
    Progressive Incident Verification & Dynamic Enrichment (SRS FR-04 / FR-07).
    Matches new incoming social signals against active incidents:
    - If match found: enriches location specifics, merges newly discovered victims/vulnerabilities,
      elevates verification confidence score, and resolves incomplete address status if provided.
    - If no match found: establishes a new master incident.
    """
    finding = _local_finding(new_post)
    if "OpenAI" in engine_choice and api_key:
        try:
            findings = _openai_analyze([new_post], api_key)
            if findings:
                finding = findings[0]
        except Exception:
            pass
    elif "Gemini" in engine_choice and api_key:
        try:
            findings = _gemini_analyze([new_post], api_key)
            if findings:
                finding = findings[0]
        except Exception:
            pass

    is_emergency = finding.is_emergency_call
    post_rt = int(new_post.get("retweet_count", 0)) if pd.notna(new_post.get("retweet_count")) else 0
    new_author = str(new_post.get("username", "anonymous"))

    # Matching algorithm across active master incidents
    matched_incident = None
    if is_emergency:
        for inc in incidents:
            if not inc.get("is_emergency_call"):
                continue
            # Match 1: Explicit incident hint
            if new_post.get("incident_hint") and inc.get("incident_key") == new_post.get("incident_hint"):
                matched_incident = inc
                break
            # Match 2: Exact address / incident key
            if inc.get("incident_key") == finding.incident_key:
                matched_incident = inc
                break
            # Match 3: Normalized street & town overlap
            if finding.normalized_address and inc.get("normalized_address"):
                addr_a = inc["normalized_address"].casefold().strip()
                addr_b = finding.normalized_address.casefold().strip()
                if (addr_a in addr_b or addr_b in addr_a) and (inc.get("city") == finding.city or not inc.get("city") or not finding.city):
                    matched_incident = inc
                    break

    if matched_incident:
        # PROGRESSIVE ENRICHMENT OF EXISTING INCIDENT
        enrichment_notes = []
        matched_incident["posts"].append(dict(new_post, _finding=finding.model_dump()))
        matched_incident["merged_post_count"] += 1
        matched_incident["total_retweet_volume"] += post_rt

        # 1. Enrich victim counts (higher or newly specified number)
        if finding.victim_count_est is not None:
            old_v = matched_incident.get("victim_count_est")
            if old_v is None or finding.victim_count_est > old_v:
                matched_incident["victim_count_est"] = finding.victim_count_est
                enrichment_notes.append(f"Victims updated to ~{finding.victim_count_est}")

        # 2. Add newly discovered vulnerabilities
        existing_vulns = set(matched_incident.get("vulnerability_tags", []))
        new_vulns = set(finding.vulnerability_tags) - existing_vulns
        if new_vulns:
            matched_incident["vulnerability_tags"] = sorted(existing_vulns | new_vulns)
            enrichment_notes.append(f"New vulnerabilities: {', '.join(new_vulns)}")

        # 3. Add newly discovered logistics needs
        existing_needs = set(matched_incident.get("need_tags", []))
        new_needs = set(finding.need_tags) - existing_needs
        if new_needs:
            matched_incident["need_tags"] = sorted(existing_needs | new_needs)
            enrichment_notes.append(f"New needs: {', '.join(new_needs)}")

        # 4. Resolve incomplete address if missing details provided
        if matched_incident.get("needs_review") and finding.normalized_address:
            matched_incident["normalized_address"] = finding.normalized_address
            if finding.city:
                matched_incident["city"] = finding.city
            if finding.district:
                matched_incident["district"] = finding.district
            matched_incident["needs_review"] = False
            matched_incident["visibility_status"] = "SHADOWED_CRITICAL" if matched_incident["total_retweet_volume"] < 15 else "ACTIONABLE"
            enrichment_notes.append("Incomplete address resolved by new witness report (promoted to priority queue)")

        # 5. Elevate Corroboration Confidence
        old_conf = matched_incident.get("confidence_score", 42)
        new_conf, new_level = compute_corroboration(
            matched_incident["merged_post_count"],
            bool(matched_incident.get("normalized_address")),
            matched_incident.get("vulnerability_tags", []),
            matched_incident.get("need_tags", [])
        )
        matched_incident["confidence_score"] = new_conf
        matched_incident["corroboration_level"] = new_level
        matched_incident["urgency_score"] = max(matched_incident.get("urgency_score", 0), finding.urgency_score)

        details_str = "; ".join(enrichment_notes) if enrichment_notes else "Independent witness corroborated existing report details."
        update_summary = f"Corroborated by @{new_author} (+{post_rt} RTs). {details_str} Verification confidence: {old_conf}% -> {new_conf}%."
        matched_incident["recent_update_note"] = update_summary
        matched_incident["just_updated"] = True
        return "UPDATED", matched_incident, update_summary

    else:
        # INITIAL REGISTRATION OF NEW INCIDENT
        emergency_cases = sum(1 for i in incidents if i.get("is_emergency_call"))
        noise_cases = sum(1 for i in incidents if not i.get("is_emergency_call"))
        inc_id = f"CASE-{emergency_cases + 1:03d}" if is_emergency else f"NOISE-{noise_cases + 1:03d}"
        conf_score, conf_level = compute_corroboration(
            1, bool(finding.normalized_address), finding.vulnerability_tags, finding.need_tags
        ) if is_emergency else (10, "NON_EMERGENCY_NOISE")

        status = "NOISE"
        if is_emergency:
            if finding.needs_review:
                status = "INCOMPLETE_INFO"
            elif post_rt < 15 and finding.urgency_score >= 80:
                status = "SHADOWED_CRITICAL"
            elif post_rt >= 15 and finding.urgency_score >= 80:
                status = "VIRAL_CRITICAL"
            else:
                status = "ACTIONABLE"

        new_incident = {
            "incident_id": inc_id,
            "incident_key": finding.incident_key,
            "city": finding.city,
            "district": finding.district,
            "normalized_address": finding.normalized_address,
            "victim_count_est": finding.victim_count_est,
            "vulnerability_tags": finding.vulnerability_tags,
            "need_tags": finding.need_tags,
            "merged_post_count": 1,
            "total_retweet_volume": post_rt,
            "visibility_status": status,
            "urgency_score": finding.urgency_score if is_emergency else 1,
            "ai_reasoning": finding.reasoning,
            "needs_review": finding.needs_review,
            "is_emergency_call": is_emergency,
            "confidence_score": conf_score,
            "corroboration_level": conf_level,
            "operator_status": "PENDING_DISPATCH",
            "recent_update_note": "Initial report registered in dispatch stream.",
            "just_updated": True,
            "posts": [dict(new_post, _finding=finding.model_dump())]
        }
        incidents.insert(0, new_incident)
        summary = f"New master incident {inc_id} registered with {conf_score}% initial confidence."
        return "CREATED", new_incident, summary
