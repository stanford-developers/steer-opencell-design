# SPDX-FileCopyrightText: 2024-2026 Stanford University
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import unittest


class TestEnvVariable(unittest.TestCase):

    def test_opencell_env_is_development(self):
        """The test suite runs in development mode (local SQLite database)."""
        env_value = os.getenv("OPENCELL_ENV", "development")
        self.assertEqual(
            env_value,
            "development",
            f"OPENCELL_ENV should be 'development' (or unset), but got: {env_value}",
        )

    def test_local_database_available(self):
        """steer-opencell-data must be installed for development mode."""
        try:
            from steer_opencell_data.DataManager import DataManager  # noqa: F401
        except ImportError:
            self.fail(
                "steer-opencell-data is required to run the test suite "
                "in development mode (pip install steer-opencell-data)"
            )


if __name__ == "__main__":
    unittest.main()
