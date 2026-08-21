import os
from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_ollama import ChatOllama
import tools  # Local tools module reading JSON files

# 1. Define State Schema
class AuditState(TypedDict):
    evidence_data: dict
    risk_analysis: str
    final_report: str
    approved: bool

# 2. Initialize Ollama LLM
llm = ChatOllama(model="llama3.2", temperature=0)

# 3. Define Graph Nodes

def evidence_collector_node(state: AuditState) -> dict:
    print("\n🔍 [Agent 1: Evidence Collector] Reading mock infrastructure data...")
    aws_data = tools.fetch_aws_s3_config()
    jira_data = tools.fetch_jira_tickets()
    servicenow_data = tools.fetch_servicenow_incidents()
    
    evidence = {
        "aws_s3": aws_data,
        "jira_tickets": jira_data,
        "servicenow_incidents": servicenow_data
    }
    return {"evidence_data": evidence}

def compliance_risk_node(state: AuditState) -> dict:
    print("⚖️  [Agent 2: Compliance & Risk Agent] Analyzing security vulnerabilities...")
    evidence = state.get("evidence_data", {})
    
    prompt = f"""
    You are a Senior Compliance & Risk Auditor. Review the following evidence:
    {evidence}
    
    Identify:
    1. Unencrypted or publicly exposed S3 buckets.
    2. Open high-severity Jira tickets.
    3. Critical unresolved ServiceNow incidents.
    Summarize risks clearly in bullet points.
    """
    
    response = llm.invoke([SystemMessage(content=prompt)])
    return {"risk_analysis": response.content}

def human_approval_node(state: AuditState) -> dict:
    """Node where execution pauses for human review before report formatting."""
    print("\n🛑 [Human Guardrail Triggered] Reviewing risk findings before final report generation...")
    print("--------------------------------------------------")
    print(state.get("risk_analysis"))
    print("--------------------------------------------------")
    
    user_input = input("👉 Approve generating and sending the CISO report? (yes/no): ").strip().lower()
    
    if user_input in ["yes", "y"]:
        print("✅ Approval received! Proceeding to report generation...")
        return {"approved": True}
    else:
        print("❌ Approval denied! Aborting final report execution.")
        return {"approved": False}

def reporting_node(state: AuditState) -> dict:
    if not state.get("approved"):
        return {"final_report": "REPORT CANCELLED BY AUDITOR APPROVAL GUARDRAIL."}
        
    print("\n📝 [Agent 3: Reporting Agent] Formatting Executive CISO Compliance Report...")
    risk_analysis = state.get("risk_analysis", "")
    
    prompt = f"""
    Format the following risk analysis into a professional Executive Compliance Report for the CISO:
    {risk_analysis}
    Include Executive Summary, Detailed Findings, and Recommended Actions.
    """
    
    response = llm.invoke([SystemMessage(content=prompt)])
    return {"final_report": response.content}

# 4. Build State Graph
workflow = StateGraph(AuditState)

workflow.add_node("EvidenceCollector", evidence_collector_node)
workflow.add_node("ComplianceRisk", compliance_risk_node)
workflow.add_node("HumanApproval", human_approval_node)
workflow.add_node("ReportingAgent", reporting_node)

workflow.set_entry_point("EvidenceCollector")

workflow.add_edge("EvidenceCollector", "ComplianceRisk")
workflow.add_edge("ComplianceRisk", "HumanApproval")

# Conditional path based on human decision
def check_approval(state: AuditState):
    if state.get("approved"):
        return "ReportingAgent"
    return END

workflow.add_conditional_edges("HumanApproval", check_approval, ["ReportingAgent", END])
workflow.add_edge("ReportingAgent", END)

# 5. Compile Graph with Checkpointer (Required for interrupts/state persistence)
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

# 6. Run Execution Pipeline
if __name__ == "__main__":
    initial_state = {
        "evidence_data": {},
        "risk_analysis": "",
        "final_report": "",
        "approved": False
    }
    
    # Thread ID is required when using checkpointers
    config = {"configurable": {"thread_id": "audit_session_1"}}
    
    print("🚀 Starting Multi-Agent Compliance Audit Flow (with HITL Guardrails)...")
    output = app.invoke(initial_state, config=config)
    
    print("\n================ FINAL REPORT OUTPUT ================")
    print(output.get("final_report"))
