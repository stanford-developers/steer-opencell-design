from typing import Union, Dict, Tuple, Any
from abc import ABC, abstractmethod
from copy import copy, deepcopy
import pandas as pd
import numpy as np
from shapely.geometry import Polygon
import plotly.graph_objects as go

from steer_opencell_design.Constructions.Layups import Laminate
from steer_core.Constants.Units import *
from steer_core.Constants.Universal import PI
from steer_core.Decorators.General import calculate_all_properties
from steer_opencell_design.Constructions.ElectrodeAssemblies.Base import _ElectrodeAssembly
from steer_opencell_design.AuxillaryComponents.WindingEquipment import RoundMandrel, FlatMandrel
from steer_opencell_design.Constructions.ElectrodeAssemblies.SpiralUtils import SpiralCalculator

import time

# Constants for array column indices
THETA_COL = 0
X_UNWRAPPED_COL = 1
RADIUS_COL = 2
X_COORD_COL = 3
Z_COORD_COL = 4
TURNS_COL = 5

# Constants for calculations
TWO_PI = 2.0 * PI
DEFAULT_DTHETA = 0.4
DEFAULT_DS_TARGET = 0.5e-3
DEFAULT_PRESSED_HEIGHT = 0.0008
TARGET_ERROR = 5e-5
MAX_ITERATIONS = 500000
MAX_POINTS = 120000


