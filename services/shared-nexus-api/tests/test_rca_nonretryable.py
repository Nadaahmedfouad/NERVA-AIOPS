import requests

from app.providers.resilient import Breaker, resilient_call


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = 0

    def request(self, method, url, **kwargs):
        self.calls += 1
        return self.response


def test_nonretryable_m3_502_does_not_open_breaker():
    response = requests.Response()
    response.status_code = 502
    response._content = (
        b'{"detail":{"category":"invalid_response",'
        b'"retryable":false}}'
    )

    session = FakeSession(response)
    breaker = Breaker(threshold=3, cooldown=30)

    for _ in range(5):
        result = resilient_call(
            breaker,
            session,
            "POST",
            "http://m3/internal/rca/analyze",
            inspect_nonretryable=True,
        )
        assert result.status_code == 502

    assert session.calls == 5
    assert breaker.state == "closed"


def test_retryable_m3_502_opens_breaker():
    response = requests.Response()
    response.status_code = 502
    response._content = (
        b'{"detail":{"category":"dependency_error",'
        b'"retryable":true}}'
    )

    session = FakeSession(response)
    breaker = Breaker(threshold=3, cooldown=30)

    for _ in range(3):
        resilient_call(
            breaker,
            session,
            "POST",
            "http://m3/internal/rca/analyze",
            inspect_nonretryable=True,
        )

    assert breaker.state == "open"