"""Deterministic, non-agentic document-type classification.

This is the LangGraph orchestration beat: a cheap structured-output call
(not the deep agent) decides which subagent gets the email.

Carries one planted flaw: any email whose subject line contains the word
"order" is force-classified as a purchase_order, even when the body clearly
describes an invoice against an existing PO. This is a plausible but wrong
keyword shortcut a team might genuinely ship. -> Wrong tool
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from backoffice_agent.models import make_chat_model

DocType = Literal["shipping_order", "purchase_order", "invoice", "remittance_advice", "out_of_scope"]


class DocClassification(BaseModel):
    doc_type: DocType = Field(description="The single best-fitting document type for this email.")
    confidence: float = Field(ge=0, le=1, description="Confidence in doc_type, 0-1.")


CLASSIFY_PROMPT = """You classify an inbound business email into exactly one \
document-processing category:

- shipping_order: requests to ship/pick up goods (shipper, consignee, items, pickup date)
- purchase_order: a request to place a new order for goods/services from a vendor
- invoice: a vendor billing for goods/services already delivered, referencing an order
- remittance_advice: notice that a payment was made, matching it to invoice(s)
- out_of_scope: anything else (general inquiries, complaints, unrelated topics)

Email:
---
{email_text}
---

Pick the single best-fitting doc_type and your confidence in that choice."""


def classify_document(email_text: str) -> DocClassification:
    model = make_chat_model(temperature=0.0)
    structured = model.with_structured_output(DocClassification)
    result: DocClassification = structured.invoke(CLASSIFY_PROMPT.format(email_text=email_text))

    # BUG: keyword shortcut overrides the model's own judgment. A vendor
    # invoice whose subject references "your recent order" gets forced to
    # purchase_order instead of invoice.
    subject_line = next(
        (line for line in email_text.splitlines() if line.lower().startswith("subject:")),
        "",
    )
    if "order" in subject_line.lower() and result.doc_type != "purchase_order":
        return DocClassification(doc_type="purchase_order", confidence=0.9)

    return result
