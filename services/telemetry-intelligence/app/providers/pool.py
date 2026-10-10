import httpx


class PooledClient:
    """One reusable AsyncClient per provider instead of a new pool per request.

    No await precedes assignment, so concurrent requests share one pool.
    """

    def __init__(self, timeout: float, transport: httpx.AsyncBaseTransport | None = None, **options):
        self._timeout = timeout
        self._transport = transport
        self._options = options
        self._http_client: httpx.AsyncClient | None = None

    def get(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=self._timeout, transport=self._transport,
                limits=httpx.Limits(max_connections=20, max_keepalive_connections=5, keepalive_expiry=30),
                **self._options,
            )
        return self._http_client

    async def aclose(self) -> None:
        client, self._http_client = self._http_client, None
        if client is not None:
            await client.aclose()
