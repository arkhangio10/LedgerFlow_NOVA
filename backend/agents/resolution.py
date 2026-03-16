"""
LedgerFlow AI — Exception Resolution Agent
Uses Nova 2 Lite to reason about discrepancies and decide actions.
"""
import json
import logging
from agents.state import CaseState
from services.bedrock_client import bedrock_client

logger = logging.getLogger(__name__)

RESOLUTION_SYSTEM_PROMPT = """You are the Exception Resolution Agent for LedgerFlow AI, 
a financial operations automation system. Your job is to:

1. Compare invoice data against the purchase order
2. Identify discrepancies (amount, quantity, vendor, tax, dates, etc.)
3. Evaluate each discrepancy against the retrieved policies
4. Determine the appropriate action

You must respond with a JSON object containing:
{
  "discrepancies": [
    {
      "field": "string (e.g., 'amount_total', 'tax_amount', 'vendor_status')",
      "expected": "value from PO or policy",
      "actual": "value from invoice",
      "difference": "numeric or descriptive difference",
      "difference_percent": number or null,
      "severity": "low | medium | high | critical",
      "policy_ref": "which policy applies (e.g., AP-01)"
    }
  ],
  "resolution_plan": {
    "action": "auto_correct | escalate_human | block | approve_as_is",
    "corrections": [
      {
        "field": "field to correct",
        "current_value": "current wrong value",
        "corrected_value": "what it should be",
        "reason": "why this correction"
      }
    ],
    "justification": "detailed explanation of the decision",
    "confidence": 0.0 to 1.0,
    "risk_level": "low | medium | high",
    "tools_needed": ["list of tools needed, e.g., 'update_invoice_erp', 'notify_vendor'"]
  },
  "requires_human_approval": true/false
}

IMPORTANT RULES:
- If total discrepancy exceeds 5% or any policy violation is critical, set requires_human_approval to true
- If vendor status is suspended or blocked, always escalate
- If amount is within tolerance (AP-01: ±2% or ±$50), approve_as_is
- Be conservative: when in doubt, escalate to human

Return ONLY the JSON object."""


async def resolution_agent(state: CaseState) -> dict:
    """
    Exception Resolution Agent — compares invoice vs. PO, evaluates against
    policies, and produces a resolution plan using Nova 2 Lite.
    """
    parsed = state.get("parsed_fields", {})
    po = state.get("retrieved_po")
    vendor = state.get("vendor_info")
    policies = state.get("retrieved_policies", [])
    
    logger.info(f"[Resolution] Reasoning about case {state['case_id']}")

    trace_step = {
        "step_number": 3,
        "agent_name": "Exception Resolution Agent",
        "step_type": "reason",
        "objective": "Analyze discrepancies and determine resolution action",
        "tool_called": "nova_2_lite_reasoning",
        "policy_refs": [p.get("title", "") for p in policies[:5]],
        "evidence_refs": [],
        "result_summary": "",
        "confidence": 0.0,
        "status": "completed",
    }

    try:
        # Build context message for Nova 2 Lite
        context = f"""
CASE DATA:
- Case ID: {state['case_id']}
- Case Type: {state.get('case_type', 'invoice_exception')}

INVOICE DATA (extracted from documents):
{json.dumps(parsed, indent=2, default=str)}

PURCHASE ORDER:
{json.dumps(po, indent=2, default=str) if po else "Not found"}

VENDOR INFORMATION:
{json.dumps(vendor, indent=2, default=str) if vendor else "Not found"}

APPLICABLE POLICIES:
"""
        for p in policies[:5]:
            context += f"\n--- {p['title']} (similarity: {p.get('similarity', 'N/A')}) ---\n{p['content']}\n"

        messages = [
            {
                "role": "user",
                "content": [{"text": context}],
            }
        ]

        response = await bedrock_client.invoke_nova_lite(
            messages=messages,
            system_prompt=RESOLUTION_SYSTEM_PROMPT,
            max_tokens=4096,
            temperature=0.2,
        )

        content = response.get("content", "")
        
        # Parse the structured response
        try:
            start_idx = content.find('{')
            end_idx = content.rfind('}')
            if start_idx != -1 and end_idx != -1:
                cleaned = content[start_idx:end_idx+1]
            else:
                cleaned = content.strip()
            result = json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning("[Resolution] Could not parse structured response, using fallback")
            result = {
                "discrepancies": [],
                "resolution_plan": {
                    "action": "escalate_human",
                    "corrections": [],
                    "justification": f"Unable to parse structured analysis. Raw response: {content[:500]}",
                    "confidence": 0.3,
                    "risk_level": "high",
                    "tools_needed": [],
                },
                "requires_human_approval": True,
            }

        discrepancies = result.get("discrepancies", [])
        resolution_plan = result.get("resolution_plan", {})
        requires_approval = result.get("requires_human_approval", True)

        trace_step["confidence"] = resolution_plan.get("confidence", 0.5)
        trace_step["result_summary"] = (
            f"Found {len(discrepancies)} discrepancies. "
            f"Action: {resolution_plan.get('action', 'unknown')}. "
            f"Risk: {resolution_plan.get('risk_level', 'unknown')}. "
            f"Requires approval: {requires_approval}. "
            f"Justification: {resolution_plan.get('justification', '')[:200]}"
        )

    except Exception as e:
        logger.error(f"[Resolution] Error: {e}")
        trace_step["status"] = "failed"
        trace_step["result_summary"] = f"Resolution reasoning failed: {str(e)}"
        return {
            "discrepancies": [],
            "resolution_plan": {
                "action": "escalate_human",
                "justification": f"Error during analysis: {str(e)}",
                "confidence": 0.0,
                "risk_level": "high",
            },
            "requires_human_approval": True,
            "decision_trace": [trace_step],
            "errors": [f"Resolution error: {str(e)}"],
        }

    return {
        "discrepancies": discrepancies,
        "resolution_plan": resolution_plan,
        "requires_human_approval": requires_approval,
        "decision_trace": [trace_step],
    }
