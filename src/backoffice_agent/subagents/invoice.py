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

from backoffice_agent.mock_data import OPEN_POS
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
    po_stated_by_sender: bool,
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
        po_stated_by_sender: True only if the email explicitly stated this PO number.
    """
    if not po_stated_by_sender:
        po = OPEN_POS.get(po_number)
        po_line_items = po.get("line_items", []) if po else []
        matching_items = {
            item.get("description"): item for item in po_line_items
        }
        if (
            not po
            or len(line_items) != len(po_line_items)
            or any(
                item.get("description") not in matching_items
                or item.get("qty") != matching_items[item.get("description")].get("qty")
                or item.get("unit_price") != matching_items[item.get("description")].get("unit_price")
                for item in line_items
            )
        ):
            return {
                "status": "validation_failed",
                "error": "po_line_items_mismatch",
                "message": "Unstated PO could not be matched to the invoice line items; escalate for human review.",
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


INVOICE_PROMPT = f"""\
You extract invoice details from an inbound vendor email and post them via
post_invoice.

Required fields: vendor, invoice number, PO number, line items, currency,
total amount, and due date. Look up the PO on file to confirm the vendor
and line items match. When the email does not explicitly state a PO number,
call list_open_pos_for_vendor and select a PO only if its line-item
descriptions, quantities, and unit prices correspond to the invoice. If no
candidate matches, several candidates match, or the quantities differ, call
escalate_to_human with the extracted fields and do not post the invoice.
Line items must be copied verbatim from the email or from the matched ERP PO
record. Never invent, split, or pad a line item to reconcile a quantity
difference.

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
