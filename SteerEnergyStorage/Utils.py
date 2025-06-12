import plotly.colors as pc
import numpy as np
import plotly.graph_objects as go

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

        return area



