from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage
from langchain_core.tools import tool
from deepagents import create_deep_agent

from backoffice_agent.subagents.invoice import INVOICE_PROMPT


EMAIL = """From: ap@northfieldcomponents.com
Subject: Invoice INV-88213 for PO-10045

Please find our invoice INV-88213 for PO-10045: 480 units of precision
aluminum brackets at $12.40/unit, total $5,952.00, due net 30 (2026-09-20).

Thanks,
Northfield Components AP Team
"""


class ToolCallingFakeChatModel(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kwargs):
        return self


def test_northfield_invoice_posts_with_grounded_vendor():
    calls = []

    @tool
    def lookup_open_po(po_number: str) -> dict:
        """Look up the open purchase order."""
        calls.append(("lookup_open_po", po_number))
        return {"match": "single", "po_number": po_number, "vendor": "Northfield Components"}

    @tool
    def lookup_vendor(vendor_name: str) -> dict:
        """Look up the vendor."""
        calls.append(("lookup_vendor", vendor_name))
        return {"match": "single", "vendor_name": vendor_name}

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
        """Post the invoice."""
        calls.append(
            (
                "post_invoice",
                {
                    "vendor": vendor,
                    "invoice_number": invoice_number,
                    "po_number": po_number,
                    "line_items": line_items,
                    "currency": currency,
                    "total_amount": total_amount,
                    "due_date": due_date,
                },
            )
        )
        return {"status": "posted", "details": {"vendor": vendor}}

    @tool
    def request_clarification(missing_fields: list[str], question: str) -> dict:
        """Request missing invoice information."""
        calls.append(("request_clarification", missing_fields))
        return {"status": "clarification_requested"}

    responses = [
        AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "lookup_open_po",
                    "args": {"po_number": "PO-10045"},
                    "id": "call-po",
                    "type": "tool_call",
                }
            ],
        ),
        AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "lookup_vendor",
                    "args": {"vendor_name": "Northfield Components"},
                    "id": "call-vendor",
                    "type": "tool_call",
                }
            ],
        ),
        AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "post_invoice",
                    "args": {
                        "vendor": "Northfield Components",
                        "invoice_number": "INV-88213",
                        "po_number": "PO-10045",
                        "line_items": [
                            {
                                "description": "precision aluminum brackets",
                                "qty": 480,
                                "unit_price": 12.40,
                            }
                        ],
                        "currency": "USD",
                        "total_amount": 5952.00,
                        "due_date": "2026-09-20",
                    },
                    "id": "call-post",
                    "type": "tool_call",
                }
            ],
        ),
        AIMessage(content="Invoice INV-88213 posted."),
    ]
    agent = create_deep_agent(
        model=ToolCallingFakeChatModel(responses=responses),
        tools=[lookup_open_po, lookup_vendor, post_invoice, request_clarification],
        system_prompt=INVOICE_PROMPT,
    )

    result = agent.invoke({"messages": [{"role": "user", "content": EMAIL}]})

    vendor_lookups = [value for name, value in calls if name == "lookup_vendor"]
    assert vendor_lookups
    assert all(value == "Northfield Components" for value in vendor_lookups)
    posted = next(details for name, details in calls if name == "post_invoice")
    assert posted["vendor"] == "Northfield Components"
    assert not any(name == "request_clarification" for name, _ in calls)
    assert result["messages"][-1].content == "Invoice INV-88213 posted."
