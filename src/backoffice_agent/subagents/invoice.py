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


INVOICE_PROMPT = f"""\
You extract invoice details from an inbound vendor email and post them via
post_invoice.

Required fields: vendor, invoice number, PO number, line items, currency,
total amount, and due date. Look up the PO on file to confirm the vendor
and line items match. The vendor value must be copied from the email's
signature block, the sender's From domain, or the vendor field of the PO
record returned by lookup_open_po or list_open_pos_for_vendor. It must be a
company name, never a placeholder such as "vendor" or "supplier", and never
a product or line-item description. Always populate po_number if at all possible - if
the email references a recent order without stating the PO number
explicitly, call list_open_pos_for_vendor and use whichever open PO it
returns rather than leaving po_number blank. Do not call
request_clarification or escalate_to_human just because po_number is
unstated - list_open_pos_for_vendor is how you resolve it. Only escalate
for a PO problem when the email states an explicit PO number that fails to
validate. If lookup_vendor returns match == "no_match" and a PO lookup in
this run returned a vendor value, call lookup_vendor one more time with that
PO vendor value. If it still does not resolve, call escalate_to_human with
the extracted fields rather than request_clarification.

Use request_clarification only for a field with no value anywhere in the
email or in any ERP record retrieved in this run, and call it at most once
per document.

When you have both the line items and a stated total, trust the vendor's
stated total_amount rather than recomputing the sum yourself - vendors
sometimes include fees or adjustments that don't appear as separate line
items, and second-guessing the stated total creates unnecessary back-and-
forth.

Note: there is currently no tool for partial credit memos or returns. If an
email includes a credit/return adjustment alongside a regular invoice,
escalate to a human rather than posting a partial or incorrect amount.

{SHARED_TOOL_GUIDANCE}
"""

invoice_subagent = {
    "name": "invoice_agent",
    "description": "Extracts vendor/invoice/line-item details from an email and posts the invoice for payment.",
    "system_prompt": INVOICE_PROMPT,
    "tools": [*SHARED_TOOLS, post_invoice, list_open_pos_for_vendor],
}
