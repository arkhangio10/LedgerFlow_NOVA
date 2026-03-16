"""
LedgerFlow AI — UI Execution Agent
Uses Nova Act for browser automation on mock ERP portal.
Falls back to direct Playwright automation for the local mock ERP when
Nova Act cannot start or authenticate.
"""
import asyncio
import importlib.metadata
import logging
import os
from typing import Any

from agents.state import CaseState
from config import settings
from services.storage import storage_service

logger = logging.getLogger(__name__)


async def ui_executor_agent(state: CaseState) -> dict:
    """
    UI Execution Agent — automates actions on the mock ERP portal using Nova Act.
    
    Navigates the legacy ERP interface, fills forms, corrects data, and captures
    before/after screenshots as evidence.
    """
    plan = state.get("resolution_plan", {})
    parsed = state.get("parsed_fields", {})
    
    logger.info(f"[UI Executor] Executing UI actions for case {state['case_id']}")

    trace_step = {
        "step_number": 5,
        "agent_name": "UI Execution Agent",
        "step_type": "execute_ui",
        "objective": f"Execute '{plan.get('action', 'unknown')}' on mock ERP portal",
        "tool_called": "nova_act",
        "policy_refs": [],
        "evidence_refs": [],
        "result_summary": "",
        "confidence": 0.0,
        "status": "completed",
    }

    ui_result = {
        "outcome": "pending",
        "action_summary": "",
        "screenshot_before": None,
        "screenshot_after": None,
        "error": None,
    }

    action = plan.get("action", "")
    corrections = plan.get("corrections", [])

    try:
        result, tool_used = await _execute_real_ui_action(
            case_id=state["case_id"],
            erp_url=settings.mock_erp_url,
            action=action,
            corrections=corrections,
            parsed_fields=parsed,
        )
        ui_result.update(result)
        trace_step["tool_called"] = tool_used
        trace_step["result_summary"] = (
            f"ERP action completed. Outcome: {result.get('outcome', 'unknown')}. "
            f"{result.get('action_summary', '')}"
        )
        trace_step["confidence"] = 0.9 if result.get("outcome") == "success" else 0.5

    except Exception as e:
        logger.error(f"[UI Executor] Nova Act encountered a fatal error ({e})")
        ui_result["outcome"] = "failure"
        ui_result["error"] = str(e)
        trace_step["tool_called"] = "ui_automation"
        trace_step["result_summary"] = f"[Failed] UI Action blocked due to error: {e}"
        trace_step["confidence"] = 0.0
        
    return {
        "ui_execution_result": ui_result,
        "decision_trace": [trace_step],
}


async def _execute_real_ui_action(
    case_id: str,
    erp_url: str,
    action: str,
    corrections: list[dict],
    parsed_fields: dict,
) -> tuple[dict[str, Any], str]:
    """
    Execute a real browser automation path.

    Preference order:
    1. Nova Act if it can start and authenticate
    2. Direct Playwright automation against the local mock ERP
    """
    last_error: Exception | None = None

    if settings.nova_act_api_key and _is_supported_nova_act_version():
        try:
            result = await asyncio.to_thread(
                _sync_execute_with_nova_act,
                erp_url=erp_url,
                action=action,
                corrections=corrections,
                parsed_fields=parsed_fields,
            )
            return await _persist_screenshots(case_id, result), "nova_act"
        except Exception as exc:
            last_error = exc
            logger.warning("[UI Executor] Nova Act failed, switching to direct Playwright: %s", exc)
    elif settings.nova_act_api_key:
        logger.warning(
            "[UI Executor] Installed nova-act SDK is older than 3.x; using direct Playwright for local UI automation"
        )

    try:
        result = await asyncio.to_thread(
            _sync_execute_with_playwright,
            erp_url=erp_url,
            action=action,
            corrections=corrections,
            parsed_fields=parsed_fields,
        )
        return await _persist_screenshots(case_id, result), "playwright"
    except Exception as exc:
        if last_error:
            raise RuntimeError(f"Nova Act failed ({last_error}); Playwright failed ({exc})") from exc
        raise


async def _persist_screenshots(case_id: str, result: dict[str, Any]) -> dict[str, Any]:
    """Store screenshot bytes and replace them with storage paths."""
    before_bytes = result.pop("screenshot_before_bytes", None)
    after_bytes = result.pop("screenshot_after_bytes", None)

    if before_bytes:
        result["screenshot_before"] = await storage_service.upload_file(
            before_bytes,
            f"{case_id}_before.png",
            folder=f"cases/{case_id}/ui",
        )
    else:
        result["screenshot_before"] = None

    if after_bytes:
        result["screenshot_after"] = await storage_service.upload_file(
            after_bytes,
            f"{case_id}_after.png",
            folder=f"cases/{case_id}/ui",
        )
    else:
        result["screenshot_after"] = None

    return result


