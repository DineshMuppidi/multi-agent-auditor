"""Renders LLM-generated Markdown audit reports into styled, print-ready PDFs.

Used by email_utils.py to attach polished PDF reports instead of raw .md text.
"""
import re
from datetime import datetime

import markdown as md_lib
from weasyprint import HTML

BRAND_NAME = "Multi-Agent DevSecOps Compliance Auditor"

# Matches the "[**Audit Score**: 60/100]" style line the LLM is prompted to
# emit at the end of the Executive report. Pulled out and rendered as a
# dedicated score card instead of being left as a plain bracketed sentence.
_SCORE_PATTERN = re.compile(r"\[\s*\*\*([^*]+)\*\*:\s*(\d{1,3})\s*/\s*100\s*\]")

# Severity / status words that are meaningful as standalone table cell values
# in these reports (risk matrices, ticket status columns). Only whole-cell
# matches are styled so prose elsewhere is never touched.
_BADGE_WORDS = {
    "critical": "badge-critical",
    "high": "badge-high",
    "medium": "badge-medium",
    "low": "badge-low",
    "open": "badge-high",
    "in progress": "badge-medium",
    "resolved": "badge-low",
    "closed": "badge-low",
}
_BADGE_PATTERN = re.compile(
    r"(<td[^>]*>)\s*(" + "|".join(re.escape(w) for w in _BADGE_WORDS) + r")\s*(</td>)",
    re.IGNORECASE,
)

REPORT_CSS = """
@page {
    size: A4;
    margin: 2.4cm 1.8cm 2.4cm 1.8cm;
    @bottom-left {
        content: "CONFIDENTIAL \\2014 INTERNAL DISTRIBUTION ONLY";
        font-family: 'Liberation Sans', Arial, sans-serif;
        font-size: 7.5pt;
        letter-spacing: 0.5px;
        color: #a0aec0;
    }
    @bottom-right {
        content: "Page " counter(page) " of " counter(pages);
        font-family: 'Liberation Sans', Arial, sans-serif;
        font-size: 7.5pt;
        color: #a0aec0;
    }
}

* { box-sizing: border-box; }

body {
    font-family: 'Liberation Sans', 'Helvetica Neue', Arial, sans-serif;
    font-size: 10.3pt;
    line-height: 1.55;
    color: #1a202c;
}

.topbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 10px;
    border-bottom: 2px solid #1a365d;
    margin-bottom: 4px;
}
.topbar .brand {
    font-size: 10.5pt;
    font-weight: 700;
    color: #1a365d;
    letter-spacing: 0.2px;
}
.topbar .doc-tag {
    font-size: 8pt;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: #ffffff;
    background: #2b6cb0;
    padding: 4px 10px;
    border-radius: 3px;
}
.meta-line {
    font-size: 8pt;
    color: #718096;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    margin: 6px 0 22px 0;
}

h1 {
    font-size: 20pt;
    color: #1a365d;
    margin: 0 0 6px 0;
    padding-bottom: 10px;
    border-bottom: 3px solid #2b6cb0;
}
h2 {
    font-size: 13pt;
    color: #1a365d;
    background: #ebf4ff;
    border-left: 4px solid #2b6cb0;
    padding: 6px 10px;
    margin: 26px 0 12px 0;
    page-break-after: avoid;
}
h3 {
    font-size: 11pt;
    color: #2d3748;
    margin: 18px 0 8px 0;
    page-break-after: avoid;
}
p { margin: 0 0 10px 0; }
ul, ol { margin: 0 0 12px 0; padding-left: 22px; }
li { margin-bottom: 4px; }

table {
    width: 100%;
    border-collapse: collapse;
    margin: 10px 0 18px 0;
    font-size: 9.3pt;
}
th {
    background: #1a365d;
    color: #ffffff;
    text-align: left;
    padding: 7px 9px;
    font-weight: 700;
}
td {
    padding: 7px 9px;
    border-bottom: 1px solid #e2e8f0;
    vertical-align: top;
}
tr:nth-child(even) td { background: #f7fafc; }
tr { page-break-inside: avoid; }

.badge {
    display: inline-block;
    padding: 2px 9px;
    border-radius: 10px;
    font-size: 8.3pt;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.3px;
    color: #ffffff;
}
.badge-critical { background: #742a2a; }
.badge-high { background: #c53030; }
.badge-medium { background: #c05621; }
.badge-low { background: #2f855a; }

code {
    font-family: 'Liberation Mono', 'DejaVu Sans Mono', monospace;
    background: #edf2f7;
    color: #b83280;
    padding: 1px 5px;
    border-radius: 3px;
    font-size: 9pt;
}
pre {
    background: #0f172a;
    color: #e2e8f0;
    padding: 12px 14px;
    border-radius: 6px;
    margin: 10px 0 16px 0;
    white-space: pre-wrap;
    word-break: break-word;
    page-break-inside: avoid;
}
pre code {
    background: none;
    color: inherit;
    padding: 0;
    font-size: 8.7pt;
    line-height: 1.5;
}
blockquote {
    border-left: 4px solid #cbd5e0;
    color: #4a5568;
    font-style: italic;
    margin: 10px 0;
    padding: 2px 14px;
}

.score-card {
    width: 60%;
    margin: 6px auto 26px auto;
    padding: 18px 22px;
    text-align: center;
    background: #f7fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
}
.score-card .score-value {
    font-size: 34pt;
    font-weight: 700;
}
.score-card .score-max {
    font-size: 13pt;
    color: #a0aec0;
    font-weight: 400;
}
.score-card .score-label {
    font-size: 8.5pt;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: #718096;
    margin-top: 2px;
}
.score-card .score-bar {
    height: 7px;
    background: #e2e8f0;
    border-radius: 4px;
    margin: 12px 0 8px 0;
    overflow: hidden;
}
.score-card .score-bar-fill {
    height: 100%;
    border-radius: 4px;
}
.score-card .score-tier {
    font-size: 9pt;
    font-weight: 700;
    letter-spacing: 0.3px;
}

.risk-register-title {
    font-size: 9pt;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    color: #718096;
    margin: 4px 0 8px 0;
}
.control-chip {
    display: inline-block;
    background: #edf2f7;
    color: #2d3748;
    border: 1px solid #cbd5e0;
    border-radius: 3px;
    padding: 1px 6px;
    margin: 1px 3px 1px 0;
    font-size: 7.8pt;
    font-family: 'Liberation Mono', 'DejaVu Sans Mono', monospace;
}
.finding-resource { font-weight: 700; }
.finding-category { color: #718096; font-size: 8.6pt; }
"""


