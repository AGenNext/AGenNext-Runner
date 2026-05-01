import requests
import json
import time
import os
import base64

BASE_URL = os.getenv("KERNEL_API_URL", "http://localhost:8000")
ADMIN_KEY = os.getenv("KERNEL_MASTER_KEY", "admin_secret_12345") # Fallback to default if not set

def get_auth_header():
    auth_str = f"admin:{ADMIN_KEY}"
    encoded = base64.b64encode(auth_str.encode()).decode()
    return {"Authorization": f"Basic {encoded}"}

def run_journey():
    print("🚀 Starting Governed Agent Journey: GitHub -> CGL -> Slack")
    
    # 1. Register a Federated Project Agent
    print("\n--- [PHASE 1: IDENTITY & CIAM] ---")
    agent_id = "analyst-agent-007"
    reg_payload = {
        "id": agent_id,
        "type": "Agent",
        "name": "Repo Analyst",
        "domain": "PROJECT",
        "sponsor_id": "admin",
        "metadata": {"project": "Kernel Stability Audit"}
    }
    
    # Register with sponsorship
    res = requests.post(f"{BASE_URL}/api/v1/identity/register", json=reg_payload, headers=get_auth_header())
    print(f"Agent Registered: {res.json()}")

    # 2. Establish a 24-Hour Time-Bound Handshake
    print("\n--- [PHASE 2: FEDERATED HANDSHAKE] ---")
    did = res.json()["did"]
    handshake_res = requests.post(
        f"{BASE_URL}/api/v1/ciam/handshake?agent_did={did}&sponsor_id=admin&duration_hours=24",
        headers=get_auth_header()
    )
    print(f"Handshake Complete. Expires at: {handshake_res.json()['expires_at']}")

    # 3. Activate the Agent (Lifecycle Management)
    print("\n--- [PHASE 3: LIFECYCLE ACTIVATION] ---")
    requests.post(f"{BASE_URL}/api/v1/lifecycle/activate/{agent_id}", headers=get_auth_header())
    print(f"Agent {agent_id} is now ACTIVE.")

    # 4. Action 1: Analyze GitHub Repository (Pre-Gate -> Tool -> Post-Gate)
    print("\n--- [PHASE 4: GOVERNED GITHUB ACCESS] ---")
    github_action = {
        "@context": "https://schema.org",
        "@type": "UpdateAction",
        "name": "Crawl Repo for Status",
        "agent": {"name": agent_id},
        "object": {"name": "openagx/caas", "identifier": "github"},
        "payload": {"branch": "main", "file_path": "audit_report.txt"},
        "semantic_extension": {
            "taxonomy": {"labels": ["audit", "github"]},
            "lineage": {"source_artifacts": ["urn:agnxxt:research:baseline"]}
        }
    }
    
    action_res = requests.post(f"{BASE_URL}/api/v1/action", json=github_action)
    print(f"GitHub Action Result: {action_res.json()['status']}")
    execution_id = action_res.json()["execution_id"]

    # 5. CAAS Reasoning (Cognition-as-a-Service)
    print("\n--- [PHASE 5: COGNITIVE REASONING (CAAS)] ---")
    reasoning_payload = {
        "agent_id": agent_id,
        "prompt": "Summarize the repository state based on the previous audit. Ensure no secrets are leaked.",
        "context": {"impact_level": 5, "drift_score": 0.05}
    }
    reason_res = requests.post(f"{BASE_URL}/api/v1/caas/reason", json=reasoning_payload)
    summary = reason_res.json().get("thought_process", "Default summary: System is stable.")
    print(f"CAAS Summary: {summary[:100]}...")

    # 6. Action 2: Send Slack Summary
    print("\n--- [PHASE 6: GOVERNED SLACK COMMUNICATION] ---")
    slack_action = {
        "@context": "https://schema.org",
        "@type": "CommunicateAction",
        "name": "Post Summary",
        "agent": {"name": agent_id},
        "recipient": "security-alerts@slack",
        "message": {"@type": "Message", "text": summary},
        "semantic_extension": {
            "taxonomy": {"labels": ["notification", "slack"]}
        }
    }
    
    slack_res = requests.post(f"{BASE_URL}/api/v1/action", json=slack_action)
    print(f"Slack Action Result: {slack_res.json()['status']}")

    print("\n✅ Journey Complete. Check the Dashboard Audit Trail for the full forensic trace.")

if __name__ == "__main__":
    run_journey()
