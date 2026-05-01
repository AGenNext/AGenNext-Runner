import requests
import pytest
import time
import os
import subprocess
import signal

BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8000")

def test_full_agent_lifecycle():
    """
    E2E Test: Validates a full cognitive action lifecycle.
    """
    # 1. Setup Action Payload (Universal Schema)
    payload = {
        "@context": "https://schema.org",
        "@type": "AssessAction",
        "name": "E2E Reliability Test",
        "agent": { "@type": "SoftwareApplication", "name": "Test-Agent-01" },
        "object": { "name": "Test-Target" },
        "payload": {"text": "Perform safety audit on network zone B."},
        "runtime": {
            "provider_topology": { "primary_provider": "aws", "is_multi_cloud": False },
            "framework_signature": { "name": "Pytest-Harness", "language": "Python" }
        },
        "semantic_extension": {
            "taxonomy": { "labels": ["testing", "e2e"] },
            "attributes": { "failure_risk": 0.1, "goal_alignment": 1.0 },
            "lineage": {
                "source_artifacts": ["urn:agnxxt:test:baseline"],
                "transformation_logic": "Standard E2E validation path."
            }
        }
    }

    # 2. Process Action
    response = requests.post(f"{BASE_URL}/api/v1/action", json=payload)
    assert response.status_code == 200
    result = response.json()
    
    assert "execution_id" in result
    assert result["status"] == "CompletedActionStatus"
    assert "trust_score" in result

    # 3. Verify Identity Sync
    id_response = requests.get(f"{BASE_URL}/api/v1/identity/Test-Agent-01")
    assert id_response.status_code == 200
    assert id_response.json()["agent_id"] == "Test-Agent-01"

    # 4. Verify Graph Ingestion
    graph_response = requests.get(f"{BASE_URL}/api/v1/graph/query?subject_id={result['execution_id']}")
    assert graph_response.status_code == 200
    assert len(graph_response.json()["facts"]) > 0

if __name__ == "__main__":
    # If running directly, attempt to start the server locally if it is not up
    try:
        requests.get(f"{BASE_URL}/api/v1/identity/ping")
    except Exception:
        print("Starting local API server for testing...")
        proc = subprocess.Popen(["uvicorn", "kernel_api.main:app", "--port", "8000"], 
                                cwd=os.path.join(os.getcwd(), "../../"))
        time.sleep(3) # Wait for start
        
    try:
        test_full_agent_lifecycle()
        print("✅ E2E Platform Flow Test Passed.")
    except Exception as e:
        print(f"❌ E2E Test Failed: {e}")
