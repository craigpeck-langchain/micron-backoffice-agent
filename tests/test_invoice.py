import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from backoffice_agent.subagents.invoice import INVOICE_PROMPT, invoice_subagent, post_invoice, record_credit_memo


class InvoiceCreditTests(unittest.TestCase):
    def test_mixed_invoice_ih_5602_uses_gross_invoice_and_credit_memo(self):
        line_items = [{"description": "welded steel frame assembly", "qty": 15, "unit_price": 640.00}]

        rejected = post_invoice.invoke({
            "vendor": "Iron Harbor Fabrication",
            "invoice_number": "IH-5602",
            "po_number": "PO-10093",
            "line_items": line_items,
            "currency": "USD",
            "total_amount": 8320.00,
            "due_date": "2026-09-24",
        })
        invoice = post_invoice.invoke({
            "vendor": "Iron Harbor Fabrication",
            "invoice_number": "IH-5602",
            "po_number": "PO-10093",
            "line_items": line_items,
            "currency": "USD",
            "total_amount": 9600.00,
            "due_date": "2026-09-24",
        })
        credit = record_credit_memo.invoke({
            "vendor": "Iron Harbor Fabrication",
            "credit_reference": "IH-5602-DAMAGE",
            "original_invoice_number": "IH-5602",
            "po_number": "PO-10093",
            "reason": "damaged goods",
            "line_items": [{"description": "damaged welded steel frame assembly", "qty": 2, "unit_price": 640.00}],
            "currency": "USD",
            "credit_amount": 1280.00,
        })

        self.assertEqual(rejected["status"], "validation_failed")
        self.assertEqual(rejected["error"], "unexplained_credit")
        self.assertEqual(invoice["status"], "posted")
        self.assertEqual(invoice["details"]["total_amount"], 9600.00)
        self.assertEqual(credit["status"], "posted")
        self.assertTrue(credit["record_id"].startswith("CM-"))

    def test_mixed_invoice_ap_7801_uses_gross_invoice_and_credit_memo(self):
        line_items = [{"description": "foam insert", "qty": 3000, "unit_price": 1.85}]

        rejected = post_invoice.invoke({
            "vendor": "Anchor Point Packaging",
            "invoice_number": "AP-7801",
            "po_number": "PO-10101",
            "line_items": line_items,
            "currency": "USD",
            "total_amount": 5240.00,
            "due_date": "2026-09-26",
        })
        invoice = post_invoice.invoke({
            "vendor": "Anchor Point Packaging",
            "invoice_number": "AP-7801",
            "po_number": "PO-10101",
            "line_items": line_items,
            "currency": "USD",
            "total_amount": 5550.00,
            "due_date": "2026-09-26",
        })
        credit = record_credit_memo.invoke({
            "vendor": "Anchor Point Packaging",
            "credit_reference": "AP-7801-RETURN",
            "original_invoice_number": "AP-7801",
            "po_number": "PO-10101",
            "reason": "over-shipment return",
            "line_items": [{"description": "returned over-shipped foam insert", "qty": 1, "unit_price": 310.00}],
            "currency": "USD",
            "credit_amount": 310.00,
        })

        self.assertEqual(rejected["status"], "validation_failed")
        self.assertEqual(rejected["error"], "unexplained_credit")
        self.assertEqual(invoice["status"], "posted")
        self.assertEqual(invoice["details"]["total_amount"], 5550.00)
        self.assertEqual(credit["status"], "posted")
        self.assertTrue(credit["record_id"].startswith("CM-"))

    def test_prompt_and_tool_list_require_separate_credit_record(self):
        self.assertIn(record_credit_memo, invoice_subagent["tools"])
        self.assertIn("GROSS invoice", INVOICE_PROMPT)
        self.assertIn("Never reduce total_amount to a net figure", INVOICE_PROMPT)
        self.assertNotIn("trust the vendor's stated total_amount", INVOICE_PROMPT)


if __name__ == "__main__":
    unittest.main()
