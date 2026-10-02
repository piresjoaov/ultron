"""Microsoft Graph mailbox operations exposed to Ultron tools."""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import quote

from .auth import get_access_token
from .graph import GraphClient, GraphError

_MESSAGE_SELECT = (
    "id,subject,sender,receivedDateTime,isRead,hasAttachments,importance,webLink,"
    "bodyPreview"
)
_ALLOWED_FOLDERS = {
    "inbox": "Inbox",
    "archive": "Archive",
    "drafts": "Drafts",
    "sent items": "Sent Items",
    "junk email": "Junk Email",
}


def _json_result(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _sender(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    address = value.get("emailAddress")
    if not isinstance(address, dict):
        return None
    return {"name": address.get("name"), "address": address.get("address")}


def _recipients(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in (_sender(entry) for entry in value) if item]


def _compact_message(message: dict[str, Any]) -> dict[str, Any]:
    return {
        "message_id": message.get("id"),
        "subject": message.get("subject"),
        "sender": _sender(message.get("sender")),
        "received_datetime": message.get("receivedDateTime"),
        "is_read": message.get("isRead"),
        "has_attachments": message.get("hasAttachments"),
        "importance": message.get("importance"),
        "web_link": message.get("webLink"),
        "body_preview": message.get("bodyPreview"),
    }


def _list_pages(client: GraphClient, path: str, **kwargs: Any) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    next_path = path
    request_kwargs = dict(kwargs)
    max_results = request_kwargs.pop("max_results", 50)
    while next_path and len(items) < max_results:
        page = client.get(next_path, **request_kwargs)
        values = page.get("value", [])
        if not isinstance(values, list):
            raise GraphError("Microsoft Graph returned an invalid message list.")
        items.extend(item for item in values if isinstance(item, dict))
        next_path = page.get("@odata.nextLink")
        if not isinstance(next_path, str):
            break
        request_kwargs.pop("params", None)
    return items


def authenticate_microsoft() -> str:
    """Authenticate Microsoft Graph without exposing the access token."""
    try:
        get_access_token()
        return "Microsoft authentication succeeded."
    except Exception as exc:
        return f"Error authenticating Microsoft: {exc}"


def list_emails(max_results: int = 25) -> str:
    """List compact metadata for recent Outlook messages."""
    try:
        client = GraphClient()
        safe_max = max(1, min(int(max_results), 100))
        messages = _list_pages(
            client, "/me/messages",
            params={"$select": _MESSAGE_SELECT, "$orderby": "receivedDateTime DESC",
                    "$top": min(safe_max, 50)},
            max_results=safe_max,
        )
        return _json_result([_compact_message(message) for message in messages[:safe_max]])
    except (GraphError, ValueError, TypeError) as exc:
        return f"Error listing Outlook emails: {exc}"


def read_email(message_id: str) -> str:
    """Read one Outlook message and attachment metadata."""
    if not isinstance(message_id, str) or not message_id.strip():
        return "Error: 'message_id' cannot be empty."
    if any(character.isspace() for character in message_id):
        return (
            "Error: 'message_id' must be the Microsoft Graph message ID returned "
            "by list_emails or search_emails, not a subject or sender. Search "
            "or list emails first."
        )
    try:
        client = GraphClient()
        fields = "id,subject,sender,toRecipients,ccRecipients,receivedDateTime,body,bodyPreview,attachments,importance,isRead"
        message = client.get(
            f"/me/messages/{quote(message_id, safe='')}",
            params={"$select": fields, "$expand": "attachments($select=id,name,size,contentType,isInline)"},
        )
        return _json_result({
            "id": message.get("id"),
            "subject": message.get("subject"),
            "sender": _sender(message.get("sender")),
            "recipients": {
                "to": _recipients(message.get("toRecipients")),
                "cc": _recipients(message.get("ccRecipients")),
            },
            "received_datetime": message.get("receivedDateTime"),
            "body": message.get("body"),
            "body_preview": message.get("bodyPreview"),
            "attachments": [
                {key: attachment.get(key) for key in
                 ("id", "name", "size", "contentType", "isInline")}
                for attachment in message.get("attachments", [])
                if isinstance(attachment, dict)
            ],
            "importance": message.get("importance"),
            "is_read": message.get("isRead"),
        })
    except GraphError as exc:
        return f"Error reading Outlook email: {exc}"


def search_emails(query: str, max_results: int = 25) -> str:
    """Search Outlook using Microsoft Graph's server-side message search."""
    if not query or not query.strip():
        return "Error: 'query' cannot be empty."
    try:
        client = GraphClient()
        safe_max = max(1, min(int(max_results), 100))
        messages = _list_pages(
            client, "/me/messages",
            params={"$search": f'"{query.strip()}"', "$select": _MESSAGE_SELECT,
                    "$top": min(safe_max, 50)},
            headers={"ConsistencyLevel": "eventual"},
            max_results=safe_max,
        )
        return _json_result([_compact_message(message) for message in messages[:safe_max]])
    except (GraphError, ValueError, TypeError) as exc:
        return f"Error searching Outlook emails: {exc}"


def _resolve_folder(client: GraphClient, destination_folder: str) -> str:
    if not isinstance(destination_folder, str):
        raise ValueError("destination folder must be a string")
    key = (destination_folder or "").strip().casefold()
    if key not in _ALLOWED_FOLDERS:
        allowed = ", ".join(_ALLOWED_FOLDERS.values())
        raise ValueError(f"invalid destination folder; choose one of: {allowed}")
    folders = _list_pages(
        client, "/me/mailFolders",
        params={"$select": "id,displayName", "$top": 100},
        max_results=100,
    )
    wanted = _ALLOWED_FOLDERS[key].casefold()
    for folder in folders:
        if str(folder.get("displayName", "")).casefold() == wanted:
            folder_id = folder.get("id")
            if folder_id:
                return str(folder_id)
    raise GraphError(f"mailbox folder '{_ALLOWED_FOLDERS[key]}' was not found.")


def move_email(message_id: str, destination_folder: str) -> str:
    """Move an Outlook message to one of the approved mailbox folders."""
    if not isinstance(message_id, str) or not message_id.strip():
        return "Error: 'message_id' cannot be empty."
    try:
        client = GraphClient()
        folder_id = _resolve_folder(client, destination_folder)
        client.post(
            f"/me/messages/{quote(message_id, safe='')}/move",
            json={"destinationId": folder_id},
        )
        return f"Email moved to {_ALLOWED_FOLDERS[destination_folder.strip().casefold()]}."
    except (GraphError, ValueError) as exc:
        return f"Error moving Outlook email: {exc}"
