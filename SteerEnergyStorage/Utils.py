import plotly.colors as pc
import numpy as np

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
