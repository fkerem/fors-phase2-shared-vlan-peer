#!/usr/bin/env python3

import pathlib
import sys
import unittest


sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from validation import validate_parameters  # noqa: E402


class ValidationTests(unittest.TestCase):
    def test_valid_configuration(self):
        self.assertEqual([], validate_parameters(
            "oran-vlan-stage2", "10.254.254.2", "255.255.255.0",
            "10.254.254.1", 32222))

    def test_portal_unicode_values_are_accepted(self):
        self.assertEqual([], validate_parameters(
            "oran-vlan-stage2", "10.254.254.2", "255.255.255.0",
            "10.254.254.1", 32222))

    def test_blank_vlan_name_is_rejected(self):
        self.assertTrue(validate_parameters(
            "", "10.254.254.2", "255.255.255.0", "10.254.254.1", 32222))

    def test_owner_must_be_distinct_and_in_subnet(self):
        errors = validate_parameters(
            "phase2", "10.254.254.2", "255.255.255.0", "10.254.254.2", 70000)
        fields = {field for field, _ in errors}
        self.assertIn("owner_ip", fields)
        self.assertIn("e2_node_port", fields)


if __name__ == "__main__":
    unittest.main()
