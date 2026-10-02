import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parents[1] / "backend" / "src"))

from integrations.microsoft.auth import MicrosoftAuthenticationError
from integrations.microsoft.graph import GraphClient, GraphError
from integrations.microsoft.mail import (
    list_emails,
    move_email,
    read_email,
    search_emails,
)
from tools.registry import TOOLS, TOOL_DEFINITIONS


class FakeResponse:
    def __init__(self, payload=None, status_code=200, text=""):
        self._payload = payload or {}
        self.status_code = status_code
        self.content = b"{}" if payload is not None else b""
        self.text = text
        self.ok = 200 <= status_code < 300

    def json(self):
        return self._payload


class GraphClientTests(unittest.TestCase):
    def test_authentication_failure_is_not_silent(self):
        with patch(
            "integrations.microsoft.graph.get_access_token",
            side_effect=MicrosoftAuthenticationError("missing client id"),
        ):
            with self.assertRaisesRegex(GraphError, "authentication failed"):
                GraphClient().get("/me")

    def test_http_error_contains_status_and_graph_message(self):
        session = Mock()
        session.request.return_value = FakeResponse(
            {"error": {"message": "Access denied"}}, status_code=403
        )
        with self.assertRaisesRegex(GraphError, "HTTP 403: Access denied"):
            GraphClient(token_provider=lambda: "test-token", session=session).get("/me")
        sent_headers = session.request.call_args.kwargs["headers"]
        self.assertEqual(sent_headers["Authorization"], "Bearer test-token")

    def test_external_graph_host_is_rejected(self):
        with self.assertRaisesRegex(GraphError, "unexpected host"):
            GraphClient(token_provider=lambda: "token").get(
                "https://example.com/v1.0/me"
            )


class MailToolTests(unittest.TestCase):
    def setUp(self):
        self.client = Mock()

    def test_list_and_search_parse_compact_message_metadata(self):
        payload = {
            "value": [{
                "id": "m1",
                "subject": "Hello",
                "sender": {"emailAddress": {"name": "Ada", "address": "ada@example.com"}},
                "receivedDateTime": "2026-10-02T12:00:00Z",
                "isRead": False,
                "hasAttachments": True,
                "importance": "normal",
                "webLink": "https://outlook.office.com/mail/id/m1",
            }]
        }
        self.client.get.return_value = payload
        with patch("integrations.microsoft.mail.GraphClient", return_value=self.client):
            result = json.loads(list_emails())
            search_result = json.loads(search_emails("from:ada"))
        self.assertEqual(result[0]["message_id"], "m1")
        self.assertEqual(result[0]["sender"]["address"], "ada@example.com")
        self.assertEqual(search_result[0]["subject"], "Hello")

    def test_list_follows_graph_next_link_without_reusing_initial_params(self):
        self.client.get.side_effect = [
            {"value": [{"id": "m1"}], "@odata.nextLink": "https://graph.microsoft.com/v1.0/me/messages?$skip=1"},
            {"value": [{"id": "m2"}]},
        ]
        with patch("integrations.microsoft.mail.GraphClient", return_value=self.client):
            result = json.loads(list_emails(max_results=2))
        self.assertEqual([item["message_id"] for item in result], ["m1", "m2"])
        self.assertIn("params", self.client.get.call_args_list[0].kwargs)
        self.assertNotIn("params", self.client.get.call_args_list[1].kwargs)

    def test_read_email_parses_body_recipients_and_attachment_metadata(self):
        self.client.get.return_value = {
            "id": "m1",
            "subject": "Hello",
            "sender": {"emailAddress": {"name": "Ada", "address": "ada@example.com"}},
            "toRecipients": [{"emailAddress": {"name": "Me", "address": "me@example.com"}}],
            "body": {"contentType": "html", "content": "<p>Hello</p>"},
            "attachments": [{"id": "a1", "name": "x.pdf", "size": 10, "contentType": "application/pdf"}],
        }
        with patch("integrations.microsoft.mail.GraphClient", return_value=self.client):
            result = json.loads(read_email("m1"))
        self.assertEqual(result["recipients"]["to"][0]["address"], "me@example.com")
        self.assertEqual(result["attachments"][0]["name"], "x.pdf")

    def test_read_email_rejects_natural_language_identifier(self):
        with patch("integrations.microsoft.mail.GraphClient") as client_type:
            result = read_email(
                "Psst, your Prime Big Deal Days sneak peek is here! 👀"
            )
        self.assertIn("must be the Microsoft Graph message ID", result)
        client_type.assert_not_called()

    def test_move_rejects_invalid_and_deleted_destinations(self):
        with patch("integrations.microsoft.mail.GraphClient") as client_type:
            self.assertIn("invalid destination folder", move_email("m1", "../mail"))
            self.assertIn("invalid destination folder", move_email("m1", "Deleted Items"))
            client_type.return_value.post.assert_not_called()


class RegistryTests(unittest.TestCase):
    def test_only_requested_microsoft_operations_are_registered(self):
        for name in (
            "authenticate_microsoft", "list_emails", "read_email",
            "search_emails", "move_email",
        ):
            self.assertIn(name, TOOLS)
        self.assertNotIn("send_email", TOOLS)
        self.assertNotIn("delete_email", TOOLS)
        names = {entry["function"]["name"] for entry in TOOL_DEFINITIONS}
        self.assertNotIn("send_email", names)
        self.assertNotIn("delete_email", names)

    def test_read_schema_requires_search_before_natural_identifier_reads(self):
        definition = next(
            item for item in TOOL_DEFINITIONS
            if item["function"]["name"] == "read_email"
        )
        description = definition["function"]["description"]
        self.assertIn("search_emails or list_emails first", description)
        self.assertIn("never a subject", description)


class AuthCacheTests(unittest.TestCase):
    def test_cached_token_is_used_without_interactive_login(self):
        import integrations.microsoft.auth as auth

        class Cache:
            has_state_changed = False

        application = Mock()
        application.get_accounts.return_value = [{"username": "user"}]
        application.acquire_token_silent.return_value = {"access_token": "cached"}
        with tempfile.TemporaryDirectory() as directory, patch.object(
            auth.config, "MICROSOFT_CLIENT_ID", "client"
        ), patch.object(
            auth.config, "MICROSOFT_TENANT_ID", "tenant"
        ), patch.object(
            auth.config, "MICROSOFT_CACHE_PATH", os.path.join(directory, "cache.bin")
        ), patch.object(
            auth, "_load_cache", return_value=Cache()
        ), patch.object(
            auth, "_application", return_value=application
        ):
            self.assertEqual(auth.get_access_token(), "cached")
        application.acquire_token_interactive.assert_not_called()


if __name__ == "__main__":
    unittest.main()
