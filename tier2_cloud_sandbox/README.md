# Tier 2: Local AWS Sandbox Auditor  
### Moto‑Backed Cloud Emulation & Boto3 Telemetry Collection

Tier 2 introduces a realistic **local cloud sandbox** using Moto to emulate AWS services and Boto3 to query them. This tier upgrades the system from static JSON mocks (Tier 1) to **live infrastructure scanning**, enabling your LangGraph workflow to interact with actual S3 buckets, metadata, and permissions — all without touching real AWS.

---

## 🏛️ System Architecture
```
+-------------------------------------------------------------+
|                     LangGraph Agent Workflow                |
|                     (tier2_sandbox/app.py)                  |
+-------------------------------------------------------------+
|                                         |
| 1. Directly Invokes Boto3 SDK           | 2. Passes Telemetry
v                                         v
+-----------------------+                 +--------------------+
|   Local Moto AWS S3   |                 |   Local Ollama LLM |
| (http://localhost:4566)                 |      (llama3.2)    |
+-----------------------+                 +--------------------+
```

### 🔑 Key Highlights
- **Live API Telemetry:** Replaces static JSON with real Boto3 calls against a running Moto S3 emulator.  
- **Zero AWS Costs:** No IAM roles, no AWS credentials, no billing — everything runs offline.  
- **Realistic Cloud Scanning:** Buckets, ACLs, encryption flags, and metadata are inspected exactly as they would be in AWS.  
- **LLM‑Driven Analysis:** Telemetry is passed to a local Ollama model (`llama3.2`) for risk evaluation and report generation.

---

## 📂 File Structure

```text
tier2_sandbox_aws/
├── audit_agent.py   # LangGraph workflow performing Boto3 S3 scans
├── app.py           # Entry point for Tier 2 audit pipeline
└── README.md        # Documentation for Tier 2 module
```
🛠️ Prerequisites & Setup
Activate your virtual environment and install required dependencies:

```bash
source venv/bin/activate
pip install moto boto3 langchain-openai langgraph
```
🚀 Execution Steps

Step 1 — Start Local AWS Emulator (Moto)
```bash
moto_server -p 4566 > /dev/null 2>&1 &
```
Step 2 — Seed Test S3 Buckets
```bash
python3 -c "
import boto3
s3 = boto3.client('s3', endpoint_url='http://localhost:4566',
                  aws_access_key_id='test', aws_secret_access_key='test',
                  region_name='us-east-1')
s3.create_bucket(Bucket='public-marketing-assets-temp')
s3.create_bucket(Bucket='unencrypted-storage-bucket')
print('✅ Test S3 buckets initialized in Moto!')
"
```
Step 3 — Run the Tier 2 Audit Pipeline
```bash
python tier2_sandbox_aws/app.py
```
📊 Expected Output
```text
🔍 [Agent 1: Evidence Collector] Scanning live emulated AWS S3 endpoint (http://localhost:4566)...
   • Found Bucket: public-marketing-assets-temp
   • Found Bucket: unencrypted-storage-bucket

⚖️ [Agent 2: Risk Compliance Agent] Evaluating telemetry with Ollama (llama3.2)...

=================== FINAL TIER 2 AUDIT REPORT ===================
1. Discovered Resources:
   - Target Endpoint: http://localhost:4566
   - Scanned S3 Buckets: 'public-marketing-assets-temp', 'unencrypted-storage-bucket'

2. Security Findings:
   - Potential public access exposure on 'public-marketing-assets-temp'.
   - Missing server-side encryption on 'unencrypted-storage-bucket'.

3. Remediation Recommendations:
   - Enforce S3 Block Public Access policies.
   - Apply default KMS/AES-256 bucket encryption.
================================================================

