import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from dotenv import load_dotenv

from pdf_report import render_report_pdf

load_dotenv()

def send_audit_report_email(executive_report: str, technical_guide: str, recipient_email: str = None):
    """Sends an email with two attachments: Executive Report & Technical Remediation Playbook."""
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")
    target_recipient = recipient_email or os.getenv("DEFAULT_RECIPIENT")

    if not sender_email or not sender_password:
        print("❌ [Email Error] Missing SMTP credentials in .env file.")
        return False

    msg = MIMEMultipart()
    msg['From'] = f"DevSecOps Auditor <{sender_email}>"
    msg['To'] = target_recipient
    msg['Subject'] = "[Compliance Audit] CISO Executive Report & Remediation Playbook"

    # HTML Email Body
    html_body = """
    <html>
      <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
        <h2 style="color: #1a365d;">🛡️ Automated DevSecOps Compliance Audit Complete</h2>
        <p>Hello Security & Cloud Engineering Team,</p>
        <p>The automated <b>Multi-Agent Compliance Auditor</b> has completed its telemetry scan and risk evaluation.</p>
        <p>Following Human-In-The-Loop (HITL) approval, two comprehensive reports have been attached:</p>
        <ul>
          <li><b>CISO_Executive_Summary.pdf</b>: High-level risk score, metrics, and CIS compliance benchmarks for leadership.</li>
          <li><b>Engineering_Remediation_Playbook.pdf</b>: Step-by-step CLI commands and patch instructions for cloud engineers.</li>
        </ul>
        <br>
        <p>Best regards,<br><b>Automated DevSecOps Governance Pipeline</b></p>
      </body>
    </html>
    """
    msg.attach(MIMEText(html_body, 'html'))

    try:
        executive_pdf = render_report_pdf(executive_report, "Executive Summary")
        technical_pdf = render_report_pdf(technical_guide, "Remediation Playbook")
    except Exception as e:
        print(f"❌ [PDF Error] Failed to render report PDFs: {e}")
        return False

    # Attachment 1: Executive Report
    part1 = MIMEApplication(executive_pdf, _subtype='pdf', Name='CISO_Executive_Summary.pdf')
    part1['Content-Disposition'] = 'attachment; filename="CISO_Executive_Summary.pdf"'
    msg.attach(part1)

    # Attachment 2: Technical Remediation Playbook
    part2 = MIMEApplication(technical_pdf, _subtype='pdf', Name='Engineering_Remediation_Playbook.pdf')
    part2['Content-Disposition'] = 'attachment; filename="Engineering_Remediation_Playbook.pdf"'
    msg.attach(part2)

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print(f"✅ [Email Dispatch] Both reports successfully sent to {target_recipient}!")
        return True
    except Exception as e:
        print(f"❌ [Email Error] Failed to dispatch email: {e}")
        return False