class _JellyRoll(_ElectrodeAssembly, ABC):
    """Abstract base class for jelly roll electrode assemblies.

    A jelly roll assembly consists of electrodes and separators wound around a mandrel
    into a spiral configuration. This class provides the common functionality for
    calculating spiral paths, component placement, and interfacial areas.

    Parameters
    ----------
    laminate : Laminate
        The layup structure containing electrode and separator layers
    mandrel : Union[FlatMandrel, RoundMandrel]
        The mandrel around which the layers are wound

    Attributes
    ----------
    mandrel : Union[FlatMandrel, RoundMandrel]
        The winding mandrel
    layup : Laminate
        The electrode/separator layup structure
    _spiral : np.ndarray
        Base spiral coordinates [theta, x_unwrapped, r, x, z, turns]
    _component_spirals : Dict[str, np.ndarray]
        Individual component spiral coordinates
    _extruded_spirals : Dict[str, np.ndarray]
        Thickness-extruded component spirals for visualization
    _roll_properties : Dict[str, float]
        Turn counts and other roll characteristics
    """
    
    def __init__(
            self, 
            laminate: Laminate,
            mandrel: Union[FlatMandrel, RoundMandrel]
        ) -> None:
        """Initialize jelly roll electrode assembly.
        
        Parameters
        ----------
        laminate : Laminate
            The layup structure to be wound
        mandrel : Union[FlatMandrel, RoundMandrel]
            The mandrel for winding
            
        Raises
        ------
        TypeError
            If mandrel is not FlatMandrel or RoundMandrel
        ValueError
            If laminate is invalid or incompatible
        """
        if not isinstance(mandrel, (FlatMandrel, RoundMandrel)):
            raise TypeError(f"mandrel must be FlatMandrel or RoundMandrel, got {type(mandrel)}")
        if not isinstance(laminate, Laminate):
            raise TypeError(f"laminate must be Laminate, got {type(laminate)}")
            
        self.mandrel = mandrel
        super().__init__(laminate)

    def _calculate_all_properties(self) -> None:
        """Calculate all properties of the jelly roll electrode assembly.
        
        This method orchestrates the calculation of spiral geometry, component
        placement, and derived properties in the correct sequence.
        """
        self._calculate_roll()
        self._calculate_roll_properties()
        super()._calculate_all_properties()

    def _calculate_roll(self) -> None:
        """Generate variable-thickness winding spiral and component placement.
        
        This method orchestrates the complete spiral calculation process:
        1. Calculate base spiral path
        2. Map components onto spiral
        3. Create extruded visualization shapes
        4. Calculate derived spiral properties
        """
        self._calculate_variable_thickness_spiral()
        self._build_component_spirals()
        self._build_extruded_component_spirals()
        self._calculate_spiral_properties()

    def _calculate_interfacial_area(self) -> float:
        """Calculate the interfacial area between cathode and anode surfaces in a wound jelly roll.
        
        Computes two interfacial surfaces:
        1. Inner surface: cathode b-side to anode a-side (first contact)
        2. Outer surface: cathode a-side to anode b-side (after one full rotation)
        
        Returns
        -------
        float
            Total interfacial area in m²
            
        Raises
        ------
        ValueError
            If electrode coordinates cannot be calculated
        """
        # Extract electrode coordinates
        cathode_coords = self._get_electrode_coordinates('cathode')
        anode_coords = self._get_electrode_coordinates('anode')
        
        # Calculate inner interfacial area (first contact)
        inner_area = self._calculate_inner_interface_area(
            cathode_coords['b_side'], anode_coords['a_side']
        )
        
        # Calculate outer interfacial area (after one full rotation)
        outer_area = self._calculate_outer_interface_area(
            cathode_coords['a_side'], anode_coords['b_side']
        )
        
        self._interfacial_area = inner_area + outer_area

        return self._interfacial_area
            
    def _get_electrode_coordinates(self, electrode_type: str) -> Dict[str, np.ndarray]:
        """Extract electrode coating coordinates.
        
        Parameters
        ----------
        electrode_type : str
            Either 'cathode' or 'anode'
            
        Returns
        -------
        Dict[str, np.ndarray]
            Dictionary with 'a_side' and 'b_side' coordinate arrays (2D)
            
        Raises
        ------
        ValueError
            If electrode_type is not 'cathode' or 'anode'
        AttributeError
            If electrode or coordinates are not available
        """
        if electrode_type not in ('cathode', 'anode'):
            raise ValueError(f"electrode_type must be 'cathode' or 'anode', got {electrode_type}")
            
        electrode = getattr(self._layup, f'_{electrode_type}')
        current_collector = electrode._current_collector
        
        # Extract 2D coordinates (x, y plane)
        a_side_coords = current_collector._a_side_coated_coordinates[:, :2]
        b_side_coords = current_collector._b_side_coated_coordinates[:, :2]
        
        return {
            'a_side': a_side_coords,
            'b_side': b_side_coords
        }

    def _calculate_inner_interface_area(self, cathode_coords: np.ndarray, anode_coords: np.ndarray) -> float:
        """Calculate interfacial area for inner surface contact.
        
        Parameters
        ----------
        cathode_coords : np.ndarray
            Cathode b-side coordinates (2D)
        anode_coords : np.ndarray  
            Anode a-side coordinates (2D)
            
        Returns
        -------
        float
            Inner interfacial area in m²
            
        Raises
        ------
        ValueError
            If coordinates are invalid or polygons cannot be created
        """
        cathode_polygon = Polygon(cathode_coords)
        anode_polygon = Polygon(anode_coords)
        intersection = cathode_polygon.intersection(anode_polygon)
        return intersection.area

    def _calculate_outer_interface_area(self, cathode_coords: np.ndarray, anode_coords: np.ndarray) -> float:
        """Calculate interfacial area for outer surface contact after one full rotation.
        
        Parameters
        ----------
        cathode_coords : np.ndarray
            Cathode a-side coordinates (2D)
        anode_coords : np.ndarray
            Anode b-side coordinates (2D)
            
        Returns
        -------
        float
            Outer interfacial area in m²
            
        Raises
        ------
        ValueError
            If coordinates are invalid or shift calculation fails
        """
        cathode_shift = self._calculate_full_rotation_shift()
        shifted_cathode_coords = cathode_coords + np.array([cathode_shift, 0])
        shifted_cathode_polygon = Polygon(shifted_cathode_coords)
        anode_polygon = Polygon(anode_coords)
        intersection = shifted_cathode_polygon.intersection(anode_polygon)
        return intersection.area
    
    def _calculate_full_rotation_shift(self) -> float:
        """Calculate the x-direction shift after cathode completes one full rotation.
        
        Returns
        -------
        float
            Shift distance in meters
            
        Raises
        ------
        KeyError
            If cathode spiral data is not available
        ValueError
            If spiral data is insufficient for calculation
        """
        # Get cathode a-side spiral data
        cathode_spiral = self._component_spirals['cathode_current_collector']
        
        # Get starting position
        cathode_start_angle = cathode_spiral[0, THETA_COL]
        cathode_start_x = cathode_spiral[0, X_UNWRAPPED_COL]
        
        # Find point where cathode completes one full rotation (2π radians)
        if type(self) == WoundJellyRoll:
            full_rotation_angle = cathode_start_angle - TWO_PI
        elif type(self) == FlatWoundJellyRoll:
            full_rotation_angle = cathode_start_angle + TWO_PI
        else:
            raise ValueError(f"Unknown jelly roll type: {type(self)}")

        theta_values = np.argsort(cathode_spiral[:, THETA_COL])
        x_values = cathode_spiral[theta_values, X_UNWRAPPED_COL]

        length_one_rotation_ahead = np.interp(
            full_rotation_angle, 
            cathode_spiral[theta_values, THETA_COL], 
            x_values
        )

        return length_one_rotation_ahead - cathode_start_x
    
    def _calculate_spiral_properties(self) -> None:
        """Calculate spiral properties of the electrode assembly.
        
        Computes interfacial area and geometric parameters derived from spiral.
        """
        self._calculate_interfacial_area()
        self._calculate_geometry_parameters()

    @abstractmethod
    def _calculate_variable_thickness_spiral(self) -> np.ndarray:
        """Calculate the base spiral with variable thickness.
        
        This method must be implemented by subclasses to define the specific
        spiral calculation algorithm for their geometry type.
        
        Returns
        -------
        np.ndarray
            Base spiral coordinates [theta, x_unwrapped, r, x, z, turns]
        """
        pass

    @abstractmethod
    def _build_component_spirals(self) -> Dict[str, np.ndarray]:
        """Build individual component spirals from the base spiral.
        
        This method must be implemented by subclasses to define how components
        are mapped onto the base spiral geometry.
        
        Returns
        -------
        Dict[str, np.ndarray]
            Component spirals keyed by component name
        """
        pass

    @abstractmethod
    def _build_extruded_component_spirals(self) -> Dict[str, np.ndarray]:
        """Build thickness-extruded component spirals for visualization.
        
        This method must be implemented by subclasses to create filled shapes
        representing component thickness for 3D visualization.
        
        Returns
        -------
        Dict[str, np.ndarray]
            Extruded component spirals keyed by component name
        """
        pass

    @abstractmethod
    def _calculate_geometry_parameters(self) -> Union[Tuple[float, float], Tuple[float, float, float]]:
        """Calculate geometry-specific parameters (radius, thickness, etc.).
        
        This method must be implemented by subclasses to calculate the characteristic
        dimensions of their specific geometry.
        
        Returns
        -------
        Union[Tuple[float, float], Tuple[float, float, float]]
            Geometry-specific parameters (varies by subclass)
        """
        pass

    def _calculate_roll_properties(self) -> Dict[str, float]:
        """Calculate roll properties with optimized performance and error handling.
        
        Computes turn counts for all components and separator inner/outer turns
        relative to anode placement.
        
        Returns
        -------
        Dict[str, float]
            Roll properties including component turn counts and separator metrics
            
        Raises
        ------
        KeyError
            If required component spirals are missing
        ValueError
            If spiral data is invalid or insufficient
        """
        roll_properties = {}
        
        # Cache component spirals to avoid repeated dictionary lookups
        component_spirals = copy(self._component_spirals)
        component_names = [n for n in component_spirals.keys()]
        
        # Validate required components exist
        required_components = ["anode_a_side_coating", "anode_b_side_coating"]
        missing_components = [comp for comp in required_components if comp not in component_spirals]
        if missing_components:
            raise KeyError(f"Missing required components: {missing_components}")
        
        # Calculate basic turn counts for all components
        for name in component_names:
            spiral_data = component_spirals[name]
            if len(spiral_data) > 0:
                roll_properties[f"{name}_turns"] = np.max(spiral_data[:, TURNS_COL])
            else:
                roll_properties[f"{name}_turns"] = 0.0

        # Get anode theta boundaries
        anode_a_spiral = component_spirals["anode_a_side_coating"]
        anode_b_spiral = component_spirals["anode_b_side_coating"]
        
        if len(anode_a_spiral) == 0 or len(anode_b_spiral) == 0:
            raise ValueError("Empty anode spiral data")
            
        roll_start_theta = anode_a_spiral[0, THETA_COL]
        roll_end_theta = anode_b_spiral[-1, THETA_COL]
        
        # Process both separators with the same logic
        for sep_name in ["bottom_separator", "top_separator"]:
            if sep_name not in component_spirals:
                roll_properties[f"{sep_name}_inner_turns"] = 0.0
                roll_properties[f"{sep_name}_outer_turns"] = 0.0
                continue
                
            separator_spiral = component_spirals[sep_name]
            
            if len(separator_spiral) == 0:
                roll_properties[f"{sep_name}_inner_turns"] = 0.0
                roll_properties[f"{sep_name}_outer_turns"] = 0.0
                continue
            
            # Inner turns: separator region after anode starts
            if type(self).__name__ == 'WoundJellyRoll':
                inner_mask = separator_spiral[:, THETA_COL] > roll_start_theta
                outer_mask = separator_spiral[:, THETA_COL] < roll_end_theta
            else:  # FlatWoundJellyRoll
                inner_mask = separator_spiral[:, THETA_COL] < roll_start_theta
                outer_mask = separator_spiral[:, THETA_COL] > roll_end_theta
            
            inner_turns = np.max(separator_spiral[inner_mask, TURNS_COL]) if np.any(inner_mask) else 0.0
            
            # Outer turns: separator region before anode ends (turn range)
            if np.any(outer_mask):
                outer_spiral = separator_spiral[outer_mask, TURNS_COL]
                outer_turns = np.max(outer_spiral) - np.min(outer_spiral) if len(outer_spiral) > 0 else 0.0
            else:
                outer_turns = 0.0
            
            # Store results
            roll_properties[f"{sep_name}_inner_turns"] = inner_turns
            roll_properties[f"{sep_name}_outer_turns"] = outer_turns

        self._roll_properties = roll_properties
        return self._roll_properties

    def _calculate_mass_properties(self) -> float:
        """Calculate total mass and mass breakdown of the jelly roll assembly.
        
        Returns
        -------
        float
            Total mass of the assembly in kg
            
        Raises
        ------
        AttributeError
            If component mass properties are not available
        """
        separators = [self.layup._bottom_separator, self.layup._top_separator]

        self._mass = self.layup.anode._mass + self.layup.cathode._mass + sum(s._mass for s in separators)

        self._mass_breakdown = {
            "Anode": self.layup.anode._mass_breakdown,
            "Cathode": self.layup.cathode._mass_breakdown,
            "Separators": self.sum_breakdowns(separators, "mass"),
        }

        return self._mass

    def _calculate_cost_properties(self) -> float:
        """Calculate total cost and cost breakdown of the jelly roll assembly.
        
        Returns
        -------
        float
            Total cost of the assembly in currency units
            
        Raises
        ------
        AttributeError
            If component cost properties are not available
        """
        separators = [self.layup._bottom_separator, self.layup._top_separator]

        self._cost = self.layup.anode._cost + self.layup.cathode._cost + sum(s._cost for s in separators)

        self._cost_breakdown = {
            "Anode": self.layup.anode._cost_breakdown,
            "Cathode": self.layup.cathode._cost_breakdown,
            "Separators": self.sum_breakdowns(separators, "cost"),
        }

        return self._cost

    def get_spiral_plot(
            self, 
            layered: bool = True,
            extruded: bool = True,
            **kwargs: Any
        ) -> go.Figure:
        """Generate interactive spiral plot using Plotly.
        
        Parameters
        ----------
        layered : bool, default=True
            Whether to show individual layer traces
        extruded : bool, default=True
            Whether to show filled thickness shapes
        **kwargs : Any
            Additional plot styling options (paper_bgcolor, plot_bgcolor, etc.)
            
        Returns
        -------
        go.Figure
            Interactive Plotly figure with spiral visualization
        """

        fig = go.Figure()

        if layered and not extruded:
            fig.add_trace(self.top_separator_spiral_trace)
            fig.add_trace(self.anode_a_side_coating_spiral_trace)
            fig.add_trace(self.anode_current_collector_spiral_trace)
            fig.add_trace(self.anode_b_side_coating_spiral_trace)
            fig.add_trace(self.bottom_separator_spiral_trace)
            fig.add_trace(self.cathode_a_side_coating_spiral_trace)
            fig.add_trace(self.cathode_current_collector_spiral_trace)
            fig.add_trace(self.cathode_b_side_coating_spiral_trace)

        elif layered and extruded:
            fig.add_trace(self.top_separator_extruded_spiral_trace)
            fig.add_trace(self.anode_a_side_coating_extruded_spiral_trace)
            fig.add_trace(self.anode_current_collector_extruded_spiral_trace)
            fig.add_trace(self.anode_b_side_coating_extruded_spiral_trace)
            fig.add_trace(self.bottom_separator_extruded_spiral_trace)
            fig.add_trace(self.cathode_a_side_coating_extruded_spiral_trace)
            fig.add_trace(self.cathode_current_collector_extruded_spiral_trace)
            fig.add_trace(self.cathode_b_side_coating_extruded_spiral_trace)

            fig.add_trace(self.top_separator_spiral_trace)
            fig.add_trace(self.anode_a_side_coating_spiral_trace)
            fig.add_trace(self.anode_current_collector_spiral_trace)
            fig.add_trace(self.anode_b_side_coating_spiral_trace)
            fig.add_trace(self.bottom_separator_spiral_trace)
            fig.add_trace(self.cathode_a_side_coating_spiral_trace)
            fig.add_trace(self.cathode_current_collector_spiral_trace)
            fig.add_trace(self.cathode_b_side_coating_spiral_trace)

        elif not layered:
            fig.add_trace(self.spiral_trace)

        fig.update_layout(
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            xaxis=self.SCHEMATIC_X_AXIS,
            yaxis=self.SCHEMATIC_Z_AXIS,
            hovermode="closest",
        )

        return fig

    def _format_spiral_trace(self, property_name: str, color: str, name: str, line_width: int = 0) -> go.Scatter:
        """Format spiral data into Plotly scatter trace.
        
        Parameters
        ----------
        property_name : str
            Name of the DataFrame property to use for trace data
        color : str
            Color for the trace line
        name : str
            Display name for the trace
        line_width : int, default=0
            Width of the trace line
            
        Returns
        -------
        go.Scatter
            Plotly scatter trace with hover information
            
        Raises
        ------
        AttributeError
            If property_name does not exist on the object
        """
        
        df = getattr(self, property_name)

        # Build customdata array for rich hover (theta, length, radius, x, z, turns)
        customdata = np.stack([
            df['Theta (degrees)'],
            df['Unwrapped Length (mm)'],
            df['Radius (mm)'],
            df['X (mm)'],
            df['Z (mm)'],
            df['Turns']
        ], axis=-1)

        hovertemplate = (
            '<b>'+name+'</b><br>'
            'Theta: %{customdata[0]:.2f}°<br>'
            'Unwrapped Length: %{customdata[1]:.2f} mm<br>'
            'Radius: %{customdata[2]:.2f} mm<br>'
            'X: %{customdata[3]:.2f} mm<br>'
            'Z: %{customdata[4]:.2f} mm<br>'
            'Turns: %{customdata[5]:.2f}<extra></extra>'
        )

        trace = go.Scatter(
            x=df['X (mm)'],
            y=df['Z (mm)'],
            mode='lines',
            line=dict(color=color, width=line_width),
            line_shape='spline',
            name=name,
            customdata=customdata,
            hovertemplate=hovertemplate,
            legendgroup=name,
        )

        trace.showlegend = False

        return trace
    
    def _format_extruded_spiral_trace(self, property_name: str, color: str, name: str) -> go.Scatter:
        """Format extruded spiral data into filled Plotly scatter trace.
        
        Parameters
        ----------
        property_name : str
            Name of the DataFrame property to use for trace data
        color : str
            Fill color for the extruded shape
        name : str
            Display name for the trace
            
        Returns
        -------
        go.Scatter
            Plotly scatter trace with fill for thickness visualization
            
        Raises
        ------
        AttributeError
            If property_name does not exist on the object
        """
        
        df = getattr(self, property_name)
        # Use same hover data schema as line spirals
        customdata = np.stack([
            df['Theta (degrees)'],
            df['Unwrapped Length (mm)'],
            df['Radius (mm)'],
            df['X (mm)'],
            df['Z (mm)'],
            df['Turns']
        ], axis=-1)

        hovertemplate = (
            '<b>'+name+' (Extruded)</b><br>'
            'Theta: %{customdata[0]:.2f}°<br>'
            'Unwrapped Length: %{customdata[1]:.2f} mm<br>'
            'Radius: %{customdata[2]:.2f} mm<br>'
            'X: %{customdata[3]:.2f} mm<br>'
            'Z: %{customdata[4]:.2f} mm<br>'
            'Turns: %{customdata[5]:.2f}<extra></extra>'
        )

        return go.Scatter(
            x=df['X (mm)'],
            y=df['Z (mm)'],
            mode='lines',
            fill='toself',
            fillcolor=color,
            line=dict(color="black", width=0.1),
            line_shape='spline',
            name=name,
            customdata=customdata,
            hovertemplate=hovertemplate,
            legendgroup=name,
        )

    @property
    def roll_properties(self) -> pd.DataFrame:
        """Return the roll properties as a pandas DataFrame with values rounded to 2 decimal places.
        
        Returns
        -------
        pd.DataFrame
            DataFrame containing roll properties with component names as index and turn counts as values.
        """
        # Create a formatted dictionary with rounded values
        formatted_props = {key: round(value, 2) for key, value in self._roll_properties.items()}
        
        # Convert to DataFrame with descriptive names
        df = pd.DataFrame.from_dict(formatted_props, orient='index', columns=['Turns'])
        df.index.name = 'Component'
        
        # Sort by component type for better readability
        component_order = [
            'anode_a_side_coating_turns',
            'anode_current_collector_turns', 
            'anode_b_side_coating_turns',
            'cathode_a_side_coating_turns',
            'cathode_current_collector_turns',
            'cathode_b_side_coating_turns',
            'bottom_separator_turns',
            'bottom_separator_inner_turns',
            'bottom_separator_outer_turns',
            'top_separator_turns',
            'top_separator_inner_turns',
            'top_separator_outer_turns'
        ]
        
        # Reorder DataFrame according to component_order, keeping any additional components at the end
        existing_components = [comp for comp in component_order if comp in df.index]
        additional_components = [comp for comp in df.index if comp not in component_order]
        ordered_index = existing_components + additional_components
        
        return df.reindex(ordered_index)

    @property
    def spiral(self) -> pd.DataFrame:
        """Return the spiral as a pandas DataFrame.

        Columns: theta, x_unwrapped, thickness, r, x, y
        """
        spiral = self._spiral
        return SpiralCalculator.format_np_spiral_for_df(spiral)

    @property
    def spiral_trace(self) -> go.Scatter:
        return self._format_spiral_trace("spiral", "black", "Spiral", 1)

    @property
    def top_separator_spiral(self) -> pd.DataFrame:
        """Return the top separator spiral as a pandas DataFrame.
        Columns: theta, x_unwrapped, thickness, r, x, y
        """
        ts_spiral = self._component_spirals.get("top_separator")
        return SpiralCalculator.format_np_spiral_for_df(ts_spiral)

    @property
    def bottom_separator_spiral(self) -> pd.DataFrame:
        """Return the bottom separator spiral as a pandas DataFrame.
        Columns: theta, x_unwrapped, thickness, r, x, y
        """
        bs_spiral = self._component_spirals.get("bottom_separator")
        return SpiralCalculator.format_np_spiral_for_df(bs_spiral)

    @property
    def anode_a_side_coating_spiral(self) -> pd.DataFrame:
        """Return the anode a-side coating spiral as a pandas DataFrame.
        Columns: theta, x_unwrapped, thickness, r, x, y
        """
        aasc_spiral = self._component_spirals.get("anode_a_side_coating")
        return SpiralCalculator.format_np_spiral_for_df(aasc_spiral)

    @property
    def anode_current_collector_spiral(self) -> pd.DataFrame:
        """Return the anode current collector spiral as a pandas DataFrame.
        Columns: theta, x_unwrapped, thickness, r, x, y
        """
        acc_spiral = self._component_spirals.get("anode_current_collector")
        return SpiralCalculator.format_np_spiral_for_df(acc_spiral)
    
    @property
    def anode_b_side_coating_spiral(self) -> pd.DataFrame:
        """Return the anode b-side coating spiral as a pandas DataFrame.
        Columns: theta, x_unwrapped, thickness, r, x, y
        """
        absc_spiral = self._component_spirals.get("anode_b_side_coating")
        return SpiralCalculator.format_np_spiral_for_df(absc_spiral)
    
    @property
    def cathode_a_side_coating_spiral(self) -> pd.DataFrame:
        """Return the cathode a-side coating spiral as a pandas DataFrame.
        Columns: theta, x_unwrapped, thickness, r, x, y
        """
        casc_spiral = self._component_spirals.get("cathode_a_side_coating")
        return SpiralCalculator.format_np_spiral_for_df(casc_spiral)

    @property
    def cathode_current_collector_spiral(self) -> pd.DataFrame:
        """Return the cathode current collector spiral as a pandas DataFrame.
        Columns: theta, x_unwrapped, thickness, r, x, y
        """
        ccc_spiral = self._component_spirals.get("cathode_current_collector")
        return SpiralCalculator.format_np_spiral_for_df(ccc_spiral)
    
    @property
    def cathode_b_side_coating_spiral(self) -> pd.DataFrame:
        """Return the cathode b-side coating spiral as a pandas DataFrame.
        Columns: theta, x_unwrapped, thickness, r, x, y
        """
        cbsc_spiral = self._component_spirals.get("cathode_b_side_coating")
        return SpiralCalculator.format_np_spiral_for_df(cbsc_spiral)

    @property
    def top_separator_extruded_spiral(self) -> pd.DataFrame:
        ts_extruded_spiral = self._extruded_spirals.get("top_separator")
        return SpiralCalculator.format_np_spiral_for_df(ts_extruded_spiral)

    @property
    def bottom_separator_extruded_spiral(self) -> pd.DataFrame:
        bs_extruded_spiral = self._extruded_spirals.get("bottom_separator")
        return SpiralCalculator.format_np_spiral_for_df(bs_extruded_spiral)

    @property
    def anode_a_side_coating_extruded_spiral(self) -> pd.DataFrame:
        aasc_extruded_spiral = self._extruded_spirals.get("anode_a_side_coating")
        return SpiralCalculator.format_np_spiral_for_df(aasc_extruded_spiral)
    
    @property
    def anode_current_collector_extruded_spiral(self) -> pd.DataFrame:
        acc_extruded_spiral = self._extruded_spirals.get("anode_current_collector")
        return SpiralCalculator.format_np_spiral_for_df(acc_extruded_spiral)
    
    @property
    def anode_b_side_coating_extruded_spiral(self) -> pd.DataFrame:
        absc_extruded_spiral = self._extruded_spirals.get("anode_b_side_coating")
        return SpiralCalculator.format_np_spiral_for_df(absc_extruded_spiral)

    @property
    def cathode_a_side_coating_extruded_spiral(self) -> pd.DataFrame:
        casc_extruded_spiral = self._extruded_spirals.get("cathode_a_side_coating")
        return SpiralCalculator.format_np_spiral_for_df(casc_extruded_spiral)
    
    @property
    def cathode_current_collector_extruded_spiral(self) -> pd.DataFrame:
        ccc_extruded_spiral = self._extruded_spirals.get("cathode_current_collector")
        return SpiralCalculator.format_np_spiral_for_df(ccc_extruded_spiral)
    
    @property
    def cathode_b_side_coating_extruded_spiral(self) -> pd.DataFrame:
        cbsc_extruded_spiral = self._extruded_spirals.get("cathode_b_side_coating")
        return SpiralCalculator.format_np_spiral_for_df(cbsc_extruded_spiral)

    @property
    def top_separator_spiral_trace(self) -> go.Scatter:
        return self._format_spiral_trace("top_separator_spiral", self.layup.top_separator.material._color, f"Top Separator")
    
    @property
    def bottom_separator_spiral_trace(self) -> go.Scatter:
        return self._format_spiral_trace("bottom_separator_spiral", self.layup.bottom_separator.material._color, f"Bottom Separator")
    
    @property
    def anode_a_side_coating_spiral_trace(self) -> go.Scatter:
        return self._format_spiral_trace("anode_a_side_coating_spiral", self.layup.anode.formulation._color, f"Anode a-side Coating")
    
    @property
    def anode_current_collector_spiral_trace(self) -> go.Scatter:
        return self._format_spiral_trace("anode_current_collector_spiral", self.layup.anode.current_collector.material._color, f"Anode Current Collector")
    
    @property
    def anode_b_side_coating_spiral_trace(self) -> go.Scatter:
        return self._format_spiral_trace("anode_b_side_coating_spiral", self.layup.anode.formulation._color, f"Anode b-side Coating")
    
    @property
    def cathode_a_side_coating_spiral_trace(self) -> go.Scatter:
        return self._format_spiral_trace("cathode_a_side_coating_spiral", self.layup.cathode.formulation._color, f"Cathode a-side Coating")

    @property
    def cathode_current_collector_spiral_trace(self) -> go.Scatter:
        return self._format_spiral_trace("cathode_current_collector_spiral", self.layup.cathode.current_collector.material._color, f"Cathode Current Collector")
    
    @property
    def cathode_b_side_coating_spiral_trace(self) -> go.Scatter:
        return self._format_spiral_trace("cathode_b_side_coating_spiral", self.layup.cathode.formulation._color, f"Cathode b-side Coating")
    
    @property
    def top_separator_extruded_spiral_trace(self) -> go.Scatter:
        return self._format_extruded_spiral_trace("top_separator_extruded_spiral", self.layup.top_separator.material._color, f"Top Separator")

    @property
    def bottom_separator_extruded_spiral_trace(self) -> go.Scatter:
        return self._format_extruded_spiral_trace("bottom_separator_extruded_spiral", self.layup.bottom_separator.material._color, f"Bottom Separator")

    @property
    def anode_a_side_coating_extruded_spiral_trace(self) -> go.Scatter:
        return self._format_extruded_spiral_trace("anode_a_side_coating_extruded_spiral", self.layup.anode.formulation._color, f"Anode a-side Coating")

    @property
    def anode_current_collector_extruded_spiral_trace(self) -> go.Scatter:
        return self._format_extruded_spiral_trace("anode_current_collector_extruded_spiral", self.layup.anode.current_collector.material._color, f"Anode Current Collector")   

    @property
    def anode_b_side_coating_extruded_spiral_trace(self) -> go.Scatter:
        return self._format_extruded_spiral_trace("anode_b_side_coating_extruded_spiral", self.layup.anode.formulation._color, f"Anode b-side Coating")

    @property
    def cathode_a_side_coating_extruded_spiral_trace(self) -> go.Scatter:
        return self._format_extruded_spiral_trace("cathode_a_side_coating_extruded_spiral", self.layup.cathode.formulation._color, f"Cathode a-side Coating")
    
    @property
    def cathode_current_collector_extruded_spiral_trace(self) -> go.Scatter:
        return self._format_extruded_spiral_trace("cathode_current_collector_extruded_spiral", self.layup.cathode.current_collector.material._color, f"Cathode Current Collector")
    
    @property
    def cathode_b_side_coating_extruded_spiral_trace(self) -> go.Scatter:
        return self._format_extruded_spiral_trace("cathode_b_side_coating_extruded_spiral", self.layup.cathode.formulation._color, f"Cathode b-side Coating")

    @property
    def mandrel(self) -> Union[RoundMandrel, FlatMandrel]:
        """Return the mandrel instance.
        
        Returns
        -------
        Union[RoundMandrel, FlatMandrel]
            The winding mandrel used for the jelly roll
        """
        return self._mandrel

    @property
    def layup(self) -> Laminate:
        """Return the underlying Laminate instance.
        
        Returns
        -------
        Laminate
            The electrode/separator layup structure
        """
        return self._layup

    @property
    def total_layup_length(self) -> float:
        """Return the total length of the layup in mm.
        
        Returns
        -------
        float
            Total unwrapped length of the layup in millimeters
        """
        return self.layup.total_length

    @mandrel.setter
    @calculate_all_properties
    def mandrel(self, value: Union[RoundMandrel, FlatMandrel]) -> None:
        """Set the mandrel and recalculate properties.
        
        Parameters
        ----------
        value : Union[RoundMandrel, FlatMandrel]
            The new mandrel to use
            
        Raises
        ------
        TypeError
            If value is not a valid mandrel type
        """
        self.validate_type(value, (RoundMandrel, FlatMandrel), "mandrel")
        self._mandrel = value

    @layup.setter
    @calculate_all_properties
    def layup(self, value: Laminate) -> None:
        """Set the layup and recalculate properties.
        
        Parameters
        ----------
        value : Laminate
            The new layup structure
            
        Raises
        ------
        TypeError
            If value is not a Laminate instance
        """

        # validate type
        self.validate_type(value, Laminate, "layup")
    
        # get the min x in the flattened center lines
        x_list = [c[:, 0] for c in value._flattened_center_lines.values()]
        min_x = min([np.min(mx) for mx in x_list])

        # get the most negative z value
        z_min = np.min(value._flattened_center_lines['cathode_b_side_coating'][:, 1]) # - value.cathode._coating_thickness

        # set the new x value
        new_x = (value.datum[0] * MM_TO_M) - min_x

        # set the new y value
        new_y = (value.datum[1] * MM_TO_M)

        # set the new z value
        new_z = (value.datum[2] * MM_TO_M) - z_min + value.cathode._coating_thickness / 2 + self.mandrel._radius

        # Convert back to mm and set the new datum
        value.datum = (new_x * M_TO_MM, new_y * M_TO_MM, new_z * M_TO_MM)

        # set to self
        self._layup = value


