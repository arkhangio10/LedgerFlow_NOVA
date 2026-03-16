"""
LedgerFlow AI — Case API Routes
Full CRUD + workflow trigger, trace, approval, and result endpoints.
"""
import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_session
from models.case import Case
from models.evidence import Evidence
from models.decision_step import DecisionStep
from models.approval import Approval
from models.ui_execution import UIExecution
from schemas import (
    CaseCreate, CaseResponse, CaseListResponse,
    EvidenceResponse,
    TraceResponse, DecisionStepResponse,
    ApprovalRequest, ApprovalResponse,
    UIExecutionResponse,
    CaseResultResponse,
    WorkflowRunResponse,
)
from services.storage import storage_service

logger = logging.getLogger(__name__)
router = APIRouter()


# ─── Create Case ────────────────────────────────────────────────

@router.post("", response_model=CaseResponse, status_code=201)
async def create_case(payload: CaseCreate, session: AsyncSession = Depends(get_session)):
    """Create a new exception case."""
    case = Case(
        case_type=payload.case_type,
        title=payload.title,
        description=payload.description,
        submitted_by=payload.submitted_by,
        priority=payload.priority,
    )
    session.add(case)
    await session.flush()
    return case


# ─── List Cases ─────────────────────────────────────────────────

@router.get("", response_model=CaseListResponse)
async def list_cases(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
):
    """List all cases with optional status filter."""
    query = select(Case).order_by(Case.created_at.desc())
    if status:
        query = query.where(Case.status == status)
    query = query.offset(offset).limit(limit)

    result = await session.execute(query)
    cases = result.scalars().all()

    count_query = select(func.count(Case.id))
    if status:
        count_query = count_query.where(Case.status == status)
    total = (await session.execute(count_query)).scalar()

    return CaseListResponse(cases=cases, total=total)


# ─── Get Case Detail ────────────────────────────────────────────

@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(case_id: str, session: AsyncSession = Depends(get_session)):
    """Get case details by ID."""
    result = await session.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


# ─── Upload Evidence ────────────────────────────────────────────

@router.post("/{case_id}/evidence", response_model=EvidenceResponse, status_code=201)
async def upload_evidence(
    case_id: str,
    file: UploadFile = File(...),
    evidence_type: str = Form(default="pdf"),
    session: AsyncSession = Depends(get_session),
):
    """Upload evidence file for a case."""
    # Verify case exists
    result = await session.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Read and store file
    file_bytes = await file.read()
    file_path = await storage_service.upload_file(
        file_bytes, file.filename, folder=f"cases/{case_id}"
    )

    evidence = Evidence(
        case_id=case_id,
        evidence_type=evidence_type,
        filename=file.filename,
        file_path=file_path,
        content_type=file.content_type,
    )
    session.add(evidence)
    await session.flush()
    return evidence


# ─── Run Workflow ───────────────────────────────────────────────

@router.post("/{case_id}/run", response_model=WorkflowRunResponse)
async def run_workflow(
    case_id: str,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    """Trigger the LangGraph agent workflow for a case."""
    result = await session.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if case.status not in ("created", "error"):
        raise HTTPException(
            status_code=400,
            detail=f"Case is already in status '{case.status}', cannot re-run",
        )

    # Update status
    case.status = "processing"
    await session.flush()

    # Run workflow in background
    background_tasks.add_task(_run_agent_workflow, case_id)

    return WorkflowRunResponse(
        case_id=case_id,
        status="processing",
        message="Workflow started. Monitor via GET /cases/{id}/trace",
    )


async def _run_agent_workflow(case_id: str):
    """Background task that orchestrates the LangGraph workflow."""
    from agents.graph import run_case_workflow
    try:
        await run_case_workflow(case_id)
    except Exception as e:
        logger.error(f"Workflow failed for case {case_id}: {e}")
        # Update case status to error
        from database import async_session as session_factory
        async with session_factory() as session:
            result = await session.execute(select(Case).where(Case.id == case_id))
            case = result.scalar_one_or_none()
            if case:
                case.status = "error"
                case.final_outcome = f"Workflow error: {str(e)}"
                await session.commit()


# ─── Get Trace ──────────────────────────────────────────────────

@router.get("/{case_id}/trace", response_model=TraceResponse)
async def get_trace(case_id: str, session: AsyncSession = Depends(get_session)):
    """Get the decision trace for a case."""
    result = await session.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    steps_result = await session.execute(
        select(DecisionStep)
        .where(DecisionStep.case_id == case_id)
        .order_by(DecisionStep.step_number)
    )
    steps = steps_result.scalars().all()

    return TraceResponse(
        case_id=case_id,
        case_status=case.status,
        steps=steps,
        total_steps=len(steps),
    )


# ─── Approve ────────────────────────────────────────────────────

@router.post("/{case_id}/approve", response_model=ApprovalResponse)
async def approve_case(
    case_id: str,
    payload: ApprovalRequest,
    session: AsyncSession = Depends(get_session),
):
    """Approve or reject a case awaiting human decision."""
    result = await session.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if case.status != "awaiting_approval":
        raise HTTPException(
            status_code=400,
            detail=f"Case is in status '{case.status}', not awaiting approval",
        )

    # Find pending approval
    approvals_result = await session.execute(
        select(Approval)
        .where(Approval.case_id == case_id, Approval.status == "pending")
    )
    approval = approvals_result.scalar_one_or_none()

    if not approval:
        # Create one
        approval = Approval(case_id=case_id, requested_to=payload.approved_by)
        session.add(approval)

    approval.status = payload.decision
    approval.decision_note = payload.decision_note
    approval.approved_at = datetime.now(timezone.utc)

    # Update case status based on decision
    if payload.decision == "approved":
        case.status = "processing"
        # Resume workflow
        from agents.graph import resume_after_approval
        import asyncio
        asyncio.create_task(resume_after_approval(case_id, "approved"))
    else:
        case.status = "rejected"
        case.final_outcome = f"Rejected by {payload.approved_by}: {payload.decision_note or 'No reason given'}"

    await session.flush()
    return approval


# ─── Get Result ─────────────────────────────────────────────────

@router.get("/{case_id}/result", response_model=CaseResultResponse)
async def get_result(case_id: str, session: AsyncSession = Depends(get_session)):
    """Get the full case result with all related data."""
    result = await session.execute(
        select(Case)
        .where(Case.id == case_id)
        .options(
            selectinload(Case.evidences),
            selectinload(Case.decision_steps),
            selectinload(Case.approvals),
            selectinload(Case.ui_executions),
        )
    )
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    return CaseResultResponse(
        case=case,
        evidences=case.evidences,
        trace=sorted(case.decision_steps, key=lambda s: s.step_number),
        approvals=case.approvals,
        ui_executions=case.ui_executions,
    )
