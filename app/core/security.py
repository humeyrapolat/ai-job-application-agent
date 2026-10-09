from fastapi import Header, HTTPException, status

from app.core.config import get_api_key


def require_api_key(authorization: str | None = Header(default=None)) -> None:
    """Guard an endpoint with a shared-secret API key.

    Protects endpoints that return previously stored candidate data
    (name, job/company details, the full LLM-generated analysis) from
    being readable by anyone who finds the deployed URL — there was
    previously no authentication on these endpoints at all.

    Expects `Authorization: Bearer <API_KEY>`. The key is read from the
    environment on every call (not cached on the Settings object) so
    deployments can rotate it without a restart-sensitive singleton,
    and so tests can set/unset it per-test via monkeypatch.
    """
    configured_key = get_api_key()
    if not configured_key:
        # Fail closed: an unconfigured key must not mean "no auth required".
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API_KEY is not configured on the server.",
        )

    if authorization != f"Bearer {configured_key}":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
            headers={"WWW-Authenticate": "Bearer"},
        )
