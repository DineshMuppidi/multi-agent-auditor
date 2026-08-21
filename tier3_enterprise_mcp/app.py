import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Dict, Any

# 1. Initialize local Ollama LLM
llm = ChatOpenAI(
    model="llama3.2",
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

# 2. Define LangGraph Audit State
class AuditState(TypedDict):
    mcp_tools_output: Dict[str, Any]
    risk_assessment: str
    final_report: str

async def run_mcp_audit():
    # Configure MCP Client parameters to execute your mcp_server.py
    server_params = StdioServerParameters(
        command="python3",
        args=["tier3_enterprise_mcp/mcp_server.py"],
        env=None
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 1. Discover Tools available via MCP Protocol
            tools_response = await session.list_tools()
            print("\n📡 [MCP Layer] Successfully connected! Discovered Tools:")
            for tool in tools_response.tools:
                print(f"   • Tool Name: {tool.name} | Description: {tool.description}")

            # 2. Invoke MCP Tools standardized across the protocol
            print("\n🔍 [Agent 1: MCP Evidence Collector] Requesting live S3 & Jira telemetry...")
            s3_result = await session.call_tool("inspect_s3_buckets", {})
            jira_result = await session.call_tool("get_jira_compliance_status", {})

            collected_data = {
                "s3_buckets": json.loads(s3_result.content[0].text),
                "jira_tickets": json.loads(jira_result.content[0].text)
            }

            # 3. Pass MCP output through LangGraph LLM Pipeline
            print("⚖️ [Agent 2: Risk Compliance Agent] Evaluating MCP telemetry with Ollama...")
            prompt = f"Analyze the following security telemetry gathered via Model Context Protocol:\n{json.dumps(collected_data, indent=2)}\nHighlight security risks and actionable next steps."
            response = llm.invoke(prompt)

            print("\n=================== FINAL MCP AUDIT REPORT ===================")
            print(response.content)
            print("==============================================================")

if __name__ == "__main__":
    asyncio.run(run_mcp_audit())
