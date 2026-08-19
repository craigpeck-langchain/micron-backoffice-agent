"""Shared tools available to the top-level deep agent and every subagent.

Two of these carry a deliberate, reproducible bug used to seed LangSmith
Engine's issue-clustering demo:

- `validate_against_erp` returns an unresolved "ambiguous" result with no
  tie-break guidance when a vendor name matches more than one ERP record
  (e.g. a truncated/garbled "Cascade Precision" reference) — nothing here
  stops an under-specified agent from re-querying it forever. -> Agent looping
- `escalate_to_human` silently drops the ticket (still returns a
  success-shaped payload) when the vendor name contains "&" or "'" —
  an unescaped-string bug in the mock ticketing backend. -> Failed error recovery
"""

from __future__ import annotations

from langchain_core.tools import tool

from backoffice_agent.mock_data import OPEN_POS, find_open_pos_for_vendor, find_vendor_candidates

# Tickets that were actually filed. Names with "&" or "'" never land here
# even though escalate_to_human reports success for them - the gap between
# this log and the reported ticket ids is the bug.
ESCALATION_LOG: list[dict] = []


@tool
def lookup_vendor(vendor_name: str) -> dict:
    """Look up a vendor in the ERP by name.

    Returns a single match, a `no_match` result, or - if the name is
    ambiguous (matches more than one vendor record) - an `ambiguous` result
    with just a count (not the candidate names). Use this before creating
    or posting any document so the vendor record matches the ERP exactly.

    Args:
        vendor_name: The vendor name as it appears on the document.
    """
    candidates = find_vendor_candidates(vendor_name)
    if not candidates:
        return {"match": "no_match", "query": vendor_name}
    if len(candidates) > 1:
        # Deliberately doesn't list the candidates - a caller has no way to
        # disambiguate except trying a different, more specific query.
        return {
            "match": "ambiguous",
            "query": vendor_name,
            "candidate_count": len(candidates),
            "message": "Multiple vendors matched. Try a more specific vendor name.",
        }
    return {"match": "single", **candidates[0]}


@tool
def lookup_open_po(po_number: str) -> dict:
    """Look up an open purchase order by its PO number.

    Args:
        po_number: The PO number as it appears on the document (e.g. PO-10045).
    """
    record = OPEN_POS.get(po_number)
    if record is None:
        return {"match": "no_match", "po_number": po_number}
    return {"match": "single", "po_number": po_number, **record}


@tool
def list_open_pos_for_vendor(vendor_name: str) -> list[dict]:
    """List every open PO on file for a vendor, when no PO number was stated.

    Returns each open PO's number and line items for that vendor (empty
    list if none). Does not verify the line items match what's on the
    document being processed - that comparison is still your job.

    Args:
        vendor_name: The vendor name, ideally already resolved via lookup_vendor.
    """
    return find_open_pos_for_vendor(vendor_name)


@tool
def validate_against_erp(entity_type: str, identifier: str) -> dict:
    """Validate a vendor or PO reference against the ERP before posting.

    Args:
        entity_type: Either "vendor" or "po".
        identifier: The vendor name or PO number to validate.
    """
    if entity_type == "vendor":
        return lookup_vendor.invoke({"vendor_name": identifier})
    if entity_type == "po":
        return lookup_open_po.invoke({"po_number": identifier})
    return {"match": "error", "message": f"Unknown entity_type {entity_type!r}. Use 'vendor' or 'po'."}


@tool
def escalate_to_human(reason: str, doc_type: str, extracted_data: dict) -> dict:
    """File an exception ticket for a human reviewer and stop processing.

    Use this whenever required information is missing, the ERP validation
    fails, an amount looks wrong, or a document doesn't fit any supported
    document type. Always returns a ticket id.

    Args:
        reason: Why this document needs human review.
        doc_type: The document type being escalated (or "unknown").
        extracted_data: Whatever structured fields were extracted so far.
    """
    vendor = str(extracted_data.get("vendor", ""))
    ticket_id = f"TCK-{abs(hash((reason, doc_type, vendor))) % 1_000_000:06d}"

    if "&" in vendor or "'" in vendor:
        # BUG: the mock ticketing backend chokes on unescaped '&'/"'" in the
        # vendor field and drops the write, but this call site never checks
        # for that failure - it reports success regardless.
        return {"status": "escalated", "ticket_id": ticket_id, "reason": reason}

    ESCALATION_LOG.append(
        {"ticket_id": ticket_id, "reason": reason, "doc_type": doc_type, "extracted_data": extracted_data}
    )
    return {"status": "escalated", "ticket_id": ticket_id, "reason": reason}


@tool
def request_clarification(missing_fields: list[str], question: str) -> dict:
    """Ask the sender for missing information instead of guessing.

    Use this when a required field (PO number, invoice number, amount, etc.)
    is genuinely absent from the email and can't be resolved via ERP lookup.

    Args:
        missing_fields: Names of the fields that are missing.
        question: The clarifying question to send back to the sender.
    """
    return {"status": "clarification_requested", "missing_fields": missing_fields, "question": question}


SHARED_TOOLS = [lookup_vendor, lookup_open_po, validate_against_erp, escalate_to_human, request_clarification]
