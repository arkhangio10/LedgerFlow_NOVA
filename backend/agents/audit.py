"""
LedgerFlow AI — Audit & Trace Agent
Compiles final decision trace, logs results, and closes the case.
"""
import json
import logging
from datetime import datetime, timezone
from agents.state import CaseState

logger = logging.getLogger(__name__)


async def audit_agent(state: CaseState) -> dict:
    """
    Audit & Trace Agent — compiles the final structured trace,
    summarizes the case outcome, and prepares audit records.
    """
    logger.info(f"[Audit] Generating trace for case {state['case_id']}")

    existing_trace = state.get("decision_trace", [])
    discrepancies = state.get("discrepancies", [])
    plan = state.get("resolution_plan", {})
    ui_result = state.get("ui_execution_result", {})
    human_decision = state.get("human_decision")

    # Determine final resolution type
    if human_decision == "rejected":
        resolution_type = "rejected_by_human"
        final_status = "rejected"
    elif ui_result.get("outcome") == "success":
        resolution_type = plan.get("action", "auto_resolved")
        final_status = "resolved"
    elif ui_result.get("outcome") == "skipped" and plan.get("action") == "approve_as_is":
        resolution_type = "approved_within_tolerance"
        final_status = "resolved"
    elif ui_result.get("outcome") == "failure":
        resolution_type = "ui_execution_failed"
        final_status = "error"
    else:
        resolution_type = "unknown"
        final_status = "error"

    # Build audit summary
    trace_step = {
        "step_number": len(existing_trace) + 1,
        "agent_name": "Audit & Trace Agent",
        "step_type": "emit_trace",
        "objective": "Generate audit trail and close case",
        "tool_called": "audit_log",
        "policy_refs": [p for step in existing_trace for p in step.get("policy_refs", [])],
        "evidence_refs": [e for step in existing_trace for e in step.get("evidence_refs", [])],
        "result_summary": "",
        "confidence": 1.0,
        "status": "completed",
    }

    # Calculate aggregate confidence
    confidences = [s.get("confidence", 0) for s in existing_trace if s.get("confidence")]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

    final_outcome = {
        "status": final_status,
        "resolution_type": resolution_type,
        "summary": _build_summary(state, final_status, resolution_type),
        "discrepancies_found": len(discrepancies),
        "policies_consulted": len(set(trace_step["policy_refs"])),
        "evidence_processed": len(set(trace_step["evidence_refs"])),
        "total_steps": len(existing_trace) + 1,
        "average_confidence": round(avg_confidence, 3),
        "human_intervention": human_decision is not None,
        "ui_automation": ui_result.get("outcome", "none") != "skipped",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    trace_step["result_summary"] = (
        f"Case {final_status}. Resolution: {resolution_type}. "
        f"{len(discrepancies)} discrepancies processed across {len(existing_trace)} steps. "
        f"Average confidence: {avg_confidence:.1%}."
    )

    return {
        "status": final_status,
        "final_outcome": final_outcome,
        "decision_trace": [trace_step],
    }


def _build_summary(state: CaseState, final_status: str, resolution_type: str) -> str:
    """Build a human-readable summary of the case resolution."""
    parsed = state.get("parsed_fields", {})
    discrepancies = state.get("discrepancies", [])
    plan = state.get("resolution_plan", {})
    ui_result = state.get("ui_execution_result", {})

    lines = [
        f"Case {state['case_id']} — {final_status.upper()}",
        f"Invoice: {parsed.get('invoice_number', 'N/A')} | Vendor: {parsed.get('vendor_name', 'N/A')} | Amount: {parsed.get('amount_total', 'N/A')}",
        "",
    ]

    if discrepancies:
        lines.append(f"Discrepancies ({len(discrepancies)}):")
        for d in discrepancies[:5]:
            lines.append(f"  • {d.get('field', '?')}: expected {d.get('expected', '?')}, "
                        f"actual {d.get('actual', '?')} (severity: {d.get('severity', '?')})")
        lines.append("")

    lines.append(f"Resolution: {resolution_type}")
    if plan.get("justification"):
        lines.append(f"Justification: {plan['justification'][:300]}")

    if ui_result.get("action_summary"):
        lines.append(f"ERP Action: {ui_result['action_summary'][:200]}")

    if state.get("human_decision"):
        lines.append(f"Human Decision: {state['human_decision']}")

    return "\n".join(lines)
