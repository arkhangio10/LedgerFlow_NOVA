"""
LedgerFlow AI — LangGraph Workflow Graph
Orchestrates the full agent pipeline with conditional edges and human-in-the-loop.

Flow:
  ingest → retrieve → resolve → [human_gate?] → execute_ui → audit → persist
"""
import json
import logging
import os

import aiofiles
from langgraph.graph import StateGraph, END
from agents.state import CaseState
from agents.intake import intake_agent
from agents.retrieval import retrieval_agent
from agents.resolution import resolution_agent
from agents.ui_executor import ui_executor_agent
from agents.audit import audit_agent
from sqlalchemy import select
from config import settings

logger = logging.getLogger(__name__)


def should_require_approval(state: CaseState) -> str:
    """Conditional edge: check if human approval is needed."""
    if state.get("requires_human_approval", False):
        return "human_gate"
    return "execute_ui"


async def human_gate_node(state: CaseState) -> dict:
    """
    Human Gate — pauses the workflow and waits for approval.
    Updates the case status to 'awaiting_approval' in the database.
    """
    logger.info(f"[Human Gate] Case {state['case_id']} requires human approval")
    await _save_workflow_snapshot(state["case_id"], state)

    trace_step = {
        "step_number": 4,
        "agent_name": "Human Gate",
        "step_type": "human_gate",
        "objective": "Escalate to human for review and approval",
        "tool_called": "human_approval_request",
        "policy_refs": [],
        "evidence_refs": [],
        "result_summary": (
            f"Case escalated for human review. "
            f"Risk level: {state.get('resolution_plan', {}).get('risk_level', 'unknown')}. "
            f"Confidence: {state.get('resolution_plan', {}).get('confidence', 0):.1%}. "
            f"Reason: {state.get('resolution_plan', {}).get('justification', 'N/A')[:200]}"
        ),
        "confidence": 1.0,
        "requires_approval": True,
        "status": "pending",
    }

    # Update case status in database
    from database import async_session
    from models.case import Case
    from models.approval import Approval
    from models.decision_step import DecisionStep

    async with async_session() as session:
        result = await session.execute(select(Case).where(Case.id == state["case_id"]))
        case = result.scalar_one_or_none()
        if case:
            case.status = "awaiting_approval"

            # Create approval record
            approval = Approval(
                case_id=state["case_id"],
                requested_to="supervisor",
                status="pending",
            )
            session.add(approval)

            # Save decision steps up to this point
            for step_data in state.get("decision_trace", []):
                step = DecisionStep(
                    case_id=state["case_id"],
                    step_number=step_data.get("step_number", 0),
                    agent_name=step_data.get("agent_name", ""),
                    step_type=step_data.get("step_type", ""),
                    objective=step_data.get("objective"),
                    input_summary=step_data.get("input_summary"),
                    tool_called=step_data.get("tool_called"),
                    policy_refs=step_data.get("policy_refs"),
                    evidence_refs=step_data.get("evidence_refs"),
                    result_summary=step_data.get("result_summary"),
                    confidence=step_data.get("confidence"),
                    requires_approval=step_data.get("requires_approval", False),
                    status=step_data.get("status", "completed"),
                )
                session.add(step)

            # Also save the gate step
            gate_step = DecisionStep(
                case_id=state["case_id"],
                step_number=4,
                agent_name="Human Gate",
                step_type="human_gate",
                objective=trace_step["objective"],
                tool_called=trace_step["tool_called"],
                result_summary=trace_step["result_summary"],
                confidence=1.0,
                requires_approval=True,
                status="pending",
            )
            session.add(gate_step)

            await session.commit()

    return {
        "status": "awaiting_approval",
        "decision_trace": [trace_step],
    }


def should_continue_after_approval(state: CaseState) -> str:
    """After human gate: if approved, continue to UI execution; if rejected, go to audit."""
    decision = state.get("human_decision")
    if decision == "approved":
        return "execute_ui"
    return "audit"


# ─── Build the Graph ────────────────────────────────────────────

