"""Non-interactive continuous-monitoring scan for CI (GitHub Actions).

Unlike app.py, this does NOT depend on a local Ollama model or a human at a
terminal — it exists to run unattended on a schedule. It connects to the same
FastMCP server over stdio, runs the deterministic risk_engine (no LLM), and:

  1. Writes a findings JSON snapshot to reports/latest_risk_findings.json
  2. Writes a Markdown summary to $GITHUB_STEP_SUMMARY, if set (renders as a
     persistent "dashboard" page on the workflow run in GitHub's UI)
  3. Posts a Slack alert via SLACK_WEBHOOK_URL, if set
  4. Exits non-zero when any Critical finding exists, so the Action goes red
     and functions as an actual continuous-compliance gate
"""
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import asyncio

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from risk_engine import score_findings

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MCP_SERVER_PATH = os.path.join(CURRENT_DIR, "mcp_server.py")
REPORTS_DIR = os.path.join(CURRENT_DIR, "reports")
FINDINGS_PATH = os.path.join(REPORTS_DIR, "latest_risk_findings.json")

SEVERITY_EMOJI = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}


def _port_open(host: str, port: int) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0


def ensure_moto_running(startup_timeout: float = 15.0):
    if _port_open('127.0.0.1', 4566):
        print("✅ [Auto-Manager] Local AWS Emulator (moto_server) is already running on port 4566.")
        return None

    print("🚀 [Auto-Manager] Starting background moto_server instance on port 4566...")
    proc = subprocess.Popen(
        ["moto_server", "-p", "4566"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    deadline = time.monotonic() + startup_timeout
    while time.monotonic() < deadline:
        if _port_open('127.0.0.1', 4566):
            return proc
        time.sleep(0.5)

    raise RuntimeError(
        f"moto_server did not start listening on port 4566 within {startup_timeout}s"
    )


def _markdown_summary(risk_result: dict) -> str:
    counts = risk_result["severity_counts"]
    compliance_score = max(0, min(100, 100 - risk_result["risk_exposure_index"]))

    lines = [
        "## 🛡️ Continuous Compliance Monitor",
        "",
        f"**Compliance Score:** {compliance_score}/100  ",
        f"**Risk Exposure Index:** {risk_result['risk_exposure_index']}/100 (higher = worse)  ",
        f"**Scanned:** {risk_result['generated_at']}",
        "",
        f"🔴 Critical: {counts['Critical']}&nbsp;&nbsp;"
        f"🟠 High: {counts['High']}&nbsp;&nbsp;"
        f"🟡 Medium: {counts['Medium']}&nbsp;&nbsp;"
        f"🟢 Low: {counts['Low']}",
        "",
    ]

    if risk_result["findings"]:
        lines.append("| Severity | Resource | Finding | Risk Score | SOC 2 | NIST 800-53 |")
        lines.append("|---|---|---|---|---|---|")
        for f in risk_result["findings"]:
            emoji = SEVERITY_EMOJI.get(f["severity"], "")
            lines.append(
                f"| {emoji} {f['severity']} | {f['resource']} | {f['category']} | "
                f"{f['risk_score']}/25 | {', '.join(f['soc2_controls'])} | "
                f"{', '.join(f['nist_800_53_controls'])} |"
            )
    else:
        lines.append("No findings — all scanned resources passed control checks.")

    return "\n".join(lines) + "\n"


def _post_slack_alert(risk_result: dict, webhook_url: str):
    counts = risk_result["severity_counts"]
    compliance_score = max(0, min(100, 100 - risk_result["risk_exposure_index"]))
    top_findings = risk_result["findings"][:3]

    text_lines = [
        f"*🛡️ Continuous Compliance Monitor* — Score: *{compliance_score}/100*",
        f"🔴 Critical: {counts['Critical']}  🟠 High: {counts['High']}  "
        f"🟡 Medium: {counts['Medium']}  🟢 Low: {counts['Low']}",
    ]
    if top_findings:
        text_lines.append("Top findings:")
        for f in top_findings:
            text_lines.append(
                f"• [{f['severity']}] {f['resource']} — {f['category']} (risk {f['risk_score']}/25)"
            )

    payload = json.dumps({"text": "\n".join(text_lines)}).encode("utf-8")
    req = urllib.request.Request(
        webhook_url, data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        urllib.request.urlopen(req, timeout=10)
        print("✅ [Slack] Alert posted.")
    except urllib.error.URLError as e:
        print(f"❌ [Slack] Failed to post alert: {e}")


async def run_scan():
    moto_process = ensure_moto_running()

    server_params = StdioServerParameters(
        command="python3", args=[MCP_SERVER_PATH], env=None
    )

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                print("🔍 [Continuous Scan] Requesting live S3 & Jira telemetry via MCP...")
                s3_result = await session.call_tool("inspect_s3_buckets", {})
                jira_result = await session.call_tool("get_jira_compliance_status", {})

                evidence = {
                    "s3_buckets": json.loads(s3_result.content[0].text),
                    "jira_tickets": json.loads(jira_result.content[0].text),
                }

        risk_result = score_findings(evidence)

        os.makedirs(REPORTS_DIR, exist_ok=True)
        with open(FINDINGS_PATH, "w") as f:
            json.dump(risk_result, f, indent=2)
        print(f"📄 [Continuous Scan] Findings written to {FINDINGS_PATH}")

        summary_md = _markdown_summary(risk_result)
        print("\n" + summary_md)

        step_summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
        if step_summary_path:
            with open(step_summary_path, "a") as f:
                f.write(summary_md)

        webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
        if webhook_url:
            _post_slack_alert(risk_result, webhook_url)
        else:
            print("ℹ️ [Slack] SLACK_WEBHOOK_URL not set — skipping alert.")

        if risk_result["severity_counts"]["Critical"] > 0:
            print("\n🛑 Continuous monitoring gate FAILED — Critical findings present.")
            return 1

        print("\n✅ Continuous monitoring gate PASSED.")
        return 0

    finally:
        if moto_process:
            print("\n🧹 [Auto-Manager] Shutting down auto-started moto_server process...")
            moto_process.terminate()


if __name__ == "__main__":
    sys.exit(asyncio.run(run_scan()))
