import plotly.colors as pc
import numpy as np
import pandas as pd

from typing import Tuple, Type
from OpenCell.Constants import ALLOWED_REFERENCE
from scipy.interpolate import PchipInterpolator

class ColorMixin:
    """
    A class to manage colors, including conversion between hex and RGB formats,
    and generating color gradients.
    """
    @staticmethod
    def rgb_tuple_to_hex(rgb):
        return '#{:02x}{:02x}{:02x}'.format(*rgb)

    @staticmethod
    def get_colorway(color1, color2, n):
        """
        Generate a list of n hex colors interpolated between two HTML hex colors.

        Parameters
        ----------
        color1 : str
            The first color in HTML hex format (e.g., '#ff0000').
        color2 : str
            The second color in HTML hex format (e.g., '#0000ff').
        n : int
            The number of colors to generate in the gradient.
        """
        # Convert hex to RGB (0–255)
        rgb1 = np.array(pc.hex_to_rgb(color1))
        rgb2 = np.array(pc.hex_to_rgb(color2))

        # Interpolate and convert to hex
        colors = [
            ColorMixin.rgb_tuple_to_hex(tuple(((1 - t) * rgb1 + t * rgb2).astype(int)))
            for t in np.linspace(0, 1, n)
        ]

        return colors


class CoordinateMixin:
    """
    A class to manage and manipulate 3D coordinates.
    Provides methods for rotation, area calculation, and coordinate ordering.
    """
    @staticmethod
    def rotate_coordinates(coords: np.ndarray, axis: str, angle: float, center: tuple = None) -> np.ndarray:
        """
        Rotate a (N, 3) NumPy array of 3D coordinates around the specified axis.
        Can handle coordinates with None values (preserves None positions).

        :param coords: NumPy array of shape (N, 3), where columns are x, y, z
        :param axis: Axis to rotate around ('x', 'y', or 'z')
        :param angle: Angle in degrees
        :param center: Point to rotate around as (x, y, z) tuple. If None, rotates around origin.
        :return: Rotated NumPy array of shape (N, 3)
        """
        if coords.shape[1] != 3:
            raise ValueError("Input array must have shape (N, 3) for x, y, z coordinates")

        # Validate center parameter
        if center is not None:
            if not isinstance(center, (tuple, list)) or len(center) != 3:
                raise ValueError("Center must be a tuple or list of 3 coordinates (x, y, z)")
            if not all(isinstance(coord, (int, float)) for coord in center):
                raise TypeError("All center coordinates must be numbers")
            center = np.array(center, dtype=float)

        # Check if we have None values
        has_nones = np.any(pd.isna(coords[:, 0])) if hasattr(pd, 'isna') else np.any(coords[:, 0] == None)
        
        if has_nones:
            # Create a copy to preserve original
            result = coords.copy()
            
            # Find non-None rows
            x_is_none = pd.isna(coords[:, 0]) if hasattr(pd, 'isna') else (coords[:, 0] == None)
            valid_mask = ~x_is_none
            
            if np.any(valid_mask):
                # Extract valid coordinates and convert to float
                valid_coords = coords[valid_mask].astype(float)
                
                # Apply rotation to valid coordinates
                rotated_valid = CoordinateMixin._rotate_around_center(valid_coords, axis, angle, center)
                
                # Put rotated coordinates back in result
                result[valid_mask] = rotated_valid
                
            return result
        
        else:
            # No None values - use rotation with center
            return CoordinateMixin._rotate_around_center(coords.astype(float), axis, angle, center)

    @staticmethod
    def _rotate_around_center(coords: np.ndarray, axis: str, angle: float, center: np.ndarray = None) -> np.ndarray:
        """
        Rotate coordinates around a specified center point.
        
        :param coords: NumPy array of shape (N, 3) with valid coordinates
        :param axis: Axis to rotate around ('x', 'y', or 'z')
        :param angle: Angle in degrees
        :param center: Center point as np.array of shape (3,). If None, rotates around origin.
        :return: Rotated coordinates
        """
        if center is None:
            # Rotate around origin - use existing method
            return CoordinateMixin._rotate_valid_coordinates(coords, axis, angle)
        
        # Translate coordinates to center at origin
        translated_coords = coords - center
        
        # Rotate around origin
        rotated_coords = CoordinateMixin._rotate_valid_coordinates(translated_coords, axis, angle)
        
        # Translate back to original position
        return rotated_coords + center

    @staticmethod
    def build_square_array(x: float, y: float, x_width: float, y_width: float) -> Tuple[np.ndarray, np.ndarray]:
        """
        Build a NumPy array representing a square or rectangle defined by its bottom-left corner (x, y)
        and its width and height.

        Parameters
        ----------
        x : float
            The x-coordinate of the bottom-left corner of the square.
        y : float
            The y-coordinate of the bottom-left corner of the square.
        x_width : float
            The width of the square.
        y_width : float
            The height of the square.
        """
        x_coords = [x, x, x + x_width, x + x_width, x]
        y_coords = [y, y + y_width, y + y_width, y, y]
        return x_coords, y_coords

    @staticmethod
    def order_coordinates_clockwise(df: pd.DataFrame, plane='xy') -> pd.DataFrame:

        axis_1 = plane[0]
        axis_2 = plane[1]

        cx = df[axis_1].mean()
        cy = df[axis_2].mean()

        angles = np.arctan2(df[axis_2] - cy, df[axis_1] - cx)

        df['angle'] = angles
        df_sorted = df.sort_values(by='angle').drop(columns='angle').reset_index(drop=True)

        return df_sorted

    @staticmethod    
    def _rotate_valid_coordinates(coords: np.ndarray, axis: str, angle: float) -> np.ndarray:
        """
        Rotate coordinates without None values using rotation matrices.
        """
        angle_rad = np.radians(angle)
        cos_a = np.cos(angle_rad)
        sin_a = np.sin(angle_rad)

        if axis == 'x':
            R = np.array([[1, 0, 0],
                        [0, cos_a, -sin_a],
                        [0, sin_a, cos_a]])
        elif axis == 'y':
            R = np.array([[cos_a, 0, sin_a],
                        [0, 1, 0],
                        [-sin_a, 0, cos_a]])
        elif axis == 'z':
            R = np.array([[cos_a, -sin_a, 0],
                        [sin_a, cos_a, 0],
                        [0, 0, 1]])
        else:
            raise ValueError("Axis must be 'x', 'y', or 'z'.")

        return coords @ R.T
    
    @staticmethod
    def _calculate_single_area(x: np.ndarray, y: np.ndarray) -> float:
        """
        Calculate the area of a single closed shape using the shoelace formula.
        """
        if len(x) < 3 or len(y) < 3:
            raise ValueError("Trace must contain at least 3 points to form a closed shape.")
        
        # Convert to float arrays to avoid object dtype issues
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)
        
        # Ensure the shape is closed by appending the first point to the end
        if (x[0], y[0]) != (x[-1], y[-1]):
            x = np.append(x, x[0])
            y = np.append(y, y[0])

        # Calculate the area using the shoelace formula
        area = 0.5 * np.abs(np.dot(x[:-1], y[1:]) - np.dot(y[:-1], x[1:]))

        return float(area)
    
    @staticmethod
    def get_area_from_points(x: np.ndarray, y: np.ndarray) -> float:
        """
        Calculate the area of a closed shape defined by the coordinates in x and y using the shoelace formula.
        Can handle multiple shapes separated by None values.
        """
        # Convert to numpy arrays and handle object dtype
        x = np.asarray(x)
        y = np.asarray(y)
        
        # Check if we have None values (multiple shapes)
        x_is_none = pd.isna(x) if hasattr(pd, 'isna') else (x == None)
        
        if np.any(x_is_none):
            total_area = 0.0
            
            # Find None indices to split the shapes
            none_indices = np.where(x_is_none)[0]
            start_idx = 0
            
            # Process each shape segment
            for none_idx in none_indices:
                if none_idx > start_idx:
                    # Extract segment coordinates
                    segment_x = x[start_idx:none_idx]
                    segment_y = y[start_idx:none_idx]
                    
                    # Calculate area for this segment if it has enough points
                    if len(segment_x) >= 3:
                        area = CoordinateMixin._calculate_single_area(segment_x, segment_y)
                        total_area += area
                        
                start_idx = none_idx + 1
            
            # Handle the last segment if it exists
            if start_idx < len(x):
                segment_x = x[start_idx:]
                segment_y = y[start_idx:]
                if len(segment_x) >= 3:
                    area = CoordinateMixin._calculate_single_area(segment_x, segment_y)
                    total_area += area
                    
            return total_area
        
        else:
            # Single shape - use original logic
            return CoordinateMixin._calculate_single_area(x, y)

    @staticmethod
    def extrude_footprint(
            x: np.ndarray, 
            y: np.ndarray,
            datum: np.ndarray,
            thickness: float
        ) -> Tuple[
            np.ndarray, 
            np.ndarray, 
            np.ndarray, 
            np.ndarray
        ]:
        """
        Extrude the 2D footprint to 3D and label each point with its side ('a' or 'b'), with 'a' being the top side and 'b' the bottom side.

        Parameters
        ----------
        x : np.ndarray
            Array of x coordinates (length N)
        y : np.ndarray
            Array of y coordinates (length N)
        datum : np.ndarray
            Datum point for extrusion (shape (3,))
        thickness : float
            Thickness of the extrusion

        Returns
        -------
        Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]
            Arrays of x, y, z, and side for both A and B sides (each of length 2N)
        """
        z_a = datum[2] + thickness / 2
        z_b = datum[2] - thickness / 2

        # Repeat x and y coordinates for both sides
        x_full = np.concatenate([x, x])
        y_full = np.concatenate([y, y])
        z_full = np.concatenate([np.full_like(x, z_a), np.full_like(x, z_b)])
        side_full = np.array(['a'] * len(x) + ['b'] * len(x))

        return x_full, y_full, z_full, side_full
    
    @staticmethod
    def remove_skip_coat_area(
        x_coords: np.ndarray, 
        y_coords: np.ndarray, 
        weld_tab_positions: np.ndarray, 
        skip_coat_width: float
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Remove skip coat areas around weld tab positions from coordinates.
        
        Parameters
        ----------
        x_coords : np.ndarray
            Array of x coordinates defining the boundary
        y_coords : np.ndarray  
            Array of y coordinates defining the boundary
        weld_tab_positions : np.ndarray
            Array of x positions where weld tabs are located
        skip_coat_width : float
            Width of the skip coat area around each weld tab
            
        Returns
        -------
        Tuple[np.ndarray, np.ndarray]
            Modified x and y coordinate arrays with None separators between segments
        """
        if len(x_coords) == 0 or len(y_coords) == 0:
            return np.array([]), np.array([])
        
        x_min, x_max = np.min(x_coords), np.max(x_coords)
        y_min, y_max = np.min(y_coords), np.max(y_coords)
        
        # Filter weld tab positions to only include those within bounds
        valid_positions = weld_tab_positions[
            (weld_tab_positions + skip_coat_width >= x_min) & (weld_tab_positions - skip_coat_width <= x_max)
        ]
        
        # If no valid positions, return original rectangle
        if len(valid_positions) == 0:
            rect_x = [x_min, x_max, x_max, x_min, x_min]
            rect_y = [y_min, y_min, y_max, y_max, y_min]
            return np.array(rect_x, dtype=object), np.array(rect_y, dtype=object)
        
        # Sort weld tab cut positions
        cuts = np.sort(valid_positions)
        half_width = skip_coat_width / 2
        
        # Build kept horizontal segments by removing [cut - half, cut + half] around each cut
        segments = []
        start = x_min
        
        for cut in cuts:
            end = cut - half_width
            if end > start:
                segments.append((start, end))
            start = cut + half_width
        
        # Add final segment if there's remaining space
        if start < x_max:
            segments.append((start, x_max))
        
        # Build rectangles for each kept segment with None separators
        x_result = []
        y_result = []
        
        for i, (segment_start, segment_end) in enumerate(segments):
            # Create rectangle coordinates: bottom-left -> bottom-right -> top-right -> top-left -> close
            rect_x = [segment_start, segment_end, segment_end, segment_start, segment_start]
            rect_y = [y_min, y_min, y_max, y_max, y_min]
            
            x_result.extend(rect_x)
            y_result.extend(rect_y)
            
            # Add None separator (except for the last segment)
            if i < len(segments) - 1:  # Fixed: use index comparison
                x_result.append(None)
                y_result.append(None)
        
        return np.array(x_result, dtype=object), np.array(y_result, dtype=object)


class ValidationMixin:

    @staticmethod
    def validate_formulations(value: Type) -> None:
        """
        Validate that a value is an instance of _ElectrodeFormulation.

        Parameters
        ----------
        value : Type
            The value to validate.

        Raises
        ------
        TypeError
            If the value is not an instance of _ElectrodeFormulation.
        """
        from OpenCell.Formulations.ElectrodeFormulations import _ElectrodeFormulation

        if not isinstance(value, _ElectrodeFormulation):
            raise TypeError(f"Expected an instance of _ElectrodeFormulation. Provided: {type(value)}.")

    @staticmethod
    def validate_insulation_material(value: Type) -> None:
        """
        Validate that a value is an instance of InsulationMaterial.

        Parameters
        ----------
        value : Type
            The value to validate.

        Raises
        ------
        TypeError
            If the value is not an instance of InsulationMaterial.
        """
        from OpenCell.Materials.RawMaterials import InsulationMaterial

        if not isinstance(value, InsulationMaterial):
            raise TypeError(f"Expected an instance of InsulationMaterial. Provided: {type(value)}.")

    @staticmethod
    def validate_current_collector(value: Type) -> None:
        """
        Validate that a value is an instance of _CurrentCollector.
        
        Parameters
        ----------
        value : Type
            The value to validate.

        Raises
        ------
        TypeError
            If the value is not an instance of _CurrentCollector.
        """
        from OpenCell.Materials.CurrentCollectors import _CurrentCollector

        if not isinstance(value, _CurrentCollector):
            raise TypeError(f"Expected an instance of _CurrentCollector. Provided: {type(value)}.")

    @staticmethod
    def validate_active_material(value: Type) -> None:
        """
        Validate that a value is an instance of _ActiveMaterial.
        
        Parameters
        ----------
        value : Type
            The value to validate.

        Raises
        ------
        TypeError
            If the value is not an instance of _ActiveMaterial.
        """
        from OpenCell.Materials.ElectrodeMaterials import _ActiveMaterial

        if not isinstance(value, _ActiveMaterial):
            raise TypeError(f"Expected an instance of _ActiveMaterial. Provided: {type(value)}.")

    @staticmethod
    def validate_binder(value: Type) -> None:
        """
        Validate that a value is an instance of Binder.
        
        Parameters
        ----------
        value : Type
            The value to validate.

        Raises
        ------
        TypeError
            If the value is not an instance of Binder.
        """
        from OpenCell.Materials.ElectrodeMaterials import Binder

        if not isinstance(value, Binder):
            raise TypeError(f"Expected an instance of Binder. Provided: {type(value)}.")
        
    @staticmethod
    def validate_conductive_additive(value: Type) -> None:
        """
        Validate that a value is an instance of ConductiveAdditive.
        
        Parameters
        ----------
        value : Type
            The value to validate.

        Raises
        ------
        TypeError
            If the value is not an instance of ConductiveAdditive.
        """
        from OpenCell.Materials.ElectrodeMaterials import ConductiveAdditive

        if not isinstance(value, ConductiveAdditive):
            raise TypeError(f"Expected an instance of ConductiveAdditive. Provided: {type(value)}.")

    @staticmethod
    def validate_percentage(value: float, name: str) -> None:
        """
        Validate that a value is a percentage (between 0 and 100).

        Parameters
        ----------
        value : float
            The value to validate.
        name : str
            The name of the parameter for error messages.

        Raises
        ------
        ValueError
            If the value is not a percentage.
        """
        if not isinstance(value, (int, float)):
            raise TypeError(f"{name} must be a number. Provided: {value}.")

        if not (0 <= value <= 100):
            raise ValueError(f"{name} must be a percentage between 0 and 100. Provided: {value}.")

    @staticmethod
    def validate_fraction(value: float, name: str) -> None:
        """
        Validate that a value is a fraction (between 0 and 1).

        Parameters
        ----------
        value : float
            The value to validate.
        name : str
            The name of the parameter for error messages.

        Raises
        ------
        ValueError
            If the value is not a fraction.
        """
        if not (0 <= value <= 1):
            raise ValueError(f"{name} must be a fraction between 0 and 1. Provided: {value}.")

    @staticmethod
    def validate_pandas_dataframe(
        df: pd.DataFrame, 
        name: str,
        column_names: list = None
    ) -> None:
        """
        Validate that the input is a pandas DataFrame.

        Parameters
        ----------
        df : pd.DataFrame
            The DataFrame to validate.
        name : str
            The name of the DataFrame for error messages.

        Raises
        ------
        TypeError
            If the input is not a pandas DataFrame.
        """
        if not isinstance(df, pd.DataFrame):
            raise TypeError(f"{name} must be a pandas DataFrame. Provided: {type(df)}.")

        if column_names is not None:
            missing_columns = [col for col in column_names if col not in df.columns]
            if missing_columns:
                raise ValueError(f"{name} is missing required columns: {missing_columns}. "
                                 f"Available columns: {df.columns.tolist()}.")

    @staticmethod
    def validate_electrochemical_reference(reference: str) -> None:
        """
        Validate the electrochemical reference electrode.

        Parameters
        ----------
        reference : str
            The reference electrode to validate.

        Raises
        ------
        ValueError
            If the reference is not a valid electrochemical reference.
        """
        ValidationMixin.validate_string(reference, "Electrochemical reference")

        if reference not in ALLOWED_REFERENCE:
            raise ValueError(f"Invalid electrochemical reference: {reference}. "
                             f"Must be one of {ALLOWED_REFERENCE}.")

    @staticmethod
    def validate_datum(datum: np.ndarray) -> None:
        """
        Validate the datum point for extrusion.

        Parameters
        ----------
        datum : np.ndarray
            Datum point for extrusion (shape (3,))

        Raises
        ------
        ValueError
            If the datum does not have exactly 3 coordinates.
        """
        if type(datum) is not tuple and len(datum) != 3:
            raise ValueError("Datum must be a 3D point with exactly 3 coordinates.")
        
        if not all(isinstance(coord, (int, float)) for coord in datum):
            raise TypeError("All coordinates in datum must be numbers.")
    
    @staticmethod
    def validate_current_collector_material(material: Type) -> None:
        """
        Validate the current collector material.

        Parameters
        ----------
        material : str
            The material to validate.

        Raises
        ------
        ValueError
            If the material is not a valid current collector material.
        """
        from OpenCell.Materials.RawMaterials import CurrentCollectorMaterial

        if type(material) is not CurrentCollectorMaterial:

            raise ValueError(f"Invalid current collector material: {material}. "
                             "Must be an instance of CurrentCollectorMaterial.")

    @staticmethod
    def validate_weld_tab(tab) -> None:
        """
        Validate the weld tab.

        Parameters
        ----------
        tab : WeldTab
            The weld tab to validate.

        Raises
        ------
        ValueError
            If the weld tab is not valid.
        """
        from OpenCell.Materials.CurrentCollectors import WeldTab
        
        if not isinstance(tab, WeldTab):
            raise ValueError(f"Invalid weld tab: {tab}. Must be an instance of WeldTab.")

    @staticmethod
    def validate_positive_float(value: float, name: str) -> None:
        """
        Validate that a value is a positive float.

        Parameters
        ----------
        value : float
            The value to validate.
        name : str
            The name of the parameter for error messages.

        Raises
        ------
        ValueError
            If the value is not a positive float.
        """
        if not isinstance(value, (int, float)):
            raise ValueError(f"{name} must be a positive float. Provided: {value}.")
        
    @staticmethod
    def validate_string(value: str, name: str) -> None:
        """
        Validate that a value is a string.

        Parameters
        ----------
        value : str
            The value to validate.
        name : str
            The name of the parameter for error messages.

        Raises
        ------
        TypeError
            If the value is not a string.
        """
        if not isinstance(value, str):
            raise TypeError(f"{name} must be a string. Provided: {value}.")
        
    @staticmethod
    def validate_two_iterable_of_floats(value: tuple, name: str) -> None:
        """
        Validate that a value is a tuple of two iterables.

        Parameters
        ----------
        value : tuple
            The value to validate.
        name : str
            The name of the parameter for error messages.

        Raises
        ------
        TypeError
            If the value is not a tuple of two floats.
        """
        # Accept both tuples and lists
        if not isinstance(value, (tuple, list)) or len(value) != 2:
            raise TypeError(f"{name} must be a tuple or list of two numbers. Provided: {value}.")
        
        # Check if all values are numeric (int or float)
        if not all(isinstance(v, (int, float)) for v in value):
            raise TypeError(f"{name} must be a tuple or list of two numbers. Provided: {value}.")
        
        # Check if all values are non-negative
        if not all(v >= 0 for v in value):
            raise ValueError(f"{name} must be a tuple or list of two non-negative numbers. Provided: {value}.")
        
    @staticmethod
    def validate_positive_float_list(value: list, name: str) -> None:
        """
        Validate that a value is a list of positive floats.

        Parameters
        ----------
        value : list
            The value to validate.
        name : str
            The name of the parameter for error messages.

        Raises
        ------
        TypeError
            If the value is not a list of positive floats.
        """
        if not isinstance(value, list) or not all(isinstance(v, (int, float)) and v > 0 for v in value):
            raise TypeError(f"{name} must be a list of positive floats. Provided: {value}.")
        
        if len(value) == 0:
            raise ValueError(f"{name} must not be an empty list. Provided: {value}.")
        

class DataMixin:
    """
    A mixin class to handle data processing and validation for electrode materials.
    Provides methods to calculate properties, check curve directions, and process half-cell curves.
    """
    @staticmethod
    def enforce_monotonicity(array: np.ndarray) -> np.ndarray:
        """
        Enforces a monotonic version of the input array.
        If the array is not monotonic, it is smoothed using cumulative max/min.
        """
        x = np.arange(len(array))
        diff = np.diff(array)

        if np.all(diff >= 0):
            return array  # Already monotonic increasing

        if np.all(diff <= 0):
            return array  # Already monotonic decreasing, reverse it

        # Determine general trend (ascending or descending)
        ascending = array[-1] >= array[0]

        # Sort by x so that PCHIP works (PCHIP requires increasing x)
        # We'll smooth the array using PCHIP, then enforce monotonicity
        interpolator = PchipInterpolator(x, array, extrapolate=False)
        new_array = interpolator(x)

        # Enforce strict monotonicity post-smoothing
        if ascending:
            new_array = np.maximum.accumulate(new_array)
        else:
            new_array = np.minimum.accumulate(new_array)

        return new_array
    