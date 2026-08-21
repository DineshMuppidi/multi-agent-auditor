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

# 1. Initialize Local Ollama LLM
llm = ChatOpenAI(
    model="llama3.2",
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MCP_SERVER_PATH = os.path.join(CURRENT_DIR, "mcp_server.py")


def ensure_moto_running():
    """Checks if local AWS emulator is running; auto-starts if offline."""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', 4566))
    sock.close()
    
    if result == 0:
        print("✅ [Auto-Manager] Local AWS Emulator (moto_server) is already running on port 4566.")
        return None
    else:
        print("🚀 [Auto-Manager] Starting background moto_server instance on port 4566...")
        proc = subprocess.Popen(
            ["moto_server", "s3", "-p", "4566"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        import time
        time.sleep(2)
        return proc


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

                # 3. LLM Call #1: Executive CISO Summary (No Code)
                print("\n⚖️ [Agent 2.1: Risk Auditor] Generating Executive CISO Summary with Ollama...")
                exec_prompt = f"""
You are a Lead CISO Compliance Auditor. Analyze the following security telemetry:
{json.dumps(collected_data, indent=2)}

Generate an Executive CISO Audit Report in Markdown.
STRICT RULES:
- DO NOT output code blocks, JSON, or AWS CLI commands.
- Focus ONLY on business risk, overall compliance score (0-100), telemetry risk matrix, and CIS AWS benchmarks violated.

Format:
# 📊 Executive CISO Security Audit Report
## 1. Executive Summary Brief
## 2. Key Telemetry Findings & Risk Matrix (Table format)
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
                        recipient_email=recipient
                    )
                else:
                    print("⚠️ [Dispatch Node] Approval declined. Dispatch cancelled.")

    finally:
        if moto_process:
            print("\n🧹 [Auto-Manager] Shutting down auto-started moto_server process...")
            moto_process.terminate()


if __name__ == "__main__":
    asyncio.run(run_mcp_audit())
