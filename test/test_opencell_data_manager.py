# SPDX-FileCopyrightText: 2024-2026 Stanford University
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for ``Data/OpenCellDataManager.py``.

Network access is fully mocked: every test patches ``_request`` (the
single HTTP-touching method on the base ``DataManager``) and asserts on
the exact ``(method, path, kwargs)`` we issued. This gives us coverage
of the URL routing, body shape, auth flag, and DataFrame-shaping logic
without ever hitting a real API.
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from steer_opencell_design.Data.OpenCellDataManager import (
    ALL_TABLES,
    CELL_META_COLS,
    CELL_TABLES,
    MATERIAL_META_COLS,
    MATERIAL_TABLES,
    OpenCellDataManager,
    register_opencell_tables,
)


def _build_manager() -> OpenCellDataManager:
    """Construct an ``OpenCellDataManager`` with a stable test ``API_URL``."""
    os.environ["API_URL"] = "https://api.test.example.com"
    return OpenCellDataManager(jwt_token="test-token")


class TestModuleLevelConstants(unittest.TestCase):
    def test_all_tables_is_union_of_material_and_cell_tables(self):
        self.assertEqual(ALL_TABLES, MATERIAL_TABLES | CELL_TABLES)

    def test_material_and_cell_tables_are_disjoint(self):
        self.assertEqual(MATERIAL_TABLES & CELL_TABLES, set())

    def test_register_opencell_tables_is_idempotent(self):
        register_opencell_tables()
        register_opencell_tables()  # must not raise.

    def test_meta_cols_contain_name(self):
        self.assertIn("name", MATERIAL_META_COLS)
        self.assertIn("name", CELL_META_COLS)


class TestMaterialGetters(unittest.TestCase):
    def setUp(self):
        self.manager = _build_manager()

    def _make_response_items(self):
        return {
            "items": [
                {
                    "name": "LFP",
                    "date": "2025-01-01",
                    "version": 1,
                    "reference": "ref-1",
                    "extra_column_to_filter_out": "ignore_me",
                },
                {
                    "name": "NMC811",
                    "date": "2025-02-01",
                    "version": 2,
                    "reference": "ref-2",
                },
            ]
        }

    def test_get_cathode_materials_routes_to_correct_endpoint(self):
        with patch.object(
            OpenCellDataManager, "_request", return_value=self._make_response_items()
        ) as mock_request:
            df = self.manager.get_cathode_materials()

        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        self.assertEqual(args[0], "GET")
        self.assertEqual(args[1], "/materials/cathode_materials")
        self.assertFalse(kwargs.get("auth_required"))
        # Default most_recent=True should yield no `most_recent` query param.
        self.assertEqual(kwargs.get("params"), {})

        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(set(df.columns), set(MATERIAL_META_COLS))
        self.assertEqual(len(df), 2)

    def test_most_recent_false_sets_query_parameter(self):
        with patch.object(
            OpenCellDataManager, "_request", return_value=self._make_response_items()
        ) as mock_request:
            self.manager.get_anode_materials(most_recent=False)

        _, kwargs = mock_request.call_args
        self.assertEqual(kwargs.get("params"), {"most_recent": "false"})

    def test_empty_items_returns_empty_dataframe_with_meta_cols(self):
        with patch.object(
            OpenCellDataManager, "_request", return_value={"items": []}
        ):
            df = self.manager.get_binder_materials()
        self.assertEqual(len(df), 0)
        self.assertEqual(list(df.columns), MATERIAL_META_COLS)

    def test_each_typed_getter_uses_its_table_name(self):
        """Spot-check that every typed getter forwards its corresponding table name."""
        cases = [
            ("get_current_collector_materials", "current_collector_materials"),
            ("get_insulation_materials", "insulation_materials"),
            ("get_cathode_materials", "cathode_materials"),
            ("get_anode_materials", "anode_materials"),
            ("get_binder_materials", "binder_materials"),
            ("get_conductive_additive_materials", "conductive_additive_materials"),
            ("get_separator_materials", "separator_materials"),
            ("get_tape_materials", "tape_materials"),
            ("get_prismatic_container_materials", "prismatic_container_materials"),
        ]
        for method_name, table_name in cases:
            with patch.object(
                OpenCellDataManager, "_request", return_value={"items": []}
            ) as mock_request:
                getattr(self.manager, method_name)()
            args, _ = mock_request.call_args
            self.assertEqual(
                args[1],
                f"/materials/{table_name}",
                msg=f"{method_name} must route to /materials/{table_name}",
            )


