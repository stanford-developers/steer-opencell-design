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

def get_area_from_trace(trace: go.Scatter) -> float:
        """
        Calculate the area of a closed shape defined by a Plotly Scatter trace.
        """
        x = np.array(trace.x)
        y = np.array(trace.y)

        if len(x) < 3 or len(y) < 3:
            raise ValueError("Trace must contain at least 3 points to form a closed shape.")
        
        # Ensure the shape is closed by appending the first point to the end
        if (x[0], y[0]) != (x[-1], y[-1]):
            x = np.append(x, x[0])
            y = np.append(y, y[0])

        # Calculate the area using the shoelace formula
        area = 0.5 * np.abs(np.dot(x[:-1], y[1:]) - np.dot(y[:-1], x[1:]))

        return float(area)

def build_square_df(x: float, y: float, x_width: float, y_width: float) -> pd.DataFrame:
    """
    Build a DataFrame representing a square or rectangle defined by its bottom-left corner (x, y)
    and its width and height.

    :param x: float, x-coordinate of the bottom-left corner
    :param y: float, y-coordinate of the bottom-left corner
    :param x_width: float, width of the square/rectangle
    :param y_width: float, height of the square/rectangle
    """
    return pd.DataFrame({
        'x': [x, x, x + x_width, x + x_width, x],
        'y': [y, y + y_width, y + y_width, y, y]
    })

def rotate_coordinates(df: pd.DataFrame, axis: str, angle: float) -> pd.DataFrame:
    """
    Rotate the 3D coordinates ('x', 'y', 'z') in a DataFrame around the specified axis.

    :param df: DataFrame containing at least 'x', 'y', 'z' columns
    :param axis: Axis to rotate around ('x', 'y', or 'z')
    :param angle: Angle in degrees
    :return: A new DataFrame with rotated coordinates and other columns unchanged
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

    # Copy DataFrame to avoid modifying in-place
    df_rotated = df.copy()

    # Perform rotation
    coords = df[['x', 'y', 'z']].to_numpy()
    rotated_coords = coords @ R.T

    # Assign rotated values back
    df_rotated[['x', 'y', 'z']] = rotated_coords

    return df_rotated

