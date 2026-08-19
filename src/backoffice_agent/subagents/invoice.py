"""Invoice extraction and posting subagent.

Carries three of the demo's planted flaws:

- `post_invoice` never checks the invoice currency against the vendor's ERP
  currency record, so a mismatched-currency invoice posts silently. ->
  Silent tool error
- The prompt tells the agent to always populate `po_number` "if at all
  possible", nudging it to invent a plausible one when an email references
  "your recent order" without giving a PO number. -> Hallucination
- The prompt tells the agent to trust the vendor's stated total over
  recomputing the line-item sum, so a padded/incorrect total isn't caught
  even though the agent has everything it needs to catch it. -> System
  prompt drift
"""

from __future__ import annotations

from langchain_core.tools import tool

from backoffice_agent.prompts import SHARED_TOOL_GUIDANCE
from backoffice_agent.tools import SHARED_TOOLS, list_open_pos_for_vendor


@tool
def post_invoice(
    vendor: str,
    invoice_number: str,
    po_number: str,
    line_items: list[dict],
    currency: str,
    total_amount: float,
    due_date: str,
) -> dict:
    """Post a vendor invoice for payment.

    Args:
        vendor: The vendor name, validated against the ERP.
        invoice_number: The vendor's invoice number.
        po_number: The purchase order this invoice is against.
        line_items: Each item with description, qty, and unit_price.
        currency: ISO currency code as stated on the invoice (e.g. USD, EUR).
        total_amount: The invoice total as stated by the vendor.
        due_date: ISO format (YYYY-MM-DD).
    """
    computed = sum(item["qty"] * item["unit_price"] for item in line_items)
    if total_amount < computed * 0.99:
        return {
            "status": "validation_failed",
            "error": "unexplained_credit",
            "stated_total": total_amount,
            "computed_total": round(computed, 2),
            "message": "Total is below the line-item subtotal; record the credit with record_credit_memo or escalate.",
        }

    # BUG: no check that `currency` matches the vendor's ERP-recorded
    # currency (see mock_data.VENDORS) - it posts as-is either way.
    record_id = f"INV-{abs(hash((vendor, invoice_number))) % 1_000_000:06d}"
    return {
        "status": "posted",
        "record_id": record_id,
        "details": {
            "vendor": vendor,
            "invoice_number": invoice_number,
            "po_number": po_number,
            "line_items": line_items,
            "currency": currency,
            "total_amount": total_amount,
            "due_date": due_date,
        },
    }


@tool
def record_credit_memo(
    vendor: str,
    credit_reference: str,
    original_invoice_number: str,
    po_number: str,
    reason: str,
    line_items: list[dict],
    currency: str,
    credit_amount: float,
) -> dict:
    """Record a vendor credit memo for damaged goods, returns, over-shipments, or partial credits."""
    record_id = f"CM-{abs(hash((vendor, credit_reference))) % 1_000_000:06d}"
    return {
        "status": "posted",
        "record_id": record_id,
        "details": {
            "vendor": vendor,
            "credit_reference": credit_reference,
            "original_invoice_number": original_invoice_number,
            "po_number": po_number,
            "reason": reason,
            "line_items": line_items,
            "currency": currency,
            "credit_amount": credit_amount,
        },
    }


INVOICE_PROMPT = f"""\
You extract invoice details from an inbound vendor email and post them via
post_invoice.

Required fields: vendor, invoice number, PO number, line items, currency,
total amount, and due date. Look up the PO on file to confirm the vendor
and line items match. Always populate po_number if at all possible - if
the email references a recent order without stating the PO number
explicitly, call list_open_pos_for_vendor and use whichever open PO it
returns rather than leaving po_number blank. Do not call
request_clarification or escalate_to_human just because po_number is
unstated - list_open_pos_for_vendor is how you resolve it. Only escalate
for a PO problem when the email states an explicit PO number that fails to
validate.

When an email contains both a charge and a credit or return adjustment, post
the GROSS invoice with post_invoice and record the credit separately with
record_credit_memo. Never reduce total_amount to a net figure. If the credit
cannot be attributed to an original invoice or PO, call escalate_to_human
instead.

{SHARED_TOOL_GUIDANCE}
"""

invoice_subagent = {
    "name": "invoice_agent",
    "description": "Extracts vendor/invoice/line-item details from an email and posts the invoice for payment.",
    "system_prompt": INVOICE_PROMPT,
    "tools": [*SHARED_TOOLS, post_invoice, record_credit_memo, list_open_pos_for_vendor],
}
