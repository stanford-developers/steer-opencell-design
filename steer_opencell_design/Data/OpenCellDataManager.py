# SPDX-FileCopyrightText: 2024-2026 Stanford University
# SPDX-License-Identifier: AGPL-3.0-or-later

"""OpenCell-specific DataManager subclass with material and cell convenience methods."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from steer_core.Data.DataManager import DataManager
from steer_core.Constants.Units import H_TO_S, mA_TO_A, G_TO_KG


# ---------------------------------------------------------------------------
# Domain-specific table constants
# ---------------------------------------------------------------------------

MATERIAL_TABLES: set[str] = {
    "anode_materials",
    "cathode_materials",
    "binder_materials",
    "conductive_additive_materials",
    "current_collector_materials",
    "insulation_materials",
    "separator_materials",
    "tape_materials",
    "prismatic_container_materials",
}

CELL_TABLES: set[str] = {
    "cell_references",
    "teardowns",
    "user_designs",
    "cell_submissions",
}

ALL_TABLES: set[str] = MATERIAL_TABLES | CELL_TABLES

MATERIAL_META_COLS: list[str] = ["name", "date", "version", "reference"]

CELL_META_COLS: list[str] = [
    "name",
    "form_factor",
    "internal_construction",
    "date_created",
    "version",
    "chemistry",
    "visibility",
    "owner_id",
]


def register_opencell_tables() -> None:
    """Register the OpenCell table names on the base ``DataManager``.

    Called automatically when ``steer_opencell_design.Data`` is imported.
    Safe to call multiple times.
    """
    DataManager.register_tables(
        material_tables=MATERIAL_TABLES,
        cell_tables=CELL_TABLES,
        material_meta_cols=MATERIAL_META_COLS,
        cell_meta_cols=CELL_META_COLS,
    )


class OpenCellDataManager(DataManager):
    """DataManager with OpenCell-specific convenience methods.

    Provides material getters, cell fork/publish/submit operations, and
    the ``read_half_cell_curve`` utility.
    """

    def __init__(self, jwt_token: str | None = None):
        # Ensure tables are registered even if __init__.py wasn't imported
        register_opencell_tables()
        super().__init__(jwt_token)

    # -- Material-specific getters -----------------------------------------

    def _get_materials(self, table_name: str, most_recent: bool = True) -> pd.DataFrame:
        params = {}
        if not most_recent:
            params["most_recent"] = "false"
        data = self._request(
            "GET", f"/materials/{table_name}", auth_required=False, params=params
        )
        items = data.get("items", [])
        if not items:
            return pd.DataFrame(columns=MATERIAL_META_COLS)
        df = pd.DataFrame(items)
        available = [c for c in MATERIAL_META_COLS if c in df.columns]
        return df[available].reset_index(drop=True)

    def get_current_collector_materials(self, most_recent: bool = True) -> pd.DataFrame:
        return self._get_materials("current_collector_materials", most_recent)

    def get_insulation_materials(self, most_recent: bool = True) -> pd.DataFrame:
        return self._get_materials("insulation_materials", most_recent)

    def get_cathode_materials(self, most_recent: bool = True) -> pd.DataFrame:
        return self._get_materials("cathode_materials", most_recent)

    def get_anode_materials(self, most_recent: bool = True) -> pd.DataFrame:
        return self._get_materials("anode_materials", most_recent)

    def get_binder_materials(self, most_recent: bool = True) -> pd.DataFrame:
        return self._get_materials("binder_materials", most_recent)

    def get_conductive_additive_materials(self, most_recent: bool = True) -> pd.DataFrame:
        return self._get_materials("conductive_additive_materials", most_recent)

    def get_separator_materials(self, most_recent: bool = True) -> pd.DataFrame:
        return self._get_materials("separator_materials", most_recent)

    def get_tape_materials(self, most_recent: bool = True) -> pd.DataFrame:
        return self._get_materials("tape_materials", most_recent)

    def get_prismatic_container_materials(self, most_recent: bool = True) -> pd.DataFrame:
        return self._get_materials("prismatic_container_materials", most_recent)

    # -- Cell operations ---------------------------------------------------

    def fork_cell(self, source_table: str, source_name: str, new_name: str) -> dict:
        """Fork *source_name* into ``user_designs`` with *new_name*."""
        encoded = self._encode(source_name)
        return self._request(
            "POST",
            f"/cells/{source_table}/{encoded}/fork",
            auth_required=True,
            json={"name": new_name},
        )

    def publish_cell(
        self,
        source_table: str,
        source_name: str,
        new_name: str,
        target_table: str | None = None,
    ) -> dict:
        """Publish *source_name* with *new_name* (admin only)."""
        encoded = self._encode(source_name)
        body: dict = {"name": new_name}
        if target_table:
            body["target_table"] = target_table
        return self._request(
            "POST",
            f"/cells/{source_table}/{encoded}/publish",
            auth_required=True,
            json=body,
        )

    def submit_cell(self, source_table: str, source_name: str) -> dict:
        """Submit a cell for admin review."""
        encoded = self._encode(source_name)
        return self._request(
            "POST",
            f"/cells/{source_table}/{encoded}/submit",
            auth_required=True,
        )

    def reject_cell(self, table_name: str, name: str) -> None:
        """Reject (hard-delete) a submission (admin only)."""
        encoded = self._encode(name)
        self._request(
            "POST",
            f"/cells/{table_name}/{encoded}/reject",
            auth_required=True,
        )

    def check_name_available(self, name: str) -> bool:
        """Return ``True`` if *name* is available across all cell tables."""
        encoded = self._encode(name)
        data = self._request(
            "GET", f"/cells/check-name/{encoded}", auth_required=False
        )
        return data.get("available", False)

    # -- Static utilities --------------------------------------------------

    @staticmethod
    def read_half_cell_curve(half_cell_path: str | Path) -> pd.DataFrame:
        """Read a half-cell voltage curve from a local CSV file.

        Parameters
        ----------
        half_cell_path : str or Path
            Path to the CSV file.

        Returns
        -------
        pd.DataFrame
            Columns: specific_capacity, voltage, step_id.
        """
        try:
            data = pd.read_csv(half_cell_path)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Could not find the file at {half_cell_path}"
            )
        except Exception as e:
            raise ValueError(
                f"Error reading file at {half_cell_path}: {str(e)}"
            )

        if "Specific Capacity (mAh/g)" not in data.columns:
            raise ValueError(
                "The file must have a column named 'Specific Capacity (mAh/g)'"
            )
        if "Voltage (V)" not in data.columns:
            raise ValueError(
                "The file must have a column named 'Voltage (V)'"
            )
        if "Step_ID" not in data.columns:
            raise ValueError(
                "The file must have a column named 'Step_ID'"
            )

        data = (
            data.rename(
                columns={
                    "Specific Capacity (mAh/g)": "specific_capacity",
                    "Voltage (V)": "voltage",
                    "Step_ID": "step_id",
                }
            )
            .assign(
                specific_capacity=lambda x: x["specific_capacity"]
                * (H_TO_S * mA_TO_A / G_TO_KG)
            )
            .filter(["specific_capacity", "voltage", "step_id"])
            .groupby(["specific_capacity", "step_id"], group_keys=False)["voltage"]
            .max()
            .reset_index()
            .sort_values(["step_id", "specific_capacity"])
        )

        return data
