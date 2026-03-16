import sys
sys.path.append('c:/Users/braya/Desktop/project_personal/NOVA_AWS/backend')
import asyncio
from database import async_session
from sqlalchemy import select
from models.case import Case
from models.decision_step import DecisionStep
import models.evidence
import models.approval
import models.ui_execution
import models.policy_document

async def check():
    async with async_session() as session:
        cases = (await session.execute(select(Case))).scalars().all()
        for c in cases:
            print(f'Case: {c.id}, status: {c.status}')
            steps = (await session.execute(select(DecisionStep).where(DecisionStep.case_id == c.id))).scalars().all()
            for s in steps:
                print(f'  Step {s.step_number}: {s.agent_name} - {s.status}')
asyncio.run(check())
