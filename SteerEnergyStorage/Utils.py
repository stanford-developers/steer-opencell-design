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
        """
        if len(x) < 3 or len(y) < 3:
            raise ValueError("Trace must contain at least 3 points to form a closed shape.")
        
        # Ensure the shape is closed by appending the first point to the end
        if (x[0], y[0]) != (x[-1], y[-1]):
            x = np.append(x, x[0])
            y = np.append(y, y[0])

        # Calculate the area using the shoelace formula
        area = 0.5 * np.abs(np.dot(x[:-1], y[1:]) - np.dot(y[:-1], x[1:]))

        return float(area)

def build_square_array(x: float, y: float, x_width: float, y_width: float) -> np.ndarray:
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

    :param coords: NumPy array of shape (N, 3), where columns are x, y, z
    :param axis: Axis to rotate around ('x', 'y', or 'z')
    :param angle: Angle in degrees
    :return: Rotated NumPy array of shape (N, 3)
    """
    if coords.shape[1] != 3:
        raise ValueError("Input array must have shape (N, 3) for x, y, z coordinates")

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

