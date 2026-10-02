"""Microsoft Entra public-client authentication using MSAL."""

from __future__ import annotations

import os
from pathlib import Path
from threading import Lock

import msal

import config

SCOPES = ["User.Read", "Mail.ReadWrite"]
_CACHE_LOCK = Lock()


class MicrosoftAuthenticationError(RuntimeError):
    """Raised when Microsoft interactive or silent authentication fails."""


def _cache_path() -> Path:
    return Path(config.MICROSOFT_CACHE_PATH).expanduser()


def _load_cache(path: Path) -> msal.SerializableTokenCache:
    cache = msal.SerializableTokenCache()
    if path.is_file():
        try:
            cache.deserialize(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise MicrosoftAuthenticationError(
                "The Microsoft token cache could not be read. Remove the cache "
                "file and authenticate again."
            ) from exc
    return cache


def _save_cache(cache: msal.SerializableTokenCache, path: Path) -> None:
    if not cache.has_state_changed:
        return
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(cache.serialize(), encoding="utf-8")
        os.replace(temporary, path)
    except OSError as exc:
        raise MicrosoftAuthenticationError(
            "Microsoft authentication succeeded, but the token cache could not "
            "be saved locally."
        ) from exc


def _application(cache: msal.SerializableTokenCache) -> msal.PublicClientApplication:
    if not config.MICROSOFT_CLIENT_ID:
        raise MicrosoftAuthenticationError(
            "MICROSOFT_CLIENT_ID is not configured."
        )
    if not config.MICROSOFT_TENANT_ID:
        raise MicrosoftAuthenticationError(
            "MICROSOFT_TENANT_ID is not configured."
        )
    authority = f"https://login.microsoftonline.com/{config.MICROSOFT_TENANT_ID}"
    return msal.PublicClientApplication(
        config.MICROSOFT_CLIENT_ID,
        authority=authority,
        token_cache=cache,
    )


def get_access_token() -> str:
    """Return a cached Microsoft token, falling back to browser login."""
    with _CACHE_LOCK:
        path = _cache_path()
        cache = _load_cache(path)
        application = _application(cache)
        accounts = application.get_accounts()
        result = application.acquire_token_silent(SCOPES, account=accounts[0]) if accounts else None
        if not result:
            result = application.acquire_token_interactive(
                scopes=SCOPES,
            )
        _save_cache(cache, path)

    if not result or "access_token" not in result:
        error = result.get("error_description") if isinstance(result, dict) else None
        raise MicrosoftAuthenticationError(
            f"Microsoft authentication failed{': ' + error if error else '.'}"
        )
    return result["access_token"]
