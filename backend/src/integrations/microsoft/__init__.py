"""Microsoft Graph integrations for Ultron."""

from .auth import get_access_token
from .mail import (
    authenticate_microsoft,
    list_emails,
    move_email,
    read_email,
    search_emails,
)

__all__ = [
    "authenticate_microsoft",
    "get_access_token",
    "list_emails",
    "move_email",
    "read_email",
    "search_emails",
]
