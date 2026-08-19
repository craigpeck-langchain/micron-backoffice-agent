import unittest
from unittest.mock import Mock

from backoffice_agent.prompts import SHARED_TOOL_GUIDANCE
from backoffice_agent.subagents.invoice import post_invoice
from backoffice_agent.tools import escalate_to_human, lookup_vendor


class AmbiguousVendorTest(unittest.TestCase):
    def test_cp4402_ambiguous_vendor_escalates_without_retry_or_post(self):
        email = """From: ap@cascadeprecision.com
Subject: Invoice CP-4402 - Cascade Precision

Invoice CP-4402 for 40 units of precision-machined housing at $96.50/unit,
total $3,860.00, due net 30 (2026-09-28).

Thanks,
Cascade Precision AP"""
        lookup = Mock(wraps=lookup_vendor.invoke)
        post = Mock(wraps=post_invoice.invoke)
        escalate = Mock(wraps=escalate_to_human.invoke)

        result = lookup({"vendor_name": "Cascade Precision"})
        self.assertEqual(result["match"], "ambiguous")
        self.assertEqual(
            {candidate["vendor_name"] for candidate in result["candidates"]},
            {"Cascade Precision Machining", "Cascade Precision Manufacturing"},
        )

        extracted_data = {
            "vendor": "Cascade Precision",
            "invoice_number": "CP-4402",
            "email": email,
            "vendor_candidates": result["candidates"],
        }
        escalation = escalate(
            {
                "reason": "Vendor match is ambiguous; document does not uniquely identify a candidate.",
                "doc_type": "invoice",
                "extracted_data": extracted_data,
            }
        )

        self.assertEqual(lookup.call_count, 1)
        self.assertEqual(post.call_count, 0)
        self.assertEqual(escalation["status"], "escalated")
        escalation_data = escalate.call_args.args[0]["extracted_data"]
        self.assertEqual(
            {
                candidate["vendor_name"]
                for candidate in escalation_data["vendor_candidates"]
            },
            {"Cascade Precision Machining", "Cascade Precision Manufacturing"},
        )

    def test_shared_guidance_forbids_ambiguous_lookup_retries_and_random_selection(self):
        self.assertIn("Repeating a lookup with arguments already tried is forbidden", SHARED_TOOL_GUIDANCE)
        self.assertIn("do not pick a candidate at random", SHARED_TOOL_GUIDANCE)
        self.assertIn("pass the candidate list in extracted_data", SHARED_TOOL_GUIDANCE)
