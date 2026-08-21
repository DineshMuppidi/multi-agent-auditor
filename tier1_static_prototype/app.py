import os
from typing import TypedDict
from dotenv import load_dotenv

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, END

# Import local tools
from tools import fetch_aws_s3_config, fetch_jira_tickets, fetch_servicenow_incidents

load_dotenv()

class AuditState(TypedDict):
    query: str
    raw_evidence: dict
    risk_assessment: str
    final_report: str

LOCAL_MODEL = "llama3.2"

def evidence_collector_node(state: AuditState) -> dict:
    """Agent 1: Collects raw telemetry and compliance tickets via local tools."""
    print("\n🔍 [Agent 1: Evidence Collector] Fetching data from enterprise tools...")
    
    evidence = {
        "aws_s3": fetch_aws_s3_config(),
        "jira_tickets": fetch_jira_tickets(),
        "servicenow_incidents": fetch_servicenow_incidents()
    }
    return {"raw_evidence": evidence}

def compliance_risk_node(state: AuditState) -> dict:
    """Agent 2: Evaluates collected evidence against compliance rules locally."""
    print("⚖️  [Agent 2: Compliance & Risk Agent] Analyzing security risks with Ollama...")
    
    llm = ChatOllama(model=LOCAL_MODEL, temperature=0)
    evidence = state["raw_evidence"]
    
    prompt = (
        "You are a Senior Compliance & Security Auditor.\n"
        "Analyze the following evidence gathered from AWS, Jira, and ServiceNow:\n\n"
        f"{evidence}\n\n"
        "Identify:\n"
        "1. Any security violations (e.g., publicly accessible S3 buckets, unencrypted storage).\n"
        "2. Active tickets/incidents addressing these issues.\n"
        "3. High-level severity rating (Low, Medium, High, Critical) for the overall security posture."
    )
    
    response = llm.invoke([SystemMessage(content=prompt)])
    return {"risk_assessment": response.content}

def reporter_node(state: AuditState) -> dict:
    """Agent 3: Compiles the assessment into a clean markdown audit report locally."""
    print("📝 [Agent 3: Reporting Agent] Compiling final audit report with Ollama...")
    
    llm = ChatOllama(model=LOCAL_MODEL, temperature=0)
    risk_data = state["risk_assessment"]
    
    prompt = (
        "You are an Executive Compliance Reporting Agent.\n"
        "Take the following risk analysis and structure it into a clean, professional Markdown report for CISO leadership:\n\n"
        f"{risk_data}\n\n"
        "Include sections for: Executive Summary, Key Audit Findings, and Recommended Actions."
    )
    
    response = llm.invoke([SystemMessage(content=prompt)])
    return {"final_report": response.content}

# Workflow Graph Setup
workflow = StateGraph(AuditState)
workflow.add_node("EvidenceCollector", evidence_collector_node)
workflow.add_node("ComplianceRisk", compliance_risk_node)
workflow.add_node("Reporter", reporter_node)

workflow.add_edge(START, "EvidenceCollector")
workflow.add_edge("EvidenceCollector", "ComplianceRisk")
workflow.add_edge("ComplianceRisk", "Reporter")
workflow.add_edge("Reporter", END)

app = workflow.compile()

if __name__ == "__main__":
    print("🚀 Starting Offline Multi-Agent Compliance Audit Flow...")
    initial_state = {"query": "Run quarterly cloud infrastructure security audit."}
    output = app.invoke(initial_state)
    
    print("\n=================== FINAL AUDIT REPORT ===================")
    print(output["final_report"])
    print("==========================================================")
