"""Shipping-order extraction subagent."""

from __future__ import annotations

from langchain_core.tools import tool

from backoffice_agent.prompts import SHARED_TOOL_GUIDANCE
from backoffice_agent.tools import SHARED_TOOLS


@tool
def create_shipping_order(
    shipper: str,
    consignee: str,
    pickup_date: str,
    items: list[dict],
    weight_lbs: float,
    mode: str,
) -> dict:
    """Create a shipping order in the TMS.

    Args:
        shipper: Name of the party shipping the goods.
        consignee: Name of the receiving party/location.
        pickup_date: Requested pickup date, ISO format (YYYY-MM-DD).
        items: Line items being shipped, each with a description and quantity.
        weight_lbs: Total shipment weight in pounds.
        mode: Shipping mode - one of "truckload", "ltl", "air", "ocean".
    """
    record_id = f"SO-{abs(hash((shipper, consignee, pickup_date))) % 1_000_000:06d}"
    return {
        "status": "posted",
        "record_id": record_id,
        "details": {
            "shipper": shipper,
            "consignee": consignee,
            "pickup_date": pickup_date,
            "items": items,
            "weight_lbs": weight_lbs,
            "mode": mode,
        },
    }


SHIPPING_ORDER_PROMPT = f"""\
You extract shipping-order details from an inbound email and post them to
the TMS via create_shipping_order.

Required fields: shipper, consignee, pickup date, line items, total weight,
and shipping mode. Infer shipping mode from context (e.g. "full truckload"
-> truckload, a small parcel count -> ltl) only when it's reasonably clear;
otherwise ask. Shipping orders have no PO number field - never ask for one
or treat one as missing.

Shipping orders have no vendor to validate either - the shipper and
consignee are logistics parties (often a Micron site name, not an ERP
vendor record), not something to look up. Do not call lookup_vendor or
lookup_open_po for this document type. Only escalate if a required field
(shipper, consignee, pickup date, items, or weight) is genuinely missing
from the email and can't be inferred - use request_clarification for that,
not escalate_to_human."""

shipping_order_subagent = {
    "name": "shipping_order_agent",
    "description": "Extracts shipper/consignee/items/pickup details from an email and posts a shipping order.",
    "system_prompt": SHIPPING_ORDER_PROMPT,
    "tools": [*SHARED_TOOLS, create_shipping_order],
}
