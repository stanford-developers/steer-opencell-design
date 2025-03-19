import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

def get_colorway(color1, color2, n):
    """
    Function to get a colorway between two colors with n colors in between
    
    :param color1: color in any format supported by matplotlib
    :param color2: color in any format supported by matplotlib
    :param n: int: number of colors in between
    :return: list: list of n colors in between color1 and color2
    """
    rgb1 = np.array(mcolors.to_rgb(color1))
    rgb2 = np.array(mcolors.to_rgb(color2))
    colors = [mcolors.to_hex((1 - t) * rgb1 + t * rgb2) for t in np.linspace(0, 1, n)]
    
    return colors
