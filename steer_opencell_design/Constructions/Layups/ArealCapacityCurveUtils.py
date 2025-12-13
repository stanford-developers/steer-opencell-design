import numpy as np
from typing import Tuple


CAPACITY_INTERPOLATION_POINTS = 100  # Number of points for capacity curve interpolation


class ArealCapacityCurveMixin:

    @staticmethod
    def _compute_areal_full_cell_curve(cathode_areal_curve: np.ndarray, anode_areal_curve: np.ndarray) -> Tuple[float, np.ndarray]:
        """
        Compute the full-cell areal capacity curve from cathode and anode half-cell curves.

        Parameters
        ----------
        cathode_areal_curve : np.ndarray
            Cathode half-cell curve with shape (n, 3) containing [capacity, voltage, direction].
        anode_areal_curve : np.ndarray
            Anode half-cell curve with shape (n, 3) containing [capacity, voltage, direction].

        Returns
        -------
        Tuple[float, np.ndarray]
            A tuple containing:
            - np_ratio : float
                The n/p ratio (anode to cathode capacity ratio).
            - areal_capacity_curve : np.ndarray
                The full-cell capacity curve with shape (2*n_points, 3).
        """
        # Calculate n/p ratio using numpy operations
        max_cap_cathode = cathode_areal_curve[:, 0].max()
        max_cap_anode = anode_areal_curve[:, 0].max()
        np_ratio = max_cap_anode / max_cap_cathode

        # Create boolean masks once for reuse
        cathode_charge_mask = cathode_areal_curve[:, 2] == 1
        cathode_discharge_mask = cathode_areal_curve[:, 2] == -1
        anode_charge_mask = anode_areal_curve[:, 2] == 1
        anode_discharge_mask = anode_areal_curve[:, 2] == -1

        # Split curves using masks
        cathode_charge = cathode_areal_curve[cathode_charge_mask]
        cathode_discharge = cathode_areal_curve[cathode_discharge_mask]
        anode_charge = anode_areal_curve[anode_charge_mask]
        anode_discharge = anode_areal_curve[anode_discharge_mask]

        # Calculate overlapping ranges in one go
        charge_x_min = max(cathode_charge[:, 0].min(), anode_charge[:, 0].min())
        charge_x_max = min(cathode_charge[:, 0].max(), anode_charge[:, 0].max())
        discharge_x_min = max(cathode_discharge[:, 0].min(), anode_discharge[:, 0].min())
        discharge_x_max = min(cathode_discharge[:, 0].max(), anode_discharge[:, 0].max())

        # Sort once using argsort
        cathode_charge_idx = cathode_charge[:, 0].argsort()
        cathode_discharge_idx = cathode_discharge[:, 0].argsort()
        anode_charge_idx = anode_charge[:, 0].argsort()
        anode_discharge_idx = anode_discharge[:, 0].argsort()

        # Create common x arrays for interpolation
        n_points = CAPACITY_INTERPOLATION_POINTS
        charge_x_common = np.linspace(charge_x_min, charge_x_max, n_points)
        discharge_x_common = np.linspace(discharge_x_min, discharge_x_max, n_points)

        # Interpolate all voltages
        cathode_charge_voltage = np.interp(
            charge_x_common, 
            cathode_charge[cathode_charge_idx, 0], 
            cathode_charge[cathode_charge_idx, 1]
        )
        cathode_discharge_voltage = np.interp(
            discharge_x_common,
            cathode_discharge[cathode_discharge_idx, 0],
            cathode_discharge[cathode_discharge_idx, 1],
        )
        anode_charge_voltage = np.interp(
            charge_x_common, 
            anode_charge[anode_charge_idx, 0], 
            anode_charge[anode_charge_idx, 1]
        )
        anode_discharge_voltage = np.interp(
            discharge_x_common,
            anode_discharge[anode_discharge_idx, 0],
            anode_discharge[anode_discharge_idx, 1],
        )

        # Calculate full-cell voltages
        charge_voltage_full = cathode_charge_voltage - anode_charge_voltage
        discharge_voltage_full = cathode_discharge_voltage - anode_discharge_voltage

        # Pre-allocate output array for better performance
        total_points = 2 * n_points
        areal_capacity_curve = np.empty((total_points, 3))
        
        # Fill charge curve (first half)
        areal_capacity_curve[:n_points, 0] = charge_x_common
        areal_capacity_curve[:n_points, 1] = charge_voltage_full
        areal_capacity_curve[:n_points, 2] = 1
        
        # Fill discharge curve (second half, reversed)
        areal_capacity_curve[n_points:, 0] = discharge_x_common[::-1]
        areal_capacity_curve[n_points:, 1] = discharge_voltage_full[::-1]
        areal_capacity_curve[n_points:, 2] = -1

        return np_ratio, areal_capacity_curve