class WoundJellyRoll(_JellyRoll):
    """Wound jelly roll electrode assembly for cylindrical cells.

    A wound jelly roll consists of electrodes and separators wound around a round mandrel
    in a circular spiral pattern. This configuration is commonly used in cylindrical
    lithium-ion batteries.

    Parameters
    ----------
    laminate : Laminate
        The layup structure containing electrode and separator layers
    mandrel : RoundMandrel
        Round mandrel for cylindrical winding

    Attributes
    ----------
    radius : float
        Outer radius of the wound roll in mm
    diameter : float
        Outer diameter of the wound roll in mm
        
    Examples
    --------
    >>> from steer_opencell_design import Laminate, RoundMandrel
    >>> mandrel = RoundMandrel(radius=0.001)  # 1mm radius
    >>> layup = Laminate(...)  # Define layup structure
    >>> jelly_roll = WoundJellyRoll(laminate=layup, mandrel=mandrel)
    >>> print(f"Outer diameter: {jelly_roll.diameter} mm")
    """
    
    def __init__(
            self, 
            laminate: Laminate,
            mandrel: RoundMandrel
        ) -> None:
        """Initialize wound jelly roll electrode assembly.
        
        Parameters
        ----------
        laminate : Laminate
            The layup structure to be wound
        mandrel : RoundMandrel
            Round mandrel for cylindrical winding
            
        Raises
        ------
        TypeError
            If mandrel is not RoundMandrel or laminate is not Laminate
        """
        self.validate_type(mandrel, RoundMandrel, "mandrel")

        super().__init__(
            laminate=laminate,
            mandrel=mandrel,
        )

        self._calculate_all_properties()
        self._update_properties = True

    def _calculate_geometry_parameters(self) -> Tuple[float, float]:
        """Calculate outer radius and diameter of the wound jelly roll.
        
        Determines the minimum bounding circle for all component spirals to find
        the overall dimensions of the wound assembly.
        
        Returns
        -------
        Tuple[float, float]
            (radius, diameter) in meters
            
        Raises
        ------
        ValueError
            If component spiral data is invalid or insufficient
        """
        radius_list = []

        # Create the bounding surface for each component
        for _, spiral_data in self._component_spirals.items():
        
            x_coords = spiral_data[:, X_COORD_COL]
            z_coords = spiral_data[:, Z_COORD_COL]
            coords_2d = np.column_stack((x_coords, z_coords))
            radius_list.append(SpiralCalculator.get_radius_of_spiral(coords_2d))

        self._radius = max(radius_list)
        self._diameter = self._radius * 2

        return self._radius, self._diameter

    def _calculate_variable_thickness_spiral(self) -> np.ndarray:

        self._spiral = SpiralCalculator.calculate_variable_thickness_spiral(
            laminate=self.layup,
            start_radius=self.mandrel._radius
        )

        return self._spiral

    def _build_component_spirals(self) -> Dict[str, np.ndarray]:
        """Build component spirals by mapping flattened center lines onto the wound spiral.
        
        Maps individual electrode and separator components from the layup onto the base
        spiral geometry, accounting for their specific thickness and positioning.
        
        Returns
        -------
        Dict[str, np.ndarray]
            Component spirals keyed by component name
        """
        self._component_spirals = SpiralCalculator.build_component_spirals(
            base_spiral=self._spiral,
            layup=self.layup,
            mandrel_radius=self._mandrel._radius
        )
        return self._component_spirals

    def _build_extruded_component_spirals(self) -> Dict[str, np.ndarray]:
        """Build extruded component spirals by radially thickening center line spirals.
        
        For each component, creates a filled shape by:
        1. Taking the center line spiral from _component_spirals
        2. Creating outer spiral by adding thickness/2 to radius
        3. Creating inner spiral by subtracting thickness/2 from radius
        4. Reversing inner spiral direction for proper winding
        5. Combining outer + inner spirals into a closed filled shape
        
        Returns
        -------
        Dict[str, np.ndarray]
            Extruded component spirals for 3D visualization
        """
        self._extruded_spirals = SpiralCalculator.build_extruded_component_spirals(
            component_spirals=self._component_spirals,
            layup=self.layup
        )
        return self._extruded_spirals

    @property
    def radius(self) -> float:
        """Return the outer radius of the wound jelly roll in mm.
        
        Returns
        -------
        float
            Outer radius in millimeters, rounded to 2 decimal places
        """
        return round(self._radius * M_TO_MM, 2)

    @property
    def radius_range(self) -> Tuple[float, float]:
        """Return the radius range (min, max) of the wound jelly roll in mm.
        
        Returns
        -------
        Tuple[float, float]
            (min_radius, max_radius) in millimeters, rounded to 2 decimal places
        """
        # make layup with small length
        small_layup = deepcopy(self.layup)

        # set layup length to small
        small_layup.length = 100

        # make small jelly roll
        small_jelly_roll = WoundJellyRoll(
            laminate=small_layup,
            mandrel=self.mandrel
        )

        min_radius = small_jelly_roll.mandrel.radius
        max_radius = 50

        return (round(min_radius, 2), round(max_radius, 2))
    
    @property
    def radius_hard_range(self) -> Tuple[float, float]:
        """Return the hard radius range (min, max) of the wound jelly roll in mm.
        
        Returns
        -------
        Tuple[float, float]
            (min_radius, max_radius) in millimeters, rounded to 2 decimal places
        """
        min_radius = self.radius_range[0]
        max_radius = 200

        return (round(min_radius, 2), round(max_radius, 2))

    @property
    def diameter(self) -> float:
        """Return the outer diameter of the wound jelly roll in mm.
        
        Returns
        -------
        float
            Outer diameter in millimeters, rounded to 2 decimal places
        """
        return round(self._diameter * M_TO_MM, 2)
    
    @property
    def diameter_range(self) -> Tuple[float, float]:
        """Return the diameter range (min, max) of the wound jelly roll in mm.
        
        Returns
        -------
        Tuple[float, float]
            (min_diameter, max_diameter) in millimeters, rounded to 2 decimal places
        """
        radius_range = self.radius_range
        min_diameter = radius_range[0] * 2
        max_diameter = radius_range[1] * 2

        return (round(min_diameter, 2), round(max_diameter, 2))
    
    @property
    def diameter_hard_range(self) -> Tuple[float, float]:
        """Return the hard diameter range (min, max) of the wound jelly roll in mm.
        
        Returns
        -------
        Tuple[float, float]
            (min_diameter, max_diameter) in millimeters, rounded to 2 decimal places
        """
        radius_hard_range = self.radius_hard_range
        min_diameter = radius_hard_range[0] * 2
        max_diameter = radius_hard_range[1] * 2

        return (round(min_diameter, 2), round(max_diameter, 2))

    @radius.setter
    @calculate_all_properties
    def radius(self, value: float) -> None:

        # validate input
        self.validate_positive_float(value, "radius")

        # to si units
        _target_radius = value * MM_TO_M

        # check if value is less than mandrel radius
        if _target_radius <= self.mandrel._radius:
            raise ValueError(f"radius must be greater than mandrel radius of {self.mandrel._radius * M_TO_MM} mm")

        return None


