import unittest

from mobile_harness.schema import validate


class SchemaValidatorTests(unittest.TestCase):
    def test_reports_nested_required_and_enum_errors(self):
        schema = {
            "type": "object",
            "required": ["status", "items"],
            "properties": {
                "status": {"enum": ["passed", "failed"]},
                "items": {"type": "array", "minItems": 1, "items": {"type": "string"}},
            },
        }

        errors = validate({"status": "maybe", "items": []}, schema)

        self.assertTrue(any("must be one of" in error for error in errors))
        self.assertTrue(any("at least 1" in error for error in errors))

    def test_accepts_a_valid_document(self):
        schema = {"type": "object", "required": ["version"], "properties": {"version": {"const": 1}}}
        self.assertEqual(validate({"version": 1}, schema), [])


if __name__ == "__main__":
    unittest.main()

