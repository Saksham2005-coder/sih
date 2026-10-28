from typing import Dict, Any, Tuple


class NotificationTemplateEngine:
    """
    Approved Regulatory Notification Templates.
    Generates consistent, transparent communications with explicit institution/application references,
    deadlines, required actions, and authenticated portal deep links.
    """

    TEMPLATES = {
        "DEFICIENCY_COMMUNICATED": {
            "subject": "[AICTE ReguFlow 360] Urgent: Deficiency Communicated for Application #{app_num}",
            "text": (
                "ALL INDIA COUNCIL FOR TECHNICAL EDUCATION\n"
                "Statutory Regulatory Scrutiny Notice\n\n"
                "To: {institution_name}\n"
                "Application Number: {app_num}\n"
                "Category: {category}\n\n"
                "Notice Details:\n"
                "The Regional Scrutiny Officer has identified deficiencies during the scrutiny of your application.\n"
                "Summary: {summary}\n"
                "Statutory Cure Deadline: {deadline}\n\n"
                "Action Required:\n"
                "Access the Institution Portal immediately to review deficiency items and upload required evidence.\n"
                "Portal Link: {link_url}\n\n"
                "Note: Failure to rectify deficiencies within the stipulated timeline will result in statutory rejection."
            )
        },
        "CURE_SUBMITTED": {
            "subject": "[AICTE ReguFlow 360] Deficiency Cure Submitted for Application #{app_num}",
            "text": (
                "ALL INDIA COUNCIL FOR TECHNICAL EDUCATION\n"
                "Application Resubmission Notice\n\n"
                "Institution: {institution_name}\n"
                "Application Number: {app_num}\n"
                "Resubmitted At: {timestamp}\n\n"
                "Details:\n"
                "The institution has submitted deficiency cure responses and accompanying verification evidence.\n"
                "Summary: {summary}\n\n"
                "Action Required:\n"
                "Regional Scrutiny Officers are requested to review resubmitted evidence.\n"
                "Portal Link: {link_url}"
            )
        },
        "SLA_WARNING": {
            "subject": "[AICTE ReguFlow 360] SLA Warning: Approaching Scrutiny Deadline for Application #{app_num}",
            "text": (
                "ALL INDIA COUNCIL FOR TECHNICAL EDUCATION\n"
                "Automated SLA Warning Notice\n\n"
                "Application Number: {app_num}\n"
                "Institution: {institution_name}\n"
                "Region: {region}\n"
                "Days Remaining: {days_remaining} day(s)\n"
                "Prescribed SLA Deadline: {deadline}\n\n"
                "Action Required:\n"
                "The case is approaching the regional processing SLA threshold. Please expedite scrutiny.\n"
                "Portal Link: {link_url}"
            )
        },
        "SLA_BREACHED": {
            "subject": "[AICTE ReguFlow 360] SLA Escalation: Scrutiny Timeline Exceeded for #{app_num}",
            "text": (
                "ALL INDIA COUNCIL FOR TECHNICAL EDUCATION\n"
                "Statutory SLA Escalation Notice\n\n"
                "Application Number: {app_num}\n"
                "Institution: {institution_name}\n"
                "Region: {region}\n"
                "Days Overdue: {days_overdue} day(s)\n"
                "Escalation Level: {escalation_level}\n\n"
                "Action Required:\n"
                "Statutory scrutiny timeline has been breached. Immediate administrative intervention required.\n"
                "Portal Link: {link_url}"
            )
        },
        "EVC_SCHEDULED": {
            "subject": "[AICTE ReguFlow 360] Expert Visit Committee (EVC) Scheduled: Application #{app_num}",
            "text": (
                "ALL INDIA COUNCIL FOR TECHNICAL EDUCATION\n"
                "Notice of Expert Visiting Committee Inspection\n\n"
                "Institution: {institution_name}\n"
                "Application Number: {app_num}\n"
                "Inspection Date: {inspection_date}\n\n"
                "Details:\n"
                "An Expert Visiting Committee has been dispatched to verify physical infrastructure and labs.\n"
                "Action Required:\n"
                "Ensure all statutory documents, original land deeds, and laboratory equipment are available on site.\n"
                "Portal Link: {link_url}"
            )
        },
        "EVC_REPORT_SUBMITTED": {
            "subject": "[AICTE ReguFlow 360] EVC Inspection Report Submitted for #{app_num}",
            "text": (
                "ALL INDIA COUNCIL FOR TECHNICAL EDUCATION\n"
                "EVC Inspection Report Notice\n\n"
                "Institution: {institution_name}\n"
                "Application Number: {app_num}\n"
                "Recommendation: {recommendation}\n\n"
                "Action Required:\n"
                "EVC Report has been recorded and submitted for Standing Appellate / Hearing Committee review.\n"
                "Portal Link: {link_url}"
            )
        },
        "UNDERTAKING_DUE_SOON": {
            "subject": "[AICTE ReguFlow 360] Reminder: Compliance Undertaking Due Soon for {institution_name}",
            "text": (
                "ALL INDIA COUNCIL FOR TECHNICAL EDUCATION\n"
                "Compliance Passport Obligation Notice\n\n"
                "Institution: {institution_name}\n"
                "Undertaking Category: {category}\n"
                "Condition Title: {title}\n"
                "Due Date: {deadline} (Within {days_remaining} days)\n\n"
                "Action Required:\n"
                "Upload notarized compliance evidence and fulfillment affidavit to prevent statutory deficiency.\n"
                "Portal Link: {link_url}"
            )
        },
        "UNDERTAKING_OVERDUE": {
            "subject": "[AICTE ReguFlow 360] OVERDUE Notice: Compliance Undertaking Condition Breached",
            "text": (
                "ALL INDIA COUNCIL FOR TECHNICAL EDUCATION\n"
                "Notice of Non-Compliance\n\n"
                "Institution: {institution_name}\n"
                "Undertaking Category: {category}\n"
                "Condition Title: {title}\n"
                "Days Overdue: {days_overdue} day(s)\n"
                "Escalation Level: {escalation_level}\n\n"
                "Action Required:\n"
                "The compliance undertaking has expired without verified fulfillment. Immediate explanation required.\n"
                "Portal Link: {link_url}"
            )
        },
        "DOCUMENT_EXPIRING": {
            "subject": "[AICTE ReguFlow 360] Document Validity Warning: {doc_type} Expiring Soon",
            "text": (
                "ALL INDIA COUNCIL FOR TECHNICAL EDUCATION\n"
                "Document Vault Renewal Notice\n\n"
                "Institution: {institution_name}\n"
                "Document Type: {doc_type}\n"
                "Document Number: {doc_num}\n"
                "Expiry Date: {expiry_date} (Within {days_remaining} days)\n\n"
                "Action Required:\n"
                "Upload a renewed certificate or registered lease extension in the Document Vault.\n"
                "Portal Link: {link_url}"
            )
        },
        "DOCUMENT_EXPIRED": {
            "subject": "[AICTE ReguFlow 360] CRITICAL: Mandatory Regulatory Document Has Expired",
            "text": (
                "ALL INDIA COUNCIL FOR TECHNICAL EDUCATION\n"
                "Notice of Mandatory Document Expiry\n\n"
                "Institution: {institution_name}\n"
                "Document Type: {doc_type}\n"
                "Document Number: {doc_num}\n"
                "Expired On: {expiry_date}\n\n"
                "Action Required:\n"
                "The regulatory approval condition is breached due to expired certification. Upload renewal immediately.\n"
                "Portal Link: {link_url}"
            )
        },
        "ORDER_ISSUED": {
            "subject": "[AICTE ReguFlow 360] Official Decision Order Issued for Application #{app_num}",
            "text": (
                "ALL INDIA COUNCIL FOR TECHNICAL EDUCATION\n"
                "Statutory Decision Order Notification\n\n"
                "To: {institution_name}\n"
                "Application Number: {app_num}\n"
                "Statutory Decision: {decision}\n"
                "Order Reference Number: {order_number}\n"
                "Order Date: {order_date}\n\n"
                "Summary:\n"
                "{remarks}\n\n"
                "Action Required:\n"
                "Download the formal statutory order artifact from the portal or verify via QR code.\n"
                "Portal Link: {link_url}\n\n"
                "Registry Integrity Note: Verify cryptographic SHA-256 integrity on the AICTE public portal."
            )
        },
        "ORDER_REVOKED": {
            "subject": "[AICTE ReguFlow 360] Notice of Statutory Order Revocation: #{order_number}",
            "text": (
                "ALL INDIA COUNCIL FOR TECHNICAL EDUCATION\n"
                "Notice of Statutory Order Revocation\n\n"
                "Institution: {institution_name}\n"
                "Order Reference Number: {order_number}\n"
                "Revocation Reason: {reason}\n\n"
                "Status: The referenced regulatory approval order has been formally revoked by Competent Authority.\n"
                "Portal Link: {link_url}"
            )
        }
    }

    @classmethod
    def render(cls, template_code: str, params: Dict[str, Any]) -> Tuple[str, str, str]:
        """
        Renders template into (Subject, PlainText, HTML).
        Gracefully falls back to generic formatting if template_code is unfamiliar.
        """
        tpl = cls.TEMPLATES.get(template_code)
        if not tpl:
            # Generic fallback
            subject = params.get("subject") or f"[AICTE ReguFlow 360] Notification: {template_code}"
            text = params.get("message") or f"Notification for event '{template_code}' regarding entity #{params.get('entity_id', '')}."
        else:
            safe_params = {k: str(v) if v is not None else "" for k, v in params.items()}
            # Default missing keys to empty string to avoid KeyError
            for k in ["app_num", "institution_name", "category", "summary", "deadline", "link_url",
                      "timestamp", "region", "days_remaining", "days_overdue", "escalation_level",
                      "inspection_date", "recommendation", "title", "doc_type", "doc_num", "expiry_date",
                      "decision", "order_number", "order_date", "remarks", "reason"]:
                if k not in safe_params:
                    safe_params[k] = "N/A"

            try:
                subject = tpl["subject"].format(**safe_params)
                text = tpl["text"].format(**safe_params)
            except Exception:
                subject = f"[AICTE ReguFlow 360] Notification: {template_code}"
                text = params.get("message") or f"Notification for event '{template_code}'."

        # Generate standard Civic Precision HTML wrapper
        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #F4F6F8; margin: 0; padding: 24px; color: #152536; }}
  .container {{ max-width: 600px; margin: 0 auto; background: #FFFFFF; border: 1px solid #DFE5E9; border-radius: 8px; overflow: hidden; }}
  .header {{ background-color: #152536; color: #FFFFFF; padding: 20px 24px; }}
  .header h1 {{ margin: 0; font-size: 16px; font-weight: 700; letter-spacing: 0.5px; }}
  .header p {{ margin: 4px 0 0; font-size: 11px; color: #94A3B8; text-transform: uppercase; }}
  .content {{ padding: 24px; line-height: 1.6; font-size: 14px; }}
  .badge {{ display: inline-block; padding: 4px 10px; background-color: #F1F5F9; border: 1px solid #CBD5E1; border-radius: 4px; font-weight: 600; font-size: 12px; }}
  .button {{ display: inline-block; margin-top: 18px; padding: 10px 20px; background-color: #0E746B; color: #FFFFFF; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 13px; }}
  .footer {{ padding: 16px 24px; background-color: #F8FAFC; border-top: 1px solid #DFE5E9; font-size: 11px; color: #64748B; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>ALL INDIA COUNCIL FOR TECHNICAL EDUCATION</h1>
    <p>AvedanSetu (आवेदनसेतु) Regulatory Workflow & Compliance Platform</p>
  </div>
  <div class="content">
    <div style="white-space: pre-line;">{text}</div>
    {f'<p><a href="{params.get("link_url", "#")}" class="button">Access AvedanSetu (आवेदनसेतु) Portal</a></p>' if params.get("link_url") else ''}
  </div>
  <div class="footer">
    <p>This is an automated regulatory notification issued under AICTE Act 1987. Do not reply to this email.</p>
    <p>Ref: SIH Problem Statement 26262 | Verification: https://aicte.gov.in</p>
  </div>
</div>
</body>
</html>"""

        return subject, text, html
