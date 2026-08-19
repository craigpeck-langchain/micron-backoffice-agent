import unittest

from backoffice_agent.tools import ESCALATION_LOG, escalate_to_human


class EscalateToHumanTests(unittest.TestCase):
    def setUp(self):
        ESCALATION_LOG.clear()

    def test_punctuated_vendor_names_are_logged(self):
        for vendor in ("Delacroix Freight & Logistics", "O'Malley Industrial Supply"):
            result = escalate_to_human.invoke(
                {
                    "reason": "PO vendor mismatch",
                    "doc_type": "invoice",
                    "extracted_data": {"vendor": vendor},
                }
            )

            self.assertEqual(result["status"], "escalated")
            self.assertTrue(
                any(record["ticket_id"] == result["ticket_id"] for record in ESCALATION_LOG)
            )


if __name__ == "__main__":
    unittest.main()
