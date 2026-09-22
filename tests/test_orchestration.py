import importlib
import os
import unittest
from unittest.mock import patch

from models.catalog import ModelCatalog
from models.types import ModelProfile
from orchestration.model_router import ModelRouter
from orchestration.orchestrator import Orchestrator
from orchestration.output_policy import PlainTextOutputPolicy
from orchestration.task_classifier import TaskClassifier

class OrchestrationTests(unittest.TestCase):
    def setUp(self): self.classifier = TaskClassifier()
    def test_general_classification(self): self.assertEqual(self.classifier.classify("Olá, como você está?").category, "general")
    def test_coding_classification(self): self.assertEqual(self.classifier.classify("Explique este erro Python").category, "coding")
    def test_java_is_coding(self): self.assertEqual(self.classifier.classify("Explain a Java deletion algorithm").category, "coding")
    def test_complex_classification(self): self.assertEqual(self.classifier.classify("Analyze architecture tradeoff and prove why").complexity, "high")
    def test_long_prompt(self): self.assertTrue(self.classifier.classify("x" * 25000).requires_long_context)
    def test_tools_required(self): self.assertTrue(self.classifier.classify("encontre arquivos Python").requires_tools)
    def test_model_selection(self):
        decision = ModelRouter(ModelCatalog()).route(self.classifier.classify("Python bug"))
        self.assertEqual(decision.model_id, "qwen3-8b")
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
    def test_tool_round_limit(self):
        calls = []
        def client(*args, **kwargs):
            calls.append(1)
            return "", [{"id": str(len(calls)), "name": "get_time", "arguments": "{}"}]
        response = Orchestrator(chat_client=client, max_tool_rounds=2).handle_message("what time")
        self.assertEqual(len(calls), 2)
        self.assertEqual(len(response.tool_calls), 2)
    def test_environment_configuration(self):
        with patch.dict(os.environ, {"ULTRON_REQUEST_TIMEOUT": "17"}):
            import config
            importlib.reload(config)
            self.assertEqual(config.REQUEST_TIMEOUT, 17)
        import config
        importlib.reload(config)

if __name__ == "__main__": unittest.main()
