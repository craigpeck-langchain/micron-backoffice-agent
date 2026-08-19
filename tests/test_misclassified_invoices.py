import unittest

from backoffice_agent.prompts import TOP_LEVEL_SYSTEM_PROMPT
from backoffice_agent.subagents.purchase_order import PURCHASE_ORDER_PROMPT


ORDER_INVOICE_EMAIL = """From: billing@vantagepointelec.com
Subject: Order INV-77401 - Payment Due

Please process invoice INV-77401 against PO-10088 for payment: SMD component
kits as previously supplied. This invoice covers goods already delivered.
"""

PAYMENT_INVOICE_EMAIL = """From: ap@sableridgematerials.com
Subject: Invoice for your recent order PO-10071

Invoice SR-9044 for PO-10071. This is an invoice, not a new order request -
please process for payment.
"""


class MisclassifiedInvoicePromptTests(unittest.TestCase):
    def test_delivered_invoice_cannot_create_purchase_order(self):
        self.assertIn("NEW order", PURCHASE_ORDER_PROMPT)
        self.assertIn("existing PO number", PURCHASE_ORDER_PROMPT)
        self.assertIn("goods already delivered or previously supplied", PURCHASE_ORDER_PROMPT)
        self.assertIn("call escalate_to_human instead of create_purchase_order", PURCHASE_ORDER_PROMPT)
        self.assertIn("PO-10088", ORDER_INVOICE_EMAIL)
        self.assertIn("goods already delivered", ORDER_INVOICE_EMAIL)

    def test_explicit_invoice_for_payment_escalates_without_false_success(self):
        self.assertIn("invoice to be\npaid", PURCHASE_ORDER_PROMPT)
        self.assertIn("Never state that a document was created, posted, validated, or processed for", PURCHASE_ORDER_PROMPT)
        self.assertIn("If no\nposting tool ran, state what was not done and escalate", PURCHASE_ORDER_PROMPT)
        self.assertIn("verbatim contradicting\nquote", TOP_LEVEL_SYSTEM_PROMPT)
        self.assertIn("only to explicit self-identification", TOP_LEVEL_SYSTEM_PROMPT)
        self.assertIn("not a new order request", PAYMENT_INVOICE_EMAIL)
        self.assertIn("process for payment", PAYMENT_INVOICE_EMAIL)


if __name__ == "__main__":
    unittest.main()
