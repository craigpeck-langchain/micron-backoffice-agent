from backoffice_agent.mock_data import OPEN_POS
from backoffice_agent.subagents.invoice import INVOICE_PROMPT, post_invoice


NC_9910_EMAIL = """From: ap@northfieldcomponents.com
Subject: Invoice for units from your recent shipment

Please find our invoice for the 500 aluminum brackets from your recent order,
at $12.40/unit, total $6,200.00, due net 30 (2026-09-27). Invoice number NC-9910.
"""


def test_unstated_po_with_quantity_mismatch_is_not_posted():
    invoice_line_items = [{
        "description": "Precision aluminum bracket, Type-C",
        "qty": 500,
        "unit_price": 12.40,
    }]

    result = post_invoice.invoke({
        "vendor": "Northfield Components",
        "invoice_number": "NC-9910",
        "po_number": "PO-10045",
        "line_items": invoice_line_items,
        "currency": "USD",
        "total_amount": 6200.00,
        "due_date": "2026-09-27",
        "po_stated_by_sender": False,
    })

    assert result["status"] == "validation_failed"
    assert result["error"] == "po_line_items_mismatch"
    assert result.get("record_id") is None
    allowed_descriptions = {
        item["description"] for item in OPEN_POS["PO-10045"]["line_items"]
    }
    email_text = NC_9910_EMAIL.lower()
    assert all(
        item["description"] in allowed_descriptions
        or item["description"].lower() in email_text
        for item in invoice_line_items
    )


def test_invoice_prompt_requires_match_or_escalation():
    assert "select a PO only if its line-item" in INVOICE_PROMPT
    assert "call\nescalate_to_human" in INVOICE_PROMPT
    assert "Never invent, split, or pad a line item" in INVOICE_PROMPT