def _sync_execute_with_nova_act(
    erp_url: str,
    action: str,
    corrections: list[dict],
    parsed_fields: dict,
) -> dict:
    """
    Execute ERP actions using Amazon Nova Act browser automation.
    """
    os.environ.setdefault("NOVA_ACT_SKIP_PLAYWRIGHT_INSTALL", "1")
    from nova_act import NovaAct

    invoice_number = parsed_fields.get("invoice_number", "INV-0000")
    
    with NovaAct(starting_page=f"{erp_url}/invoices.html", ignore_https_errors=True) as nova:
        # Step 1: Take before screenshot
        screenshot_before = nova.page.screenshot(type="png", full_page=True)
        
        # Step 2: Navigate to the invoice
        nova.act(
            f"Find and click on invoice number '{invoice_number}' in the invoice list table"
        )

        if action == "auto_correct" and corrections:
            for correction in corrections:
                field = correction.get("field", "")
                new_value = correction.get("corrected_value", "")
                
                # Nova Act navigates the form and corrects the field
                nova.act(
                    f"Find the input field for '{field}' in the invoice edit form "
                    f"and change its value to '{new_value}'"
                )

            # Submit the form
            nova.act("Click the 'Save' or 'Update' button to save the changes")
        
        elif action == "escalate_human":
            nova.act(
                "Click the 'Flag for Review' or 'Escalate' button for this invoice"
            )
        elif action == "approve_as_is":
            nova.act("Click the 'Approve' button for this invoice")
        elif action == "block":
            nova.act("Click the 'Reject' button for this invoice")
        else:
            raise ValueError(f"Unsupported UI action '{action}'")

        # Step 3: Take after screenshot
        screenshot_after = nova.page.screenshot(type="png", full_page=True)

        return {
            "outcome": "success",
            "action_summary": (
                f"Navigated to invoice {invoice_number} in mock ERP. "
                f"Applied {len(corrections)} corrections. "
                f"Action: {action}"
            ),
            "screenshot_before_bytes": screenshot_before,
            "screenshot_after_bytes": screenshot_after,
            "error": None,
        }


def _is_supported_nova_act_version() -> bool:
    """Nova Act versions older than 3.x are rejected by the service."""
    try:
        version = importlib.metadata.version("nova-act")
    except importlib.metadata.PackageNotFoundError:
        return False

    major = version.split(".", 1)[0]
    return major.isdigit() and int(major) >= 3


def _sync_execute_with_playwright(
    erp_url: str,
    action: str,
    corrections: list[dict],
    parsed_fields: dict,
) -> dict:
    """
    Execute the local mock ERP workflow with Playwright directly.
    This is real browser automation, not a simulation.
    """
    from playwright.sync_api import sync_playwright

    invoice_number = parsed_fields.get("invoice_number", "INV-0000")
    row_selector = f"#invoice-row-{invoice_number}"

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"{erp_url}/invoices.html", wait_until="networkidle")
        page.wait_for_selector("#invoice-tbody tr", timeout=10000)
        before_bytes = page.screenshot(type="png", full_page=True)

        if page.locator(row_selector).count() == 0:
            browser.close()
            raise ValueError(f"Invoice '{invoice_number}' was not found in the mock ERP")

        page.click(row_selector)
        page.wait_for_selector("#invoice-form.active", timeout=5000)

        applied_corrections = _apply_playwright_corrections(page, corrections)

        if action == "auto_correct":
            page.click("button:has-text('Save')")
        elif action == "escalate_human":
            page.click("button:has-text('Flag for Review')")
        elif action == "approve_as_is":
            page.click("button:has-text('Approve')")
        elif action == "block":
            page.click("button:has-text('Reject')")
        else:
            browser.close()
            raise ValueError(f"Unsupported UI action '{action}'")

        page.wait_for_timeout(300)
        after_bytes = page.screenshot(type="png", full_page=True)
        alert_text = page.locator("#invoice-alert").inner_text()
        browser.close()

    return {
        "outcome": "success",
        "action_summary": (
            f"Automated invoice {invoice_number} in mock ERP with Playwright. "
            f"Action: {action}. "
            f"Corrections applied: {applied_corrections or 'none'}. "
            f"ERP response: {alert_text}"
        ),
        "screenshot_before_bytes": before_bytes,
        "screenshot_after_bytes": after_bytes,
        "error": None,
    }


def _apply_playwright_corrections(page: Any, corrections: list[dict]) -> str:
    """Map resolution-plan fields to real form controls in the mock ERP."""
    field_map = {
        "vendor_name": ("#edit-vendor", "input"),
        "vendor": ("#edit-vendor", "input"),
        "vendor_id": ("#edit-vendor-id", "input"),
        "amount_subtotal": ("#edit-amount", "input"),
        "amount": ("#edit-amount", "input"),
        "tax_rate": ("#edit-tax-rate", "input"),
        "tax_amount": ("#edit-tax-amount", "input"),
        "amount_total": ("#edit-total", "input"),
        "total": ("#edit-total", "input"),
        "po_reference": ("#edit-po-reference", "input"),
        "date": ("#edit-date", "input"),
        "due_date": ("#edit-due-date", "input"),
        "cost_center": ("#edit-cost-center", "input"),
        "status": ("#edit-status", "select"),
        "currency": ("#edit-currency", "input"),
    }

    applied: list[str] = []
    for correction in corrections:
        field = correction.get("field", "")
        new_value = correction.get("corrected_value")
        mapping = field_map.get(field)
        if not mapping or new_value is None:
            continue

        selector, control_type = mapping
        value = str(new_value)
        if control_type == "select":
            page.select_option(selector, value)
        else:
            page.fill(selector, value)
        applied.append(f"{field}={value}")

    return "; ".join(applied)
