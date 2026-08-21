import boto3

# Configuration for local AWS S3 emulator (Moto / LocalStack)
S3_ENDPOINT_URL = "http://localhost:4566"

def fetch_s3_buckets():
    """Fetches real bucket metadata from the local S3 emulator API."""
    s3_client = boto3.client(
        's3',
        endpoint_url=S3_ENDPOINT_URL,
        aws_access_key_id='test',
        aws_secret_access_key='test',
        region_name='us-east-1'
    )
    
    response = s3_client.list_buckets()
    buckets_data = []
    
    for bucket in response.get('Buckets', []):
        name = bucket['Name']
        # Simulated compliance risk check based on bucket configuration/naming
        is_public = "public" in name or "temp" in name
        is_encrypted = "unencrypted" not in name
        
        buckets_data.append({
            "bucket_name": name,
            "region": "us-east-1",
            "is_public": is_public,
            "encryption_enabled": is_encrypted
        })
        
    return buckets_data

def fetch_jira_tickets():
    """Simulates querying live Jira/Issue tracker REST API endpoint."""
    return [
        {
            "ticket_id": "COMP-101",
            "issue": "Publicly Accessible S3 Bucket Detected",
            "status": "In Progress",
            "assignee": "DevSecOps Team"
        }
    ]

def fetch_servicenow_incidents():
    """Simulates querying live ServiceNow REST API endpoint."""
    return [
        {
            "incident_id": "INC0098234",
            "description": "Unencrypted Storage Bucket Identified",
            "priority": "High",
            "state": "Open"
        }
    ]

def get_all_audit_evidence():
    """Aggregates evidence across all live/sandbox developer endpoints."""
    return {
        "s3_buckets": fetch_s3_buckets(),
        "jira_tickets": fetch_jira_tickets(),
        "servicenow_incidents": fetch_servicenow_incidents()
    }

if __name__ == "__main__":
    print("🔍 Testing Live Sandbox Tools...")
    evidence = get_all_audit_evidence()
    print("Fetched Evidence:", evidence)
