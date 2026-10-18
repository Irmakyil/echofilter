# EchoFilter AI · Crisis Triage Intelligence Command

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40%2B-FF4B4B.svg)](https://streamlit.io/)
[![SDGs](https://img.shields.io/badge/SDG-11%20%7C%2013%20%7C%2016-green.svg)](https://sdgs.un.org/)
[![Architecture](https://img.shields.io/badge/Architecture-Local--First%20%7C%20Optional%20GenAI-38bdf8.svg)](#ethical-ai--humanitarian-data-governance)
[![Design](https://img.shields.io/badge/Design-Cybernetic%20HUD%20(Vector%20Icons)-purple.svg)](#command-center-features)

> **The Core Compass Directive:**  
> *"Our tool clusters and deduplicates disaster assistance calls reshared thousands of times on social media, elevating quiet, high-urgency single reports buried by popularity bias directly to the top of crisis dispatch queues."*

---

## The Problem: The Disaster Popularity Cascade Paradox

During major disasters (earthquakes, flash floods, hurricanes), social media platforms become informal emergency hotlines. However, platform recommendation algorithms are optimized for **engagement, retweets, and virality**—not humanitarian urgency:

1. **Cognitive Overload:** A single well-known building collapse can generate thousands of duplicate retweets and quote-tweets, flooding first-responder dashboards and creating a false perception of separate incidents.
2. **The Blind-Spot Danger:** A quiet report from a stranded victim with low follower count (0–5 retweets) detailing a newborn trapped under debris gets buried by the algorithm, resulting in preventable loss of life.
3. **Data Loss & Privacy Leaks:** Raw citizen telephone numbers are exposed publicly across social feeds, while well-intentioned filters often discard duplicate posts entirely, erasing vital timestamps and corroborating details.

**EchoFilter AI solves this challenge through an explainable, reverse-popularity crisis triage engine.**

---

## Sustainable Development Goals (SDG) Alignment

- **SDG 11 (Target 11.5):** Substantially reduce the number of deaths and people affected by disasters, with a direct operational focus on protecting vulnerable populations under rubble (infants, seniors, oxygen/insulin dependent).
- **SDG 13 (Target 13.1):** Strengthen resilience and digital response velocity during climate and extreme natural hazards.
- **SDG 16 (Target 16.6):** Build effective, accountable, and transparent emergency institutions through explainable, auditable triage logs.

---

## Core Benchmark Metrics (SRS 1.3)

| Metric | Target | EchoFilter AI Benchmark | Description |
| :--- | :--- | :--- | :--- |
| **Deduplication Efficiency** | Evaluation target | Demo output varies by input | Must be measured against a labeled test set before presenting as validated performance. |
| **Low-visibility prioritization** | Evaluation target | Rule-based flag at <15 reposts and urgency >=80 | This is a configured rule, not a measured recall result. |
| **Ingestion throughput** | Evaluation target | Measure in the target deployment | Timing depends on hardware, batch size, selected engine, and network. |
| **Data retention** | Preserve source records | SQLite persistence is implemented | Verify retention and recovery behavior before operational use. |

---

## Architectural Modules & SRS Compliance

- **FR-01 (Stream Ingestion):** Staged batch CSV/JSON ingestion and real-time live radar simulation.
- **FR-02 (Noise Separation):** Automated isolation of condolences, prayers, and generic broadcasts into the Noise Vault without deletion.
- **FR-03 (Entity Extraction & Parsing):** Extraction of regions, streets, building numbers, trapped persons, vulnerabilities (Infants, Elderly, Insulin/Oxygen, Mobility), and logistics needs (Heavy Cranes, USAR, Ambulances).
- **FR-04 (Semantic Deduplication):** Cross-post clustering of varied syntactic formulations under identical master incident coordinates (`CASE-XXX` vs `NOISE-XXX`).
- **FR-05 (Inverse Visibility Balancing):** Algorithmic inversion of social engagement to elevate low-RT, high-urgency reports to `SHADOWED_CRITICAL`.
- **FR-06 (Explainable Triage Scoring):** 1–100 Urgency Index paired with transparent, human-readable operator reasoning.
- **FR-07 (Human-in-the-Loop):** Dedicated Verification Desk for ambiguous or coordinate-deficient distress calls.
- **NFR-02 (Zero-Data-Loss Reliability):** SQLite database (`crisis_db.sqlite`) retaining every raw source message in expandable evidence blocks.
- **NFR-03 (Zero-Trust PII Masking):** Automated regex sanitization of victim phone numbers (`+1 (555) ***-**78`) with authorized command unmasking.
- **NFR-04 (Privacy-aware modes):** Offline deterministic rules plus optional external Gemini/OpenAI APIs with operator disclosure and consent.

---

## Command Center Navigation (The 5 Workspaces)

The interface is engineered as an **interactive Cybernetic HUD** using crisp vector SVG icons (zero emojis):

1. **Priority Incident Queue:**  
   Displays visibility-balanced master incidents. Includes instant filters for `Only Shadowed Critical` (<15 RTs) and `Infants / Children Involved`. Each card provides direct `[ Dispatch USAR Units ]` and `[ Mark Resolved ]` triggers.
2. **Human Verification Desk (HITL):**  
   Quarantines distress calls with missing street coordinates or vague descriptions for operator review and coordinate promotion.
3. **Live Simulation Radar:**  
   Interactive post generator to test live crisis signals against preset disaster scenarios (Trapped Newborn with 0 RT, Viral Downtown Cascade with 3,500 RT, Missing Location, Community Noise).
4. **Filtered Noise Vault:**  
   Quarantines well-wishes, prayers, and news updates without cluttering primary dispatch queues, maintaining a 100% auditable record.
5. **Executive SITREP & Export Center:**  
   Multi-format disaster reporting:
   - **Official Executive PDF Report (`.pdf`):** UN OCHA / FEMA Level-1 Situation Report (SITREP) generated via `fpdf2`.
   - **Printable HTML Dashboard Dossier (`.html`):** Standalone full-screen presentation dossier (`Ctrl+P` print-ready).
   - **CAD Interoperability Dataset (`.csv`):** Formatted for 112 / 911 / AKUT / AFAD computer-aided dispatch centers.
   - **Structured Geo-Incident Dataset (`.json`):** Full geospatial coordinates for GIS / ESRI mapping layers.

---

## Project Repository Structure

```text
echofilter-ai/
├── app.py                     # Streamlit Crisis Command Center HUD UI
├── crisis_triage.py           # Ingestion, NLP entity extraction, clustering & SQLite engine
├── report_generator.py        # FPDF2 official SITREP PDF and printable HTML compiler
├── icons.py                   # Standardized vector SVG icon system (28 icons)
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variable templates
├── .gitignore                 # Strict data privacy & zero-leakage ignore policy
├── README.md                  # Comprehensive technical documentation
├── SPEC.md                    # Software Requirements Specification (SRS) mapping
├── data/
│   ├── synthetic_incidents.csv # 60-post fictional English gold benchmark (0 PII, 10KB)
│   ├── DEPREMKIT_LICENSE.txt  # Dataset license terms
│   └── README.md              # Data governance & privacy documentation
└── scripts/
    ├── generate_synthetic_data.py   # Deterministic benchmark data generator
    └── prepare_depremkit_benchmark.py # Anonymization and staging pipeline
```

---

## Ethical AI & Humanitarian Data Governance

- **Multiple analysis modes:** The deterministic local rule engine works offline. Optional Gemini and OpenAI analysis send selected message text (with detected phone numbers masked) to the configured provider. The app asks for operator consent before these calls.
- **Anti-Popularity Bias Filter (FR-05):** Inverts social media engagement metrics to prevent algorithmically induced neglect of quiet emergency calls.
- **Local audit trail:** Raw posts are retained in SQLite for traceability. Restrict database access and define retention controls before handling real incident data.
- **PII masking:** Phone-like strings are masked in the display and in external-model payloads. Pattern matching can miss personal data; the prototype is not a guarantee of anonymization.
- **Human review:** Triage scores and extracted details are decision support only. Operators must verify reports before any dispatch action.

---

## Quickstart & Installation

### Prerequisites
- Python 3.10, 3.11, 3.12, or 3.13
- Git

### 1. Clone & Set Up Environment

```bash
# Clone the repository
git clone https://github.com/Irmakyil/<REPO_NAME>.git
cd echofilter-ai

# Create and activate a virtual environment
# Windows (PowerShell):
python -m venv .venv
.venv\Scripts\Activate.ps1

# Linux / macOS:
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Launch the Crisis Command Center

```bash
streamlit run app.py
```

Open your browser at: **`http://localhost:8502`**

---

## License & Credits

- **Event:** Generative AI for SDGs Hackathon (16–18 October 2026)
- **Team:** Group 3
- **License:** Open Humanitarian & Academic License (Apache 2.0 / MIT compatible)