def _score_tier(score: int):
    if score >= 80:
        return "#2f855a", "Strong Posture"
    if score >= 50:
        return "#c05621", "Moderate Risk"
    return "#c53030", "Critical Risk"


def _score_card_html(label: str, score: int) -> str:
    color, tier = _score_tier(score)
    return f"""
    <div class="score-card">
        <div class="score-value" style="color:{color};">{score}<span class="score-max">/100</span></div>
        <div class="score-label">{label}</div>
        <div class="score-bar"><div class="score-bar-fill" style="width:{score}%; background:{color};"></div></div>
        <div class="score-tier" style="color:{color};">{tier}</div>
    </div>
    """


def _extract_score_card(markdown_text: str):
    """Fallback path: pulls a trailing "[**Label**: NN/100]" line out of the
    markdown if present and returns (remaining_markdown, score_card_html_or_None).
    Only used when the caller doesn't pass a deterministic compliance_score —
    the risk engine's score should always be preferred over an LLM-guessed one.
    """
    match = _SCORE_PATTERN.search(markdown_text)
    if not match:
        return markdown_text, None

    label, score = match.group(1).strip(), int(match.group(2))
    remaining = (markdown_text[: match.start()] + markdown_text[match.end():]).strip()
    return remaining, _score_card_html(label, score)


CONTROL_FRAMEWORK_LABELS = {
    "soc2_controls": "SOC 2",
    "nist_800_53_controls": "NIST 800-53",
}

