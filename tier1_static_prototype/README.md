# Tier 1: Static Offline Prototype

Welcome to **Tier 1** of the Multi-Agent DevSecOps Compliance Auditor. This tier serves as the **Proof-of-Concept (PoC)** maturity layer , designed to validate multi-agent state graphs, tool-calling workflows, and governance guardrails completely offline using static JSON files.

---

## 📌 Directory Structure

```text
tier1_static_prototype/
├── app.py              # Automated pipeline (runs autonomously end-to-end)
├── app_humanloop.py    # Guardrail pipeline (requires explicit human approval)
├── tools.py            # Local file I/O tools for reading mock telemetry
└── mock_data/          # Static JSON telemetry files (AWS S3, Jira, etc.)

```

---

## 🔍 Overview & Capabilities

* 
**Zero-Dependency Prototyping**: Operates completely offline without external cloud SDK connections, local emulators, or active network ports.
* 
**Deterministic Tool Execution**: Custom file-reading tools in `tools.py` ingest mock AWS S3 configurations and Jira ticketing states from `mock_data/`.
* 
**State Graph Orchestration**: Built with **LangGraph** to coordinate multi-agent transitions between evidence collection, compliance analysis, and report generation.
* 
**Dual Execution Modes**: Provides both fully automated execution (`app.py`) and explicit Human-in-the-Loop governance (`app_humanloop.py`) to demonstrate controlled risk mitigation.

---

## 🚀 Execution Guide & Workflow Modes

### Prerequisites

Ensure your virtual environment is active and your local **Ollama** LLM engine (`llama3.2`) is running:

```bash
# From the project root (~/multi-agent-auditor)
source venv/bin/activate
ollama run llama3.2

```

Navigate to the Tier 1 directory:

```bash
cd ~/multi-agent-auditor/tier1_static_prototype

```

---

### Execution Modes

#### Option A: Standard Automated Pipeline (`app.py`)

Executes the multi-agent compliance scan autonomously from start to finish using the provided set of JSON files. It ingests the telemetry data, processes it through the agent workflow, and directly prints the finalized CISO audit report without pausing.

```bash
python app.py

```

#### Option B: Human-in-the-Loop (HITL) Guardrail Pipeline (`app_humanloop.py`)

Demonstrates strict security governance using LangGraph state checkpointers (`MemorySaver`). Before the final compliance report is generated, the workflow interrupts its execution at high-risk decision points and prompts the user in the terminal for manual confirmation.

```bash
python app_humanloop.py

```

> **What to expect in HITL mode:** The execution will pause and prompt you in the terminal:
> `Proceed with generating high-risk compliance report? (yes/no):`
> Entering `yes` resumes the graph state and outputs the final report; entering `no` safely aborts report generation.
> 
> 

---

## ⚙️ How It Works Under the Hood

```
[mock_data/*.json] ──> [tools.py] ──> [Agent 1: Evidence Collector]
                                              │
                                              ▼
                                   [Agent 2: Compliance Auditor]
                                              │
         ┌────────────────────────────────────┴────────────────────────────────────┐
         ▼                                                                         ▼
  [app.py Pipeline]                                                    [app_humanloop.py Pipeline]
         │                                                                         │
         ▼                                                                         ▼
[Auto-Generated Report]                                               [HITL MemorySaver Guardrail]
                                                                                   │
                                                                           (Approve / Reject)
                                                                                   │
                                                                                   ▼
                                                                     [Confirmed CISO Audit Report]

```
