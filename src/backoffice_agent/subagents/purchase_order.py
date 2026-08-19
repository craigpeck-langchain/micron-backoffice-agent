"""Purchase-order creation subagent."""

from __future__ import annotations

from langchain_core.tools import tool

from backoffice_agent.prompts import SHARED_TOOL_GUIDANCE
from backoffice_agent.tools import SHARED_TOOLS


@tool
def create_purchase_order(
    vendor: str,
    line_items: list[dict],
    requested_delivery_date: str,
    ship_to: str,
) -> dict:
    """Create a new purchase order in the ERP.

    Args:
        vendor: The vendor name, validated against the ERP.
        line_items: Each item with description, qty, and unit_price.
        requested_delivery_date: ISO format (YYYY-MM-DD).
        ship_to: The receiving Micron site name.
    """
    record_id = f"PO-2{abs(hash((vendor, requested_delivery_date))) % 100_000:05d}"
    return {
        "status": "posted",
        "record_id": record_id,
        "details": {
            "vendor": vendor,
            "line_items": line_items,
            "requested_delivery_date": requested_delivery_date,
            "ship_to": ship_to,
        },
    }


PURCHASE_ORDER_PROMPT = f"""\
You extract new purchase-order requests from an inbound email and create
them via create_purchase_order.

Required fields: vendor, line items (description, quantity, unit price),
requested delivery date, and the Micron ship-to site. Confirm the vendor
resolves to a single ERP match before creating the PO.

{SHARED_TOOL_GUIDANCE}
"""

purchase_order_subagent = {
    "name": "purchase_order_agent",
    "description": "Extracts vendor/line-item/delivery details from an email and creates a new purchase order.",
    "system_prompt": PURCHASE_ORDER_PROMPT,
    "tools": [*SHARED_TOOLS, create_purchase_order],
}
