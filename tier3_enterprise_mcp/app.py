import os
import sys
import json
import asyncio
import subprocess
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_openai import ChatOpenAI

load_dotenv()

# Add directory to sys path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from email_utils import send_audit_report_email
from risk_engine import score_findings

# 1. Initialize Local Ollama LLM
llm = ChatOpenAI(
    model="llama3.2",
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MCP_SERVER_PATH = os.path.join(CURRENT_DIR, "mcp_server.py")


def _port_open(host, port):
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0


def ensure_moto_running(startup_timeout=15.0):
    """Checks if local AWS emulator is running; auto-starts if offline."""
    import time

    if _port_open('127.0.0.1', 4566):
        print("✅ [Auto-Manager] Local AWS Emulator (moto_server) is already running on port 4566.")
        return None

    print("🚀 [Auto-Manager] Starting background moto_server instance on port 4566...")
    proc = subprocess.Popen(
        ["moto_server", "-p", "4566"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    deadline = time.monotonic() + startup_timeout
    while time.monotonic() < deadline:
        if _port_open('127.0.0.1', 4566):
            return proc
        time.sleep(0.5)

    raise RuntimeError(f"moto_server did not start listening on port 4566 within {startup_timeout}s")


async def run_mcp_audit():
    moto_process = ensure_moto_running()
    
    server_params = StdioServerParameters(
        command="python3",
        args=[MCP_SERVER_PATH],
        env=None
    )

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # 1. Discover Tools via MCP
                tools_response = await session.list_tools()
                print("\n📡 [MCP Layer] Successfully connected! Discovered Tools:")
                for tool in tools_response.tools:
                    print(f"   • Tool Name: {tool.name} | Description: {tool.description}")

                # 2. Collect Telemetry
                print("\n🔍 [Agent 1: MCP Evidence Collector] Requesting live S3 & Jira telemetry...")
                s3_result = await session.call_tool("inspect_s3_buckets", {})
                jira_result = await session.call_tool("get_jira_compliance_status", {})

                collected_data = {
                    "s3_buckets": json.loads(s3_result.content[0].text),
                    "jira_tickets": json.loads(jira_result.content[0].text)
                }

                # 2b. Deterministic Risk Scoring (Likelihood x Impact, mapped to
                # SOC 2 / NIST 800-53 controls) — computed in Python, not guessed
                # by the LLM. See risk_engine.py.
                print("📐 [Agent 1b: Risk Scoring] Computing Likelihood x Impact risk register...")
                risk_result = score_findings(collected_data)
                compliance_score = max(0, min(100, 100 - risk_result["risk_exposure_index"]))
                counts = risk_result["severity_counts"]
                print(
                    f"   • Compliance Score: {compliance_score}/100  |  "
                    f"Critical: {counts['Critical']}  High: {counts['High']}  "
                    f"Medium: {counts['Medium']}  Low: {counts['Low']}"
                )

                # 3. LLM Call #1: Executive CISO Summary (No Code)
                print("\n⚖️ [Agent 2.1: Risk Auditor] Generating Executive CISO Summary with Ollama...")
                exec_prompt = f"""
You are a Lead CISO Compliance Auditor. A deterministic risk-scoring engine has
already analyzed the telemetry below and computed an authoritative risk register
(Likelihood x Impact, 1-25 scale, mapped to SOC 2 / NIST 800-53 controls). Do NOT
invent your own numeric risk scores or compliance score — reference the ones given.

Raw telemetry:
{json.dumps(collected_data, indent=2)}

Computed risk register (authoritative — use these numbers):
{json.dumps(risk_result, indent=2)}

Overall Compliance Score (authoritative): {compliance_score}/100

Generate an Executive CISO Audit Report in Markdown.
STRICT RULES:
- DO NOT output code blocks, JSON, or AWS CLI commands.
- DO NOT invent a different compliance score or risk matrix — narrate the ones given above.
- Focus on business risk narrative, what the risk register means for the organization, and CIS AWS benchmarks violated.

Format:
# 📊 Executive CISO Security Audit Report
## 1. Executive Summary Brief
## 2. Risk Register Narrative (reference the provided Likelihood/Impact findings — do not re-tabulate, a Risk Register table is attached separately)
## 3. CIS AWS Benchmark Violations
## 4. Strategic Governance Recommendations
"""
                exec_response = await llm.ainvoke(exec_prompt)
                executive_report = exec_response.content

                # 4. LLM Call #2: Technical Engineering Playbook (With Commands)
                print("🛠️ [Agent 2.2: Risk Auditor] Generating Technical Remediation Playbook with Ollama...")
                tech_prompt = f"""
You are a Senior DevSecOps Engineer. Based on this telemetry:
{json.dumps(collected_data, indent=2)}

The following findings were ranked by a deterministic risk-scoring engine
(highest risk_score first) — remediate in this order:
{json.dumps(risk_result["findings"], indent=2)}

Generate a Technical Remediation Playbook for Cloud Engineers in Markdown.

Format:
# 🛠️ Engineering Remediation Playbook
## 1. Overview of Affected Assets
## 2. Step-by-Step Remediation Commands
Provide valid AWS CLI bash commands for:
- Enabling AES-256 Server-Side Encryption (`aws s3api put-bucket-encryption`) on unencrypted buckets.
- Enabling Public Access Blocks (`aws s3api put-public-access-block`) on public buckets.
## 3. Ticket Closure Procedure
Instructions to verify fixes and update Jira tickets (e.g. COMP-101) to RESOLVED.
"""
                tech_response = await llm.ainvoke(tech_prompt)
                technical_playbook = tech_response.content

                print("\n=================== EXECUTIVE REPORT PREVIEW ===================")
                print(executive_report[:500] + "\n...[truncated for display]...")
                print("===============================================================")

                # 5. Human-in-the-Loop (HITL) Approval Gate
                print("\n🛑 [HITL Guardrail] Execution paused for operator review.")
                loop = asyncio.get_running_loop()
                user_approval = await loop.run_in_executor(
                    None, 
                    input, 
                    "Do you approve dispatching BOTH reports (Executive + Technical) to stakeholders? (yes/no): "
                )

                if user_approval.strip().lower() in ["yes", "y"]:
                    recipient = await loop.run_in_executor(
                        None, 
                        input, 
                        "Enter recipient email address (press Enter for default from .env): "
                    )
                    recipient = recipient.strip() if recipient.strip() else None

                    print("📧 [Dispatch Node] Human approval granted. Delivering dual reports via email...")
                    send_audit_report_email(
                        executive_report=executive_report,
                        technical_guide=technical_playbook,
                        recipient_email=recipient,
                        risk_result=risk_result
                    )
                else:
                    print("⚠️ [Dispatch Node] Approval declined. Dispatch cancelled.")

    finally:
        if moto_process:
            print("\n🧹 [Auto-Manager] Shutting down auto-started moto_server process...")
            moto_process.terminate()


if __name__ == "__main__":
    asyncio.run(run_mcp_audit())
