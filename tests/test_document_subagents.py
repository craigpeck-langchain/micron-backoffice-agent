import re
import unittest

from backoffice_agent.subagents.remittance import (
    REMITTANCE_PROMPT,
    match_remittance_advice,
    remittance_subagent,
)
from backoffice_agent.subagents.shipping_order import (
    SHIPPING_ORDER_PROMPT,
    create_shipping_order,
    shipping_order_subagent,
)


class DocumentSubagentRegressionTests(unittest.TestCase):
    def test_shipping_email_has_only_applicable_tools_and_posts(self):
        email = """Pickup request from Sable Ridge Materials to Fab 11 - Boise, ID.
Pickup date: 2026-08-24
25 sheets of 304 stainless, 9,800 lbs, truckload.
"""
        tool_names = {tool.name for tool in shipping_order_subagent["tools"]}

        result = create_shipping_order.invoke(
            {
                "shipper": "Sable Ridge Materials",
                "consignee": "Fab 11 - Boise, ID",
                "pickup_date": "2026-08-24",
                "items": [{"description": "304 stainless", "quantity": 25}],
                "weight_lbs": 9800,
                "mode": "truckload",
            }
        )

        self.assertIn("create_shipping_order", tool_names)
        self.assertNotIn("lookup_open_po", tool_names)
        self.assertNotIn("lookup_vendor", tool_names)
        self.assertNotIn("validate_against_erp", tool_names)
        self.assertEqual(result["status"], "posted")
        self.assertNotIn("request_clarification", email)

    def test_remittance_email_has_only_applicable_tools_and_matches(self):
        email = """Sable Ridge Materials payment reference WIRE-550213 settles invoice SR-9012 for $5,250.00
and invoice SR-9013 for $1,800.00.
"""
        tool_names = {tool.name for tool in remittance_subagent["tools"]}

        result = match_remittance_advice.invoke(
            {
                "payer": "Sable Ridge Materials",
                "payment_reference": "WIRE-550213",
                "invoice_numbers": ["SR-9012", "SR-9013"],
                "amounts": [5250.00, 1800.00],
            }
        )

        self.assertIn("match_remittance_advice", tool_names)
        self.assertNotIn("lookup_open_po", tool_names)
        self.assertNotIn("lookup_vendor", tool_names)
        self.assertNotIn("validate_against_erp", tool_names)
        self.assertEqual(result["status"], "posted")
        self.assertNotIn("request_clarification", email)

    def test_prompts_allowlist_fields_and_limit_clarification(self):
        self.assertIn("shipper, consignee,\npickup date, items, weight, and mode", SHIPPING_ORDER_PROMPT)
        self.assertIn("payer, payment\nreference, invoice numbers, and amounts", REMITTANCE_PROMPT)
        for prompt in (SHIPPING_ORDER_PROMPT, REMITTANCE_PROMPT):
            normalized_prompt = re.sub(r"\s+", " ", prompt)
            self.assertIn("No field outside this list may ever be reported as missing", normalized_prompt)
            self.assertIn("PO numbers and vendor ERP records are not part", normalized_prompt)
            self.assertIn("at most once per document", normalized_prompt)


if __name__ == "__main__":
    unittest.main()