def build_workflow() -> StateGraph:
    """Build the LangGraph workflow for case processing."""
    
    workflow = StateGraph(CaseState)

    # Add nodes
    workflow.add_node("ingest", intake_agent)
    workflow.add_node("retrieve", retrieval_agent)
    workflow.add_node("resolve", resolution_agent)
    workflow.add_node("human_gate", human_gate_node)
    workflow.add_node("execute_ui", ui_executor_agent)
    workflow.add_node("audit", audit_agent)

    # Add edges
    workflow.set_entry_point("ingest")
    workflow.add_edge("ingest", "retrieve")
    workflow.add_edge("retrieve", "resolve")

    # Conditional: does it need human approval?
    workflow.add_conditional_edges(
        "resolve",
        should_require_approval,
        {
            "human_gate": "human_gate",
            "execute_ui": "execute_ui",
        },
    )

    # Human gate ends the graph (workflow resumes via resume_after_approval)
    workflow.add_edge("human_gate", END)

    # After UI execution, go to audit
    workflow.add_edge("execute_ui", "audit")

    # Audit is the final node
    workflow.add_edge("audit", END)

    return workflow


# Compile the graph
app_graph = build_workflow().compile()


# ─── Workflow Runner ────────────────────────────────────────────

async def run_case_workflow(case_id: str) -> dict:
    """
    Run the full agent workflow for a case.
    Loads evidence from DB, invokes the graph, and persists results.
    """
    from database import async_session
    from models.case import Case
    from models.evidence import Evidence
    from models.decision_step import DecisionStep
    from models.ui_execution import UIExecution

    # Load case and evidence from DB
    async with async_session() as session:
        result = await session.execute(select(Case).where(Case.id == case_id))
        case = result.scalar_one_or_none()
        if not case:
            raise ValueError(f"Case {case_id} not found")

        ev_result = await session.execute(
            select(Evidence).where(Evidence.case_id == case_id)
        )
        evidences = ev_result.scalars().all()

    # Build initial state
    initial_state: CaseState = {
        "case_id": case_id,
        "case_type": case.case_type,
        "status": "processing",
        "raw_evidence": [
            {
                "id": e.id,
                "type": e.evidence_type,
                "filename": e.filename,
                "file_path": e.file_path,
                "content_type": e.content_type,
                "evidence_type": e.evidence_type,
            }
            for e in evidences
        ],
        "parsed_fields": {},
        "retrieved_policies": [],
        "retrieved_po": None,
        "vendor_info": None,
        "discrepancies": [],
        "resolution_plan": {},
        "requires_human_approval": False,
        "human_decision": None,
        "ui_execution_result": None,
        "decision_trace": [],
        "final_outcome": None,
        "errors": [],
    }

    logger.info(f"[Workflow] Starting case {case_id} with {len(evidences)} evidence items")

    # Run the graph
    final_state = await app_graph.ainvoke(initial_state)

    # Persist results (if not paused at human gate)
    if final_state.get("status") != "awaiting_approval":
        await _persist_results(case_id, final_state)

    return final_state