class FlatWoundJellyRoll(_JellyRoll):
    """Flat wound jelly roll electrode assembly for prismatic cells.

    A flat wound jelly roll consists of electrodes and separators wound around a flat mandrel
    in a racetrack spiral pattern. This configuration is commonly used in prismatic and
    pouch lithium-ion batteries and includes hot-pressing simulation.

    Parameters
    ----------
    laminate : Laminate
        The layup structure containing electrode and separator layers
    mandrel : FlatMandrel
        Flat mandrel for racetrack winding

    Attributes
    ----------
    thickness : float
        Overall thickness of the flat wound roll in mm
    width : float
        Overall width of the flat wound roll in mm
    pressed_radius : float
        Mandrel radius after hot pressing in mm
    pressed_straight_length : float
        Mandrel straight length after hot pressing in mm
        
    Examples
    --------
    >>> from steer_opencell_design import Laminate, FlatMandrel
    >>> mandrel = FlatMandrel(radius=0.002, straight_length=0.050)  # 2mm radius, 50mm straight
    >>> layup = Laminate(...)  # Define layup structure
    >>> jelly_roll = FlatWoundJellyRoll(laminate=layup, mandrel=mandrel)
    >>> print(f"Dimensions: {jelly_roll.width} x {jelly_roll.thickness} mm")
    """
    
    def __init__(
            self, 
            laminate: Laminate,
            mandrel: FlatMandrel,
        ) -> None:
        """Initialize flat wound jelly roll electrode assembly.
        
        Parameters
        ----------
        laminate : Laminate
            The layup structure to be wound
        mandrel : FlatMandrel
            Flat mandrel for racetrack winding
            
        Raises
        ------
        TypeError
            If mandrel is not FlatMandrel or laminate is not Laminate
        """
        if not isinstance(mandrel, FlatMandrel):
            raise TypeError(f"mandrel must be FlatMandrel, got {type(mandrel)}")

        super().__init__(
            laminate=laminate,
            mandrel=mandrel
        )

        self._calculate_all_properties()
        self._update_properties = True

    def _calculate_roll(self) -> None:
        """Calculate roll properties including hot-pressing effects.
        
        Extends base roll calculation to include pressed racetrack geometry
        simulation for realistic flat wound jelly roll dimensions.
        """
        self._calculate_pressed_racetrack()
        super()._calculate_roll()

    def _calculate_geometry_parameters(self) -> Tuple[float, float]:
        """Calculate overall thickness and width of the flat wound jelly roll.
        
        Determines the bounding box dimensions by analyzing all component spirals
        to find the overall envelope of the flat wound assembly.
        
        Returns
        -------
        Tuple[float, float]
            (thickness, width) in meters
            
        Raises
        ------
        ValueError
            If component spiral data is invalid or insufficient
        """
        thickness_list = []
        width_list = []

        # Create the bounding surface for each component
        for _, spiral_data in self._component_spirals.items():
                
            max_z = spiral_data[:, Z_COORD_COL].max()
            min_z = spiral_data[:, Z_COORD_COL].min()
            max_x = spiral_data[:, X_COORD_COL].max()
            min_x = spiral_data[:, X_COORD_COL].min()
            thickness = max_z - min_z
            width = max_x - min_x
            thickness_list.append(thickness)
            width_list.append(width)

        self._thickness = max(thickness_list)
        self._width = max(width_list)

        return self._thickness, self._width

    def _calculate_pressed_racetrack(self, pressed_height: float = DEFAULT_PRESSED_HEIGHT) -> Tuple[float, float]:
        """Simulate hot pressing by creating a new spiral with a flatter mandrel geometry.
        
        This approach calculates the circumference of the original racetrack mandrel,
        then creates a new mandrel with the specified pressed height and adjusts the
        width to maintain the same circumference. A completely new spiral is then
        calculated for this flatter geometry.
        
        Parameters
        ----------
        pressed_height : float
            Height of the mandrel after hot pressing in meters (default 0.8mm)
            
        Returns
        -------
        Tuple[float, float]
            (pressed_radius, pressed_straight_length) in meters
            
        Raises
        ------
        ValueError
            If pressed height is invalid or circumference calculation fails
        """
        # Get original mandrel parameters
        original_radius = self._mandrel._radius  # height/2 of original racetrack
        original_straight_length = self._mandrel._straight_length
        
        # Calculate original mandrel circumference (perimeter of racetrack cross-section)
        original_circumference = self._calculate_racetrack_circumference(
            original_radius, original_straight_length
        )
        
        # Create new mandrel geometry with pressed height
        pressed_radius = pressed_height / 2  # New radius from pressed height
        
        # Calculate new straight length to maintain same circumference
        # Circumference = 2 * π * radius + 2 * straight_length
        # Solve for new straight_length: straight_length = (circumference - 2 * π * radius) / 2
        new_straight_length = (original_circumference - TWO_PI * pressed_radius) / 2

        self._pressed_radius = pressed_radius
        self._pressed_straight_length = new_straight_length

        return self._pressed_radius, self._pressed_straight_length

    def _calculate_variable_thickness_spiral_for_height(
            self, 
            mandrel_radius: float, 
            straight_length: float, 
            ds_target: float = DEFAULT_DS_TARGET
        ) -> np.ndarray:
        """Calculate spiral path for given mandrel geometry parameters (clockwise direction).
        
        The racetrack consists of:
        - Two semicircular ends (radius = height/2)
        - Two straight sections (length = width - height)
        
        Calculates spiral in clockwise direction, consistent with WoundJellyRoll.
        
        Parameters
        ----------
        mandrel_radius : float
            Radius of semicircular ends (height/2) in meters
        straight_length : float
            Length of straight sections (width - height) in meters
        ds_target : float
            Target arc length step size in meters
            
        Returns
        -------
        np.ndarray
            Columns: [theta, x_unwrapped, r, x, z, turns]
        """
        total_length = self.layup._total_length  # meters

        # Initialize arrays for spiral path
        positions = []
        x_unwrapped = 0.0
        accumulated_thickness = 0.0  # Track actual thickness buildup
        turn_count = 0.0
        
        # Start at top of right semicircle (theta=2π in racetrack coordinates, will decrease clockwise)
        theta_racetrack = TWO_PI
        
        while x_unwrapped < total_length:
            # Get thickness at current unwrapped position
            thickness = self.layup.get_thickness_at_x(x_unwrapped)
            current_radius = mandrel_radius + accumulated_thickness
            
            # Calculate position on current racetrack
            x_pos, z_pos = self._racetrack_position(theta_racetrack, current_radius, straight_length)
            
            # Calculate normalized theta for clockwise motion (starting from 2π, decreasing)
            # Total turns traveled = (initial_theta - current_theta) / (2π) + full_turns_completed
            theta_traveled = (TWO_PI - theta_racetrack) + turn_count * TWO_PI
            total_turns = theta_traveled / TWO_PI
            normalized_theta = theta_traveled  # Represents cumulative angle traveled clockwise
            
            # Store position data
            positions.append([
                normalized_theta, # Normalized theta representing cumulative angle traveled clockwise
                x_unwrapped,      # Cumulative unwrapped length
                current_radius,   # Distance from center to current layer
                x_pos,           # Cartesian x coordinate
                z_pos,           # Cartesian z coordinate  
                total_turns      # Total number of turns (fractional)
            ])
            
            # Calculate step size based on local curvature and thickness
            curvature = self._racetrack_curvature(theta_racetrack, current_radius, straight_length)
            if curvature > 0:
                # On curved sections, limit step by curvature
                ds_max = min(ds_target, 0.1 / curvature)
            else:
                # On straight sections, use target step size
                ds_max = ds_target
            
            ds_actual = min(ds_max, total_length - x_unwrapped)
            
            # Calculate how much thickness to add based on this step
            # Thickness accumulation rate depends on perimeter
            perimeter_current = TWO_PI * current_radius + 2 * straight_length
            dtheta = ds_actual * TWO_PI / perimeter_current
            
            # Add thickness proportional to angular progress
            thickness_increment = thickness * dtheta / TWO_PI
            accumulated_thickness += thickness_increment
            
            # Move clockwise (decrease theta)
            theta_racetrack -= dtheta
            x_unwrapped += ds_actual
            
            # Update turn count when completing full loops (theta goes below 0)
            if theta_racetrack < 0:
                full_turns = (-theta_racetrack) // TWO_PI + 1
                turn_count += full_turns
                theta_racetrack = theta_racetrack + full_turns * TWO_PI
        
        # Convert to numpy array
        return np.array(positions)
    
    def _racetrack_position(self, theta: float, radius: float, straight_length: float) -> tuple:
        """Calculate x,z position on racetrack at given parametric angle (clockwise direction).
        
        For clockwise motion starting at top-right:
        - theta=2π: top of right semicircle 
        - theta=3π/2: right side
        - theta=π: bottom of right semicircle
        - theta=π/2: bottom of left semicircle
        - theta=0: top of left semicircle
        
        Parameters
        ----------
        theta : float
            Parametric angle (0 to 2π), decreases clockwise from 2π
        radius : float
            Current layer radius
        straight_length : float
            Length of straight sections
            
        Returns
        -------
        tuple
            (x_position, z_position) in meters
        """
        # Normalize theta to [0, 2π)
        theta = theta % (2 * np.pi)
        
        # Calculate total perimeter proportions
        semi_arc_length = np.pi * radius
        total_perimeter = 2 * semi_arc_length + 2 * straight_length
        
        # For clockwise motion, map theta to arc_length position around perimeter
        # Start at theta=2π (top right) and go clockwise
        # Convert to arc position: theta=2π -> 0, theta=3π/2 -> π/4*perimeter, etc.
        clockwise_fraction = (2 * np.pi - theta) / (2 * np.pi)
        arc_length = clockwise_fraction * total_perimeter
        
        if arc_length <= semi_arc_length:
            # Right semicircle (starting from top, going clockwise)
            phi = arc_length / radius  # Actual geometric angle from top
            x = straight_length/2 + radius * np.cos(np.pi/2 - phi)  # Start at top (π/2), go clockwise
            z = radius * np.sin(np.pi/2 - phi)
            
        elif arc_length <= semi_arc_length + straight_length:
            # Bottom straight section (right to left)
            progress = (arc_length - semi_arc_length) / straight_length
            x = straight_length/2 - progress * straight_length
            z = -radius
            
        elif arc_length <= 2 * semi_arc_length + straight_length:
            # Left semicircle (bottom to top, clockwise)
            phi = (arc_length - semi_arc_length - straight_length) / radius
            # For left semicircle, start at bottom (-π/2) and go clockwise (decreasing angle)
            angle = -np.pi/2 - phi  # Start at -π/2, go clockwise (more negative)
            x = -straight_length/2 + radius * np.cos(angle)  # Center at -straight_length/2
            z = radius * np.sin(angle)
            
        else:
            # Top straight section (left to right)
            progress = (arc_length - 2 * semi_arc_length - straight_length) / straight_length
            x = -straight_length/2 + progress * straight_length
            z = radius
        
        return x, z
    
    def _racetrack_curvature(self, theta: float, radius: float, straight_length: float) -> float:
        """Calculate curvature at given position on racetrack.
        
        Parameters
        ----------
        theta : float
            Parametric angle (0 to 2π)
        radius : float
            Current layer radius
        straight_length : float
            Length of straight sections
            
        Returns
        -------
        float
            Curvature (1/radius on curves, 0 on straight sections)
        """
        # Normalize theta to [0, 2π)
        theta = theta % (2 * np.pi)
        
        # Calculate position fractions
        semi_arc_length = np.pi * radius
        total_perimeter = 2 * semi_arc_length + 2 * straight_length
        fraction = theta / (2 * np.pi)
        arc_length = fraction * total_perimeter
        
        # Determine if on curved or straight section
        if (arc_length <= semi_arc_length or 
            (semi_arc_length + straight_length <= arc_length <= 2 * semi_arc_length + straight_length)):
            # On semicircular sections
            return 1.0 / radius if radius > 0 else 0.0
        else:
            # On straight sections
            return 0.0

    def _build_component_spirals(self):
        
        # Build component spirals for the hot-pressed geometry
        self._component_spirals = self._build_component_spirals_for_geometry(
            self._spiral, self._pressed_radius, self._pressed_straight_length
        )

        return self._component_spirals
        
    def _build_component_spirals_for_geometry(
            self, 
            base_spiral: np.ndarray, 
            mandrel_radius: float, 
            straight_length: float
        ) -> dict:
        """Build component spirals for a given base spiral and mandrel geometry.
        
        This is a generalized version of _build_component_spirals that can work with
        any mandrel geometry parameters, used for hot-pressed spirals.
        
        Parameters
        ----------
        base_spiral : np.ndarray
            Base spiral to map components onto
        mandrel_radius : float
            Radius of semicircular ends (height/2) in meters
        straight_length : float
            Length of straight sections (width - height) in meters
            
        Returns
        -------
        dict
            Component spirals dictionary
        """
        component_spirals = {}
        
        # Component names in processing order
        component_names = [
            'bottom_separator', 'top_separator',
            'anode_a_side_coating', 'anode_current_collector', 'anode_b_side_coating',
            'cathode_a_side_coating', 'cathode_current_collector', 'cathode_b_side_coating'
        ]
        
        # Pre-compute all center line data to avoid repeated access
        center_line_data = {}
        for component_name in component_names:
            center_line = self.layup._flattened_center_lines[component_name]
            center_line_data[component_name] = {
                'x_coords': center_line[:, 0],
                'z_coords': center_line[:, 1],
                'x_min': np.min(center_line[:, 0]),
                'x_max': np.max(center_line[:, 0])
            }
    
        # Process each component
        for component_name in component_names:

            cl_data = center_line_data[component_name]
            
            # Vectorized spiral clipping using boolean mask
            x_unwrapped = base_spiral[:, 1]  # Extract x_unwrapped column
            mask = (x_unwrapped >= cl_data['x_min']) & (x_unwrapped <= cl_data['x_max'])
            
            # Apply mask to get component spiral slice
            component_spiral = base_spiral[mask].copy()
            
            # Vectorized height calculation using numpy interpolation
            x_vals = component_spiral[:, 1]
            z_unwrapped = np.interp(x_vals, cl_data['x_coords'], cl_data['z_coords'])
            height_adjustments = z_unwrapped - self._mandrel._radius
            
            # Apply height adjustments in correct direction based on racetrack position
            component_spiral = self._apply_flat_mandrel_height_adjustments(
                component_spiral, height_adjustments, mandrel_radius, straight_length
            )
            
            # Recalculate turns starting from 0 for this component
            theta_start_component = component_spiral[0, 0]  # Starting theta for this component
            theta_traveled_component = component_spiral[:, 0] - theta_start_component  # Angle traveled from component start
            component_spiral[:, 5] = theta_traveled_component / (2 * np.pi)  # Turns relative to component start
        
            component_spirals[component_name] = component_spiral

        return component_spirals
    
    def _apply_flat_mandrel_height_adjustments(
            self, 
            spiral: np.ndarray, 
            height_adjustments: np.ndarray, 
            mandrel_radius: float, 
            straight_length: float
        ):
        """Apply height adjustments to spiral points based on their position on the racetrack.
        
        Parameters
        ----------
        spiral : np.ndarray
            Component spiral array (modified in-place)
        height_adjustments : np.ndarray
            Height adjustments to apply at each point
        mandrel_radius : float
            Radius of the semicircular ends
        straight_length : float
            Length of straight sections
        """
        # Process each point to determine adjustment direction
        for i in range(len(spiral)):
            current_x = spiral[i, 3]  # Current x position
            current_z = spiral[i, 4]  # Current z position
            height_adj = height_adjustments[i]
            
            # Determine position type and adjustment direction based on actual coordinates
            adjustment_vector = self._get_coordinate_based_adjustment_direction(
                current_x, current_z, mandrel_radius, straight_length
            )
            
            # Apply height adjustment in the correct direction
            new_x = current_x + height_adj * adjustment_vector[0]
            new_z = current_z + height_adj * adjustment_vector[1]
            
            # Update spiral coordinates
            spiral[i, 3] = new_x  # x coordinate
            spiral[i, 4] = new_z  # z coordinate
            
            # Update effective radius (distance from origin)
            spiral[i, 2] = np.sqrt(new_x**2 + new_z**2)

        return spiral
    
    def _get_height_adjustment_direction(self, theta: float, radius: float, straight_length: float,
                                       mandrel_radius: float) -> np.ndarray:
        """Get the direction vector for height adjustment at a given racetrack position.
        
        Parameters
        ----------
        theta : float
            Parametric angle around racetrack
        radius : float
            Current radius at this position
        straight_length : float
            Length of straight sections
        mandrel_radius : float
            Radius of semicircular ends
            
        Returns
        -------
        np.ndarray
            Unit vector [dx, dz] indicating direction for height adjustment
        """
        # Normalize theta to [0, 2π)
        theta = theta % (2 * np.pi)
        
        # Calculate position fractions to determine section
        semi_arc_length = np.pi * mandrel_radius
        total_perimeter = 2 * semi_arc_length + 2 * straight_length
        fraction = theta / (2 * np.pi)
        arc_length = fraction * total_perimeter
        
        if arc_length <= semi_arc_length:
            # Right semicircle: radial direction outward from right center
            phi = arc_length / mandrel_radius  # Actual geometric angle
            center_x = straight_length / 2
            center_z = 0.0
            # Unit vector pointing outward from semicircle center
            direction_x = np.cos(phi - np.pi/2)
            direction_z = np.sin(phi - np.pi/2)
            
        elif arc_length <= semi_arc_length + straight_length:
            # Top straight section: directly upward (positive z)
            direction_x = 0.0
            direction_z = 1.0
            
        elif arc_length <= 2 * semi_arc_length + straight_length:
            # Left semicircle: radial direction outward from left center
            phi = (arc_length - semi_arc_length - straight_length) / mandrel_radius
            center_x = -straight_length / 2
            center_z = 0.0
            # Unit vector pointing outward from semicircle center
            direction_x = np.cos(phi + np.pi/2)
            direction_z = np.sin(phi + np.pi/2)
            
        else:
            # Bottom straight section: directly downward (negative z)
            direction_x = 0.0
            direction_z = -1.0
        
        return np.array([direction_x, direction_z])

    def _get_coordinate_based_adjustment_direction(self, x: float, z: float, mandrel_radius: float,
                                                 straight_length: float) -> np.ndarray:
        """Get the direction vector for height adjustment based on actual coordinates.
        
        This method determines the adjustment direction by analyzing the actual position
        rather than using parametric angles, which avoids bunching issues on curved sections.
        
        Parameters
        ----------
        x : float
            Current x coordinate
        z : float
            Current z coordinate  
        mandrel_radius : float
            Radius of semicircular ends
        straight_length : float
            Length of straight sections
            
        Returns
        -------
        np.ndarray
            Unit vector [dx, dz] indicating direction for height adjustment
        """
        # Define the centers of the semicircular ends
        right_center_x = straight_length / 2
        left_center_x = -straight_length / 2
        center_z = 0.0
        
        # Tolerance for determining if we're on a straight section
        straight_tolerance = mandrel_radius * 0.1
        
        # Check if we're on the right semicircle
        if x > (straight_length / 2 - straight_tolerance):
            # Distance from right semicircle center
            dx_from_center = x - right_center_x
            dz_from_center = z - center_z
            distance_from_center = np.sqrt(dx_from_center**2 + dz_from_center**2)
            
            if distance_from_center > 1e-12:  # Avoid division by zero
                # Unit vector pointing radially outward from right center
                direction_x = dx_from_center / distance_from_center
                direction_z = dz_from_center / distance_from_center
            else:
                # Fallback: assume we're at the center, point upward
                direction_x = 0.0
                direction_z = 1.0
                
        # Check if we're on the left semicircle
        elif x < (-straight_length / 2 + straight_tolerance):
            # Distance from left semicircle center
            dx_from_center = x - left_center_x
            dz_from_center = z - center_z
            distance_from_center = np.sqrt(dx_from_center**2 + dz_from_center**2)
            
            if distance_from_center > 1e-12:  # Avoid division by zero
                # Unit vector pointing radially outward from left center
                direction_x = dx_from_center / distance_from_center
                direction_z = dz_from_center / distance_from_center
            else:
                # Fallback: assume we're at the center, point upward
                direction_x = 0.0
                direction_z = 1.0
                
        # We're on a straight section
        else:
            if z > 0:
                # Top straight section: directly upward
                direction_x = 0.0
                direction_z = 1.0
            else:
                # Bottom straight section: directly downward
                direction_x = 0.0
                direction_z = -1.0
        
        return np.array([direction_x, direction_z])

    def _build_extruded_component_spirals(self):

        # Build extruded component spirals for the hot-pressed geometry
        self._extruded_spirals = self._build_extruded_component_spirals_for_geometry(
            self._component_spirals, self._pressed_radius, self._pressed_straight_length
        )

        return self._extruded_spirals
        
    def _build_extruded_component_spirals_for_geometry(self, component_spirals: dict, 
                                                     mandrel_radius: float, straight_length: float) -> dict:
        """Build extruded component spirals for a given component spirals dictionary and mandrel geometry.
        
        This is a generalized version of _build_extruded_component_spirals that can work with
        any component spirals dictionary and mandrel geometry parameters, used for hot-pressed spirals.
        
        Parameters
        ----------
        component_spirals : dict
            Component spirals dictionary to extrude
        mandrel_radius : float
            Radius of semicircular ends (height/2) in meters
        straight_length : float
            Length of straight sections (width - height) in meters
            
        Returns
        -------
        dict
            Extruded component spirals dictionary
        """
        extruded_spirals = {}

        component_thicknesses = {
            'top_separator': self.layup.top_separator._thickness,
            'anode_a_side_coating': self.layup.anode._coating_thickness,
            'anode_current_collector': self.layup.anode.current_collector._thickness,
            'anode_b_side_coating': self.layup.anode._coating_thickness,
            'bottom_separator': self.layup.bottom_separator._thickness,
            'cathode_a_side_coating': self.layup.cathode._coating_thickness,
            'cathode_current_collector': self.layup.cathode.current_collector._thickness,
            'cathode_b_side_coating': self.layup.cathode._coating_thickness,
        }
        
        # Process each component that has a center line spiral
        for component_name, thickness in component_thicknesses.items():
            if component_name not in component_spirals:
                # Skip missing components
                extruded_spirals[component_name] = np.empty((0, 6))
                continue
                
            center_spiral = component_spirals[component_name]
            
            if len(center_spiral) == 0:
                # Skip empty components
                extruded_spirals[component_name] = np.empty((0, 6))
                continue
                
            half_thickness = thickness / 2.0
            
            # Create outer and inner spirals with proper flat mandrel thickness application
            outer_spiral, inner_spiral = self._create_flat_mandrel_thickness_spirals(
                center_spiral, half_thickness, mandrel_radius, straight_length
            )
            
            # Reverse inner spiral direction for proper winding (creates closed shape)
            inner_spiral_reversed = inner_spiral[::-1, :]
            
            # Add transition padding points to smooth spline interpolation
            # Duplicate end points to create smooth transitions
            outer_end_padding = np.tile(outer_spiral[-1, :], (2, 1))
            inner_start_padding = np.tile(inner_spiral_reversed[0, :], (2, 1))
            
            # Combine into filled shape: outer → padding → inner (reversed) → close
            if len(outer_spiral) > 0 and len(inner_spiral_reversed) > 0:
                filled_spiral = np.vstack([
                    outer_spiral,           # Outer boundary
                    outer_end_padding,      # Smooth transition
                    inner_start_padding,    # Smooth transition  
                    inner_spiral_reversed   # Inner boundary (reversed)
                ])
            else:
                # Fallback for edge cases
                filled_spiral = outer_spiral
            
            extruded_spirals[component_name] = filled_spiral

        return extruded_spirals
    
    def _create_flat_mandrel_thickness_spirals(self, center_spiral: np.ndarray, half_thickness: float,
                                             mandrel_radius: float, straight_length: float) -> tuple:
        """Create outer and inner spirals by applying thickness in correct directions.
        
        Parameters
        ----------
        center_spiral : np.ndarray
            Center line spiral coordinates
        half_thickness : float
            Half of the component thickness
        mandrel_radius : float
            Radius of semicircular ends
        straight_length : float
            Length of straight sections
            
        Returns
        -------
        tuple
            (outer_spiral, inner_spiral) as numpy arrays
        """
        # Initialize outer and inner spirals
        outer_spiral = center_spiral.copy()
        inner_spiral = center_spiral.copy()
        
        # Process each point to apply thickness in correct direction
        for i in range(len(center_spiral)):
            current_x = center_spiral[i, 3]  # Current x position
            current_z = center_spiral[i, 4]  # Current z position
            
            # Get the direction vector for thickness application based on coordinates
            direction_vector = self._get_coordinate_based_adjustment_direction(
                current_x, current_z, mandrel_radius, straight_length
            )
            
            # Calculate outer position (center + half_thickness in direction)
            outer_x = center_spiral[i, 3] + half_thickness * direction_vector[0]
            outer_z = center_spiral[i, 4] + half_thickness * direction_vector[1]
            
            # Calculate inner position (center - half_thickness in direction)
            inner_x = center_spiral[i, 3] - half_thickness * direction_vector[0]
            inner_z = center_spiral[i, 4] - half_thickness * direction_vector[1]
            
            # Update outer spiral
            outer_spiral[i, 3] = outer_x
            outer_spiral[i, 4] = outer_z
            outer_spiral[i, 2] = np.sqrt(outer_x**2 + outer_z**2)  # Update effective radius
            
            # Update inner spiral
            inner_spiral[i, 3] = inner_x
            inner_spiral[i, 4] = inner_z
            inner_spiral[i, 2] = np.sqrt(inner_x**2 + inner_z**2)  # Update effective radius
        
        return outer_spiral, inner_spiral

    def _calculate_variable_thickness_spiral(self) -> np.ndarray:

        # Calculate new spiral with pressed mandrel geometry (no mandrel modification needed)
        self._spiral = self._calculate_variable_thickness_spiral_for_height(
            self._pressed_radius, self._pressed_straight_length
        )
        
        return self._spiral
    
    def _calculate_racetrack_circumference(self, radius: float, straight_length: float) -> float:
        """Calculate the circumference (perimeter) of a racetrack cross-section.
        
        The racetrack consists of two semicircles connected by straight sections.
        Circumference = 2 * π * radius + 2 * straight_length
        
        Parameters
        ----------
        radius : float
            Radius of the semicircular ends
        straight_length : float
            Length of the straight sections
            
        Returns
        -------
        float
            Circumference in meters
        """
        return 2 * np.pi * radius + 2 * straight_length

    @property
    def pressed_radius(self) -> float:
        """Return the pressed mandrel radius in mm.
        
        Returns
        -------
        float
            Pressed mandrel radius in millimeters, rounded to 2 decimal places
        """
        return round(self._pressed_radius * M_TO_MM, 2)
    
    @property
    def pressed_straight_length(self) -> float:
        """Return the pressed mandrel straight length in mm.
        
        Returns
        -------
        float
            Pressed mandrel straight length in millimeters, rounded to 2 decimal places
        """
        return round(self._pressed_straight_length * M_TO_MM, 2)
    
    @property
    def thickness(self) -> float:
        """Return the overall jelly roll thickness in millimeters.
        
        Returns
        -------
        float
            Overall thickness in millimeters, rounded to 2 decimal places
        """
        return round(self._thickness * M_TO_MM, 2)
    
    @property
    def width(self) -> float:
        """Return the overall jelly roll width in millimeters.
        
        Returns
        -------
        float
            Overall width in millimeters, rounded to 2 decimal places
        """
        return round(self._width * M_TO_MM, 2)
    
