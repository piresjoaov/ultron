import importlib
import io
import os
import unittest
from io import BytesIO
from contextlib import redirect_stdout
from unittest.mock import patch

import config
from client import StreamEvent
from models.catalog import ModelCatalog
from models.types import ModelProfile
from orchestration.model_router import ModelRouter
from orchestration.orchestrator import Orchestrator
from orchestration.output_policy import PlainTextOutputPolicy
from orchestration.task_classifier import TaskClassifier

class OrchestrationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self): self.classifier = TaskClassifier()
    def test_general_classification(self): self.assertEqual(self.classifier.classify("Olá, como você está?").category, "general")
    def test_coding_classification(self): self.assertEqual(self.classifier.classify("Explique este erro Python").category, "coding")
    def test_java_is_coding(self): self.assertEqual(self.classifier.classify("Explain a Java deletion algorithm").category, "coding")
    def test_complex_classification(self): self.assertEqual(self.classifier.classify("Analyze architecture tradeoff and prove why").complexity, "high")
    def test_long_prompt(self): self.assertTrue(self.classifier.classify("x" * 25000).requires_long_context)
    def test_tools_required(self): self.assertTrue(self.classifier.classify("encontre arquivos Python").requires_tools)
    def test_model_selection(self):
        with patch.object(config, "GITHUB_MODELS_TOKEN", None):
            decision = ModelRouter(ModelCatalog()).route(self.classifier.classify("Python bug"))
        self.assertEqual(decision.model_id, "qwen3-8b")

    def test_complex_coding_uses_github_model_when_token_is_configured(self):
        with patch.object(config, "GITHUB_MODELS_TOKEN", "test-token"):
            decision = ModelRouter(ModelCatalog()).route(self.classifier.classify("Explain this Python bug"))
        self.assertEqual(decision.model_id, "gpt-4o")

    def test_cloud_model_is_unavailable_without_token(self):
        with patch.object(config, "GITHUB_MODELS_TOKEN", None):
            catalog = ModelCatalog()
        self.assertFalse(catalog.is_available(catalog.get("gpt-4o")))
    def test_fallback(self):
        catalog = ModelCatalog([ModelProfile("only", "ref", {"general"}, 1, 1, 100, False)])
        decision = ModelRouter(catalog).route(self.classifier.classify("pesquise arquivos"))
        self.assertTrue(decision.fallback_used)
    def test_invalid_tool_json_is_controlled(self):
        self.assertIn("invalid JSON", Orchestrator._execute_tool({"name": "get_time", "arguments": "{"}))
    def test_output_policy_never_renders_markdown_or_ansi(self):
        review = PlainTextOutputPolicy().review("**bold**\n```java\n\x1b[31mcode\x1b[0m\n```")
        self.assertEqual(review.text, "bold\ncode")
        self.assertTrue(review.changed)
        self.assertIn("markdown-formatting", review.violations)

    def test_console_encoding_supports_unicode_email_subjects(self):
        stream = io.TextIOWrapper(BytesIO(), encoding="cp1252")
        with patch.object(config.sys, "stdout", stream), patch.object(
            config.sys, "stderr", stream
        ):
            config.configure_console_encoding()
            stream.write("Psst, your Prime Big Deal Days sneak peek is here! 👀")
            stream.flush()
        self.assertEqual(
            stream.detach().getvalue().decode("utf-8"),
            "Psst, your Prime Big Deal Days sneak peek is here! 👀",
        )
    async def test_tool_round_limit(self):
        calls = []
        async def client(*args, **kwargs):
            calls.append(1)
            yield StreamEvent("tool_call", tool_call={"id": str(len(calls)), "name": "get_time", "arguments": "{}"})
        with redirect_stdout(io.StringIO()):
            response = await Orchestrator(chat_client=client, max_tool_rounds=2).handle_message("what time")
        self.assertEqual(len(calls), 2)
        self.assertEqual(len(response.tool_calls), 2)

    async def test_tool_markup_is_hidden_while_text_streams(self):
        async def client(*args, **kwargs):
            yield StreamEvent("content", content="before ")
            yield StreamEvent("content", content='<tool_call>{"name":"get_time","arguments":{}}</tool_call>')
            yield StreamEvent("content", content="after")

        output = io.StringIO()
        with redirect_stdout(output):
            response = await Orchestrator(chat_client=client, max_tool_rounds=1).handle_message("what time")
        self.assertEqual(output.getvalue(), "before after")
        self.assertTrue(response.text.startswith("before after"))
        self.assertEqual(response.tool_calls[0]["name"], "get_time")

    async def test_completion_usage_is_exposed_for_generation_stats(self):
        async def client(*args, **kwargs):
            yield StreamEvent("content", content="answer")
            yield StreamEvent("usage", usage={"completion_tokens": 7})

        with redirect_stdout(io.StringIO()):
            response = await Orchestrator(chat_client=client).handle_message("hello")
        self.assertEqual(response.metadata["completion_tokens"], 7)
        self.assertFalse(response.metadata["token_count_estimated"])

    def test_environment_configuration(self):
        with patch.dict(os.environ, {"ULTRON_REQUEST_TIMEOUT": "17"}):
            import config
            importlib.reload(config)
            self.assertEqual(config.REQUEST_TIMEOUT, 17)
        import config
        importlib.reload(config)

if __name__ == "__main__": unittest.main()
