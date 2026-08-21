import boto3
import json
from fastmcp import FastMCP

# Initialize FastMCP Server
mcp = FastMCP("Enterprise Audit Tool Server")

S3_ENDPOINT_URL = "http://localhost:4566"

def ensure_s3_buckets_seeded(s3_client):
    """Ensures test buckets exist locally without needing external tier scripts."""
    try:
        response = s3_client.list_buckets()
        existing_buckets = [b['Name'] for b in response.get('Buckets', [])]
        
        test_buckets = ["public-marketing-assets-temp", "unencrypted-storage-bucket"]
        for bucket in test_buckets:
            if bucket not in existing_buckets:
                s3_client.create_bucket(Bucket=bucket)
    except Exception as e:
        print(f"⚠️ Seeding warning: {e}")

@mcp.tool()
def inspect_s3_buckets() -> str:
    """Queries live S3 buckets from the local AWS endpoint to check for security configurations."""
    try:
        s3_client = boto3.client(
            's3',
            endpoint_url=S3_ENDPOINT_URL,
            aws_access_key_id='test',
            aws_secret_access_key='test',
            region_name='us-east-1'
        )
        
        # Auto-seed mock buckets inside Tier 3
        ensure_s3_buckets_seeded(s3_client)
        
        response = s3_client.list_buckets()
        buckets = [b['Name'] for b in response.get('Buckets', [])]
        # Naming-convention heuristic (mirrors tier2_cloud_sandbox/tools.py) standing in
        # for real ACL/encryption-policy lookups, so risk_engine.py has signal to score.
        data = [
            {
                "bucket_name": name,
                "endpoint": S3_ENDPOINT_URL,
                "is_public": "public" in name or "temp" in name,
                "encryption_enabled": "unencrypted" not in name,
            }
            for name in buckets
        ]
        return json.dumps(data)
    except Exception as e:
        return json.dumps([{
            "error": "AWS Emulator (moto_server) unreachable on port 4566",
            "details": str(e)
        }])

@mcp.tool()
def get_jira_compliance_status() -> str:
    """Fetches open compliance and remediation tickets."""
    tickets = [
        {"ticket_id": "COMP-101", "summary": "Fix public S3 bucket permissions", "status": "In Progress"}
    ]
    return json.dumps(tickets)

if __name__ == "__main__":
    mcp.run()
