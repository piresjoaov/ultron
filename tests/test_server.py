import unittest

from server import LlamaServer


class LlamaServerCommandTests(unittest.TestCase):
    def test_command_uses_low_latency_flags_without_speculative_decoding(self):
        command = LlamaServer.build_server_command()

        self.assertIn("--flash-attn", command)
        self.assertIn("--cache-type-k", command)
        self.assertIn("--cache-type-v", command)
        self.assertIn("--n-gpu-layers", command)
        self.assertIn("99", command)
        self.assertNotIn("--spec-draft-model", command)
        self.assertNotIn("--spec-type", command)
        self.assertNotIn("--spec-draft-n-max", command)
        self.assertNotIn("--spec-draft-ngl", command)
        self.assertNotIn("--spec-draft-device", command)

    def test_command_starts_without_missing_draft(self):
        command = LlamaServer.build_server_command()
        self.assertNotIn("--model-draft", command)


if __name__ == "__main__":
    unittest.main()