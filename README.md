# **Autonomous Infrastructure Compliance Auditor**

A fully air‑gapped, multi‑agent AI system designed to automate enterprise infrastructure compliance auditing across a structured **three‑tier maturity model** (Static Prototype → Emulated Cloud Sandbox → Model Context Protocol).

This system integrates **LangGraph**, **Ollama (`llama3.2`)**, **Moto**, and **FastMCP** to deliver deterministic, auditable, and HITL‑governed compliance assessments suitable for regulated enterprise environments. Tier 3 additionally dispatches the finished reports to stakeholders over email once a human operator approves them.

---

## **📌 Executive Summary**

The **Multi‑Agent DevSecOps Compliance Auditor** provides a secure, offline, and extensible architecture for evaluating cloud and infrastructure posture.  
It is purpose‑built for CISOs, security architects, and compliance engineering teams who require:

- Zero external cloud dependencies  
- Deterministic and reproducible audit pipelines  
- Human‑in‑the‑Loop (HITL) governance  
- Progressive integration from offline prototypes to enterprise protocol‑driven tooling  

---

## **🏛️ System Architecture Overview**

```
               +-------------------------------------------------+
               |            MULTI-AGENT STATE GRAPH              |
               |                                                 |
               |   [Agent 1: Evidence Collector]                 |
               |                 │                               |
               |                 ▼                               |
               |   [Risk Scoring Engine]  (Tier 3 only)          |
               |     Likelihood x Impact -> SOC2/NIST controls    |
               |     Deterministic — no LLM guesswork             |
               |                 │                               |
               |                 ▼                               |
               |   [Agent 2: Risk Compliance Auditor]            |
               |                 │                               |
               |                 ▼                               |
               |   [HITL Guardrail Checkpointer]                 |
               |         (Approve / Reject)                      |
               |                 │                               |
               |                 ▼                               |
               |   [Final CISO Compliance Report]                |
               |                 │                               |
               |                 ▼                               |
               |   [Email Dispatch Node]  (Tier 3 only)          |
               |     Executive + Technical reports sent          |
               |     via SMTP once HITL approval is given        |
               +-------------------------------------------------+
                                 │
                                 ▼  (scheduled, independent of the above)
               +-------------------------------------------------+
               |   [Continuous Monitoring — GitHub Actions]      |
               |     Daily cron + on-demand: Risk Scoring Engine  |
               |     runs headless, gates the build on Critical   |
               |     findings, posts a Slack alert if configured  |
               +-------------------------------------------------+
                                 │
     ┌───────────────────────────┼───────────────────────────┐
     ▼                           ▼                           ▼
+───────────────────+   +───────────────────+   +───────────────────+
|      TIER 1       |   |      TIER 2       |   |      TIER 3       |
|  Static Offline   |   |   Emulated Cloud  |   |    Enterprise     |
|     Prototype     |   |      Sandbox      |   |  MCP Integration  |
+───────────────────+   +───────────────────+   +───────────────────+
| Local JSON Files  |   | AWS Moto Emulator |   | FastMCP Protocol  |
|  (`mock_data/`)   |   |  (boto3 @ :4566)  |   |   Server (stdio)  |
+───────────────────+   +───────────────────+   +───────────────────+
```

---

## **📊 Enterprise Architecture Maturity Model**

| Tier | Directory | Telemetry Layer | Protocol | Primary Use Case |
|------|-----------|-----------------|----------|------------------|
| **Tier 1** | `tier1_static_prototype/` | Static JSON (`mock_data/`) | Local Python I/O | Deterministic offline prototyping |
| **Tier 2** | `tier2_cloud_sandbox/` | Moto AWS Emulator | boto3 SDK | Live telemetry parsing without external cloud |
| **Tier 3** | `tier3_enterprise_mcp/` | FastMCP + Moto | MCP (`stdio`) | Enterprise‑grade protocol integration, deterministic Likelihood×Impact risk scoring, SMTP email dispatch, and scheduled GitHub Actions continuous monitoring |

---

## **🛡️ Core Security & Design Principles**

- **Air‑Gapped Execution**  
  Runs entirely offline using Ollama; no external cloud calls.

- **Human‑in‑the‑Loop Governance**  
  LangGraph checkpointers enforce manual approval for high‑risk findings.

- **Protocol‑Driven Tooling (MCP)**  
  Infrastructure auditing tools are decoupled from LLM logic for enterprise portability.

- **Multi‑Agent Orchestration**  
  Separation of duties between evidence collection and risk evaluation aligns with enterprise security controls.

---

## **🤖 Full Multi‑Agent System Explanation**

### **1. Evidence Collector Agent**
Responsible for gathering all telemetry:

