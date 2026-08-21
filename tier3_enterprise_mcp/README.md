# Tier 3: Enterprise Multi-Agent Auditor (Model Context Protocol & HITL Dispatch)

This directory contains Tier 3 of the Multi-Agent DevSecOps Compliance Auditor project. In this module, local security auditing tools are decoupled into a standardized, production-ready Model Context Protocol (MCP) server architecture using FastMCP.

The pipeline features Human-in-the-Loop (HITL) safety governance, deterministic Likelihood x Impact risk scoring mapped to SOC 2 / NIST 800-53 controls, automated dual-document email dispatching for executive and engineering stakeholders, and a scheduled GitHub Actions workflow that turns the scan into continuous monitoring.

---

## System Architecture
 
 ![System Architecture](assets/system_arc.png)

### Key Highlights
- Single-Command Execution: app.py automatically checks and manages the background lifecycle of the local AWS emulator (moto_server) on port 4566, starting and shutting it down cleanly.
- Self-Contained & Decoupled: The FastMCP server auto-seeds S3 buckets (public-marketing-assets-temp, unencrypted-storage-bucket) and Jira compliance issues (COMP-101) upon tool invocation.
- Deterministic Risk Scoring: `risk_engine.py` scores every finding on Likelihood x Impact (1-25) and maps it to real SOC 2 and NIST 800-53 controls — computed in Python, not guessed by the LLM. See [Risk Scoring Methodology](#risk-scoring-methodology) below.
- Dual-Document Audience Separation: Generates two distinct audit reports:
  * CISO Executive Summary: deterministic compliance score, a full Risk Register table, and CIS AWS Benchmark violations.
  * Engineering Remediation Playbook: Valid AWS CLI bash commands and step-by-step patch scripts, ordered by risk score.
- Styled PDF Rendering: `pdf_report.py` converts each Markdown report into a branded, print-ready PDF (WeasyPrint) — cover band, a compliance score card computed by the risk engine, a Risk Register table with severity badges and control-ID chips, and dark-themed code blocks for CLI commands — instead of mailing raw `.md` text.
- Human-in-the-Loop (HITL) Safety Guardrail: Pauses execution until an operator explicitly approves dispatch in the terminal.
- Continuous Monitoring (CI): `continuous_scan.py` + a scheduled GitHub Actions workflow run the deterministic risk engine unattended, gate the build red on Critical findings, and optionally alert Slack. See [Continuous Monitoring](#continuous-monitoring-github-actions) below.
- 100% Local & Privacy-First: The interactive flow operates offline on Kali Linux using local Ollama (llama3.2) and Moto emulation without API costs or telemetry exposure.

---

## Folder Structure
```
tier3_enterprise_mcp/
├── app.py                     # Main orchestrator (auto-moto manager, MCP client, HITL, Ollama)
├── mcp_server.py             # FastMCP server exposing S3 and Jira tools with auto-seeding
├── risk_engine.py            # Deterministic Likelihood x Impact risk scoring + SOC2/NIST mapping
├── continuous_scan.py        # Non-interactive CI scan (no LLM) — used by the GH Actions workflow
├── pdf_report.py             # Markdown → styled PDF renderer (WeasyPrint) + Risk Register table
├── email_utils.py            # Multi-attachment MIME email dispatch module
├── README.md                 # Tier 3 project documentation
├── assets/                   # Execution screenshots and proof artifacts
│   ├── mcp_server_initiation.png
│   ├── hitl_operator_approval_prompt.png
│   └── smtp_email_received_proof.png
└── reports/                  # Generated audit report outputs
    ├── CISO_Executive_Summary.pdf
    ├── Engineering_Remediation_Playbook.pdf
    └── latest_risk_findings.json   # Written by continuous_scan.py each run

.github/workflows/
└── continuous-compliance-monitor.yml   # Scheduled + on-demand CI scan (repo root)
```
---

## Risk Scoring Methodology

`risk_engine.py` replaces "this control failed" with the same qualitative risk-matrix
method used in NIST SP 800-30 / ISO 27005 assessments — the muscle a GRC screen
actually tests for:

**Risk Score = Likelihood (1-5) x Impact (1-5)**, giving a 1-25 scale bucketed into:

| Risk Score | Severity |
|---|---|
| 20-25 | Critical |
| 12-19 | High |
| 6-11 | Medium |
| 1-5 | Low |

Each finding type carries a fixed Likelihood/Impact weight and a mapping to both
**SOC 2** and **NIST 800-53** controls:

| Finding | Likelihood | Impact | SOC 2 | NIST 800-53 |
|---|---|---|---|---|
| Public + unencrypted S3 bucket (compounding) | 5 | 5 | CC6.1, CC6.6, CC6.7 | AC-3, AC-4, SC-7, SC-28 |
| Publicly accessible S3 bucket | 5 | 4 | CC6.1, CC6.6 | AC-3, AC-4, SC-7 |
| Unencrypted S3 bucket | 3 | 4 | CC6.1, CC6.7 | SC-13, SC-28 |
| Open remediation ticket (POA&M) | 2 | 2 | CC7.2 | CA-5 |
| Open security incident | 3 | 2-4 (by priority) | CC7.3, CC7.4 | IR-4, IR-6 |

The engine also computes a **Risk Exposure Index** (0-100, higher = worse — the mean
risk score across all findings, scaled) and its inverse, the **Compliance Score**
(0-100, higher = better) shown on the Executive PDF's score card. Both `app.py` and
`continuous_scan.py` call `score_findings()` — it's the single source of truth for
numbers; the LLM in `app.py` is explicitly prompted to narrate the given findings,
not invent its own score or risk matrix.

---

## Execution Screenshots & Evidence

### 1. FastMCP Server Discovery & Telemetry Collection
When `app.py` runs, it connects to `mcp_server.py` over standard I/O transport, discovers exposed FastMCP tools (`inspect_s3_buckets`, `get_jira_compliance_status`), and queries live telemetry.

![MCP Server Initiation](assets/mcp_server_initiation.png)

---

### 2. Human-in-the-Loop (HITL) Approval Prompt
After local `llama3.2` synthesizes telemetry into dual Markdown reports, execution halts at an interactive security gate awaiting explicit operator confirmation before dispatching sensitive compliance findings.

![HITL Operator Approval Prompt](assets/hitl_operator_approval_prompt.png)

---

### 3. SMTP Email Dispatch Verification
Upon entering `yes` at the HITL prompt, `pdf_report.py` renders both Markdown reports into styled PDFs and `email_utils.py` connects to the configured SMTP server and delivers an email with both PDFs as attachments.

![SMTP Email Received Proof](assets/smtp_email_received_proof.png)

---

## Prerequisites & Setup

### 1. Virtual Environment Setup
Ensure your Python virtual environment is activated and required libraries are installed:

```bash
source venv/bin/activate
pip install "mcp[cli]" fastmcp boto3 "moto[server]" langchain-openai langgraph python-dotenv weasyprint markdown
```

`weasyprint` renders the PDFs and depends on system libraries (Pango, cairo, GDK-Pixbuf) for text/graphics layout — these are already present on this Kali image. On a fresh machine without them, install via `apt install libpango-1.0-0 libpangocairo-1.0-0 libcairo2 libgdk-pixbuf2.0-0` (Debian/Ubuntu) before `pip install weasyprint`.

### 2. Configure Credentials (.env)
Create a `.env` file at the **project root** (`~/multi-agent-auditor/.env`) — `email_utils.py` calls `load_dotenv()`, which walks up from the current working directory, so the root file is picked up whether you run `app.py` from `tier3_enterprise_mcp/` or elsewhere. The file is already gitignored.

```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-16-char-app-password
DEFAULT_RECIPIENT=recipient-email@example.com
```

Note: For Gmail, use a 16-character Google App Password (with 2FA enabled). If `SENDER_EMAIL`/`SENDER_PASSWORD` are missing, `email_utils.py` logs an error and skips dispatch rather than failing the whole run.

---

## How to Run

Execute the complete end-to-end pipeline with a single command from inside `tier3_enterprise_mcp`:

```bash
python app.py
```

At the HITL prompt, enter `yes` to approve dispatch, then either press Enter to send to `DEFAULT_RECIPIENT` from `.env` or type a different recipient address. Entering `no` skips email dispatch entirely.

To run just the deterministic risk scan without Ollama, HITL, or email (the same thing CI runs):

```bash
python continuous_scan.py
```

This prints a Markdown findings summary, writes `reports/latest_risk_findings.json`, and exits non-zero if any Critical finding is present.

---

## Continuous Monitoring (GitHub Actions)

`.github/workflows/continuous-compliance-monitor.yml` (repo root) runs `continuous_scan.py`
on a daily schedule (`cron: "0 13 * * *"`, plus manual `workflow_dispatch`):

1. Spins up `moto_server` and the FastMCP server, same as a local run.
2. Runs the deterministic risk engine — no Ollama dependency, so it works unattended on GitHub-hosted runners.
3. Writes the findings table to the workflow's **Job Summary** (Actions tab → run → Summary) — a zero-infrastructure "dashboard" with no hosting to set up.
4. Uploads `latest_risk_findings.json` as a 90-day workflow artifact.
5. Posts a Slack alert if the `SLACK_WEBHOOK_URL` repo secret is set (Settings → Secrets and variables → Actions → New repository secret). Skipped silently if not configured.
6. **Fails the job (red ❌) if any Critical finding is present** — the workflow functions as an actual compliance gate, not just a report generator.

The narrated Executive/Technical PDF + email dispatch flow intentionally stays a
human-run action (`python app.py`) — it needs a local Ollama model and a HITL
approval a CI runner can't provide. CI's job is fast, deterministic, continuous
scanning; the rich narrative report is a periodic human-triggered action, mirroring
how tools like Vanta/Drata separate always-on control monitoring from formal
audit-evidence generation.
