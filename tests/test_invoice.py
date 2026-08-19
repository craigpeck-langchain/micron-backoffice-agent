import unittest

from backoffice_agent.subagents.invoice import post_invoice


class PostInvoiceValidationTests(unittest.TestCase):
    def test_rejects_unreconciled_total(self):
        result = post_invoice.invoke(
            {
                "vendor": "Northfield Components",
                "invoice_number": "NC-9944",
                "po_number": "PO-10045",
                "line_items": [
                    {"description": "Precision aluminum bracket, Type-C", "qty": 480, "unit_price": 12.40}
                ],
                "currency": "USD",
                "total_amount": 6800.00,
                "due_date": "2026-09-20",
            }
        )

        self.assertEqual(result["status"], "validation_failed")
        self.assertEqual(result["error"], "total_mismatch")
        self.assertEqual(result["computed_total"], 5952.00)

    def test_rejects_vendor_currency_mismatch(self):
        result = post_invoice.invoke(
            {
                "vendor": "Baltic Circuit Works",
                "invoice_number": "BCW-2201",
                "po_number": "PO-10140",
                "line_items": [
                    {"description": "6-layer PCB, custom fab", "qty": 500, "unit_price": 18.20}
                ],
                "currency": "USD",
                "total_amount": 9100.00,
                "due_date": "2026-09-30",
            }
        )

        self.assertEqual(result["status"], "validation_failed")
        self.assertEqual(result["error"], "currency_mismatch")
        self.assertEqual(result["erp_currency"], "EUR")

    def test_posts_reconciled_invoice_in_vendor_currency(self):
        result = post_invoice.invoke(
            {
                "vendor": "Baltic Circuit Works",
                "invoice_number": "BCW-2214",
                "po_number": "PO-10140",
                "line_items": [
                    {"description": "6-layer PCB, custom fab", "qty": 500, "unit_price": 18.20}
                ],
                "currency": "eur",
                "total_amount": 9100.00,
                "due_date": "2026-10-02",
            }
        )

        self.assertEqual(result["status"], "posted")
        self.assertEqual(result["details"]["currency"], "eur")


if __name__ == "__main__":
    unittest.main()
