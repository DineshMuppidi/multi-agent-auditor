import json
import os

MOCK_DIR = os.path.join(os.path.dirname(__file__), "mock_data")

def fetch_aws_s3_config():
    """Fetches list of AWS S3 buckets and their security configurations."""
    path = os.path.join(MOCK_DIR, "aws_s3_buckets.json")
    with open(path, "r") as f:
        return json.load(f)

def fetch_jira_tickets():
    """Fetches active compliance tickets from Jira."""
    path = os.path.join(MOCK_DIR, "jira_compliance_tickets.json")
    with open(path, "r") as f:
        return json.load(f)

def fetch_servicenow_incidents():
    """Fetches security incidents from ServiceNow."""
    path = os.path.join(MOCK_DIR, "servicenow_incidents.json")
    with open(path, "r") as f:
        return json.load(f)

# Quick sanity check
if __name__ == "__main__":
    print("Testing Mock Tool Loaders:")
    print("AWS Data:", fetch_aws_s3_config())
    print("Jira Data:", fetch_jira_tickets())
    print("ServiceNow Data:", fetch_servicenow_incidents())
