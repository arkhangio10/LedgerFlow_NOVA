"""
LedgerFlow AI — Policy Seed Data
Populates the vector store with sample financial policies for RAG demo.
"""
import asyncio
import logging
from database import async_session, create_tables
from services.rag import rag_service

logger = logging.getLogger(__name__)

SEED_POLICIES = [
    {
        "title": "AP-01: Invoice Tolerance Policy",
        "category": "ap_tolerance",
        "content": """
ACCOUNTS PAYABLE — TOLERANCE POLICY (AP-01)

1. SCOPE: Applies to all vendor invoices matched against Purchase Orders.

2. TOLERANCE THRESHOLDS:
   - Amount tolerance: ±2% of PO total or ±$50.00 (whichever is lower)
   - Quantity tolerance: ±5% of ordered quantity
   - Unit price tolerance: ±1% of agreed unit price

3. ACTIONS:
   - Within tolerance: Auto-approve and process for payment
   - Outside tolerance but within 5%: Flag for supervisor review
   - Outside 5%: Block payment and escalate to AP Manager

4. EXCEPTIONS: Tax adjustments and currency rounding differences up to $5.00 are auto-accepted.
""",
    },
    {
        "title": "AP-02: Three-Way Match Requirements",
        "category": "ap_tolerance",
        "content": """
ACCOUNTS PAYABLE — THREE-WAY MATCH (AP-02)

1. REQUIREMENT: All invoices above $500 must pass three-way match:
   - Purchase Order (PO)
   - Goods Receipt / Delivery Note
   - Vendor Invoice

2. MATCHING FIELDS:
   - Vendor name and ID must match PO
   - Invoice amount must match PO total within tolerance (see AP-01)
   - Line items must correspond to PO line items
   - Delivery date must be on or after PO date

3. MISSING MATCH: If any document is missing, hold invoice for 5 business days before escalating.
""",
    },
    {
        "title": "VR-01: Vendor Validation Rules",
        "category": "vendor_rules",
        "content": """
VENDOR MANAGEMENT — VALIDATION RULES (VR-01)

1. NEW VENDOR REGISTRATION:
   - Must include: Legal name, Tax ID (RUC/EIN), bank account, contact info
   - Tax ID must be verified against government registry
   - Duplicate check: compare against existing vendors by Tax ID and name similarity

2. VENDOR STATUS:
   - Active: eligible for PO and payment
   - Suspended: blocked from new PO, existing PO honored
   - Blocked: no transactions allowed
   - Pending: awaiting verification

3. PAYMENT TERMS:
   - Default: Net 30
   - Early payment discount: 2%/10 Net 30 (if negotiated)
   - Overdue threshold: 45 days triggers vendor notification
""",
    },
    {
        "title": "TX-01: Tax Field Requirements",
        "category": "tax_requirements",
        "content": """
TAX COMPLIANCE — INVOICE REQUIREMENTS (TX-01)

1. MANDATORY TAX FIELDS on every invoice:
   - Vendor Tax ID (RUC / EIN)
   - Tax type (IVA / IGV / Sales Tax)
   - Tax rate applied
   - Tax amount (must equal rate × taxable base)
   - Withholding tax if applicable

2. VALIDATION RULES:
   - Tax amount must be recalculated: |invoice_tax - (rate × base)| < $0.50
   - If tax rate does not match standard rates (12%, 15%, 19%), flag for review
   - Zero-tax invoices require exemption certificate reference

3. MISSING TAX FIELDS: Reject invoice, request correction from vendor.
""",
    },
    {
        "title": "AH-01: Approval Hierarchy",
        "category": "approval_hierarchy",
        "content": """
APPROVAL HIERARCHY — FINANCIAL TRANSACTIONS (AH-01)

1. INVOICE APPROVAL LEVELS:
   - Up to $1,000: AP Analyst auto-approval
   - $1,001 – $10,000: AP Supervisor approval
   - $10,001 – $50,000: AP Manager + Finance Director
   - Above $50,000: CFO approval required

2. EXCEPTION APPROVAL:
   - Tolerance override: AP Supervisor minimum
   - New vendor payment: AP Manager minimum
   - Rush payment: Finance Director + justification memo
   - Blocked vendor transaction: CFO only

3. ESCALATION: If approver does not respond within 2 business days, auto-escalate to next level.
""",
    },
    {
        "title": "CC-01: Cost Center Allocation",
        "category": "general",
        "content": """
COST CENTER ALLOCATION POLICY (CC-01)

1. REQUIREMENT: Every invoice must have a valid cost center code.

2. COST CENTER FORMAT: 4-digit department code + 2-digit sub-unit (e.g., 4100-01 = IT Operations)

3. VALIDATION:
   - Cost center must exist in the Chart of Accounts
   - Cost center must be active (not closed or frozen)
   - Budget availability check: invoice amount must not exceed remaining budget for the period

4. SPLIT INVOICES: If an invoice spans multiple cost centers, each line item must specify its cost center.

5. DEFAULT: If cost center is missing, assign to the requesting department's general overhead code.
""",
    },
    {
        "title": "PY-01: Payment Processing Rules",
        "category": "general",
        "content": """
PAYMENT PROCESSING RULES (PY-01)

1. PAYMENT CYCLES:
   - Standard: Weekly batch (every Friday)
   - Urgent: Same-day wire (requires Finance Director approval)

2. CURRENCY:
   - Domestic invoices: pay in local currency
   - Foreign invoices: use exchange rate from date of invoice receipt
   - FX tolerance: ±0.5% from Central Bank reference rate

3. DUPLICATE DETECTION:
   - Check for duplicate invoice numbers from same vendor within 90 days
   - Check for same amount ± $1 from same vendor within 30 days
   - Duplicates must be manually confirmed before processing

4. REMITTANCE: Send payment notification to vendor within 1 business day.
""",
    },
    {
        "title": "AU-01: Audit Trail Requirements",
        "category": "general",
        "content": """
AUDIT TRAIL REQUIREMENTS (AU-01)

1. EVERY TRANSACTION must log:
   - Who initiated the action
   - What was changed (before/after values)
   - When the change occurred (UTC timestamp)
   - Why the change was made (justification or policy reference)
   - System or tool used

2. RETENTION:
   - Financial records: 7 years minimum
   - Audit logs: 5 years minimum
   - Screenshots of system actions: 1 year

3. ACCESS: Audit logs are read-only. Only Internal Audit and Compliance can query full logs.

4. AUTOMATED ACTIONS: Must include the AI agent identifier, model version, confidence score, and decision rationale.
""",
    },
]


async def seed_policies():
    """Seed the database with sample policies."""
    await create_tables()
    async with async_session() as session:
        for policy in SEED_POLICIES:
            try:
                await rag_service.index_policy(
                    session=session,
                    title=policy["title"],
                    category=policy["category"],
                    content=policy["content"],
                )
                print(f"✓ Seeded: {policy['title']}")
            except Exception as e:
                print(f"✗ Failed: {policy['title']} — {e}")
        await session.commit()
    print(f"\nSeeded {len(SEED_POLICIES)} policies.")


if __name__ == "__main__":
    asyncio.run(seed_policies())
