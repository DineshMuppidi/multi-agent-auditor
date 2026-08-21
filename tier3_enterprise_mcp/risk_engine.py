"""Deterministic risk-scoring layer.

Real GRC work isn't "this control failed / passed" — it's Likelihood x Impact,
mapped to a control framework, so remediation gets prioritized correctly.
This module applies that qualitative risk-matrix method (the same one used
in NIST SP 800-30 and ISO 27005 assessments) to raw AWS/Jira/ServiceNow
telemetry, so the LLM narrative layer has real numbers to explain instead of
inventing its own.

Risk score = Likelihood (1-5) x Impact (1-5), giving a 1-25 scale:
  20-25 Critical | 12-19 High | 6-11 Medium | 1-5 Low
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

SEVERITY_THRESHOLDS = [
    (20, "Critical"),
    (12, "High"),
    (6, "Medium"),
    (0, "Low"),
]


def _severity_for(risk_score: int) -> str:
    for threshold, label in SEVERITY_THRESHOLDS:
        if risk_score >= threshold:
            return label
    return "Low"


@dataclass
class Finding:
    finding_id: str
    resource: str
    category: str
    description: str
    likelihood: int  # 1-5: probability a threat actor exploits this
    impact: int       # 1-5: business/compliance consequence if realized
    soc2_controls: List[str]
    nist_800_53_controls: List[str]

    @property
    def risk_score(self) -> int:
        return self.likelihood * self.impact

    @property
    def severity(self) -> str:
        return _severity_for(self.risk_score)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "resource": self.resource,
            "category": self.category,
            "description": self.description,
            "likelihood": self.likelihood,
            "impact": self.impact,
            "risk_score": self.risk_score,
            "severity": self.severity,
            "soc2_controls": self.soc2_controls,
            "nist_800_53_controls": self.nist_800_53_controls,
        }


def _score_s3_bucket(bucket: Dict[str, Any]) -> Optional[Finding]:
    name = bucket.get("bucket_name", "unknown-bucket")
    is_public = bucket.get("is_public")
    is_encrypted = bucket.get("encryption_enabled")

    # Tools that haven't been upgraded to compute these flags yet (raw MCP
    # payloads pre-enrichment) fall back to the same naming heuristic Tier 2
    # uses, so every call site agrees on what "public"/"unencrypted" means.
    if is_public is None:
        is_public = "public" in name or "temp" in name
    if is_encrypted is None:
        is_encrypted = "unencrypted" not in name

    if is_public and not is_encrypted:
        return Finding(
            finding_id=f"S3-{name}",
            resource=name,
            category="Public & Unencrypted S3 Bucket",
            description=(
                f"'{name}' is internet-accessible AND stores data without server-side "
                "encryption — each finding compounds the other's exposure."
            ),
            likelihood=5,
            impact=5,
            soc2_controls=["CC6.1", "CC6.6", "CC6.7"],
            nist_800_53_controls=["AC-3", "AC-4", "SC-7", "SC-28"],
        )
    if is_public:
        return Finding(
            finding_id=f"S3-{name}",
            resource=name,
            category="Publicly Accessible S3 Bucket",
            description=f"'{name}' allows public access, exposing its contents to the internet.",
            likelihood=5,
            impact=4,
            soc2_controls=["CC6.1", "CC6.6"],
            nist_800_53_controls=["AC-3", "AC-4", "SC-7"],
        )
    if not is_encrypted:
        return Finding(
            finding_id=f"S3-{name}",
            resource=name,
            category="Unencrypted S3 Bucket",
            description=f"'{name}' does not enforce server-side encryption at rest.",
            likelihood=3,
            impact=4,
            soc2_controls=["CC6.1", "CC6.7"],
            nist_800_53_controls=["SC-13", "SC-28"],
        )
    return None


def _score_jira_ticket(ticket: Dict[str, Any]) -> Optional[Finding]:
    status = str(ticket.get("status", "")).strip().lower()
    if status in ("resolved", "closed", "done"):
        return None
    ticket_id = ticket.get("ticket_id", "UNKNOWN")
    summary = ticket.get("summary") or ticket.get("issue") or "Untracked remediation item"
    return Finding(
        finding_id=f"JIRA-{ticket_id}",
        resource=ticket_id,
        category="Open Remediation Item (POA&M)",
        description=f"'{summary}' is still {ticket.get('status', 'open')} and unverified as remediated.",
        likelihood=2,
        impact=2,
        soc2_controls=["CC7.2"],
        nist_800_53_controls=["CA-5"],
    )


def _score_servicenow_incident(incident: Dict[str, Any]) -> Optional[Finding]:
    state = str(incident.get("state", "")).strip().lower()
    if state in ("resolved", "closed"):
        return None
    incident_id = incident.get("incident_id", "UNKNOWN")
    description = incident.get("description", "Unresolved security incident")
    priority = str(incident.get("priority", "")).strip().lower()
    impact = 4 if priority == "high" else 3 if priority == "medium" else 2
    return Finding(
        finding_id=f"SNOW-{incident_id}",
        resource=incident_id,
        category="Open Security Incident",
        description=description,
        likelihood=3,
        impact=impact,
        soc2_controls=["CC7.3", "CC7.4"],
        nist_800_53_controls=["IR-4", "IR-6"],
    )


def score_findings(evidence: Dict[str, Any]) -> Dict[str, Any]:
    """Scores raw telemetry into a structured, ranked risk register.

    Accepts whatever subset of s3_buckets / jira_tickets / servicenow_incidents
    is present — Tier 2 and Tier 3 currently expose different subsets of
    evidence, and this stays agnostic to which ones are missing.
    """
    findings: List[Finding] = []

    for bucket in evidence.get("s3_buckets", []):
        f = _score_s3_bucket(bucket)
        if f:
            findings.append(f)

    for ticket in evidence.get("jira_tickets", []):
        f = _score_jira_ticket(ticket)
        if f:
            findings.append(f)

    for incident in evidence.get("servicenow_incidents", []):
        f = _score_servicenow_incident(incident)
        if f:
            findings.append(f)

    findings.sort(key=lambda f: f.risk_score, reverse=True)

    severity_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    for f in findings:
        severity_counts[f.severity] += 1

    max_possible_per_finding = 25
    if findings:
        risk_exposure_index = round(
            100 * sum(f.risk_score for f in findings) / (max_possible_per_finding * len(findings))
        )
    else:
        risk_exposure_index = 0

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        # 0-100, HIGHER = WORSE. Mean of each finding's risk_score/25, scaled.
        "risk_exposure_index": risk_exposure_index,
        "severity_counts": severity_counts,
        "finding_count": len(findings),
        "findings": [f.to_dict() for f in findings],
    }
