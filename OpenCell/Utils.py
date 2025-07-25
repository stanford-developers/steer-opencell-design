import plotly.colors as pc
import numpy as np
import plotly.graph_objects as go
import pandas as pd
from typing import Tuple

def rgb_tuple_to_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(*rgb)

def get_colorway(color1, color2, n):
    """
    Generate a list of n hex colors interpolated between two HTML hex colors.

    :param color1: str, hex color (e.g., '#0000ff')
    :param color2: str, hex color (e.g., '#ffa500')
    :param n: int, number of steps
    :return: list of hex color strings
    """
    # Convert hex to RGB (0–255)
    rgb1 = np.array(pc.hex_to_rgb(color1))
    rgb2 = np.array(pc.hex_to_rgb(color2))

    # Interpolate and convert to hex
    colors = [
        rgb_tuple_to_hex(tuple(((1 - t) * rgb1 + t * rgb2).astype(int)))
        for t in np.linspace(0, 1, n)
    ]

    return colors

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
                    area = _calculate_single_area(segment_x, segment_y)
                    total_area += area
                    
            start_idx = none_idx + 1
        
        # Handle the last segment if it exists
        if start_idx < len(x):
            segment_x = x[start_idx:]
            segment_y = y[start_idx:]
            if len(segment_x) >= 3:
                area = _calculate_single_area(segment_x, segment_y)
                total_area += area
                
        return total_area
    
    else:
        # Single shape - use original logic
        return _calculate_single_area(x, y)

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

def rotate_coordinates(coords: np.ndarray, axis: str, angle: float) -> np.ndarray:
    """
    Rotate a (N, 3) NumPy array of 3D coordinates around the specified axis.
    Can handle coordinates with None values (preserves None positions).

    :param coords: NumPy array of shape (N, 3), where columns are x, y, z
    :param axis: Axis to rotate around ('x', 'y', or 'z')
    :param angle: Angle in degrees
    :return: Rotated NumPy array of shape (N, 3)
    """
    if coords.shape[1] != 3:
        raise ValueError("Input array must have shape (N, 3) for x, y, z coordinates")

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
            rotated_valid = _rotate_valid_coordinates(valid_coords, axis, angle)
            
            # Put rotated coordinates back in result
            result[valid_mask] = rotated_valid
            
        return result
    
    else:
        # No None values - use original logic
        return _rotate_valid_coordinates(coords.astype(float), axis, angle)

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

def order_coordinates_clockwise(df: pd.DataFrame, plane='xy') -> pd.DataFrame:

        axis_1 = plane[0]
        axis_2 = plane[1]

        cx = df[axis_1].mean()
        cy = df[axis_2].mean()

        angles = np.arctan2(df[axis_2] - cy, df[axis_1] - cx)

        df['angle'] = angles
        df_sorted = df.sort_values(by='angle').drop(columns='angle').reset_index(drop=True)

        return df_sorted