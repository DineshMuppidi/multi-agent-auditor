import os
import json
from typing import TypedDict, Dict, Any
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from tools import get_all_audit_evidence

# 1. Initialize local Ollama LLM
llm = ChatOpenAI(
    model="llama3.2",
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

# 2. Define State
class AuditState(TypedDict):
    raw_evidence: Dict[str, Any]
    risk_assessment: str
    final_report: str

# 3. Define Nodes
def evidence_collector_node(state: AuditState) -> Dict[str, Any]:
    print("\n🔍 [Agent 1: Evidence Collector] Querying live AWS S3 API & Dev Sandbox endpoints...")
    evidence = get_all_audit_evidence()
    return {"raw_evidence": evidence}

def compliance_risk_node(state: AuditState) -> Dict[str, Any]:
    print("⚖️ [Agent 2: Compliance & Risk Agent] Analyzing live security evidence with Ollama...")
    evidence_str = json.dumps(state["raw_evidence"], indent=2)
    
    prompt = f"""You are a Senior Cybersecurity Auditor. 
Analyze the following infrastructure evidence fetched live from AWS S3 and dev tools:

{evidence_str}

Identify critical security risks (e.g., unencrypted storage, public S3 buckets). Output concise key findings."""
    
    response = llm.invoke(prompt)
    return {"risk_assessment": response.content}

def reporting_node(state: AuditState) -> Dict[str, Any]:
    print("📝 [Agent 3: Reporting Agent] Compiling final executive report...")
    prompt = f"""Convert the following risk assessment into an Executive Security Vulnerability Report:

{state['risk_assessment']}

Include Executive Summary, Key Findings, and Actionable Remediation Steps."""
    
    response = llm.invoke(prompt)
    return {"final_report": response.content}

# 4. Build LangGraph Workflow
workflow = StateGraph(AuditState)
workflow.add_node("evidence_collector", evidence_collector_node)
workflow.add_node("compliance_risk", compliance_risk_node)
workflow.add_node("reporting", reporting_node)

workflow.add_edge(START, "evidence_collector")
workflow.add_edge("evidence_collector", "compliance_risk")
workflow.add_edge("compliance_risk", "reporting")
workflow.add_edge("reporting", END)

app = workflow.compile()

if __name__ == "__main__":
    print("🚀 Starting Moto‑Backed Cloud Emulation (Live Dev/Sandbox APIs) Multi-Agent Audit Flow...")
    result = app.invoke({"raw_evidence": {}, "risk_assessment": "", "final_report": ""})
    
    print("\n=================== FINAL AUDIT REPORT (OPTION B) ===================")
    print(result["final_report"])
