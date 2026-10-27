import requests
import pytest

from app.elexon import ElexonClient, ElexonError


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"status {self.status_code}")

    def json(self):
        return self.payload


def test_client_caches_successful_response(monkeypatch):
    calls = []

    def fake_get(*args, **kwargs):
        calls.append((args, kwargs))
        return FakeResponse([{"startTime": "2026-01-01T00:00:00Z"}])

    monkeypatch.setattr(requests, "get", fake_get)
    client = ElexonClient()
    assert client.actuals() == client.actuals()
    assert len(calls) == 1


@pytest.mark.parametrize("payload", [{"unexpected": "shape"}, "not a list"])
def test_client_rejects_unexpected_json(payload, monkeypatch):
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: FakeResponse(payload))
    with pytest.raises(ElexonError, match="unexpected response shape"):
        ElexonClient().actuals()


def test_client_surfaces_network_failure(monkeypatch):
    def failing_get(*args, **kwargs):
        raise requests.Timeout("timed out")

    monkeypatch.setattr(requests, "get", failing_get)
    with pytest.raises(ElexonError, match="request failed"):
        ElexonClient().actuals()
