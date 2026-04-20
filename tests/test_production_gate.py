import json
import tempfile
import unittest
from pathlib import Path

from src.execution.production_gate import DEFAULT_MODEL, build_live_components, resolve_live_model


class TestProductionGate(unittest.TestCase):
    def test_missing_gate_file_falls_back_to_default(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            gate_file = Path(tmp_dir) / "missing_gate.json"
            resolved = resolve_live_model(gate_file=gate_file)

            self.assertEqual(resolved["model"], DEFAULT_MODEL)
            self.assertEqual(resolved["source"], "default_fallback")

    def test_supported_model_from_gate_is_applied(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            gate_file = Path(tmp_dir) / "gate.json"
            gate_file.write_text(
                json.dumps({"selected_model": "legacy_confidence_research"}),
                encoding="utf-8",
            )

            resolved = resolve_live_model(gate_file=gate_file)

            self.assertEqual(resolved["model"], "legacy_confidence_research")
            self.assertEqual(resolved["source"], "objective_gate")

    def test_unknown_model_in_gate_reverts_to_default(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            gate_file = Path(tmp_dir) / "gate.json"
            gate_file.write_text(json.dumps({"selected_model": "unknown_model"}), encoding="utf-8")

            components = build_live_components(gate_file=gate_file)

            self.assertEqual(components["model"], DEFAULT_MODEL)
            self.assertTrue(hasattr(components["manager"], "calculate_order"))
            self.assertTrue(hasattr(components["scorer"], "calculate_scores"))


if __name__ == "__main__":
    unittest.main()
