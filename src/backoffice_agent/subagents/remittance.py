"""Remittance advice matching subagent."""

from __future__ import annotations

from langchain_core.tools import tool

from backoffice_agent.prompts import SHARED_TOOL_GUIDANCE
from backoffice_agent.tools import SHARED_TOOLS


@tool
def match_remittance_advice(
    payer: str,
    payment_reference: str,
    invoice_numbers: list[str],
    amounts: list[float],
) -> dict:
    """Match a remittance advice to open invoices and record the payment.

    Args:
        payer: Name of the party that made the payment.
        payment_reference: The payer's payment/wire reference number.
        invoice_numbers: Invoice numbers this payment is settling.
        amounts: Amount applied to each invoice, same order as invoice_numbers.
    """
    record_id = f"RA-{abs(hash((payer, payment_reference))) % 1_000_000:06d}"
    status = "posted" if len(invoice_numbers) == len(amounts) and invoice_numbers else "needs_review"
    return {
        "status": status,
        "record_id": record_id,
        "details": {
            "payer": payer,
            "payment_reference": payment_reference,
            "invoice_numbers": invoice_numbers,
            "amounts": amounts,
        },
    }


REMITTANCE_PROMPT = f"""\
You extract remittance advice from an inbound email and match it to the
invoices it settles via match_remittance_advice.

Required fields: payer, payment reference, and the list of invoice numbers
with the amount applied to each. If the invoice numbers and amounts don't
line up one-to-one, or an invoice number isn't legible, escalate rather
than guessing which invoice an amount applies to.

Remittance advice has no vendor or PO number to validate - the invoice
numbers stated in the email ARE the reference. Do not call lookup_vendor or
lookup_open_po for this document type, and never ask for a PO number.

{SHARED_TOOL_GUIDANCE}
"""

remittance_subagent = {
    "name": "remittance_agent",
    "description": "Extracts payer/invoice/amount details from an email and matches the remittance to open invoices.",
    "system_prompt": REMITTANCE_PROMPT,
    "tools": [*SHARED_TOOLS, match_remittance_advice],
}
