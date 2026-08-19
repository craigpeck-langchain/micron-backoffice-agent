"""Generate the static synthetic-email fixture set.

Writes one JSON file per email to fixtures/emails/, plus an index.json
listing every scenario. Content is hand-authored (not LLM-generated at
runtime) so the fixture set is fully deterministic and reviewable - re-run
any time to regenerate from this file after an edit:

    uv run python scripts/generate_synthetic_emails.py

30 normal cases spread across the 4 document types, 14 cases (2 per
planted flaw) that specifically trigger each bug in the agent, and 6
genuinely out-of-scope cases that have no corresponding code bug - they
exist to give LangSmith Engine "missing capability" / "task evasion"
signal with nothing to fix in a tool.
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE.parent / "fixtures" / "emails"


def email(id_: str, scenario: str, doc_type_expected: str, planted_flaw: str | None, from_: str, subject: str, body: str) -> dict:
    return {
        "id": id_,
        "scenario": scenario,
        "doc_type_expected": doc_type_expected,
        "planted_flaw": planted_flaw,
        "email": {"from": from_, "subject": subject, "body": body.strip()},
    }


EMAILS: list[dict] = [
    # ---------------------------------------------------------------
    # Normal: shipping_order (8)
    # ---------------------------------------------------------------
    email(
        "001_shipping_normal", "normal_shipping_order_01", "shipping_order", None,
        "dispatch@sableridgematerials.com", "Pickup request - stainless sheet to Fab 11",
        """
        Hi logistics team,

        Please arrange a truckload pickup of the 304 stainless sheet order for
        Fab 11. We have 25 sheets (4x8ft, 16ga) ready, total weight
        approximately 9,800 lbs. We can have it ready for pickup on
        2026-08-24.

        Shipper: Sable Ridge Materials, 4100 Foundry Rd, Twin Falls, ID
        Consignee: Fab 11 - Boise, ID

        Thanks,
        Sable Ridge Materials Dispatch
        """,
    ),
    email(
        "002_shipping_normal", "normal_shipping_order_02", "shipping_order", None,
        "shipping@ironharborfab.com", "LTL delivery - welded frame assemblies for Manassas",
        """
        Good morning,

        We'd like to schedule an LTL delivery of the welded steel frame
        assemblies (15 units, Rev C) to the Manassas site. Estimated weight
        is 2,100 lbs. Requested pickup date is 2026-08-26 from our Duluth,
        MN facility.

        Shipper: Iron Harbor Fabrication
        Consignee: Manassas Site - Manassas, VA

        Best,
        Iron Harbor Fabrication Shipping
        """,
    ),
    email(
        "003_shipping_normal", "normal_shipping_order_03", "shipping_order", None,
        "logistics@vantagepointelec.com", "Air freight needed - component kits to Singapore",
        """
        Hello,

        We need to air-ship the SMD component kits (resistor + capacitor
        assortments, 400 units combined, ~140 lbs) to the Singapore Fab as
        soon as possible - production is waiting on these. Pickup can happen
        tomorrow, 2026-08-21, from our San Jose warehouse.

        Shipper: Vantage Point Electronics
        Consignee: Singapore Fab - Woodlands

        Regards,
        Vantage Point Electronics Logistics
        """,
    ),
    email(
        "004_shipping_normal", "normal_shipping_order_04", "shipping_order", None,
        "ops@anchorpointpkg.com", "Truckload - foam inserts to Lehi DC",
        """
        Hi team,

        Ready to ship the ESD-safe foam insert order (3,000 units, roughly
        6,200 lbs) via full truckload to the Lehi distribution center.
        Pickup available 2026-08-25 from our Reno plant.

        Shipper: Anchor Point Packaging
        Consignee: Distribution Center - Lehi, UT

        Thanks,
        Anchor Point Packaging Ops
        """,
    ),
    email(
        "005_shipping_normal", "normal_shipping_order_05", "shipping_order", None,
        "shipping@northfieldcomponents.com", "LTL pickup - aluminum brackets to Boise",
        """
        Hello,

        Please schedule an LTL pickup for the aluminum bracket shipment (480
        units, Type-C, approx. 1,050 lbs) heading to Fab 11 in Boise. We can
        have the pallets ready 2026-08-23.

        Shipper: Northfield Components
        Consignee: Fab 11 - Boise, ID

        Thank you,
        Northfield Components Shipping
        """,
    ),
    email(
        "006_shipping_normal", "normal_shipping_order_06", "shipping_order", None,
        "dispatch@meridiantooling.com", "Truckload shipment - tooling to Manassas",
        """
        Hi,

        Our CNC end mill order is ready. We'd like to book a truckload
        shipment (60 sets, ~3,400 lbs including packaging) to the Manassas
        site, pickup on 2026-08-27 from our Cleveland facility.

        Shipper: Meridian Tooling Co
        Consignee: Manassas Site - Manassas, VA

        Thanks,
        Meridian Tooling Co Dispatch
        """,
    ),
    email(
        "007_shipping_normal", "normal_shipping_order_07", "shipping_order", None,
        "facilities.boise@micron.com", "Inter-site transfer - surplus equipment Boise to Lehi",
        """
        Hi logistics,

        We have surplus test equipment racks to transfer from Fab 11 in
        Boise to the Lehi distribution center for redeployment. Estimated
        weight 4,500 lbs, LTL is fine. Target pickup 2026-08-28.

        Shipper: Fab 11 - Boise, ID
        Consignee: Distribution Center - Lehi, UT

        Thanks,
        Micron Facilities - Boise
        """,
    ),
    email(
        "008_shipping_normal", "normal_shipping_order_08", "shipping_order", None,
        "export@cascadeprecisionmachining.com", "Ocean freight booking - machined parts to Singapore",
        """
        Hello,

        We need to book ocean freight for a container of precision-machined
        parts heading to the Singapore Fab. Total weight approximately
        18,000 lbs. Ready for pickup at our Long Beach staging warehouse on
        2026-09-02.

        Shipper: Cascade Precision Machining
        Consignee: Singapore Fab - Woodlands

        Regards,
        Cascade Precision Machining Export Desk
        """,
    ),
    # ---------------------------------------------------------------
    # Normal: purchase_order (7)
    # ---------------------------------------------------------------
    email(
        "009_po_normal", "normal_purchase_order_01", "purchase_order", None,
        "procurement.boise@micron.com", "New PO needed - additional aluminum brackets",
        """
        Hi procurement,

        We're running low on Type-C aluminum brackets ahead of the next
        production run. Please place a new order with Northfield Components
        for 600 units at their standard unit price ($12.40). Requested
        delivery date is 2026-09-10, ship to Fab 11 - Boise.

        Thanks,
        Fab 11 Manufacturing Engineering
        """,
    ),
    email(
        "010_po_normal", "normal_purchase_order_02", "purchase_order", None,
        "eng.manassas@micron.com", "Order more stainless sheet",
        """
        Hi team,

        Please issue a new purchase order to Sable Ridge Materials for 40
        sheets of 304 stainless (4x8ft, 16ga) at $210.00/sheet. We need it by
        2026-09-15 at the Manassas site.

        Thanks,
        Manassas Engineering
        """,
    ),
    email(
        "011_po_normal", "normal_purchase_order_03", "purchase_order", None,
        "procurement.sg@micron.com", "New order - SMD component kits",
        """
        Hello,

        Please place an order with Vantage Point Electronics for 300 SMD
        resistor kits (0603 assorted, $9.75 each) and 300 SMD capacitor kits
        (0805 assorted, $11.25 each). Requested delivery 2026-09-08, ship to
        Singapore Fab - Woodlands.

        Thanks,
        Singapore Fab Procurement
        """,
    ),
    email(
        "012_po_normal", "normal_purchase_order_04", "purchase_order", None,
        "ops.lehi@micron.com", "Need a new PO for packaging foam",
        """
        Hi,

        Please issue a purchase order to Anchor Point Packaging for 5,000
        units of the custom die-cut ESD-safe foam insert at $1.85/unit.
        Requested delivery date 2026-09-12, ship to Distribution Center -
        Lehi, UT.

        Thanks,
        Lehi DC Operations
        """,
    ),
    email(
        "013_po_normal", "normal_purchase_order_05", "purchase_order", None,
        "eng.boise@micron.com", "Order welded frame assemblies",
        """
        Hi procurement,

        Please place a new order with Iron Harbor Fabrication for 20 welded
        steel frame assemblies (Rev C) at $640.00/unit. Requested delivery
        2026-09-20, ship to Fab 11 - Boise, ID.

        Thanks,
        Fab 11 Engineering
        """,
    ),
    email(
        "014_po_normal", "normal_purchase_order_06", "purchase_order", None,
        "eng.manassas@micron.com", "New tooling order",
        """
        Hi team,

        We need another batch of CNC end mills. Please issue a purchase
        order to Meridian Tooling Co for 45 sets at $84.00/set, requested
        delivery 2026-09-18, ship to Manassas Site - Manassas, VA.

        Thanks,
        Manassas Engineering
        """,
    ),
    email(
        "015_po_normal", "normal_purchase_order_07", "purchase_order", None,
        "procurement.boise@micron.com", "Order precision-machined parts",
        """
        Hi procurement,

        Please place an order with Cascade Precision Machining for 25 units
        of the precision-machined bracket assembly at $145.00/unit.
        Requested delivery date 2026-09-22, ship to Fab 11 - Boise, ID.

        Thanks,
        Fab 11 Procurement
        """,
    ),
    # ---------------------------------------------------------------
    # Normal: invoice (8)
    # ---------------------------------------------------------------
    email(
        "016_invoice_normal", "normal_invoice_01", "invoice", None,
        "ap@northfieldcomponents.com", "Invoice INV-88213 for PO-10045",
        """
        Hi team,

        Please find our invoice INV-88213 for PO-10045: 480 units of
        precision aluminum brackets at $12.40/unit, total $5,952.00, due net
        30 (2026-09-20).

        Thanks,
        Northfield Components AP Team
        """,
    ),
    email(
        "017_invoice_normal", "normal_invoice_02", "invoice", None,
        "billing@meridiantooling.com", "Invoice MT-4471 for PO-10062",
        """
        Hello,

        Invoice MT-4471 for PO-10062: 60 CNC end mill sets at $84.00/set,
        total $5,040.00. Payment terms net 30, due 2026-09-18.

        Regards,
        Meridian Tooling Co Billing
        """,
    ),
    email(
        "018_invoice_normal", "normal_invoice_03", "invoice", None,
        "ap@sableridgematerials.com", "Invoice SR-9012 - PO-10071",
        """
        Hi,

        Attached invoice SR-9012 against PO-10071: 25 sheets of 304
        stainless (4x8ft, 16ga) at $210.00/sheet, total $5,250.00, due net 30
        (2026-09-22).

        Thanks,
        Sable Ridge Materials AP
        """,
    ),
    email(
        "019_invoice_normal", "normal_invoice_04", "invoice", None,
        "billing@vantagepointelec.com", "Invoice VP-33210 for PO-10088",
        """
        Hello,

        Invoice VP-33210 against PO-10088:
        - SMD resistor kit, 0603 assorted: 200 units @ $9.75 = $1,950.00
        - SMD capacitor kit, 0805 assorted: 200 units @ $11.25 = $2,250.00

        Total: $4,200.00. Due net 30 (2026-09-25).

        Thanks,
        Vantage Point Electronics Billing
        """,
    ),
    email(
        "020_invoice_normal", "normal_invoice_05", "invoice", None,
        "ap@ironharborfab.com", "Invoice IH-5567 - PO-10093",
        """
        Hi,

        Invoice IH-5567 against PO-10093: 15 welded steel frame assemblies
        (Rev C) at $640.00/unit, total $9,600.00, due net 30 (2026-09-24).

        Thanks,
        Iron Harbor Fabrication AP
        """,
    ),
    email(
        "021_invoice_normal", "normal_invoice_06", "invoice", None,
        "billing@anchorpointpkg.com", "Invoice AP-7788 for PO-10101",
        """
        Hello,

        Invoice AP-7788 against PO-10101: 3,000 units of ESD-safe foam
        insert, custom die-cut, at $1.85/unit, total $5,550.00, due net 30
        (2026-09-26).

        Thanks,
        Anchor Point Packaging Billing
        """,
    ),
    email(
        "022_invoice_normal", "normal_invoice_07", "invoice", None,
        "billing@wrenfieldlogistics.com", "Invoice WF-2201 for PO-10112",
        """
        Hi,

        Invoice WF-2201 against PO-10112: dedicated truckload freight
        service, Boise-Lehi lane, 1 unit at $2,400.00, total $2,400.00, due
        net 15 (2026-09-05).

        Thanks,
        Wrenfield Logistics Partners Billing
        """,
    ),
    email(
        "023_invoice_normal", "normal_invoice_08", "invoice", None,
        "ap@cascadeprecisionmanufacturing.com", "Invoice CPM-6640 - PO-10125",
        """
        Hello,

        Invoice CPM-6640 against PO-10125: 40 units of precision-machined
        housing, Rev B, at $96.50/unit, total $3,860.00, due net 30
        (2026-09-28).

        Thanks,
        Cascade Precision Manufacturing AP
        """,
    ),
    # ---------------------------------------------------------------
    # Normal: remittance_advice (7)
    # ---------------------------------------------------------------
    email(
        "024_remit_normal", "normal_remittance_01", "remittance_advice", None,
        "treasury@micron.com", "Remittance advice - payment to Northfield Components",
        """
        Hi,

        This confirms payment of $5,952.00 to Northfield Components,
        settling invoice INV-88213. Payment reference: ACH-771029.

        Thanks,
        Micron Treasury
        """,
    ),
    email(
        "025_remit_normal", "normal_remittance_02", "remittance_advice", None,
        "treasury@micron.com", "Remittance advice - two invoices settled, Sable Ridge Materials",
        """
        Hi,

        Payment reference WIRE-550213 settles two invoices for Sable Ridge
        Materials: SR-9012 for $5,250.00 and SR-9013 for $1,800.00.

        Thanks,
        Micron Treasury
        """,
    ),
    email(
        "026_remit_normal", "normal_remittance_03", "remittance_advice", None,
        "treasury@micron.com", "Remittance advice - Iron Harbor Fabrication",
        """
        Hi,

        Payment reference ACH-771144 settles invoice IH-5567 for $9,600.00
        to Iron Harbor Fabrication.

        Thanks,
        Micron Treasury
        """,
    ),
    email(
        "027_remit_normal", "normal_remittance_04", "remittance_advice", None,
        "treasury@micron.com", "Remittance advice - Vantage Point Electronics, two invoices",
        """
        Hi,

        Payment reference WIRE-550298 settles two Vantage Point Electronics
        invoices: VP-33210 for $4,200.00 and VP-33255 for $2,975.00.

        Thanks,
        Micron Treasury
        """,
    ),
    email(
        "028_remit_normal", "normal_remittance_05", "remittance_advice", None,
        "treasury@micron.com", "Remittance advice - Meridian Tooling Co",
        """
        Hi,

        Payment reference ACH-771190 settles invoice MT-4471 for $5,040.00
        to Meridian Tooling Co.

        Thanks,
        Micron Treasury
        """,
    ),
    email(
        "029_remit_normal", "normal_remittance_06", "remittance_advice", None,
        "treasury@micron.com", "Remittance advice - Anchor Point Packaging",
        """
        Hi,

        Payment reference ACH-771205 settles invoice AP-7788 for $5,550.00
        to Anchor Point Packaging.

        Thanks,
        Micron Treasury
        """,
    ),
    email(
        "030_remit_normal", "normal_remittance_07", "remittance_advice", None,
        "treasury@micron.com", "Remittance advice - Delacroix Freight & Logistics",
        """
        Hi,

        Payment reference WIRE-550341 settles invoice DFL-1091 for $3,120.00
        to Delacroix Freight & Logistics.

        Thanks,
        Micron Treasury
        """,
    ),
    # ---------------------------------------------------------------
    # Flaw 1: hallucinated PO number (invoice_agent prompt) (2)
    # ---------------------------------------------------------------
    email(
        "031_flaw_hallucinated_po", "hallucinated_po_1", "invoice", "hallucinated_po",
        "ap@northfieldcomponents.com", "Invoice for units from your recent shipment",
        """
        Hi team,

        Please find our invoice for the 500 aluminum brackets from your
        recent order, at $12.40/unit, total $6,200.00, due net 30
        (2026-09-27). Invoice number NC-9910.

        Thanks,
        Northfield Components AP Team
        """,
    ),
    email(
        "032_flaw_hallucinated_po", "hallucinated_po_2", "invoice", "hallucinated_po",
        "billing@meridiantooling.com", "Invoice for the tooling we discussed",
        """
        Hello,

        Attached is invoice MT-4502 for the 75 CNC end mill sets from the
        order we discussed last month, at $84.00/set, total $6,300.00. Due
        net 30 (2026-09-29).

        Regards,
        Meridian Tooling Co Billing
        """,
    ),
    # ---------------------------------------------------------------
    # Flaw 2: currency mismatch silently accepted (post_invoice tool) (2)
    # ---------------------------------------------------------------
    email(
        "033_flaw_currency_mismatch", "currency_mismatch_1", "invoice", "currency_mismatch",
        "ap@balticcircuitworks.com", "Invoice BCW-2201 for PO-10140",
        """
        Hi,

        Invoice BCW-2201 against PO-10140: 500 units of 6-layer custom PCB
        at $18.20/unit, total $9,100.00 USD. Due net 30 (2026-09-30).

        Thanks,
        Baltic Circuit Works AP
        """,
    ),
    email(
        "034_flaw_currency_mismatch", "currency_mismatch_2", "invoice", "currency_mismatch",
        "ap@balticcircuitworks.com", "Invoice BCW-2214 for PO-10140",
        """
        Hello,

        Invoice BCW-2214 against PO-10140: 500 units of 6-layer custom PCB
        at £14.60/unit, total £7,300.00. Due net 30 (2026-10-02).

        Thanks,
        Baltic Circuit Works AP
        """,
    ),
    # ---------------------------------------------------------------
    # Flaw 3: escalate_to_human silent failure on '&'/"'" vendor names (2)
    # ---------------------------------------------------------------
    email(
        "035_flaw_escalation_drop", "escalation_drop_1", "invoice", "escalation_silent_failure",
        "ap@delacroixfreight.com", "Invoice DFL-1102 for PO-99981",
        """
        Hi,

        Invoice DFL-1102 against PO-99981: linehaul freight service, 1 unit
        at $3,450.00, total $3,450.00. Due net 15 (2026-09-05).

        Thanks,
        Delacroix Freight & Logistics AP
        """,
    ),
    email(
        "036_flaw_escalation_drop", "escalation_drop_2", "invoice", "escalation_silent_failure",
        "billing@omalleyindustrial.com", "Invoice OM-6602 referencing PO-10062",
        """
        Hello,

        Invoice OM-6602 against PO-10062: 30 units of industrial fastener
        assortment at $22.00/unit, total $660.00. Due net 30 (2026-09-19).

        Thanks,
        O'Malley Industrial Supply Billing
        """,
    ),
    # ---------------------------------------------------------------
    # Flaw 4: wrong-tool classification bias ("order" in subject) (2)
    # ---------------------------------------------------------------
    email(
        "037_flaw_wrong_tool", "wrong_tool_classification_1", "invoice", "wrong_tool_classification",
        "ap@sableridgematerials.com", "Invoice for your recent order PO-10071",
        """
        Hi team,

        Invoice SR-9044 for PO-10071: 25 sheets of 304 stainless (4x8ft,
        16ga) at $210.00/sheet, total $5,250.00, due net 30 (2026-09-23).
        This is an invoice, not a new order request - please process for
        payment.

        Thanks,
        Sable Ridge Materials AP
        """,
    ),
    email(
        "038_flaw_wrong_tool", "wrong_tool_classification_2", "invoice", "wrong_tool_classification",
        "billing@vantagepointelec.com", "Order INV-77401 - Payment Due",
        """
        Hello,

        Please process invoice INV-77401 against PO-10088 for payment: SMD
        component kits as previously supplied, total $4,200.00, due net 30
        (2026-09-24). This invoice covers goods already delivered.

        Thanks,
        Vantage Point Electronics Billing
        """,
    ),
    # ---------------------------------------------------------------
    # Flaw 5: missing capability - partial credit memo (2)
    # ---------------------------------------------------------------
    email(
        "039_flaw_credit_memo", "missing_credit_memo_1", "invoice", "missing_credit_memo_capability",
        "ap@ironharborfab.com", "Invoice IH-5602 with partial credit for damaged units",
        """
        Hi,

        Invoice IH-5602 against PO-10093: 15 welded steel frame assemblies
        at $640.00/unit, subtotal $9,600.00. Two units arrived damaged in
        transit, so we're applying a credit of -$1,280.00 for those units.
        Net amount due: $8,320.00, net 30 (2026-09-24).

        Thanks,
        Iron Harbor Fabrication AP
        """,
    ),
    email(
        "040_flaw_credit_memo", "missing_credit_memo_2", "invoice", "missing_credit_memo_capability",
        "billing@anchorpointpkg.com", "Invoice AP-7801 - includes return credit from prior shipment",
        """
        Hello,

        Invoice AP-7801 against PO-10101: 3,000 units foam insert at
        $1.85/unit, subtotal $5,550.00. We're also crediting $310.00 for the
        over-shipped units returned from our last delivery. Net total due:
        $5,240.00, due net 30 (2026-09-26).

        Thanks,
        Anchor Point Packaging Billing
        """,
    ),
    # ---------------------------------------------------------------
    # Flaw 6: agent looping on ambiguous/truncated vendor reference (2)
    # ---------------------------------------------------------------
    email(
        "041_flaw_looping", "agent_looping_1", "invoice", "agent_looping",
        "ap@cascadeprecision.com", "Invoice CP-4402 - Cascade Precision",
        """
        Hi,

        Invoice CP-4402 for 40 units of precision-machined housing at
        $96.50/unit, total $3,860.00, due net 30 (2026-09-28).

        Thanks,
        Cascade Precision AP
        """,
    ),
    email(
        "042_flaw_looping", "agent_looping_2", "purchase_order", "agent_looping",
        "eng.boise@micron.com", "Order more from Cascade Precision again",
        """
        Hi procurement,

        Please order another 25 units of the precision-machined bracket
        assembly, same as before, from Cascade Precision. Requested delivery
        2026-09-22, ship to Fab 11 - Boise, ID.

        Thanks,
        Fab 11 Procurement
        """,
    ),
    # ---------------------------------------------------------------
    # Flaw 7: system prompt drift - trusts padded total over line items (2)
    # ---------------------------------------------------------------
    email(
        "043_flaw_prompt_drift", "prompt_drift_padded_total_1", "invoice", "system_prompt_drift",
        "ap@sableridgematerials.com", "Invoice SR-9077 for PO-10071",
        """
        Hi,

        Invoice SR-9077 against PO-10071: 25 sheets of 304 stainless (4x8ft,
        16ga) at $210.00/sheet. Total due: $5,700.00, net 30 (2026-09-23).

        Thanks,
        Sable Ridge Materials AP
        """,
    ),
    email(
        "044_flaw_prompt_drift", "prompt_drift_padded_total_2", "invoice", "system_prompt_drift",
        "ap@northfieldcomponents.com", "Invoice NC-9944 for PO-10045",
        """
        Hi team,

        Invoice NC-9944 for PO-10045: 480 units of precision aluminum
        brackets at $12.40/unit. Total due: $6,800.00, due net 30
        (2026-09-20).

        Thanks,
        Northfield Components AP Team
        """,
    ),
    # ---------------------------------------------------------------
    # Out of scope (6) - no corresponding code bug, pure capability gap
    # ---------------------------------------------------------------
    email(
        "045_oos_customs", "out_of_scope_customs_inquiry", "out_of_scope", None,
        "broker@globalcustomsadvisors.com", "HTS classification question for upcoming import",
        """
        Hi,

        We're preparing the customs paperwork for an upcoming import and
        need to confirm the correct HTS classification code for the
        precision-machined aluminum components before they ship. Can someone
        from your compliance team advise on the correct code and applicable
        duty rate?

        Thanks,
        Global Customs Advisors
        """,
    ),
    email(
        "046_oos_non_english", "out_of_scope_non_english", "out_of_scope", None,
        "facturacion@proveedorlatam.com", "Factura FP-2291 por orden de compra",
        """
        Estimados,

        Adjunto la factura FP-2291 correspondiente a la orden de compra
        reciente: 200 unidades de conectores industriales a $8.40/unidad,
        total $1,680.00. Vencimiento a 30 dias.

        Saludos,
        Proveedor LatAm - Facturacion
        """,
    ),
    email(
        "047_oos_garbled", "out_of_scope_garbled_ocr", "out_of_scope", None,
        "scans@sharedmailbox.internal", "Fwd: Scanned document 08-19",
        """
        FWD from scanner -

        I–nvo1c3 N0. ####7 P0#: 10-0-45 Qty: 4B0 U/P: 1?.40
        T0tal: $$,,952.00 rn3t 3o d4ys  ***PAGE 1 OF 1 - LOW QUALITY SCAN***
        [illegible] [illegible] pls advise

        - front desk
        """,
    ),
    email(
        "048_oos_relationship", "out_of_scope_vendor_notice", "out_of_scope", None,
        "notices@ironharborfab.com", "Planned facility closure - Labor Day",
        """
        Hi,

        Just a heads up that our Duluth facility will be closed for Labor
        Day (2026-09-07) and shipping will resume 2026-09-08. No action
        needed on your end - just wanted to flag this in case you're
        planning any pickups around that date.

        Thanks,
        Iron Harbor Fabrication
        """,
    ),
    email(
        "049_oos_marketing", "out_of_scope_marketing", "out_of_scope", None,
        "sales@vantagepointelec.com", "New 2027 component catalog now available",
        """
        Hi,

        Our new 2027 catalog is live with expanded SMD component options and
        volume pricing tiers. Let us know if you'd like a walkthrough with
        your account rep - we're happy to set up time.

        Best,
        Vantage Point Electronics Sales
        """,
    ),
    email(
        "050_oos_internal", "out_of_scope_internal_hr", "out_of_scope", None,
        "hr@micron.com", "Open enrollment reminder - action needed by 8/31",
        """
        Hi all,

        This is a reminder that open enrollment for benefits closes 8/31.
        Please log into the benefits portal to make your elections if you
        haven't already.

        Thanks,
        Micron HR
        """,
    ),
]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    index = []
    for record in EMAILS:
        path = OUT_DIR / f"{record['id']}.json"
        path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        index.append(
            {
                "id": record["id"],
                "scenario": record["scenario"],
                "doc_type_expected": record["doc_type_expected"],
                "planted_flaw": record["planted_flaw"],
                "from": record["email"]["from"],
                "subject": record["email"]["subject"],
            }
        )
    (OUT_DIR / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(EMAILS)} fixture emails + index.json to {OUT_DIR}")


if __name__ == "__main__":
    main()