- Tier 1: Reads static JSON files  
- Tier 2: Queries Moto‑emulated AWS services  
- Tier 3: Invokes MCP tools via FastMCP  

Outputs normalized evidence for downstream analysis.

---

### **2. Risk Compliance Auditor Agent**
Evaluates evidence against:

- CIS AWS Benchmarks  
- Enterprise security baselines  
- IAM, encryption, and exposure policies  

Produces structured risk findings and compliance scoring. In Tier 3, the actual
scoring is deterministic (`risk_engine.py`): each finding gets a Likelihood (1-5) x
Impact (1-5) risk score, a Critical/High/Medium/Low severity bucket, and a mapping
to real SOC 2 and NIST 800-53 controls — computed in Python, not left to the LLM to
invent. The LLM's job is narrating those numbers, not generating them.

---

### **3. HITL Guardrail Checkpointer**
Before generating the final report, the workflow pauses.

A human operator must:

- Approve findings  
- Reject findings  
- Request additional evidence  

This ensures accountability and prevents autonomous high‑risk decisions.

---

### **4. Final CISO Compliance Report Generator**
Generates a defensible, audit‑ready report including:

- Executive summary  
- Risk findings  
- Evidence references  
- Recommended remediation steps  

Suitable for governance reviews and compliance documentation.

---

### **5. Email Dispatch Agent (Tier 3 only)**
Once the CISO Executive Summary and Engineering Remediation Playbook are generated and an operator approves dispatch at the HITL gate, `email_utils.py` sends both Markdown reports as attachments to stakeholders over SMTP (defaults to a `.env`‑configured recipient, or an address entered interactively at runtime).

---

### **6. Continuous Monitoring Agent (Tier 3 CI only)**
`continuous_scan.py`, run on a schedule by `.github/workflows/continuous-compliance-monitor.yml`,
executes just the deterministic Risk Scoring Engine — no Ollama, no HITL, no email — so it can run
unattended on GitHub-hosted runners. It publishes the findings as a GitHub Actions Job Summary and
a downloadable JSON artifact, optionally alerts Slack, and **fails the build when a Critical finding
is present**, turning the project from a script you run by hand into an actual continuous-monitoring
control, in the same "always-on control monitoring" language Vanta/Drata use.

---

## **🚀 Quick Start Guide**

### **Prerequisites**

- Linux / Kali Linux VM  
- Ollama running `llama3.2`  
- Python virtual environment  

---

### **Tier 1 — Static Offline Prototype**

```bash
cd tier1_static_prototype
python app.py
python app_humanloop.py
```

---

### **Tier 2 — Emulated Cloud Sandbox**

```bash
moto_server -p 4566 &
python app.py
```

---

### **Tier 3 — MCP Enterprise Integration**

Requires a `.env` file at the project root with SMTP credentials (see `tier3_enterprise_mcp/README.md`) so the Email Dispatch Agent can deliver reports after HITL approval.

```bash
cd tier3_enterprise_mcp
python app.py
```

To run just the deterministic risk scan (no Ollama, no HITL — the same thing the scheduled GitHub Action runs):

```bash
cd tier3_enterprise_mcp
python continuous_scan.py
```

---

## **📁 Repository Structure**

```
multi-agent-auditor/
├── README.md
├── .env                          # SMTP + shared credentials (gitignored; used by Tier 3)
├── .github/workflows/
│   └── continuous-compliance-monitor.yml  # Scheduled + on-demand Tier 3 risk scan (CI)
├── tier1_static_prototype/
│   ├── app.py                    # Automated pipeline (static JSON evidence)
│   ├── app_humanloop.py          # HITL guardrail pipeline
│   ├── tools.py                  # Reads mock_data/ (S3, Jira, ServiceNow)
│   ├── mock_data/
│   └── README.md
├── tier2_cloud_sandbox/
│   ├── app.py                    # LangGraph workflow + entry point (Moto/boto3)
│   ├── tools.py                  # Live boto3 S3 calls + simulated Jira/ServiceNow
│   └── README.md
└── tier3_enterprise_mcp/
    ├── app.py                    # Moto auto-manager, MCP client, HITL gate, Ollama, email trigger
    ├── mcp_server.py             # FastMCP server exposing S3 and Jira tools
    ├── risk_engine.py            # Deterministic Likelihood x Impact risk scoring + SOC2/NIST mapping
    ├── continuous_scan.py        # Non-interactive CI scan (no LLM) — drives the GH Actions workflow
    ├── pdf_report.py             # Markdown → styled PDF renderer + Risk Register table
    ├── email_utils.py            # SMTP dispatch of dual PDF reports as attachments
    ├── assets/                   # Execution screenshots
    ├── reports/                  # Generated audit report outputs + latest_risk_findings.json
    └── README.md
```

---
