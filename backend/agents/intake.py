"""
LedgerFlow AI — Intake Agent
Classifies documents and extracts key financial fields using Nova 2 Lite.
"""
import json
import logging
from agents.state import CaseState
from services.bedrock_client import bedrock_client
from services.storage import storage_service

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """You are a financial document analyst for LedgerFlow AI.
Analyze the uploaded document and extract the following fields as JSON:

{
  "document_type": "invoice | purchase_order | receipt | credit_note | other",
  "invoice_number": "string or null",
  "vendor_name": "string or null",
  "vendor_id": "string or null",
  "vendor_tax_id": "string or null",
  "amount_subtotal": number or null,
  "tax_rate": number or null,
  "tax_amount": number or null,  
  "amount_total": number or null,
  "currency": "string or null",
  "po_reference": "string or null",
  "date": "YYYY-MM-DD or null",
  "due_date": "YYYY-MM-DD or null",
  "cost_center": "string or null",
  "line_items": [
    {
      "description": "string",
      "quantity": number,
      "unit_price": number,
      "total": number
    }
  ],
  "notes": "any additional relevant information"
}

Be precise. If a field is not present in the document, set it as null.
Return ONLY the JSON object, no markdown formatting or extra text."""


async def intake_agent(state: CaseState) -> dict:
    """
    Intake Agent — classifies and extracts fields from uploaded evidence.
    
    Processes each piece of evidence through Nova 2 Lite's vision/document
    capabilities to extract structured financial data.
    """
    logger.info(f"[Intake] Processing case {state['case_id']} with {len(state['raw_evidence'])} evidence items")

    parsed_fields = {}
    trace_step = {
        "step_number": 1,
        "agent_name": "Intake Agent",
        "step_type": "parse",
        "objective": "Classify documents and extract key financial fields",
        "tool_called": "nova_2_lite_vision",
        "policy_refs": [],
        "evidence_refs": [],
        "result_summary": "",
        "confidence": 0.0,
        "status": "completed",
    }

    try:
        for evidence in state["raw_evidence"]:
            trace_step["evidence_refs"].append(evidence.get("filename", "unknown"))
            
            # Read the file
            try:
                file_bytes = await storage_service.read_file(evidence["file_path"])
            except Exception as e:
                logger.warning(f"[Intake] Could not read file {evidence['file_path']}: {e}")
                continue

            # Call Nova 2 Lite based on evidence type
            evidence_type = evidence.get("evidence_type", "pdf")
            
            if evidence_type == "pdf":
                response = await bedrock_client.invoke_nova_lite_with_document(
                    prompt=EXTRACTION_PROMPT,
                    doc_bytes=file_bytes,
                    doc_format="pdf",
                    doc_name=evidence.get("filename", "document"),
                )
            elif evidence_type in ("image", "screenshot"):
                fmt = "png" if evidence.get("filename", "").endswith(".png") else "jpeg"
                response = await bedrock_client.invoke_nova_lite_with_image(
                    prompt=EXTRACTION_PROMPT,
                    image_bytes=file_bytes,
                    image_format=fmt,
                )
            else:
                # Text-based evidence
                text_content = file_bytes.decode("utf-8", errors="replace")
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"text": f"{EXTRACTION_PROMPT}\n\nDocument content:\n{text_content[:8000]}"}
                        ],
                    }
                ]
                response = await bedrock_client.invoke_nova_lite(messages)

            # Parse the response
            content = response.get("content", "")
            try:
                # Clean potential markdown formatting
                # Find the first { and last } to isolate the JSON block
                start_idx = content.find('{')
                end_idx = content.rfind('}')
                if start_idx != -1 and end_idx != -1:
                    cleaned = content[start_idx:end_idx+1]
                else:
                    cleaned = content.strip()
                    
                extracted = json.loads(cleaned)
                
                # Merge into parsed_fields (later documents override earlier ones)
                parsed_fields.update(extracted)
            except json.JSONDecodeError:
                logger.warning(f"[Intake] Could not parse JSON from Nova response for {evidence['filename']}")
                parsed_fields["raw_extraction"] = content

        trace_step["result_summary"] = (
            f"Extracted fields from {len(state['raw_evidence'])} documents. "
            f"Document type: {parsed_fields.get('document_type', 'unknown')}. "
            f"Invoice: {parsed_fields.get('invoice_number', 'N/A')}, "
            f"Vendor: {parsed_fields.get('vendor_name', 'N/A')}, "
            f"Amount: {parsed_fields.get('amount_total', 'N/A')}"
        )
        trace_step["confidence"] = 0.85 if parsed_fields.get("invoice_number") else 0.5

    except Exception as e:
        logger.error(f"[Intake] Error: {e}")
        trace_step["status"] = "failed"
        trace_step["result_summary"] = f"Intake failed: {str(e)}"
        return {
            "parsed_fields": parsed_fields,
            "decision_trace": [trace_step],
            "errors": [f"Intake error: {str(e)}"],
        }

    return {
        "parsed_fields": parsed_fields,
        "decision_trace": [trace_step],
    }
