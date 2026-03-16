import requests
import time

BASE_URL = "http://127.0.0.1:8000"

def test_agent_workflow():
    print("1. Creating a new case...")
    case_data = {
        "case_type": "invoice_mismatch",
        "title": "Vendor Price Discrepancy",
        "description": "The invoice price is higher than the PO price.",
        "submitted_by": "test_user",
        "priority": "high"
    }
    
    response = requests.post(f"{BASE_URL}/cases", json=case_data)
    if response.status_code != 201:
        print(f"Failed to create case: {response.text}")
        return
        
    case = response.json()
    case_id = case["id"]
    print(f"Case created successfully with ID: {case_id}")
    
    print("\n2. Triggering the agent workflow...")
    run_response = requests.post(f"{BASE_URL}/cases/{case_id}/run")
    if run_response.status_code != 200:
        print(f"Failed to trigger workflow: {run_response.text}")
        return
        
    print(f"Workflow triggered: {run_response.json()['message']}")
    
    print("\n3. Polling for agent trace and results...")
    for _ in range(10):
        time.sleep(2)
        trace_response = requests.get(f"{BASE_URL}/cases/{case_id}/trace")
        if trace_response.status_code == 200:
            trace = trace_response.json()
            status = trace["case_status"]
            print(f"Current Status: {status}")
            
            for step in trace.get("steps", []):
                print(f"  Step: [{step.get('step_type')}] {step.get('agent_name')} - {step.get('result_summary')}")
                
            if status not in ("processing", "created", "submitted"):
                print(f"\nWorkflow finished with status: {status}")
                break
        else:
            print(f"Error fetching trace: {trace_response.text}")

if __name__ == "__main__":
    test_agent_workflow()
