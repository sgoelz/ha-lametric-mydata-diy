"""Tests that guard the HTTP feed auth contract."""

from __future__ import annotations

import ast
from pathlib import Path
import unittest


class HttpViewAuthTests(unittest.TestCase):
    """Ensure the direct HTTP feed keeps Home Assistant auth enabled."""

    def test_feed_view_requires_auth(self) -> None:
        source_path = (
            Path(__file__).resolve().parents[1]
            / "custom_components"
            / "lametric_mydata_diy"
            / "__init__.py"
        )
        tree = ast.parse(source_path.read_text(encoding="utf-8"))

        feed_view = next(
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "LaMetricMyDataDIYFeedView"
        )

        requires_auth = next(
            node
            for node in feed_view.body
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == "requires_auth"
                for target in node.targets
            )
        )

        self.assertIsInstance(requires_auth.value, ast.Constant)
        self.assertIs(requires_auth.value.value, True)


if __name__ == "__main__":
    unittest.main()
