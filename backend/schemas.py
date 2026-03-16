"""
LedgerFlow AI — Pydantic Schemas for API request/response validation.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ─── Case Schemas ───────────────────────────────────────────────

class CaseCreate(BaseModel):
    case_type: str = Field(default="invoice_exception", description="Type of case")
    title: Optional[str] = Field(None, description="Case title")
    description: Optional[str] = Field(None, description="Case description")
    submitted_by: str = Field(default="analyst", description="Who submitted")
    priority: str = Field(default="medium", description="Priority level")


class CaseResponse(BaseModel):
    id: str
    case_type: str
    status: str
    title: Optional[str]
    description: Optional[str]
    submitted_by: str
    priority: str
    risk_level: str
    final_outcome: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CaseListResponse(BaseModel):
    cases: list[CaseResponse]
    total: int


# ─── Evidence Schemas ───────────────────────────────────────────

class EvidenceResponse(BaseModel):
    id: str
    case_id: str
    evidence_type: str
    filename: str
    file_path: str
    content_type: Optional[str]
    parsed_metadata: Optional[dict]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Decision Step / Trace Schemas ──────────────────────────────

class DecisionStepResponse(BaseModel):
    id: str
    case_id: str
    step_number: int
    agent_name: str
    step_type: str
    objective: Optional[str]
    input_summary: Optional[str]
    tool_called: Optional[str]
    policy_refs: Optional[list]
    evidence_refs: Optional[list]
    result_summary: Optional[str]
    confidence: Optional[float]
    requires_approval: bool
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TraceResponse(BaseModel):
    case_id: str
    case_status: str
    steps: list[DecisionStepResponse]
    total_steps: int


# ─── Approval Schemas ──────────────────────────────────────────

class ApprovalRequest(BaseModel):
    decision: str = Field(..., description="approved or rejected")
    decision_note: Optional[str] = Field(None, description="Justification note")
    approved_by: str = Field(default="supervisor", description="Who approved")


class ApprovalResponse(BaseModel):
    id: str
    case_id: str
    requested_to: str
    status: str
    decision_note: Optional[str]
    approved_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── UI Execution Schemas ──────────────────────────────────────

class UIExecutionResponse(BaseModel):
    id: str
    case_id: str
    target_system: str
    action_summary: Optional[str]
    screenshot_before: Optional[str]
    screenshot_after: Optional[str]
    outcome: str
    error_detail: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Case Result (Aggregated) ─────────────────────────────────

class CaseResultResponse(BaseModel):
    case: CaseResponse
    evidences: list[EvidenceResponse]
    trace: list[DecisionStepResponse]
    approvals: list[ApprovalResponse]
    ui_executions: list[UIExecutionResponse]


# ─── Workflow Trigger ──────────────────────────────────────────

class WorkflowRunResponse(BaseModel):
    case_id: str
    status: str
    message: str
