"""
LedgerFlow AI — LangGraph State Schema
Typed state shared across all agents in the workflow.
"""
from typing import Optional, Annotated
from typing_extensions import TypedDict
import operator


def merge_lists(a: list, b: list) -> list:
    """Reducer that appends new items to existing list."""
    return a + b


class CaseState(TypedDict):
    """Shared workflow state for a financial exception case."""

    # ─── Case Identity ──────────────────────────────────────
    case_id: str
    case_type: str  # invoice_exception, vendor_registration, etc.
    status: str  # created, processing, awaiting_approval, resolved, rejected, error

    # ─── Raw Evidence ───────────────────────────────────────
    raw_evidence: list[dict]
    # Each item: {id, type, filename, file_path, content_type}

    # ─── Parsed Fields (from Intake Agent) ──────────────────
    parsed_fields: dict
    # Invoice fields: invoice_number, vendor_name, vendor_id, amount,
    #   tax_amount, tax_rate, po_reference, date, cost_center, line_items

    # ─── Retrieved Context (from Retrieval Agent) ───────────
    retrieved_policies: Annotated[list[dict], merge_lists]
    # Each: {title, category, content, similarity}

    retrieved_po: Optional[dict]
    # PO data: {po_number, vendor, total, line_items, status}

    vendor_info: Optional[dict]
    # Vendor: {id, name, tax_id, status, payment_terms}

    # ─── Discrepancies (from Resolution Agent) ──────────────
    discrepancies: list[dict]
    # Each: {field, expected, actual, difference, severity, policy_ref}

    resolution_plan: dict
    # {action, corrections, justification, confidence, risk_level, tools_needed}

    requires_human_approval: bool
    human_decision: Optional[str]  # approved | rejected

    # ─── UI Execution (from UI Executor Agent) ──────────────
    ui_execution_result: Optional[dict]
    # {outcome, action_summary, screenshot_before, screenshot_after, error}

    # ─── Decision Trace ──────────────────────────────────────
    decision_trace: Annotated[list[dict], merge_lists]
    # Each step: {step_number, agent_name, step_type, objective,
    #   tool_called, policy_refs, evidence_refs, result_summary, confidence, status}

    # ─── Final Outcome ──────────────────────────────────────
    final_outcome: Optional[dict]
    # {status, summary, resolution_type, total_steps, processing_time}

    # ─── Error Tracking ─────────────────────────────────────
    errors: Annotated[list[str], merge_lists]
