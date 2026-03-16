diff --git a/c:\Users\braya\Desktop\project_personal\NOVA_AWS\README.md b/c:\Users\braya\Desktop\project_personal\NOVA_AWS\README.md
new file mode 100644
--- /dev/null
+++ b/c:\Users\braya\Desktop\project_personal\NOVA_AWS\README.md
@@ -0,0 +1,244 @@
+# LedgerFlow AI
+
+LedgerFlow AI is an AI-powered finance exception resolution system built for the Amazon Nova AI Hackathon.
+
+It helps operations and accounts payable teams process invoice exceptions faster by combining:
+
+- Amazon Nova 2 Lite for document understanding and reasoning
+- Amazon Nova multimodal embeddings for policy retrieval
+- Nova Act and browser automation for ERP workflow execution
+- LangGraph for multi-agent orchestration
+- FastAPI, PostgreSQL, and pgvector for application and audit data
+
+This project combines three hackathon themes in one workflow:
+
+- Agentic AI
+- Multimodal Understanding
+- UI Automation
+
+## What It Does
+
+LedgerFlow AI takes a finance exception case from document upload to ERP action.
+
+The system:
+
+1. Uploads an invoice or supporting evidence
+2. Extracts structured financial fields from the document
+3. Retrieves relevant internal policies with vector search
+4. Detects discrepancies against purchase orders and vendor rules
+5. Decides whether the case can be auto-resolved or needs human approval
+6. Executes the required action in a legacy-style ERP UI
+7. Saves a full decision trace for auditability
+
+Example exception types included in the mock ERP:
+
+- Vendor discrepancy
+- Math or tax discrepancy
+- Suspended vendor
+
+Sample PDFs are included in [mock-erp/examples](/c:/Users/braya/Desktop/project_personal/NOVA_AWS/mock-erp/examples).
+
+## Architecture
+
+### Backend
+
+- FastAPI API for cases, evidence, approvals, traces, and results
+- LangGraph workflow with specialized agents:
+  - Intake Agent
+  - Retrieval Agent
+  - Resolution Agent
+  - Human Gate
+  - UI Execution Agent
+  - Audit Agent
+- PostgreSQL with pgvector for transactional data and policy embeddings
+
+### Frontend
+
+- React + TypeScript + Vite dashboard
+- Displays workflow status, agent trace, approval steps, and ERP outcomes
+
+### Mock ERP
+
+- Static HTML, CSS, and JavaScript application
+- Simulates invoice, vendor, and purchase order workflows in a legacy interface
+
+## Amazon Nova Usage
+
+### Amazon Nova 2 Lite
+
+Used for:
+
+- extracting invoice data from uploaded documents
+- reasoning over discrepancies
+- generating structured resolution plans
+
+### Amazon Nova Multimodal Embeddings
+
+Used for:
+
+- embedding internal finance policies
+- semantic retrieval of the most relevant policy context before resolution
+
+### Nova Act
+
+Used for:
+
+- navigating the ERP UI
+- flagging invoices
+- approving or rejecting invoices
+- applying corrections in browser workflows
+
+The project also supports direct Playwright-driven automation against the local mock ERP to keep the UI execution path operational during local development.
+
+## Repository Structure
+
+```text
+.
+|-- backend/       FastAPI app, models, services, agents, workflow graph
+|-- frontend/      React + Vite UI
+|-- mock-erp/      Static legacy ERP demo app + sample PDFs
+|-- docker-compose.yml
+|-- .env.example
+```
+
+## Local Setup
+
+### 1. Clone and configure environment
+
+Create a `.env` file from `.env.example` and fill in your credentials.
+
+Required values:
+
+- `AWS_REGION`
+- `AWS_ACCESS_KEY_ID`
+- `AWS_SECRET_ACCESS_KEY`
+- `DATABASE_URL`
+- `NOVA_ACT_API_KEY`
+- `MOCK_ERP_URL`
+
+### 2. Start PostgreSQL with pgvector
+
+```bash
+docker-compose up -d
+```
+
+This starts a local PostgreSQL container and runs [backend/init.sql](/c:/Users/braya/Desktop/project_personal/NOVA_AWS/backend/init.sql) to enable the `vector` extension.
+
+### 3. Install backend dependencies
+
+```bash
+cd backend
+python -m venv .venv
+.venv\Scripts\activate
+pip install -r requirements.txt
+python -m playwright install chromium
+```
+
+### 4. Run the backend
+
+```bash
+cd backend
+uvicorn main:app --reload --port 8000
+```
+
+### 5. Run the mock ERP
+
+In another terminal:
+
+```bash
+cd mock-erp
+python -m http.server 3001
+```
+
+### 6. Run the frontend
+
+In another terminal:
+
+```bash
+cd frontend
+npm install
+npm run dev
+```
+
+## Demo Flow
+
+For the easiest demo, use one of the sample PDFs from `mock-erp/examples`:
+
+- `invoice_INV-8822_vendor_discrepancy.pdf`
+- `invoice_INV-8823_math_discrepancy.pdf`
+- `invoice_INV-8824_suspended_vendor.pdf`
+
+Suggested demo steps:
+
+1. Open the frontend dashboard
+2. Upload one PDF from `mock-erp/examples`
+3. Start the workflow
+4. Watch the agent trace
+5. Approve the case if requested
+6. Verify the UI action in the mock ERP
+7. Review the result and audit trail
+
+## API Highlights
+
+Main endpoints:
+
+- `POST /cases`
+- `POST /cases/{case_id}/evidence`
+- `POST /cases/{case_id}/run`
+- `GET /cases/{case_id}/trace`
+- `POST /cases/{case_id}/approve`
+- `GET /cases/{case_id}/result`
+- `GET /health`
+
+## Why This Matters
+
+Finance exception handling is a strong use case for agentic AI because it requires both speed and accountability.
+
+LedgerFlow AI is designed to show that a Nova-powered system can do more than answer questions. It can:
+
+- understand business documents
+- retrieve policy context
+- reason about risk
+- involve humans when needed
+- execute actions in real interfaces
+- preserve a traceable audit log
+
+## Tech Stack
+
+- Python
+- FastAPI
+- SQLAlchemy
+- PostgreSQL
+- pgvector
+- LangGraph
+- LangChain Core
+- boto3
+- Amazon Nova 2 Lite
+- Amazon Nova multimodal embeddings
+- Nova Act
+- Playwright
+- React
+- TypeScript
+- Vite
+- HTML
+- CSS
+- JavaScript
+
+## Notes
+
+- The local UI execution path depends on the mock ERP being available at `http://localhost:3001`.
+- If Playwright reports missing browser binaries, run:
+
+```bash
+python -m playwright install chromium
+```
+
+- If Nova Act is configured but unavailable in a local environment, the project can still execute real browser automation against the mock ERP through Playwright.
+
+## Hackathon Submission
+
+LedgerFlow AI was built for the **Amazon Nova AI Hackathon** and showcases how Amazon Nova can support enterprise-grade workflows that combine reasoning, retrieval, multimodal document understanding, and UI automation.
+
+## License
+
+This project is provided for demo and hackathon purposes.
