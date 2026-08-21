# **Autonomous Infrastructure Compliance Auditor**

A fully air‑gapped, multi‑agent AI system designed to automate enterprise infrastructure compliance auditing across a structured **three‑tier maturity model** (Static Prototype → Emulated Cloud Sandbox → Model Context Protocol).

This system integrates **LangGraph**, **Ollama (`llama3.2`)**, **Moto**, and **FastMCP** to deliver deterministic, auditable, and HITL‑governed compliance assessments suitable for regulated enterprise environments.

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
               |   [Agent 2: Risk Compliance Auditor]            |
               |                 │                               |
               |                 ▼                               |
               |   [HITL Guardrail Checkpointer]                 |
               |         (Approve / Reject)                      |
               |                 │                               |
               |                 ▼                               |
               |   [Final CISO Compliance Report]                |
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
| **Tier 3** | `tier3_enterprise_mcp/` | FastMCP + Moto | MCP (`stdio`) | Enterprise‑grade protocol integration |

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

Produces structured risk findings and compliance scoring.

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
moto_server s3 -p 4566 &
python app.py
```

---

### **Tier 3 — MCP Enterprise Integration**

```bash
cd tier3_enterprise_mcp
python app.py
```

---

## **📁 Repository Structure**

```
multi-agent-auditor/
├── README.md
├── tier1_static_prototype/
│   ├── app.py
│   ├── app_humanloop.py
│   ├── tools.py
│   └── mock_data/
├── tier2_cloud_sandbox/
│   ├── app.py
│   ├── app_humanloop.py
│   └── README.md
└── tier3_enterprise_mcp/
    ├── app.py
    ├── mcp_server.py
    └── README.md
```

---

## **📜 License**

MIT License

---

If you want, I can also generate:

- **A CISO Executive Briefing**  
- **A Threat Model Section**  
- **Mermaid Architecture Diagrams**  
- **CIS Benchmark Mapping**  

Just tell me which one you want next.