_SEVERITY_BADGE_CLASS = {
    "Critical": "badge-critical",
    "High": "badge-high",
    "Medium": "badge-medium",
    "Low": "badge-low",
}


def _control_chips(control_ids) -> str:
    return "".join(f'<span class="control-chip">{c}</span>' for c in control_ids)


def render_risk_register(findings) -> str:
    """Renders a deterministic Likelihood x Impact risk register table from
    risk_engine.score_findings()["findings"]. Returns "" if there's nothing
    to show, so callers can splice it in unconditionally."""
    if not findings:
        return ""

    rows = []
    for f in findings:
        badge_class = _SEVERITY_BADGE_CLASS.get(f["severity"], "badge-low")
        rows.append(f"""
        <tr>
            <td>
                <span class="finding-resource">{f['resource']}</span><br>
                <span class="finding-category">{f['category']}</span>
            </td>
            <td>
                {_control_chips(f['soc2_controls'])}<br>
                {_control_chips(f['nist_800_53_controls'])}
            </td>
            <td style="text-align:center;">{f['likelihood']}</td>
            <td style="text-align:center;">{f['impact']}</td>
            <td style="text-align:center;font-weight:700;">{f['risk_score']}</td>
            <td><span class="badge {badge_class}">{f['severity']}</span></td>
        </tr>
        """)

    return f"""
    <div class="risk-register-title">Risk Register — Deterministic Likelihood &times; Impact Scoring</div>
    <table>
        <thead>
            <tr>
                <th>Resource / Finding</th>
                <th>Mapped Controls (SOC 2 / NIST 800-53)</th>
                <th style="text-align:center;">Likelihood</th>
                <th style="text-align:center;">Impact</th>
                <th style="text-align:center;">Risk Score</th>
                <th>Severity</th>
            </tr>
        </thead>
        <tbody>
            {''.join(rows)}
        </tbody>
    </table>
    """


def render_report_pdf(
    markdown_text: str,
    doc_tag: str,
    compliance_score: dict = None,
    risk_findings: list = None,
) -> bytes:
    """Converts a Markdown compliance report into a styled PDF and returns
    the raw PDF bytes.

    doc_tag: short label shown in the top-right pill, e.g. "Executive Summary"
             or "Remediation Playbook".
    compliance_score: optional {"label": str, "score": int 0-100, higher=better}
             computed deterministically by risk_engine — takes priority over
             any "[**Label**: NN/100]" bracket the LLM may have written.
    risk_findings: optional list of risk_engine finding dicts, rendered as a
             Risk Register table beneath the score card.
    """
    body_markdown, extracted_card_html = _extract_score_card(markdown_text)

    if compliance_score is not None:
        score_card_html = _score_card_html(compliance_score["label"], compliance_score["score"])
        # Still strip any LLM-invented bracket text from the body even though
        # we're not using its card, so it doesn't show up twice.
        body_markdown = re.sub(_SCORE_PATTERN, "", body_markdown).strip()
    else:
        score_card_html = extracted_card_html

    body_html = md_lib.markdown(
        body_markdown, extensions=["tables", "fenced_code", "sane_lists"]
    )
    body_html = _BADGE_PATTERN.sub(
        lambda m: f'{m.group(1)}<span class="badge {_BADGE_WORDS[m.group(2).lower()]}">{m.group(2)}</span>{m.group(3)}',
        body_html,
    )

    generated_at = datetime.now().strftime("%B %d, %Y · %H:%M")
    risk_register_html = render_risk_register(risk_findings) if risk_findings else ""

    html_doc = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{doc_tag}</title>
<style>{REPORT_CSS}</style>
</head>
<body>
    <div class="topbar">
        <span class="brand">{BRAND_NAME}</span>
        <span class="doc-tag">{doc_tag}</span>
    </div>
    <div class="meta-line">Generated {generated_at} &middot; Confidential &mdash; Internal Distribution Only</div>
    {score_card_html or ""}
    {risk_register_html}
    {body_html}
</body>
</html>"""

    return HTML(string=html_doc).write_pdf()
