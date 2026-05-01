from fastapi.testclient import TestClient

from runtime_core.main import app


def test_runtime_core_e2e_lifecycle():
    client = TestClient(app)

    init = client.post('/runtime/init', json={'runtime': 'langgraph', 'config': {'mode': 'test'}})
    assert init.status_code == 200
    session_id = init.json()['session_id']

    invoke = client.post(
        f'/runtime/{session_id}/invoke',
        json={'action': 'summarize', 'payload': {'text': 'hello'}, 'correlation_id': 'corr-1'},
        headers={'x-idempotency-key': 'idem-1'},
    )
    assert invoke.status_code == 200
    assert invoke.json()['status'] == 'accepted'

    invoke_dup = client.post(
        f'/runtime/{session_id}/invoke',
        json={'action': 'summarize', 'payload': {'text': 'hello'}, 'correlation_id': 'corr-1'},
        headers={'x-idempotency-key': 'idem-1'},
    )
    assert invoke_dup.status_code == 200
    assert invoke_dup.json() == invoke.json()

    stream = client.get(f'/runtime/{session_id}/stream')
    assert stream.status_code == 200
    event_types = [e['type'] for e in stream.json()]
    assert 'runtime.init' in event_types
    assert 'runtime.invoke' in event_types

    close = client.post(f'/runtime/{session_id}/close')
    assert close.status_code == 200


def test_runtime_core_payload_limit():
    client = TestClient(app)
    session_id = client.post('/runtime/init', json={'runtime': 'agentfield'}).json()['session_id']
    big_payload = {f'k{i}': i for i in range(300)}
    r = client.post(f'/runtime/{session_id}/invoke', json={'action': 'x', 'payload': big_payload})
    assert r.status_code == 413
