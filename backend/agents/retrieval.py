"""
LedgerFlow AI — Policy & Retrieval Agent
Searches policies, PO data, and vendor info using RAG + Nova Multimodal Embeddings.
"""
import json
import logging
from agents.state import CaseState
from services.rag import rag_service
from database import async_session

logger = logging.getLogger(__name__)

# Simulated PO and vendor data for MVP (would come from MCP/ERP in production)
MOCK_PURCHASE_ORDERS = {
    "PO-10450": {
        "po_number": "PO-10450",
        "vendor": "TechSupply Corp",
        "vendor_id": "V-001",
        "total": 15000.00,
        "currency": "USD",
        "status": "approved",
        "date": "2025-11-15",
        "line_items": [
            {"description": "Server Equipment", "quantity": 5, "unit_price": 2500.00, "total": 12500.00},
            {"description": "Installation Service", "quantity": 1, "unit_price": 2500.00, "total": 2500.00},
        ],
    },
    "PO-10452": {
        "po_number": "PO-10452",
        "vendor": "OfficeMax Solutions",
        "vendor_id": "V-003",
        "total": 4200.00,
        "currency": "USD",
        "status": "approved",
        "date": "2025-12-01",
        "line_items": [
            {"description": "Office Furniture", "quantity": 10, "unit_price": 350.00, "total": 3500.00},
            {"description": "Delivery & Assembly", "quantity": 1, "unit_price": 700.00, "total": 700.00},
        ],
    },
    "PO-10455": {
        "po_number": "PO-10455",
        "vendor": "CloudNet Services",
        "vendor_id": "V-002",
        "total": 8500.00,
        "currency": "USD",
        "status": "approved",
        "date": "2025-12-10",
        "line_items": [
            {"description": "Annual Cloud License", "quantity": 1, "unit_price": 7500.00, "total": 7500.00},
            {"description": "Premium Support", "quantity": 1, "unit_price": 1000.00, "total": 1000.00},
        ],
    },
}

MOCK_VENDORS = {
    "V-001": {
        "id": "V-001", "name": "TechSupply Corp", "tax_id": "20-5551234",
        "status": "active", "payment_terms": "Net 30",
    },
    "V-002": {
        "id": "V-002", "name": "CloudNet Services", "tax_id": "20-5559876",
        "status": "active", "payment_terms": "Net 45",
    },
    "V-003": {
        "id": "V-003", "name": "OfficeMax Solutions", "tax_id": "20-5554567",
        "status": "active", "payment_terms": "Net 30",
    },
    "V-004": {
        "id": "V-004", "name": "DataFlow Analytics", "tax_id": "20-5558765",
        "status": "suspended", "payment_terms": "Net 60",
    },
    "V-005": {
        "id": "V-005", "name": "SecureIT Partners", "tax_id": "20-5552345",
        "status": "active", "payment_terms": "Net 30",
    },
}


async def retrieval_agent(state: CaseState) -> dict:
    """
    Policy & Retrieval Agent — enriches the case with relevant policies,
    PO data, and vendor information using RAG search.
    """
    parsed = state.get("parsed_fields", {})
    logger.info(f"[Retrieval] Searching context for case {state['case_id']}")

    trace_step = {
        "step_number": 2,
        "agent_name": "Policy & Retrieval Agent",
        "step_type": "retrieve",
        "objective": "Retrieve relevant policies, PO data, and vendor information",
        "tool_called": "nova_multimodal_embeddings + pgvector",
        "policy_refs": [],
        "evidence_refs": [],
        "result_summary": "",
        "confidence": 0.0,
        "status": "completed",
    }

    retrieved_policies = []
    retrieved_po = None
    vendor_info = None

    try:
        # 1. Search for relevant policies via RAG
        queries = []
        if parsed.get("amount_total"):
            queries.append(f"invoice tolerance policy for amount {parsed['amount_total']}")
        if parsed.get("vendor_name"):
            queries.append(f"vendor validation rules for {parsed['vendor_name']}")
        if parsed.get("tax_amount") is not None:
            queries.append("tax field requirements for invoices")
        if parsed.get("amount_total") and (parsed.get("amount_total", 0) or 0) > 1000:
            queries.append("approval hierarchy for financial transactions")
        
        # Default query if nothing specific
        if not queries:
            queries = ["accounts payable invoice processing policy"]

        async with async_session() as session:
            for query in queries:
                results = await rag_service.search_policies(session, query, top_k=3)
                for r in results:
                    # Avoid duplicates
                    if r["title"] not in [p["title"] for p in retrieved_policies]:
                        retrieved_policies.append(r)
                        trace_step["policy_refs"].append(r["title"])

        # 2. Look up Purchase Order
        po_ref = parsed.get("po_reference") or ""
        if po_ref and po_ref in MOCK_PURCHASE_ORDERS:
            retrieved_po = MOCK_PURCHASE_ORDERS[po_ref]
            logger.info(f"[Retrieval] Found PO: {po_ref}")
        elif po_ref:
            # Try partial match
            for po_key, po_data in MOCK_PURCHASE_ORDERS.items():
                if po_ref in po_key or po_key in po_ref:
                    retrieved_po = po_data
                    break

        # 3. Look up Vendor
        vendor_id = parsed.get("vendor_id") or ""
        vendor_name = parsed.get("vendor_name") or ""
        
        if vendor_id and vendor_id in MOCK_VENDORS:
            vendor_info = MOCK_VENDORS[vendor_id]
        elif vendor_name:
            # Search by name
            for v_id, v_data in MOCK_VENDORS.items():
                if vendor_name.lower() in v_data["name"].lower() or v_data["name"].lower() in vendor_name.lower():
                    vendor_info = v_data
                    break

        trace_step["result_summary"] = (
            f"Retrieved {len(retrieved_policies)} policies. "
            f"PO: {'found (' + retrieved_po['po_number'] + ')' if retrieved_po else 'not found'}. "
            f"Vendor: {'found (' + vendor_info['name'] + ', status: ' + vendor_info['status'] + ')' if vendor_info else 'not found'}."
        )
        trace_step["confidence"] = 0.9 if retrieved_po and vendor_info else 0.7

    except Exception as e:
        logger.error(f"[Retrieval] Error: {e}")
        trace_step["status"] = "failed"
        trace_step["result_summary"] = f"Retrieval failed: {str(e)}"
        return {
            "retrieved_policies": retrieved_policies,
            "retrieved_po": retrieved_po,
            "vendor_info": vendor_info,
            "decision_trace": [trace_step],
            "errors": [f"Retrieval error: {str(e)}"],
        }

    return {
        "retrieved_policies": retrieved_policies,
        "retrieved_po": retrieved_po,
        "vendor_info": vendor_info,
        "decision_trace": [trace_step],
    }
