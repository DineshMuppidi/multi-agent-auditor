# Tier 3: Enterprise Multi-Agent Auditor (Model Context Protocol Interface)

This directory contains **Tier 3** of the Multi-Agent Compliance Auditor project. In this module, local python function calls are decoupled into a standardized, production-ready **Model Context Protocol (MCP)** server architecture using `FastMCP`.

---

## 🏛️ System Architecture
```
+-------------------------------------------------------------+
|                      LangGraph Client                       |
|                   (tier3_mcp/app.py)                        |
+-------------------------------------------------------------+
|                                     ^
| 1. Spawns Subprocess                | 3. Synthesizes Telemetry
v                                     |
+-----------------------+              +----------------------+
|     FastMCP Server    |              |   Local Ollama LLM   |
| (tier3_mcp/mcp_server)|              |     (llama3.2)       |
+-----------------------+              +----------------------+
|
| 2. Fetches AWS Telemetry
v
+-----------------------+
|   Local Moto AWS S3   |
| (http://localhost:4566) |
+-----------------------+
```

### Key Highlights
* **Zero Agent Rewrites:** The LLM client discovers tools via standardized MCP descriptors. If backend infrastructure changes, client logic remains untouched.
* **Fault-Tolerant Exception Handling:** The MCP server catches connection failures gracefully, providing fallback payloads if local cloud endpoints go offline.
* **Local First:** Runs completely offline on Kali Linux using local Moto AWS emulation and local Ollama (`llama3.2`).

---

## 📂 File Structure

```text
tier3_enterprise_mcp/
├── mcp_server.py   # FastMCP server exposing S3 and Jira auditing tools
├── app.py          # MCP client & LangGraph agent synthesizing telemetry
└── README.md       # Project documentation
```

🛠️ Prerequisites & Setup
Ensure your local virtual environment is active and required packages are installed:

```Bash
source venv/bin/activate
pip install "mcp[cli]" fastmcp boto3 langchain-openai langgraph
```

🚀 Execution Steps

Step 1: Start the Local AWS Endpoint (Moto)
In your terminal, launch moto_server on port 4566 in the background:

```Bash
moto_server -p 4566 > /dev/null 2>&1 &
```
Step 2: Seed Test S3 Buckets
Initialize dummy buckets in your local Moto environment:

```Bash
python3 -c "
import boto3
s3 = boto3.client('s3', endpoint_url='http://localhost:4566', aws_access_key_id='test', aws_secret_access_key='test', region_name='us-east-1')
s3.create_bucket(Bucket='public-marketing-assets-temp')
s3.create_bucket(Bucket='unencrypted-storage-bucket')
print('✅ Test S3 buckets initialized!')
"
```
Step 3: Run the MCP Multi-Agent Pipeline
Execute the main client script:

```Bash
python tier3_enterprise_mcp/app.py
```

📊 Expected Output

```Bash
Starting MCP server 'Enterprise Audit Tool Server' with transport 'stdio'

📡 [MCP Layer] Successfully connected! Discovered Tools:
   • Tool Name: inspect_s3_buckets | Description: Queries live S3 buckets from local AWS endpoint.
   • Tool Name: get_jira_compliance_status | Description: Fetches open compliance and remediation tickets.

🔍 [Agent 1: MCP Evidence Collector] Requesting live S3 & Jira telemetry...

⚖️ [Agent 2: Risk Compliance Agent] Evaluating MCP telemetry with Ollama...

=================== FINAL MCP AUDIT REPORT ===================
1. Executive Summary:
   - S3 Bucket 'public-marketing-assets-temp' contains public exposure risks.
   - S3 Bucket 'unencrypted-storage-bucket' lacks server-side encryption.

2. Jira Cross-Reference:
   - Ticket COMP-101 is actively tracking remediation.

3. Actionable Next Steps:
   - Block public access on 'public-marketing-assets-temp'.
   - Enable AES-256 server-side encryption on 'unencrypted-storage-bucket'.
==============================================================
