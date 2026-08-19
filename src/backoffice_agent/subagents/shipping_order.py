"""Shipping-order extraction subagent."""

from __future__ import annotations

from langchain_core.tools import tool

from backoffice_agent.tools import escalate_to_human, request_clarification


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


SHIPPING_ORDER_PROMPT = """\
You extract shipping-order details from an inbound email and post them to
the TMS via create_shipping_order.

The only required fields for this document type are: shipper, consignee,
pickup date, items, weight, and mode. Infer mode from context (for example,
"full truckload" means "truckload") only when reasonably clear; otherwise
ask. No field outside this list may ever be reported as missing. PO numbers
and vendor ERP records are not part of shipping orders at all, so never ask
for or look up either one. Call request_clarification at most once per
document, only when one of the listed fields is genuinely absent and cannot
be inferred."""

shipping_order_subagent = {
    "name": "shipping_order_agent",
    "description": "Extracts shipper/consignee/items/pickup details from an email and posts a shipping order.",
    "system_prompt": SHIPPING_ORDER_PROMPT,
    "tools": [escalate_to_human, request_clarification, create_shipping_order],
}
