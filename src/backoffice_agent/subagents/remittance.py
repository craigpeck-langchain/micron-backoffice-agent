"""Remittance advice matching subagent."""

from __future__ import annotations

from langchain_core.tools import tool

from backoffice_agent.tools import escalate_to_human, request_clarification


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


REMITTANCE_PROMPT = """\
You extract remittance advice from an inbound email and match it to the
invoices it settles via match_remittance_advice.

The only required fields for this document type are: payer, payment
reference, invoice numbers, and amounts. No field outside this list may ever
be reported as missing. PO numbers and vendor ERP records are not part of
remittance advice at all, so never ask for or look up either one. If invoice
numbers and amounts do not line up one-to-one, or an invoice number is not
legible, escalate rather than guessing. Call request_clarification at most
once per document, and only when one of the listed fields is genuinely
absent and cannot be inferred.
"""

remittance_subagent = {
    "name": "remittance_agent",
    "description": "Extracts payer/invoice/amount details from an email and matches the remittance to open invoices.",
    "system_prompt": REMITTANCE_PROMPT,
    "tools": [escalate_to_human, request_clarification, match_remittance_advice],
}
