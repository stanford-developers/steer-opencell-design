from plotly.subplots import make_subplots
from plotly import graph_objects as go

from App.styles import *

UM_TO_M = 1e-6
M_TO_UM = 1e6
G_TO_KG = 1e-3
CM_TO_M = 1e-2
KG_TO_G = 1e3
M_TO_CM = 1e2
MM_TO_M = 1e-3
M_TO_MM = 1e3


class Separator:

    def __init__(self,  
                 areal_cost: float, 
                 thickness: float, 
                 density: float,
                 porosity: float,
                 width: float,
                 fold_length: float,
                 name: str = 'Separator'
                 ):
        """
        Initialize an object that represents a separator
        
        :param name: str: name of the material
        :param areal_cost: float: areal cost of the material per m^2
        :param thickness: float: thickness of the separator in um
        :param density: float: density of the material in g/cm^3
        :param porosity: float: porosity of the separator in %
        :param width: float: width of the separator in mm
        :param length: float: length of the separator in mm
        :param fold_length: float: length of the fold in the separator in mm
        """
        self._check_areal_cost(areal_cost)
        self._check_thickness(thickness)
        self._check_density(density)
        self._check_porosity(porosity)
        self._check_width(width)
        self._check_fold_length(fold_length)
        self._check_name(name)

    def _check_areal_cost(self, areal_cost: float):

        if not isinstance(areal_cost, (int, float)):
            raise TypeError("Areal cost must be a number.")
        
        if areal_cost < 0:
            raise ValueError("Areal cost cannot be negative.")
        
        if areal_cost > 10:
            raise ValueError("This areal cost is too high. Check the units, it should be in $/m^2.")
        
        self._areal_cost = float(areal_cost)

    def _check_thickness(self, thickness: float):

        if not isinstance(thickness, (int, float)):
            raise TypeError("Thickness must be a number.")

        if thickness < 0:
            raise ValueError("Thickness cannot be negative.")
        
        if thickness > 100:
            raise ValueError("This thickness is too high for a separator. Check the units, it should be in um.")
        
        self._thickness = float(thickness) * UM_TO_M

    def _check_density(self, density: float):

        if not isinstance(density, (int, float)):
            raise TypeError("Density must be a number.")

        if density < 0:
            raise ValueError("Density cannot be negative.")
        
        if density > 3:
            raise ValueError("This density is too high for a separator. Check the units, it should be in g/cm^3.")
        
        self._density = float(density) * (G_TO_KG / CM_TO_M**3)

    def _check_porosity(self, porosity: float):

        if not isinstance(porosity, (int, float)):
            raise TypeError("Porosity must be a number.")

        if porosity < 0:
            raise ValueError("Porosity cannot be negative.")
        
        if porosity > 100:
            raise ValueError("This porosity is too high. Check the units, it should be in %.")
        
        if porosity < 1:
            raise ValueError("This porosity is very low. Check the units, it should be in %.")
        
        self._porosity = float(porosity) / 100

    def _check_width(self, width: float):

        if not isinstance(width, (int, float)):
            raise TypeError("Width must be a number.")

        if width < 0:
            raise ValueError("Width cannot be negative.")
        
        self._width = float(width) * MM_TO_M

    def _check_fold_length(self, fold_length: float):

        if not isinstance(fold_length, (int, float)):
            raise TypeError("Fold length must be a number.")

        if fold_length < 0:
            raise ValueError("Fold length cannot be negative.")
    
        self._fold_length = float(fold_length) * MM_TO_M

    def _check_name(self, name: str):

        if not isinstance(name, str):
            raise TypeError("Name must be a string.")
        
        self._name = name

    def _calculate_area_properties(self):

        if not hasattr(self, '_length'):
            raise AttributeError("Length not calculated defined. Put in an electrochemical assembly to calculate it.")

        self._area = self._width * self._length
        self._mass = self._thickness * self._area * self._density
        self._cost = self._area * self._areal_cost
        self._pore_volume = self._thickness * self._area * self._porosity

    def _make_top_down_shapes(self):

        fig = go.Figure()
        y_shift = -self.width / 2
        x_shift = self.fold_length / 2  # Shift value

        x = [0, self.fold_length, self.fold_length, 0, 0]
        x = [xi - x_shift for xi in x]  # Shift all x values
        y = [0, 0, self.width, self.width, 0]
        y = [yi + y_shift for yi in y]
        fig.add_trace(go.Scatter(x=x, y=y, mode='lines', line=dict(width=1, color='black'), fillcolor=SEPARATOR_COLOR, fill='toself', name='Separator'))

        return fig


    def get_top_down_view(self, paper_bgcolor='white', plot_bgcolor='white', title=None, split=True, **kwargs):
        """
        Visualize the notched current collector.
        If the collector is long, split into two subplots for left and right ends with split indicators.
        The vertical datum is centered at y = self.width / 2.
        """
        split_threshold = 2
        aspect_ratio = self.fold_length / self.width
        n_cols = 2 if aspect_ratio >= split_threshold else 1
    
        if aspect_ratio < split_threshold or not split:
            fig = self._make_top_down_shapes()
            fig.update_layout(xaxis=dict(scaleanchor='y'))
            
        else:
            fig = make_subplots(rows=1, cols=n_cols, shared_yaxes=True, horizontal_spacing=0.02)
            for trace in self._make_top_down_shapes().data:
                fig.add_trace(trace, row=1, col=1)
                fig.add_trace(trace, row=1, col=2)

            half_window = self.width
            left_xlim = [-self.fold_length/2, -self.fold_length/2 + half_window]
            right_xlim = [self.fold_length/2 - half_window, self.fold_length/2]
            fig.update_xaxes(range=left_xlim, row=1, col=1)
            fig.update_xaxes(range=right_xlim, row=1, col=2)

            # Add vertical split indicators
            bottom_y_lim = -(self.width / 2) * 1.1
            top_y_lim = (self.width / 2) * 1.1
            line = dict(color="#864C39", width=6)
            fig.add_shape(type='line', x0=left_xlim[1], x1=left_xlim[1], y0=bottom_y_lim, y1=top_y_lim, line=line, xref='x', yref='y')
            fig.add_shape(type='line', x0=right_xlim[0], x1=right_xlim[0], y0=bottom_y_lim, y1=top_y_lim, line=line, xref='x2', yref='y2')

            fig.update_layout(xaxis=dict(scaleanchor='y'), xaxis2=dict(scaleanchor='y'))

        if title is None:
            title = f'{self._name} Current Collector'

        fig.update_layout(
            title=title,
            paper_bgcolor=paper_bgcolor,
            plot_bgcolor=plot_bgcolor,
            showlegend=False,
            xaxis_title='x (mm)',
            yaxis_title='y (mm)',
            **kwargs
        )

        return fig

    @property
    def length(self):
        if hasattr(self, '_length'):
            return round(self._length * M_TO_MM, 2)

    @property
    def pore_volume(self):
        if hasattr(self, '_pore_volume'):
            return round(self._pore_volume * M_TO_CM**3, 2)
        else:
            return AttributeError("Pore volume not calculated yet. Put in a stack to calculate.")

    @property
    def cost(self):
        if hasattr(self, '_cost'):
            return round(self._cost, 2)
        else:
            return AttributeError("Cost not calculated yet. Put in a stack to calculate.")

    @property
    def mass(self):
        if hasattr(self, '_mass'):
            return round(self._mass * KG_TO_G, 2)
        else:
            return AttributeError("Mass not calculated yet. Put in a stack to calculate.")

    @property
    def area(self):
        if hasattr(self, '_area'):
            return round(self._area * M_TO_CM**2, 2)
        else:
            return AttributeError("Area not calculated yet. Put in a stack to calculate.")

    @property
    def width(self):
        if hasattr(self, '_width'):
            return round(self._width * M_TO_MM, 2)
    
    @property
    def fold_length(self):
        if hasattr(self, '_fold_length'):
            return round(self._fold_length * M_TO_MM, 2)

    @property
    def areal_cost(self):
        return round(self._areal_cost, 2)
    
    @property
    def name(self):
        return self._name

    @property
    def porosity(self):
        return self._porosity * 100

    @property
    def density(self):
        return round(self._density * (KG_TO_G/M_TO_CM**3), 2)

    @property
    def thickness(self):
        return round(self._thickness * M_TO_UM, 2)

    def __str__(self):
        if self._name is not None:
            return f"{self._name} Separator"
        else:
            return f"Separator"
    
    def __repr__(self):
        return self.__str__()