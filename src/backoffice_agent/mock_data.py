"""Mock ERP fixtures: vendors, open purchase orders, and ship-to locations.

A few entries are deliberately shaped to trigger the demo's planted flaws:

- "Delacroix Freight & Logistics" and "O'Malley Industrial Supply" have
  punctuation (``&``, ``'``) in their names, which trips the silent bug in
  ``escalate_to_human`` (see tools.py).
- "Baltic Circuit Works" is the only EUR-denominated vendor; an invoice
  posted against it in another currency should be flagged but isn't
  (see the missing currency check in ``post_invoice``).
- "Cascade Precision Machining" and "Cascade Precision Manufacturing" share
  a name prefix on purpose, so a truncated/garbled vendor reference in an
  email resolves to an ambiguous multi-match instead of a single hit.
"""

from __future__ import annotations

VENDORS: dict[str, dict] = {
    "Northfield Components": {"vendor_id": "V-1001", "currency": "USD", "status": "active"},
    "Meridian Tooling Co": {"vendor_id": "V-1002", "currency": "USD", "status": "active"},
    "Delacroix Freight & Logistics": {"vendor_id": "V-1003", "currency": "USD", "status": "active"},
    "O'Malley Industrial Supply": {"vendor_id": "V-1004", "currency": "USD", "status": "active"},
    "Baltic Circuit Works": {"vendor_id": "V-1005", "currency": "EUR", "status": "active"},
    "Anchor Point Packaging": {"vendor_id": "V-1006", "currency": "USD", "status": "active"},
    "Sable Ridge Materials": {"vendor_id": "V-1007", "currency": "USD", "status": "active"},
    "Vantage Point Electronics": {"vendor_id": "V-1008", "currency": "USD", "status": "active"},
    "Cascade Precision Machining": {"vendor_id": "V-1009", "currency": "USD", "status": "active"},
    "Cascade Precision Manufacturing": {"vendor_id": "V-1010", "currency": "USD", "status": "active"},
    "Wrenfield Logistics Partners": {"vendor_id": "V-1011", "currency": "USD", "status": "active"},
    "Iron Harbor Fabrication": {"vendor_id": "V-1012", "currency": "USD", "status": "active"},
}

# Open purchase orders on file, keyed by PO number. Invoices/remittances
# reference these; shipping orders don't need a PO on file.
OPEN_POS: dict[str, dict] = {
    "PO-10045": {
        "vendor": "Northfield Components",
        "line_items": [
            {"description": "Precision aluminum bracket, Type-C", "qty": 480, "unit_price": 12.40}
        ],
        "status": "open",
    },
    "PO-10062": {
        "vendor": "Meridian Tooling Co",
        "line_items": [
            {"description": "CNC end mill set, 1/4in carbide", "qty": 60, "unit_price": 84.00}
        ],
        "status": "open",
    },
    "PO-10071": {
        "vendor": "Sable Ridge Materials",
        "line_items": [
            {"description": "304 stainless sheet, 4x8ft, 16ga", "qty": 25, "unit_price": 210.00}
        ],
        "status": "open",
    },
    "PO-10088": {
        "vendor": "Vantage Point Electronics",
        "line_items": [
            {"description": "SMD resistor kit, 0603 assorted", "qty": 200, "unit_price": 9.75},
            {"description": "SMD capacitor kit, 0805 assorted", "qty": 200, "unit_price": 11.25},
        ],
        "status": "open",
    },
    "PO-10093": {
        "vendor": "Iron Harbor Fabrication",
        "line_items": [
            {"description": "Welded steel frame assembly, Rev C", "qty": 15, "unit_price": 640.00}
        ],
        "status": "open",
    },
    "PO-10101": {
        "vendor": "Anchor Point Packaging",
        "line_items": [
            {"description": "ESD-safe foam insert, custom die-cut", "qty": 3000, "unit_price": 1.85}
        ],
        "status": "open",
    },
    "PO-10112": {
        "vendor": "Wrenfield Logistics Partners",
        "line_items": [
            {"description": "Dedicated truckload freight service, Boise-Lehi lane", "qty": 1, "unit_price": 2400.00}
        ],
        "status": "open",
    },
    "PO-10125": {
        "vendor": "Cascade Precision Manufacturing",
        "line_items": [
            {"description": "Precision-machined housing, Rev B", "qty": 40, "unit_price": 96.50}
        ],
        "status": "open",
    },
    "PO-10140": {
        "vendor": "Baltic Circuit Works",
        "line_items": [
            {"description": "6-layer PCB, custom fab", "qty": 500, "unit_price": 18.20}
        ],
        "status": "open",
    },
}

SHIP_TO_LOCATIONS: dict[str, dict] = {
    "Fab 11 - Boise, ID": {"address": "8000 S Federal Way, Boise, ID 83716"},
    "Manassas Site - Manassas, VA": {"address": "9990 Innovation Dr, Manassas, VA 20110"},
    "Singapore Fab - Woodlands": {"address": "9 Woodlands Industrial Park D, Singapore 738406"},
    "Distribution Center - Lehi, UT": {"address": "3600 N Digital Dr, Lehi, UT 84043"},
}


def find_open_pos_for_vendor(vendor_name: str) -> list[dict]:
    """Exact-match (case-insensitive) lookup of open POs for a resolved vendor name."""
    name = vendor_name.strip().lower()
    return [
        {"po_number": po_number, **record}
        for po_number, record in OPEN_POS.items()
        if record["vendor"].lower() == name
    ]


def find_vendor_candidates(query: str) -> list[dict]:
    """Case-insensitive substring match against vendor names.

    Returns every vendor whose name contains the query (or vice versa for a
    short/truncated query), each annotated with its own name. Intentionally
    naive — this is what makes "Cascade Precision" ambiguous between the two
    similarly-named vendors.
    """
    q = query.strip().lower()
    if not q:
        return []
    hits = []
    for name, record in VENDORS.items():
        if q in name.lower() or name.lower() in q:
            hits.append({"vendor_name": name, **record})
    return hits
