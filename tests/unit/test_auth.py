import pytest
from fastapi.testclient import TestClient
from kernel_api.main import app
from kernel_engine.secret_kernel import SecretKernel
import base64

client = TestClient(app)

def test_admin_auth_required():
    response = client.post("/api/v1/admin/discover?org_name=test")
    assert response.status_code == 401

def test_admin_auth_success():
    sk = SecretKernel()
    master_key = sk.get_master_key()
    auth_str = f"admin:{master_key}"
    encoded_auth = base64.b64encode(auth_str.encode()).decode()
    
    headers = {"Authorization": f"Basic {encoded_auth}"}
    response = client.post("/api/v1/admin/discover?org_name=agnxxt", headers=headers)
    assert response.status_code == 200