async def resume_after_approval(case_id: str, decision: str):
    """
    Resume the workflow after human approval/rejection.
    Creates a mini-graph that runs execute_ui → audit.
    """
    from database import async_session
    from models.case import Case
    from models.evidence import Evidence
    from models.decision_step import DecisionStep

    # Load existing state from DB
    async with async_session() as session:
        result = await session.execute(select(Case).where(Case.id == case_id))
        case = result.scalar_one_or_none()
        if not case:
            return
    snapshot = await _load_workflow_snapshot(case_id)

    # Build a continuation graph
    resume_graph = StateGraph(CaseState)
    
    if decision == "approved":
        resume_graph.add_node("execute_ui", ui_executor_agent)
        resume_graph.add_node("audit", audit_agent)
        resume_graph.set_entry_point("execute_ui")
        resume_graph.add_edge("execute_ui", "audit")
        resume_graph.add_edge("audit", END)
    else:
        resume_graph.add_node("audit", audit_agent)
        resume_graph.set_entry_point("audit")
        resume_graph.add_edge("audit", END)

    compiled = resume_graph.compile()

    # Reconstruct state from the saved snapshot so UI execution has the
    # same parsed invoice, resolution plan, and evidence context.
    resume_state: CaseState = {
        "case_id": case_id,
        "case_type": case.case_type,
        "status": "processing",
        "raw_evidence": snapshot.get("raw_evidence", []),
        "parsed_fields": snapshot.get("parsed_fields", {}),
        "retrieved_policies": snapshot.get("retrieved_policies", []),
        "retrieved_po": snapshot.get("retrieved_po"),
        "vendor_info": snapshot.get("vendor_info"),
        "discrepancies": snapshot.get("discrepancies", []),
        "resolution_plan": snapshot.get("resolution_plan", {}),
        "requires_human_approval": False,
        "human_decision": decision,
        "ui_execution_result": None,
        "decision_trace": [],
        "final_outcome": None,
        "errors": [],
    }

    final_state = await compiled.ainvoke(resume_state)
    await _persist_results(case_id, final_state)


def _workflow_snapshot_path(case_id: str) -> str:
    return os.path.join(settings.local_storage_path, "cases", case_id, "workflow_state.json")


async def _save_workflow_snapshot(case_id: str, state: CaseState):
    os.makedirs(os.path.dirname(_workflow_snapshot_path(case_id)), exist_ok=True)
    async with aiofiles.open(_workflow_snapshot_path(case_id), "w", encoding="utf-8") as handle:
        await handle.write(json.dumps(dict(state), default=str))


async def _load_workflow_snapshot(case_id: str) -> dict:
    path = _workflow_snapshot_path(case_id)
    if not os.path.exists(path):
        return {}
    async with aiofiles.open(path, "r", encoding="utf-8") as handle:
        return json.loads(await handle.read())


async def _persist_results(case_id: str, state: CaseState):
    """Persist final workflow results to the database."""
    from database import async_session
    from models.case import Case
    from models.decision_step import DecisionStep
    from models.ui_execution import UIExecution

    async with async_session() as session:
        # Update case
        result = await session.execute(select(Case).where(Case.id == case_id))
        case = result.scalar_one_or_none()
        if case:
            case.status = state.get("status", "error")

            outcome = state.get("final_outcome")
            if outcome:
                case.final_outcome = outcome.get("summary", "")
                case.risk_level = state.get("resolution_plan", {}).get("risk_level", case.risk_level)

            # Save decision trace
            for step_data in state.get("decision_trace", []):
                step = DecisionStep(
                    case_id=case_id,
                    step_number=step_data.get("step_number", 0),
                    agent_name=step_data.get("agent_name", ""),
                    step_type=step_data.get("step_type", ""),
                    objective=step_data.get("objective"),
                    input_summary=step_data.get("input_summary"),
                    tool_called=step_data.get("tool_called"),
                    policy_refs=step_data.get("policy_refs"),
                    evidence_refs=step_data.get("evidence_refs"),
                    result_summary=step_data.get("result_summary"),
                    confidence=step_data.get("confidence"),
                    requires_approval=step_data.get("requires_approval", False),
                    status=step_data.get("status", "completed"),
                )
                session.add(step)

            # Save UI execution if present
            ui_result = state.get("ui_execution_result")
            if ui_result and ui_result.get("outcome") != "skipped":
                ui_exec = UIExecution(
                    case_id=case_id,
                    target_system="mock_erp",
                    action_summary=ui_result.get("action_summary"),
                    screenshot_before=ui_result.get("screenshot_before"),
                    screenshot_after=ui_result.get("screenshot_after"),
                    outcome=ui_result.get("outcome", "unknown"),
                    error_detail=ui_result.get("error"),
                )
                session.add(ui_exec)

            await session.commit()

    logger.info(f"[Workflow] Persisted results for case {case_id}: status={state.get('status')}")