class TestCellOperations(unittest.TestCase):
    def setUp(self):
        self.manager = _build_manager()

    def test_fork_cell_url_and_body(self):
        with patch.object(
            OpenCellDataManager, "_request", return_value={"id": "abc"}
        ) as mock_request:
            result = self.manager.fork_cell(
                source_table="cell_references",
                source_name="LG M50",
                new_name="LG M50 (fork)",
            )

        args, kwargs = mock_request.call_args
        self.assertEqual(args[0], "POST")
        self.assertIn("/cells/cell_references/", args[1])
        self.assertTrue(args[1].endswith("/fork"))
        self.assertTrue(kwargs["auth_required"])
        self.assertEqual(kwargs["json"], {"name": "LG M50 (fork)"})
        # Path must be URL-encoded (space \u2192 %2520 due to double-encoding).
        self.assertIn("%2520", args[1])
        self.assertEqual(result, {"id": "abc"})

    def test_publish_cell_without_target_table(self):
        with patch.object(
            OpenCellDataManager, "_request", return_value={}
        ) as mock_request:
            self.manager.publish_cell(
                source_table="cell_submissions",
                source_name="MyCell",
                new_name="MyCell v2",
            )

        _, kwargs = mock_request.call_args
        self.assertEqual(kwargs["json"], {"name": "MyCell v2"})

    def test_publish_cell_with_target_table(self):
        with patch.object(
            OpenCellDataManager, "_request", return_value={}
        ) as mock_request:
            self.manager.publish_cell(
                source_table="cell_submissions",
                source_name="MyCell",
                new_name="MyCell v2",
                target_table="cell_references",
            )

        _, kwargs = mock_request.call_args
        self.assertEqual(
            kwargs["json"], {"name": "MyCell v2", "target_table": "cell_references"}
        )

    def test_submit_cell_url(self):
        with patch.object(
            OpenCellDataManager, "_request", return_value={}
        ) as mock_request:
            self.manager.submit_cell("user_designs", "MyCell")

        args, kwargs = mock_request.call_args
        self.assertEqual(args[0], "POST")
        self.assertTrue(args[1].endswith("/submit"))
        self.assertIn("/cells/user_designs/", args[1])
        self.assertTrue(kwargs["auth_required"])

    def test_reject_cell_url(self):
        with patch.object(
            OpenCellDataManager, "_request", return_value=None
        ) as mock_request:
            result = self.manager.reject_cell("cell_submissions", "MyCell")

        args, kwargs = mock_request.call_args
        self.assertEqual(args[0], "POST")
        self.assertTrue(args[1].endswith("/reject"))
        self.assertTrue(kwargs["auth_required"])
        self.assertIsNone(result)  # reject_cell returns None.

    def test_check_name_available_returns_boolean(self):
        with patch.object(
            OpenCellDataManager, "_request", return_value={"available": True}
        ) as mock_request:
            self.assertTrue(self.manager.check_name_available("CellA"))

        with patch.object(
            OpenCellDataManager, "_request", return_value={"available": False}
        ):
            self.assertFalse(self.manager.check_name_available("CellB"))

        # Last-call shape check.
        args, kwargs = mock_request.call_args
        self.assertEqual(args[0], "GET")
        self.assertIn("/cells/check-name/", args[1])
        self.assertFalse(kwargs.get("auth_required"))

    def test_check_name_available_defaults_to_false_when_key_missing(self):
        with patch.object(
            OpenCellDataManager, "_request", return_value={}
        ):
            self.assertFalse(self.manager.check_name_available("CellC"))


class TestReadHalfCellCurve(unittest.TestCase):
    def test_missing_file_raises_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            OpenCellDataManager.read_half_cell_curve("/no/such/file.csv")

    def test_missing_required_column_raises_value_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "bad.csv"
            pd.DataFrame({"foo": [1, 2], "bar": [3, 4]}).to_csv(csv_path, index=False)
            with self.assertRaises(ValueError) as ctx:
                OpenCellDataManager.read_half_cell_curve(csv_path)
            self.assertIn("Specific Capacity (mAh/g)", str(ctx.exception))

    def test_missing_voltage_column_raises(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "noV.csv"
            pd.DataFrame(
                {
                    "Specific Capacity (mAh/g)": [0.0, 100.0],
                    "Step_ID": [1, 1],
                }
            ).to_csv(csv_path, index=False)
            with self.assertRaises(ValueError) as ctx:
                OpenCellDataManager.read_half_cell_curve(csv_path)
            self.assertIn("Voltage (V)", str(ctx.exception))

    def test_missing_step_id_column_raises(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "noStep.csv"
            pd.DataFrame(
                {
                    "Specific Capacity (mAh/g)": [0.0, 100.0],
                    "Voltage (V)": [3.0, 4.0],
                }
            ).to_csv(csv_path, index=False)
            with self.assertRaises(ValueError) as ctx:
                OpenCellDataManager.read_half_cell_curve(csv_path)
            self.assertIn("Step_ID", str(ctx.exception))

    def test_happy_path_renames_and_converts_units(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "good.csv"
            pd.DataFrame(
                {
                    "Specific Capacity (mAh/g)": [0.0, 100.0, 50.0],
                    "Voltage (V)": [3.0, 4.0, 3.5],
                    "Step_ID": [1, 1, 2],
                }
            ).to_csv(csv_path, index=False)

            df = OpenCellDataManager.read_half_cell_curve(csv_path)

            self.assertEqual(set(df.columns), {"specific_capacity", "voltage", "step_id"})
            # Conversion factor = H_TO_S * mA_TO_A / G_TO_KG = 3600 * 1e-3 / 1e-3 = 3600.
            # 100 mAh/g -> 100 * 3600 = 360 000 A.s/kg.
            max_capacity_si = df["specific_capacity"].max()
            self.assertAlmostEqual(max_capacity_si, 360_000.0, places=2)


if __name__ == "__main__":
    unittest.main()
