from typing import Union, Dict, Tuple, Any, Optional
from abc import ABC, abstractmethod
from copy import copy, deepcopy
import pandas as pd
import numpy as np
from scipy.optimize import brentq
import plotly.graph_objects as go
from functools import wraps
from enum import Enum

from steer_opencell_design.Constructions.Layups.Laminate import Laminate
from steer_core.Constants.Units import *
from steer_core.Constants.Universal import PI
from steer_core.Decorators.General import calculate_all_properties, calculate_bulk_properties
from steer_core.Decorators.Coordinates import calculate_coordinates
from steer_opencell_design.Constructions.ElectrodeAssemblies.Base import _ElectrodeAssembly
from steer_opencell_design.Constructions.ElectrodeAssemblies.WindingEquipment import RoundMandrel, FlatMandrel
from steer_opencell_design.Constructions.ElectrodeAssemblies.SpiralUtils import SpiralCalculator
from steer_opencell_design.Constructions.ElectrodeAssemblies.Tape import Tape
from steer_opencell_design.Components.CurrentCollectors.Tabbed import TabWeldedCurrentCollector

import time


# Constants for array column indices
THETA_COL = 0
RADIUS_COL = 2
X_UNWRAPPED_COL = 1
X_COORD_COL = 3
Z_COORD_COL = 4
TURNS_COL = 5

# Constants for calculations
TWO_PI = 2.0 * PI
DEFAULT_PRESSED_HEIGHT = 0.0008


class TapeDriver(Enum):
    """Enumeration for tape length driver modes.
    
    JELLY_ROLL_DRIVEN: Tape length is calculated from additional_tape_wraps
    TAPE_DRIVEN: Additional_tape_wraps is calculated from tape.length
    """
    JELLY_ROLL_DRIVEN = "self"
    TAPE_DRIVEN = "tape"


def calculate_tape_properties(func):
    """Decorator to recalculate tape-related properties after method execution.
    
    This decorator is used on methods that modify tape properties or geometry
    and ensures that tape roll calculations and bulk properties are updated
    automatically after the method completes.
    
    Parameters
    ----------
    func : callable
        The method to be decorated
        
    Returns
    -------
    callable
        Wrapped method that triggers tape property recalculation
        
    Notes
    -----
    Only triggers recalculation if the instance has _update_properties=True
    and a tape with additional wraps configured.
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        if hasattr(self, "_update_properties") and self._update_properties:
            self._calculate_tape_roll()
        return result

    return wrapper


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
            mandrel: Union[FlatMandrel, RoundMandrel],
            tape: Tape = None,
            additional_tape_wraps: float = 0,
            collector_tab_crumple_factor: float = 50,
            name: str = "Jelly Roll"
        ) -> None:
        """Initialize jelly roll electrode assembly.
        
        Parameters
        ----------
        laminate : Laminate
            The layup structure to be wound
        mandrel : Union[FlatMandrel, RoundMandrel]
            The mandrel for winding
        tape : Optional[Tape], default=None
            Optional tape component to wrap around the jelly roll
        additional_tape_wraps : float, default=0
            Number of additional tape wraps around the jelly roll (beyond the base spiral)
        collector_tab_crumple_factor: float, default=90
            Factor to account for crumpling of the collector tab during encapsulation (percentage)
            
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
        
        # controls
        self._tape_length_driver = TapeDriver.JELLY_ROLL_DRIVEN
            
        self.mandrel = mandrel
        self.additional_tape_wraps = additional_tape_wraps
        super().__init__(layup=laminate, name=name)
        self.collector_tab_crumple_factor = collector_tab_crumple_factor
        self.tape = tape

        self._datum = (0.0, 0.0, 0.0)

    def _calculate_all_properties(self, laminate_x_spacing=0.004, **kwargs) -> None:
        """Calculate all properties of the jelly roll electrode assembly.
        
        This method orchestrates the calculation of spiral geometry, component
        placement, and derived properties in the correct sequence.
        """
        # calculate geometry and spirals
        self._calculate_coordinates(laminate_x_spacing=laminate_x_spacing, **kwargs)

        # calculate bulk properties
        super()._calculate_all_properties()

    def _calculate_coordinates(self, laminate_x_spacing=0.004, **kwargs) -> None:

        # calculate the roll
        self._calculate_roll(laminate_x_spacing=laminate_x_spacing, **kwargs)

        # calculate tape roll if applicable
        if self._tape is not None and self._additional_tape_wraps > 0:
            self._calculate_tape_roll()

        # calculate derived properties  
        self._calculate_roll_properties()

        # calculate spiral-dependent properties
        self._calculate_spiral_properties()

        # calculate top down coordinates
        self._calculate_top_down_coordinates()

        # calculate right-left coordinates
        self._calculate_right_left_coordinates()

    def _calculate_top_down_coordinates(self) -> None:
        """Calculate and store top-down view coordinates for all components.
        
        This method pre-calculates the x and y coordinates for rectangular representations
        of each component in the top-down view. Coordinates are stored in the
        self._component_top_down_coordinates dictionary as numpy arrays (shape: [N, 2])
        for later use in trace creation.
        
        The method handles:
        - Standard components (coatings, separators, current collectors)
        - Tape component (if present)
        - Tab-welded current collector tabs (if present)
        
        Stored coordinates are in millimeters for plotting.
        """
        self._component_top_down_coordinates = {}
        
        # Check if tabs are welded
        cathode_is_tab_welded = isinstance(
            self._layup._cathode._current_collector, TabWeldedCurrentCollector
        )

        anode_is_tab_welded = isinstance(
            self._layup._anode._current_collector, TabWeldedCurrentCollector
        )
        
        # Component configuration: (spiral_key, coords_attr_path)
        component_configs = [
            ('cathode_b_side_coating', '_cathode._b_side_coating_coordinates'),
            ('cathode_current_collector', '_cathode._current_collector._foil_coordinates'),
            ('cathode_a_side_coating', '_cathode._a_side_coating_coordinates'),
            ('bottom_separator', '_bottom_separator._coordinates'),
            ('anode_b_side_coating', '_anode._b_side_coating_coordinates'),
            ('anode_current_collector', '_anode._current_collector._foil_coordinates'),
            ('anode_a_side_coating', '_anode._a_side_coating_coordinates'),
            ('top_separator', '_top_separator._coordinates'),
        ]
        
        # Calculate coordinates for standard components
        for spiral_key, coords_attr_path in component_configs:

            self._calculate_component_top_down_coords(
                spiral_key, 
                coords_attr_path,
                cathode_is_tab_welded,
                anode_is_tab_welded
            )
        
        # Calculate tape coordinates if applicable
        if hasattr(self, '_tape') and self._tape is not None and self._additional_tape_wraps > 0:
            self._calculate_tape_top_down_coords()
        
        # Calculate tab coordinates if tab welded
        if cathode_is_tab_welded:
            self._calculate_tab_top_down_coords('cathode')

        if anode_is_tab_welded:
            self._calculate_tab_top_down_coords('anode')

    def _calculate_component_top_down_coords(
        self,
        spiral_key: str,
        coords_attr_path: str,
        cathode_is_tab_welded: bool,
        anode_is_tab_welded: bool
    ) -> None:
        """Calculate top-down coordinates for a single component.
        
        Parameters
        ----------
        spiral_key : str
            Key to identify component in spiral dictionaries
        coords_attr_path : str
            Dot-separated path to component coordinates (e.g., '_anode._current_collector._foil_coordinates')
        cathode_is_tab_welded : bool
            Whether cathode uses tab-welded current collector
        anode_is_tab_welded : bool
            Whether anode uses tab-welded current collector
        """
        # Get spiral diameter
        spiral = self._extruded_spirals.get(spiral_key)
        spiral_clean = spiral[~np.isnan(spiral[:, RADIUS_COL])]
        max_x = spiral_clean[:, X_COORD_COL].max()
        min_x = spiral_clean[:, X_COORD_COL].min()
        diameter = (max_x - min_x)
        
        # Get component coordinates using attribute path navigation
        coords = self._layup
        for attr in coords_attr_path.split('.'):
            coords = getattr(coords, attr)
        
        # Get Y bounds, filtering out NaN values
        coords_clean = coords[~np.isnan(coords[:, 1])]
        max_y = coords_clean[:, 1].max()
        min_y = coords_clean[:, 1].min()
        
        # Apply tab crumple factor for non-tabbed current collectors
        if spiral_key == 'cathode_current_collector' and not cathode_is_tab_welded:
            tab_height = self._layup._cathode._current_collector._tab_height
            max_y -= tab_height * self._collector_tab_crumple_factor
        elif spiral_key == 'anode_current_collector' and not anode_is_tab_welded:
            tab_height = self._layup._anode._current_collector._tab_height
            min_y += tab_height * self._collector_tab_crumple_factor
        
        # Build rectangular coordinates
        height = max_y - min_y
        x, y = self.build_square_array(-diameter / 2, min_y, diameter, height)
        
        # Store as numpy array with shape [N, 2]
        self._component_top_down_coordinates[spiral_key] = np.column_stack((x, y))

    def _calculate_tape_top_down_coords(self) -> None:
        """Calculate top-down coordinates for tape component."""
        tape_spiral = self._extruded_spirals.get('tape')
        max_x = tape_spiral[:, X_COORD_COL].max()
        min_x = tape_spiral[:, X_COORD_COL].min()
        tape_diameter = max_x - min_x
        tape_width = self._tape._width
        start_y = -tape_width / 2 + self._tape._datum[1]
        x, y = self.build_square_array(-tape_diameter / 2, start_y, tape_diameter, tape_width)
        self._component_top_down_coordinates['tape'] = np.column_stack((x, y))

    def _calculate_tab_top_down_coords(self, electrode_type: str) -> None:
        """Calculate top-down coordinates for electrode tab.
        
        Parameters
        ----------
        electrode_type : str
            Either 'cathode' or 'anode'
        """
        # Get current collector and tab coordinates
        electrode = getattr(self._layup, f'_{electrode_type}')
        current_collector = electrode._current_collector
        tab_coords = current_collector._weld_tabs[0]._foil_coordinates
        
        # Clean NaN values
        tab_coords_clean = tab_coords[~np.isnan(tab_coords[:, 0])]
        
        # Get tab dimensions
        tab_width = tab_coords_clean[:, 0].max() - tab_coords_clean[:, 0].min()
        tab_max_y = tab_coords_clean[:, 1].max()
        tab_min_y = tab_coords_clean[:, 1].min()
        
        # Apply crumple factor adjustment
        tab_overhang = current_collector._tab_overhang
        crumple_adjustment = tab_overhang * self._collector_tab_crumple_factor
        
        if electrode_type == 'cathode':
            # Cathode tab extends upward - reduce height from top
            tab_height = (tab_max_y - crumple_adjustment) - tab_min_y
        else:  # anode
            # Anode tab extends downward - reduce height from bottom
            tab_min_y += crumple_adjustment
            tab_height = tab_max_y - tab_min_y - crumple_adjustment
        
        # Build rectangular coordinates centered on x-axis
        x, y = self.build_square_array(-tab_width / 2, tab_min_y, tab_width, tab_height)

        self._component_top_down_coordinates[f'{electrode_type}_tab'] = np.column_stack((x, y))

    def _calculate_right_left_coordinates(self) -> None:
        """Calculate and store top-down view coordinates for all components.
        
        This method pre-calculates the x and y coordinates for rectangular representations
        of each component in the top-down view. Coordinates are stored in the
        self._component_right_left dictionary as numpy arrays (shape: [N, 2])
        for later use in trace creation.
        
        The method handles:
        - Standard components (coatings, separators, current collectors)
        - Tape component (if present)
        - Tab-welded current collector tabs (if present)
        
        Stored coordinates are in millimeters for plotting.
        """
        self._component_right_left_coordinates = {}
        
        # Check if tabs are welded
        cathode_is_tab_welded = isinstance(
            self._layup._cathode._current_collector, TabWeldedCurrentCollector
        )
        anode_is_tab_welded = isinstance(
            self._layup._anode._current_collector, TabWeldedCurrentCollector
        )
        
        # Component configuration: (spiral_key, coords_attr_path)
        component_configs = [
            ('cathode_b_side_coating', '_cathode._b_side_coating_coordinates'),
            ('cathode_current_collector', '_cathode._current_collector._foil_coordinates'),
            ('cathode_a_side_coating', '_cathode._a_side_coating_coordinates'),
            ('bottom_separator', '_bottom_separator._coordinates'),
            ('anode_b_side_coating', '_anode._b_side_coating_coordinates'),
            ('anode_current_collector', '_anode._current_collector._foil_coordinates'),
            ('anode_a_side_coating', '_anode._a_side_coating_coordinates'),
            ('top_separator', '_top_separator._coordinates'),
        ]
        
        # Calculate coordinates for standard components
        for spiral_key, coords_attr_path in component_configs:
            self._calculate_component_right_left_coords(
                spiral_key, 
                coords_attr_path,
                cathode_is_tab_welded,
                anode_is_tab_welded
            )
        
        # Calculate tape coordinates if applicable
        if hasattr(self, '_tape') and self._tape is not None and self._additional_tape_wraps > 0:
            self._calculate_tape_right_left_coords()
        
        # Calculate tab coordinates if tab welded
        if cathode_is_tab_welded:
            self._calculate_tab_right_left_coords('cathode')
        if anode_is_tab_welded:
            self._calculate_tab_right_left_coords('anode')

    def _calculate_component_right_left_coords(
        self,
        spiral_key: str,
        coords_attr_path: str,
        cathode_is_tab_welded: bool,
        anode_is_tab_welded: bool
    ) -> None:
        """Calculate top-down coordinates for a single component.
        
        Parameters
        ----------
        spiral_key : str
            Key to identify component in spiral dictionaries
        coords_attr_path : str
            Dot-separated path to component coordinates (e.g., '_anode._current_collector._foil_coordinates')
        cathode_is_tab_welded : bool
            Whether cathode uses tab-welded current collector
        anode_is_tab_welded : bool
            Whether anode uses tab-welded current collector
        """
        # Get spiral diameter
        spiral = self._extruded_spirals.get(spiral_key)
        spiral_clean = spiral[~np.isnan(spiral[:, RADIUS_COL])]
        max_z = spiral_clean[:, Z_COORD_COL].max()
        min_z = spiral_clean[:, Z_COORD_COL].min()
        diameter = (max_z - min_z)
        
        # Get component coordinates using attribute path navigation
        coords = self._layup
        for attr in coords_attr_path.split('.'):
            coords = getattr(coords, attr)
        
        # Get Y bounds, filtering out NaN values
        coords_clean = coords[~np.isnan(coords[:, 1])]
        max_y = coords_clean[:, 1].max()
        min_y = coords_clean[:, 1].min()
        
        # Apply tab crumple factor for non-tabbed current collectors
        if spiral_key == 'cathode_current_collector' and not cathode_is_tab_welded:
            tab_height = self._layup._cathode._current_collector._tab_height
            max_y -= tab_height * self._collector_tab_crumple_factor
        elif spiral_key == 'anode_current_collector' and not anode_is_tab_welded:
            tab_height = self._layup._anode._current_collector._tab_height
            min_y += tab_height * self._collector_tab_crumple_factor
        
        # Build rectangular coordinates
        height = max_y - min_y
        y, z = self.build_square_array(min_y, -diameter / 2, height, diameter)
        
        # Store as numpy array with shape [N, 2]
        self._component_right_left_coordinates[spiral_key] = np.column_stack((y, z))

    def _calculate_tape_right_left_coords(self) -> None:
        """Calculate top-down coordinates for tape component."""
        tape_spiral = self._extruded_spirals.get('tape')
        max_z = tape_spiral[:, Z_COORD_COL].max()
        min_z = tape_spiral[:, Z_COORD_COL].min()
        tape_diameter = max_z - min_z
        tape_width = self._tape._width
        start_y = -tape_width / 2 + self._tape._datum[1]
        y, z = self.build_square_array(start_y, -tape_diameter / 2, tape_width, tape_diameter)
        self._component_right_left_coordinates['tape'] = np.column_stack((y, z))

    def _calculate_tab_right_left_coords(self, electrode_type: str) -> None:
        """Calculate top-down coordinates for electrode tab.
        
        Parameters
        ----------
        electrode_type : str
            Either 'cathode' or 'anode'
        """
        # Get current collector and tab coordinates
        electrode = getattr(self._layup, f'_{electrode_type}')
        current_collector = electrode._current_collector
        tab_coords = current_collector._weld_tabs[0]._foil_coordinates
        
        # Clean NaN values
        tab_coords_clean = tab_coords[~np.isnan(tab_coords[:, 0])]
        
        # Get tab dimensions
        tab_width = tab_coords_clean[:, 0].max() - tab_coords_clean[:, 0].min()
        tab_max_y = tab_coords_clean[:, 1].max()
        tab_min_y = tab_coords_clean[:, 1].min()
        
        # Apply crumple factor adjustment
        tab_overhang = current_collector.tab_overhang
        crumple_adjustment = tab_overhang * self._collector_tab_crumple_factor
        
        if electrode_type == 'cathode':
            # Cathode tab extends upward - reduce height from top
            tab_height = (tab_max_y - crumple_adjustment) - tab_min_y
        else:  # anode
            # Anode tab extends downward - reduce height from bottom
            tab_min_y += crumple_adjustment
            tab_height = tab_max_y - tab_min_y - crumple_adjustment
        
        # Build rectangular coordinates centered on x-axis
        y, z = self.build_square_array(tab_min_y, -tab_width / 2, tab_height, tab_width)
        self._component_right_left_coordinates[f'{electrode_type}_tab'] = np.column_stack((y, z))

    def _calculate_roll(self, laminate_x_spacing=0.004, **kwargs) -> None:
        """Calculate the basic jelly roll geometry and component placement.
        
        This method orchestrates the core spiral calculation workflow:
        1. Flattens the layup center lines with specified spacing
        2. Calculates the variable thickness spiral path
        3. Maps components onto the spiral
        4. Creates extruded visualization shapes
        5. Centers the spirals for proper visualization
        
        Parameters
        ----------
        laminate_x_spacing : float, default=0.004
            Spacing between points along the x-axis for center line calculation in meters
        **kwargs
            Additional arguments passed to spiral calculation methods
        """
        self._layup.calculate_flattened_center_lines(x_spacing=laminate_x_spacing)
        self._calculate_variable_thickness_spiral(**kwargs)        
        self._build_component_spirals()
        self._build_extruded_component_spirals()
        self._center_spirals()

    def _calculate_bulk_properties(self):
        """Calculate bulk properties including tape properties if tape is present.
        
        This method extends the parent's bulk property calculations to include
        tape-specific properties when a tape is configured with additional wraps.
        It then calculates geometry parameters and delegates to the parent for
        final bulk property calculations.
        """

        if hasattr(self, "_tape") and self._tape is not None:
            self._calculate_tape_bulk_properties()
        
        self._calculate_geometry_parameters()
        super()._calculate_bulk_properties()

    def _calculate_pore_volume(self):
        
        _cathode_pore_volume = self._layup._cathode._pore_volume
        _anode_pore_volume = self._layup._anode._pore_volume
        self._pore_volume = _cathode_pore_volume + _anode_pore_volume

    def _get_center_point(self) -> Tuple[float, float, float]:
        """Get the center point of the jelly roll assembly.
        
        Returns the datum of the jelly roll, which represents its center point.
        
        Returns
        -------
        Tuple[float, float, float]
            (x, y, z) coordinates of the center point in millimeters
        """
        # get all spiral coordinates
        all_spirals = np.vstack(list(self._component_spirals.values()))
        all_spirals = all_spirals[~np.isnan(all_spirals[:, X_COORD_COL])]
        x_center = (all_spirals[:, X_COORD_COL].max() + all_spirals[:, X_COORD_COL].min()) / 2
        z_center = (all_spirals[:, Z_COORD_COL].max() + all_spirals[:, Z_COORD_COL].min()) / 2

        # get all top down coordinates
        all_top_down = np.vstack(list(self._component_top_down_coordinates.values()))
        y_center = (all_top_down[:, 1].max() + all_top_down[:, 1].min()) / 2

        return (x_center, y_center, z_center)

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

    def _calculate_inner_interface_area(
            self, 
            cathode_coords: np.ndarray, 
            anode_coords: np.ndarray
        ) -> float:
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
        cathode_segments = []
        anode_segments = []

        if not np.isnan(cathode_coords).any():
            cathode_segments = [cathode_coords]
        else:
            cathode_segments = self._extract_coordinate_segments(cathode_coords[:,0], cathode_coords[:,1], unify_xy=True)

        if not np.isnan(anode_coords).any():
            anode_segments = [anode_coords]
        else:
            anode_segments = self._extract_coordinate_segments(anode_coords[:,0], anode_coords[:,1], unify_xy=True)

        intersection_area = 0.0
        for c_segment in cathode_segments:
            for a_segment in anode_segments:
                intersection_area += self.get_coordinate_intersection(c_segment, a_segment)

        return intersection_area

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
        # shift cathode coords by inner rotation amount
        cathode_shift = self._calculate_full_rotation_shift()
        shifted_cathode_coords = cathode_coords + np.array([cathode_shift, 0])
        
        if not np.isnan(shifted_cathode_coords).any():
            cathode_segments = [shifted_cathode_coords]
        else:
            cathode_segments = self._extract_coordinate_segments(shifted_cathode_coords[:,0], shifted_cathode_coords[:,1], unify_xy=True)

        if not np.isnan(anode_coords).any():
            anode_segments = [anode_coords]
        else:
            anode_segments = self._extract_coordinate_segments(anode_coords[:,0], anode_coords[:,1], unify_xy=True)

        intersection_area = 0.0
        for c_segment in cathode_segments:
            for a_segment in anode_segments:
                intersection_area += self.get_coordinate_intersection(c_segment, a_segment)

        return intersection_area
        
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
        """Calculate properties derived from the spiral geometry.
        
        This method computes secondary properties that depend on the spiral
        configuration, primarily the interfacial area between electrodes.
        Should be called after spiral geometry has been established.
        """
        self._calculate_interfacial_area()

    def _calculate_tape_bulk_properties(self) -> None:
        """Calculate bulk properties for the tape component.
        
        Determines the tape length or additional wraps based on the current driver mode:
        - JELLY_ROLL_DRIVEN: calculates tape.length from additional_tape_wraps
        - TAPE_DRIVEN: calculates additional_tape_wraps from tape.length
        
        This bidirectional approach allows users to specify either parameter
        and have the other automatically calculated based on the spiral geometry.
        
        Notes
        -----
        The tape length is calculated from the difference between maximum
        and minimum unwrapped spiral coordinates of the tape path.
        """
        tape_spiral = self._component_spirals.get('tape', None)

        if self._tape_length_driver == TapeDriver.JELLY_ROLL_DRIVEN:
            if tape_spiral is None:
                self._tape.length = 0
            else:
                tape_length = (tape_spiral[:, X_UNWRAPPED_COL].max() - tape_spiral[:, X_UNWRAPPED_COL].min()) * M_TO_MM
                self._tape.length = tape_length

        elif self._tape_length_driver == TapeDriver.TAPE_DRIVEN:
            if tape_spiral is None:
                self._additional_tape_wraps = 0
            else:
                tape_wraps = (tape_spiral[:, TURNS_COL].max() - tape_spiral[:, TURNS_COL].min())
                self._additional_tape_wraps = tape_wraps

        else: 
            raise ValueError(f"Invalid tape length driver: {self._tape_length_driver}")

    def _translate_spirals_xz(
            self, 
            x_shift: float, 
            z_shift: float
        ) -> Tuple[np.ndarray, Dict[str, np.ndarray], Dict[str, np.ndarray]]:
        """Translate all spiral coordinates by specified amounts in x and z directions.
        
        This method applies a rigid body translation to all spiral geometries,
        including the base spiral, component spirals, and extruded spirals.
        Commonly used for centering spirals or aligning them to a coordinate system.
        
        Parameters
        ----------
        x_shift : float
            Translation distance in x-direction (meters)
        z_shift : float
            Translation distance in z-direction (meters)
            
        Returns
        -------
        Tuple[np.ndarray, Dict[str, np.ndarray], Dict[str, np.ndarray]]
            Updated (spiral, component_spirals, extruded_spirals) after translation
        """
        # Use SpiralCalculator helper to translate all spirals
        self._spiral = SpiralCalculator.translate_spirals_xz(self._spiral, x_shift, z_shift)
        self._component_spirals = SpiralCalculator.translate_spirals_xz(self._component_spirals, x_shift, z_shift)
        self._extruded_spirals = SpiralCalculator.translate_spirals_xz(self._extruded_spirals, x_shift, z_shift)

        return self._spiral, self._component_spirals, self._extruded_spirals
    
    def _translate_top_down_coordinates(
            self, 
            x_shift: float, 
            y_shift: float
        ) -> Dict[str, np.ndarray]:
        """Translate all top-down coordinates by specified amounts in x and y directions.
        
        This method applies a rigid body translation to all top-down component
        coordinates stored in self._component_top_down_coordinates.
        
        Parameters
        ----------
        x_shift : float
            Translation distance in x-direction (millimeters)
        y_shift : float
            Translation distance in y-direction (millimeters)
            
        Returns
        -------
        Dict[str, np.ndarray]
            Updated top-down coordinates after translation
        """
        new_top_down_coords = {}
        for name, coords in self._component_top_down_coordinates.items():
            new_coords = coords
            new_coords[:, 0] += x_shift
            new_coords[:, 1] += y_shift
            new_top_down_coords[name] = new_coords

        self._component_top_down_coordinates = new_top_down_coords

        return self._component_top_down_coordinates
    
    def _translate_right_left_coordinates(
            self, 
            y_shift: float, 
            z_shift: float
        ) -> Dict[str, np.ndarray]:
        """Translate all right-left coordinates by specified amounts in y and z directions.
        
        This method applies a rigid body translation to all right-left component
        coordinates stored in self._component_right_left_coordinates.
        
        Parameters
        ----------
        y_shift : float
            Translation distance in y-direction (millimeters)
        z_shift : float
            Translation distance in z-direction (millimeters)
            
        Returns
        -------
        Dict[str, np.ndarray]
            Updated right-left coordinates after translation
        """
        new_right_left_coords = {}

        for name, coords in self._component_right_left_coordinates.items():
            new_coords = coords
            new_coords[:, 0] += y_shift
            new_coords[:, 1] += z_shift
            new_right_left_coords[name] = new_coords

        self._component_right_left_coordinates = new_right_left_coords

        return self._component_right_left_coordinates

    @staticmethod
    def position_layup_on_mandrel(
        layup: Laminate, 
        mandrel: Union[FlatMandrel, RoundMandrel]
        ) -> Laminate:
        """Position a layup correctly relative to a mandrel's coordinate system.
        
        This method calculates the proper datum (coordinate offset) for the layup
        so that it is correctly positioned relative to the mandrel for winding.
        The positioning ensures that:
        - The layup starts at the mandrel surface
        - Component coordinates are properly aligned
        - The minimum z-coordinate is set to mandrel radius
        
        Parameters
        ----------
        layup : Laminate
            The layup structure to be positioned
        mandrel : Union[FlatMandrel, RoundMandrel]
            The mandrel around which the layup will be wound
            
        Returns
        -------
        Laminate
            The same layup object with updated datum coordinates
            
        Notes
        -----
        This method modifies the layup's datum property to ensure proper
        positioning for spiral calculations. The datum is converted between
        meters and millimeters as needed for internal coordinate systems.
        """
        
        # get the min x of the layup
        coords = [
            layup._anode._current_collector._foil_coordinates[:,0],
            layup._cathode._current_collector._foil_coordinates[:,0],
            layup._bottom_separator._coordinates[:,0],
            layup._top_separator._coordinates[:,0]
        ]

        x_coords = np.concatenate(coords)
        x_coords = x_coords[~np.isnan(x_coords)]
        layup_min_x = np.min(x_coords)

        # get the most negative z value
        cathode_b_side_coated_z = layup._cathode._b_side_coating_coordinates[:,2]
        cathode_b_side_coated_z = cathode_b_side_coated_z[~np.isnan(cathode_b_side_coated_z)]
        layup_min_z = np.min(cathode_b_side_coated_z)

        # set the new x value
        new_x = (layup.datum[0] * MM_TO_M) - layup_min_x

        # set the new y value
        new_y = (layup.datum[1] * MM_TO_M)

        # set the new z value
        new_z = (layup.datum[2] * MM_TO_M) - layup_min_z + mandrel._radius

        # Convert back to mm and set the new datum
        layup.datum = (new_x * M_TO_MM, new_y * M_TO_MM, new_z * M_TO_MM)

        return layup

    @abstractmethod
    def _calculate_variable_thickness_spiral(self, dtheta) -> np.ndarray:
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

    def _calculate_tape_roll(self, **kwargs) -> Tuple[Dict[str, np.ndarray], Dict[str, np.ndarray]]:
        """Calculate tape spiral around the existing jelly roll assembly.
        
        This unified method handles both round and racetrack geometries by:
        1. Finding the appropriate geometry parameters for the tape starting radius
        2. Creating the appropriate spiral type (round or racetrack)
        3. Centering the tape spiral around the existing assembly
        4. Building appropriate extruded tape visualization
        5. Updating the spiral geometries
        
        Parameters
        ----------
        **kwargs
            Additional arguments passed to tape spiral calculation
            
        Returns
        -------
        Tuple[Dict[str, np.ndarray], Dict[str, np.ndarray]]
            Updated (component_spirals, extruded_spirals) including tape
            
        Notes
        -----
        The tape wraps around the outermost surface of the jelly roll,
        adding the specified number of additional turns for insulation.
        """
        # Get the extruded spirals
        extruded_spirals = self._extruded_spirals.copy()

        # Remove tape spiral if it exists to avoid wrapping around it again
        extruded_spirals.pop('tape', None)

        # Concatenate all extruded spirals to find geometry parameters
        spirals = [s for s in extruded_spirals.values()]
        spirals = np.concatenate(spirals, axis=0)
        spirals_x_z = np.column_stack((spirals[:, X_COORD_COL], spirals[:, Z_COORD_COL]))
        
        # Get geometry-specific parameters
        tape_params = self._get_tape_geometry_parameters(spirals_x_z)

        # Calculate the appropriate spiral type
        tape_spiral = self._calculate_tape_spiral(tape_params, **kwargs)

        # Build extruded tape spiral using appropriate method
        extruded_tape_spiral = self._build_tape_extruded_spiral(tape_spiral)
        
        self._component_spirals['tape'] = tape_spiral
        self._extruded_spirals['tape'] = extruded_tape_spiral['tape']

        # Update the geometry parameters after adding the tape spiral
        return self._component_spirals, self._extruded_spirals

    @abstractmethod
    def _get_tape_geometry_parameters(self, spirals_x_z: np.ndarray) -> Dict[str, Any]:
        """Get geometry-specific parameters for tape calculation.
        
        Parameters
        ----------
        spirals_x_z : np.ndarray
            Combined X-Z coordinates of all existing spirals
            
        Returns
        -------
        Dict[str, Any]
            Dictionary containing geometry-specific parameters needed for tape calculation
        """
        pass

    @abstractmethod 
    def _calculate_tape_spiral(self, tape_params: Dict[str, Any], **kwargs) -> np.ndarray:
        """Calculate the tape spiral using geometry-specific method.
        
        Parameters
        ----------
        tape_params : Dict[str, Any]
            Geometry-specific parameters from _get_tape_geometry_parameters
        **kwargs
            Additional arguments passed to spiral calculation
            
        Returns
        -------
        np.ndarray
            Tape spiral coordinates
        """
        pass

    @abstractmethod
    def _build_tape_extruded_spiral(self, tape_spiral: np.ndarray) -> Dict[str, np.ndarray]:
        """Build extruded tape spiral using geometry-specific method.
        
        Parameters
        ----------
        tape_spiral : np.ndarray
            Tape spiral coordinates
            
        Returns
        -------
        Dict[str, np.ndarray]
            Dictionary with 'tape' key containing extruded spiral
        """
        pass

    def _apply_tape_pre_centering_transforms(self, tape_params: Dict[str, Any]) -> None:
        """Apply any geometry-specific transforms before final centering.
        
        Default implementation does nothing. Subclasses can override for specific behavior.
        
        Parameters
        ----------
        tape_params : Dict[str, Any]
            Geometry-specific parameters
        """
        pass

    @abstractmethod
    def _center_spirals(self) -> None:
        """Center the spiral geometry around the origin.
        
        This method must be implemented by subclasses to adjust the spiral coordinates
        so that the center of mass or geometric center is at the origin for visualization.
        """
        pass

    def calculate_high_resolution_roll(self, **kwargs) -> None:
        """Generate high-resolution geometry for detailed analysis.
        
        Recalculates the jelly roll using finer spacing parameters for
        more accurate visualization and analysis. Subclasses can override
        the default parameters by providing them in kwargs.
        
        Parameters
        ----------
        **kwargs
            Geometry-specific high-resolution parameters
            
        Notes
        -----
        High-resolution calculations take significantly longer to compute
        but provide much smoother curves and more accurate results.
        """
        # Default high-resolution parameters
        default_params = {
            'laminate_x_spacing': 0.001,  # 1mm spacing for center lines
        }
        
        # Add geometry-specific defaults
        geometry_params = self._get_high_resolution_params()
        default_params.update(geometry_params)
        
        # Override with any user-provided parameters
        default_params.update(kwargs)
        
        # Recalculate with high-resolution parameters
        self._calculate_all_properties(**default_params)

    @abstractmethod
    def _get_high_resolution_params(self) -> Dict[str, Any]:
        """Get geometry-specific high-resolution parameters.
        
        Returns
        -------
        Dict[str, Any]
            Dictionary containing geometry-specific high-resolution parameters
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
        separators = [self._layup._bottom_separator, self._layup._top_separator]

        self._mass = self._layup._anode._mass + self._layup._cathode._mass + sum(s._mass for s in separators)

        self._mass_breakdown = {
            "Anode": self._layup._anode._mass_breakdown,
            "Cathode": self._layup._cathode._mass_breakdown,
            "Separators": self.sum_breakdowns(separators, "mass"),
        }

        if self._tape is not None and self._additional_tape_wraps > 0:
            self._mass += self._tape._mass
            self._mass_breakdown["Tape"] = self._tape._mass

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
        separators = [self._layup._bottom_separator, self._layup._top_separator]

        self._cost = self._layup._anode._cost + self._layup._cathode._cost + sum(s._cost for s in separators)

        self._cost_breakdown = {
            "Anode": self._layup._anode._cost_breakdown,
            "Cathode": self._layup._cathode._cost_breakdown,
            "Separators": self.sum_breakdowns(separators, "cost"),
        }

        if self._tape is not None and self._additional_tape_wraps > 0:
            self._cost += self._tape._cost
            self._cost_breakdown["Tape"] = self._tape._cost

        return self._cost

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
            line=dict(color='black', width=0.1),
            line_shape='spline',
            name=name,
            customdata=customdata,
            hovertemplate=hovertemplate,
            legendgroup=name,
        )

    def _get_cathode_tab_y_position(self) -> float:
        """Get cathode current collector tab Y position.
        
        Returns
        -------
        float
            Maximum Y coordinate of cathode current collector foil minus tab (meters)
        """
        from steer_opencell_design.Components.CurrentCollectors.Tabbed import TabWeldedCurrentCollector 

        if type(self._layup._cathode._current_collector) == TabWeldedCurrentCollector:
            cathode_tab_deduction = self._layup._cathode._current_collector._tab_overhang
        else:
            cathode_tab_deduction = (
                self._layup._cathode._current_collector._tab_height * 
                self._collector_tab_crumple_factor
            )

        max_y = self._layup._cathode._current_collector._foil_coordinates[:, 1].max()

        return max_y - cathode_tab_deduction

    def _get_anode_tab_y_position(self) -> float:
        """Get anode current collector tab Y position.
        
        Returns
        -------
        float
            Minimum Y coordinate of anode current collector foil plus tab (meters)
        """
        from steer_opencell_design.Components.CurrentCollectors.Tabbed import TabWeldedCurrentCollector

        if type(self._layup._anode._current_collector) == TabWeldedCurrentCollector:
            anode_tab_deduction = self._layup._anode._current_collector._tab_overhang
        else:
            anode_tab_deduction = (
                self._layup._anode._current_collector._tab_height * 
                self._collector_tab_crumple_factor
            )

        min_y = self._layup._anode._current_collector._foil_coordinates[:, 1].min()

        return min_y + anode_tab_deduction

    def get_spiral_plot(self, layered: bool = True,**kwargs: Any) -> go.Figure:
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

        if layered:

            extruded_traces = [
                self.anode_a_side_coating_extruded_spiral_trace,
                self.anode_current_collector_extruded_spiral_trace,
                self.anode_b_side_coating_extruded_spiral_trace,
                self.cathode_a_side_coating_extruded_spiral_trace,
                self.cathode_current_collector_extruded_spiral_trace,
                self.cathode_b_side_coating_extruded_spiral_trace,
                self.top_separator_extruded_spiral_trace,
                self.bottom_separator_extruded_spiral_trace,
            ]
            
            line_traces = [
                self.top_separator_spiral_trace,
                self.anode_a_side_coating_spiral_trace,
                self.anode_current_collector_spiral_trace,
                self.anode_b_side_coating_spiral_trace,
                self.bottom_separator_spiral_trace,
                self.cathode_a_side_coating_spiral_trace,
                self.cathode_current_collector_spiral_trace,
                self.cathode_b_side_coating_spiral_trace,
            ]

            if hasattr(self, "_tape") and self._tape is not None and self._additional_tape_wraps > 0:
                extruded_traces.append(self.tape_extruded_spiral_trace)
                line_traces.append(self.tape_spiral_trace)
            
            fig = go.Figure(data=extruded_traces + line_traces)
            
        else:

            fig = go.Figure(data=[self.spiral_trace])

        fig.update_layout(
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            xaxis=self.SCHEMATIC_X_AXIS,
            yaxis=self.SCHEMATIC_Z_AXIS,
            hovermode="closest",
            **kwargs
        )

        return fig
        
    def get_top_down_view(self, opacity: float = 0.5, **kwargs) -> go.Figure:
        """Generate top-down view of the jelly roll with all component layers.
        
        Parameters
        ----------
        opacity : float, default=0.5
            Opacity level for all component traces
        **kwargs
            Additional layout options for the figure
            
        Returns
        -------
        go.Figure
            Plotly figure showing the top-down view
        """
        # Collect all traces from properties
        traces = []
        
        # Add tabs first (they appear on top)
        if self.cathode_tab_top_down_trace is not None:
            traces.append(self.cathode_tab_top_down_trace)
        if self.anode_tab_top_down_trace is not None:
            traces.append(self.anode_tab_top_down_trace)
        
        # Add main component traces in order
        for trace_property in [
            self.cathode_b_side_coating_top_down_trace,
            self.cathode_current_collector_top_down_trace,
            self.cathode_a_side_coating_top_down_trace,
            self.bottom_separator_top_down_trace,
            self.anode_b_side_coating_top_down_trace,
            self.anode_current_collector_top_down_trace,
            self.anode_a_side_coating_top_down_trace,
            self.top_separator_top_down_trace,
        ]:
            if trace_property is not None:
                traces.append(trace_property)
        
        # Add tape if present
        if self.tape_top_down_trace is not None:
            traces.append(self.tape_top_down_trace)
        
        # Apply opacity to all traces
        for trace in traces:
            self.adjust_trace_opacity(trace, opacity)

        figure = go.Figure()
        figure.add_traces(traces)

        figure.update_layout(
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            xaxis=self.SCHEMATIC_X_AXIS,
            yaxis=self.SCHEMATIC_Y_AXIS,
            hovermode="closest",
            **kwargs
        )

        return figure

    def get_side_view(self, opacity: float = 0.5, **kwargs) -> go.Figure:
        """Generate right-left side view of the jelly roll with all component layers.
        
        Parameters
        ----------
        opacity : float, default=0.5
            Opacity level for all component traces
        **kwargs
            Additional layout options for the figure
            
        Returns
        -------
        go.Figure
            Plotly figure showing the right-left side view
        """
        # Collect all traces from properties
        traces = []
        
        # Add main component traces in order
        for trace_property in [
            self.cathode_b_side_coating_right_left_trace,
            self.cathode_current_collector_right_left_trace,
            self.cathode_a_side_coating_right_left_trace,
            self.bottom_separator_right_left_trace,
            self.anode_b_side_coating_right_left_trace,
            self.anode_current_collector_right_left_trace,
            self.anode_a_side_coating_right_left_trace,
            self.top_separator_right_left_trace,
        ]:
            if trace_property is not None:
                traces.append(trace_property)
        
        # Add tape if present
        if self.tape_right_left_trace is not None:
            traces.append(self.tape_right_left_trace)
        
        # Apply opacity to all traces
        for trace in traces:
            self.adjust_trace_opacity(trace, opacity)

        figure = go.Figure()
        figure.add_traces(traces)

        figure.update_layout(
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            xaxis=self.SCHEMATIC_Y_AXIS,
            yaxis=self.SCHEMATIC_Z_AXIS,
            hovermode="closest",
            **kwargs
        )

        return figure

    @property
    def tape_length_driver(self) -> TapeDriver:
        """Get the current tape length driver mode.
        
        Returns
        -------
        TapeDriver
            Current driver mode (JELLY_ROLL_DRIVEN or TAPE_DRIVEN)
        """
        return self._tape_length_driver
    
    @property
    def collector_tab_crumple_factor(self) -> float:
        """Return the collector tab crumple factor."""
        return np.round(self._collector_tab_crumple_factor * 100, 0)

    @property
    def additional_tape_wraps(self) -> float:
        """Return the number of additional tape wraps applied to the jelly roll."""
        return np.round(self._additional_tape_wraps, 2)

    @property
    def additional_tape_wraps_range(self) -> Tuple[float, float]:
        """Return the valid range for additional tape wraps."""
        return (0.0, 10.0)

    @property
    def tape(self) -> Tape:
        """Return the tape used for the jelly roll assembly."""
        return self._tape

    @property
    def roll_properties(self) -> pd.DataFrame:
        """Return the roll properties as a pandas DataFrame with values rounded to 2 decimal places.
        
        Returns
        -------
        pd.DataFrame
            DataFrame containing roll properties with component names as index and turn counts as values.
        """
        # Create a formatted dictionary with rounded values
        formatted_props = {key: np.round(value, 2) for key, value in self._roll_properties.items()}
        
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
        
        df_reordered = df.reindex(ordered_index)
        
        # Format component names: replace underscores with spaces and capitalize
        formatted_index = []
        for component_name in df_reordered.index:
            # Replace underscores with spaces and capitalize each word
            formatted_name = component_name.replace('_', ' ').title()
            formatted_index.append(formatted_name)
        
        df_reordered.index = formatted_index
        
        return df_reordered

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
    def tape_spiral(self) -> pd.DataFrame:
        """Return the tape spiral as a pandas DataFrame.
        Columns: theta, x_unwrapped, thickness, r, x, y
        """
        if hasattr(self, '_tape') and self._tape is not None and self._additional_tape_wraps > 0:
            tape_spiral = self._component_spirals.get("tape")
            return SpiralCalculator.format_np_spiral_for_df(tape_spiral)
        else:
            return pd.DataFrame(columns=['Theta (degrees)', 'Unwrapped Length (mm)', 'Thickness (mm)', 'Radius (mm)', 'X (mm)', 'Z (mm)'])

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
    def tape_extruded_spiral(self) -> pd.DataFrame:
        if hasattr(self, '_tape') and self._tape is not None and self._additional_tape_wraps > 0:
            tape_extruded_spiral = self._extruded_spirals.get("tape")
            return SpiralCalculator.format_np_spiral_for_df(tape_extruded_spiral)
        else:
            return pd.DataFrame(columns=['Theta (degrees)', 'Unwrapped Length (mm)', 'Thickness (mm)', 'Radius (mm)', 'X (mm)', 'Z (mm)'])

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
        return self._format_spiral_trace("top_separator_spiral", self._layup.top_separator.material._color, f"Top Separator")
    
    @property
    def tape_spiral_trace(self) -> go.Scatter:
        return self._format_spiral_trace("tape_spiral", self._tape._material._color, f"Tape")

    @property
    def bottom_separator_spiral_trace(self) -> go.Scatter:
        return self._format_spiral_trace("bottom_separator_spiral", self._layup.bottom_separator.material._color, f"Bottom Separator")
    
    @property
    def anode_a_side_coating_spiral_trace(self) -> go.Scatter:
        return self._format_spiral_trace("anode_a_side_coating_spiral", self._layup._anode.formulation._color, f"Anode a-side Coating")
    
    @property
    def anode_current_collector_spiral_trace(self) -> go.Scatter:
        return self._format_spiral_trace("anode_current_collector_spiral", self._layup._anode.current_collector.material._color, f"Anode Current Collector")
    
    @property
    def anode_b_side_coating_spiral_trace(self) -> go.Scatter:
        return self._format_spiral_trace("anode_b_side_coating_spiral", self._layup._anode.formulation._color, f"Anode b-side Coating")
    
    @property
    def cathode_a_side_coating_spiral_trace(self) -> go.Scatter:
        return self._format_spiral_trace("cathode_a_side_coating_spiral", self._layup._cathode.formulation._color, f"Cathode a-side Coating")

    @property
    def cathode_current_collector_spiral_trace(self) -> go.Scatter:
        return self._format_spiral_trace("cathode_current_collector_spiral", self._layup._cathode.current_collector.material._color, f"Cathode Current Collector")
    
    @property
    def cathode_b_side_coating_spiral_trace(self) -> go.Scatter:
        return self._format_spiral_trace("cathode_b_side_coating_spiral", self._layup._cathode.formulation._color, f"Cathode b-side Coating")
    
    @property
    def tape_extruded_spiral_trace(self) -> go.Scatter:
        return self._format_extruded_spiral_trace("tape_extruded_spiral", self._tape._material._color, f"Tape")

    @property
    def top_separator_extruded_spiral_trace(self) -> go.Scatter:
        return self._format_extruded_spiral_trace("top_separator_extruded_spiral", self._layup.top_separator.material._color, f"Top Separator")

    @property
    def bottom_separator_extruded_spiral_trace(self) -> go.Scatter:
        return self._format_extruded_spiral_trace("bottom_separator_extruded_spiral", self._layup.bottom_separator.material._color, f"Bottom Separator")

    @property
    def anode_a_side_coating_extruded_spiral_trace(self) -> go.Scatter:
        return self._format_extruded_spiral_trace("anode_a_side_coating_extruded_spiral", self._layup._anode._formulation._color, f"Anode a-side Coating")

    @property
    def anode_current_collector_extruded_spiral_trace(self) -> go.Scatter:
        return self._format_extruded_spiral_trace("anode_current_collector_extruded_spiral", self._layup._anode.current_collector.material._color, f"Anode Current Collector")   

    @property
    def anode_b_side_coating_extruded_spiral_trace(self) -> go.Scatter:
        return self._format_extruded_spiral_trace("anode_b_side_coating_extruded_spiral", self._layup._anode.formulation._color, f"Anode b-side Coating")

    @property
    def cathode_a_side_coating_extruded_spiral_trace(self) -> go.Scatter:
        return self._format_extruded_spiral_trace("cathode_a_side_coating_extruded_spiral", self._layup._cathode.formulation._color, f"Cathode a-side Coating")
    
    @property
    def cathode_current_collector_extruded_spiral_trace(self) -> go.Scatter:
        return self._format_extruded_spiral_trace("cathode_current_collector_extruded_spiral", self._layup._cathode.current_collector.material._color, f"Cathode Current Collector")
    
    @property
    def cathode_b_side_coating_extruded_spiral_trace(self) -> go.Scatter:
        return self._format_extruded_spiral_trace("cathode_b_side_coating_extruded_spiral", self._layup._cathode.formulation._color, f"Cathode b-side Coating")

    @property
    def cathode_b_side_coating_top_down_trace(self) -> go.Scatter:
        """Get cathode b-side coating trace for top-down view."""
        if 'cathode_b_side_coating' not in self._component_top_down_coordinates:
            return None
        coords = self._component_top_down_coordinates['cathode_b_side_coating']
        return go.Scatter(
            x=coords[:, 0] * M_TO_MM,
            y=coords[:, 1] * M_TO_MM,
            mode='lines',
            fill='toself',
            fillcolor=self._layup._cathode._formulation._color,
            line=dict(color='black', width=0.5),
            name='Cathode b-side Coating'
        )

    @property
    def cathode_current_collector_top_down_trace(self) -> go.Scatter:
        """Get cathode current collector trace for top-down view."""
        if 'cathode_current_collector' not in self._component_top_down_coordinates:
            return None
        coords = self._component_top_down_coordinates['cathode_current_collector']
        return go.Scatter(
            x=coords[:, 0] * M_TO_MM,
            y=coords[:, 1] * M_TO_MM,
            mode='lines',
            fill='toself',
            fillcolor=self._layup._cathode.current_collector.material._color,
            line=dict(color='black', width=0.5),
            name='Cathode Current Collector'
        )

    @property
    def cathode_a_side_coating_top_down_trace(self) -> go.Scatter:
        """Get cathode a-side coating trace for top-down view."""
        if 'cathode_a_side_coating' not in self._component_top_down_coordinates:
            return None
        coords = self._component_top_down_coordinates['cathode_a_side_coating']
        return go.Scatter(
            x=coords[:, 0] * M_TO_MM,
            y=coords[:, 1] * M_TO_MM,
            mode='lines',
            fill='toself',
            fillcolor=self._layup._cathode._formulation._color,
            line=dict(color='black', width=0.5),
            name='Cathode a-side Coating'
        )

    @property
    def bottom_separator_top_down_trace(self) -> go.Scatter:
        """Get bottom separator trace for top-down view."""
        if 'bottom_separator' not in self._component_top_down_coordinates:
            return None
        coords = self._component_top_down_coordinates['bottom_separator']
        return go.Scatter(
            x=coords[:, 0] * M_TO_MM,
            y=coords[:, 1] * M_TO_MM,
            mode='lines',
            fill='toself',
            fillcolor=self._layup.bottom_separator.material._color,
            line=dict(color='black', width=0.5),
            name='Bottom Separator'
        )

    @property
    def anode_b_side_coating_top_down_trace(self) -> go.Scatter:
        """Get anode b-side coating trace for top-down view."""
        if 'anode_b_side_coating' not in self._component_top_down_coordinates:
            return None
        coords = self._component_top_down_coordinates['anode_b_side_coating']
        return go.Scatter(
            x=coords[:, 0] * M_TO_MM,
            y=coords[:, 1] * M_TO_MM,
            mode='lines',
            fill='toself',
            fillcolor=self._layup._anode._formulation._color,
            line=dict(color='black', width=0.5),
            name='Anode b-side Coating'
        )

    @property
    def anode_current_collector_top_down_trace(self) -> go.Scatter:
        """Get anode current collector trace for top-down view."""
        if 'anode_current_collector' not in self._component_top_down_coordinates:
            return None
        coords = self._component_top_down_coordinates['anode_current_collector']
        return go.Scatter(
            x=coords[:, 0] * M_TO_MM,
            y=coords[:, 1] * M_TO_MM,
            mode='lines',
            fill='toself',
            fillcolor=self._layup._anode.current_collector.material._color,
            line=dict(color='black', width=0.5),
            name='Anode Current Collector'
        )

    @property
    def anode_a_side_coating_top_down_trace(self) -> go.Scatter:
        """Get anode a-side coating trace for top-down view."""
        if 'anode_a_side_coating' not in self._component_top_down_coordinates:
            return None
        coords = self._component_top_down_coordinates['anode_a_side_coating']
        return go.Scatter(
            x=coords[:, 0] * M_TO_MM,
            y=coords[:, 1] * M_TO_MM,
            mode='lines',
            fill='toself',
            fillcolor=self._layup._anode._formulation._color,
            line=dict(color='black', width=0.5),
            name='Anode a-side Coating'
        )

    @property
    def top_separator_top_down_trace(self) -> go.Scatter:
        """Get top separator trace for top-down view."""
        if 'top_separator' not in self._component_top_down_coordinates:
            return None
        coords = self._component_top_down_coordinates['top_separator']
        return go.Scatter(
            x=coords[:, 0] * M_TO_MM,
            y=coords[:, 1] * M_TO_MM,
            mode='lines',
            fill='toself',
            fillcolor=self._layup.top_separator.material._color,
            line=dict(color='black', width=0.5),
            name='Top Separator'
        )

    @property
    def tape_top_down_trace(self) -> go.Scatter:
        """Get tape trace for top-down view."""
        if 'tape' not in self._component_top_down_coordinates:
            return None
        coords = self._component_top_down_coordinates['tape']
        return go.Scatter(
            x=coords[:, 0] * M_TO_MM,
            y=coords[:, 1] * M_TO_MM,
            mode='lines',
            fill='toself',
            fillcolor=self._tape._material._color,
            line=dict(color='black', width=0.5),
            name='Tape'
        )

    @property
    def cathode_tab_top_down_trace(self) -> go.Scatter:
        """Get cathode tab trace for top-down view."""

        if 'cathode_tab' not in self._component_top_down_coordinates:
            return None
        
        if not isinstance(self._layup._cathode._current_collector, TabWeldedCurrentCollector):
            return None
        
        coords = self._component_top_down_coordinates['cathode_tab']
        
        return go.Scatter(
            x=coords[:, 0] * M_TO_MM,
            y=coords[:, 1] * M_TO_MM,
            mode='lines',
            fill='toself',
            fillcolor=self._layup._cathode._current_collector._weld_tab._material._color,
            line=dict(color='black', width=0.5),
            name='Cathode Tab'
        )

    @property
    def anode_tab_top_down_trace(self) -> go.Scatter:
        """Get anode tab trace for top-down view."""
        if 'anode_tab' not in self._component_top_down_coordinates:
            return None
        if not isinstance(self._layup._anode._current_collector, TabWeldedCurrentCollector):
            return None
        coords = self._component_top_down_coordinates['anode_tab']
        return go.Scatter(
            x=coords[:, 0] * M_TO_MM,
            y=coords[:, 1] * M_TO_MM,
            mode='lines',
            fill='toself',
            fillcolor=self._layup._anode._current_collector._weld_tab._material._color,
            line=dict(color='black', width=0.5),
            name='Anode Tab'
        )

    @property
    def cathode_b_side_coating_right_left_trace(self) -> go.Scatter:
        """Get cathode b-side coating trace for right-left view."""
        if 'cathode_b_side_coating' not in self._component_right_left_coordinates:
            return None
        coords = self._component_right_left_coordinates['cathode_b_side_coating']
        return go.Scatter(
            x=coords[:, 0] * M_TO_MM,
            y=coords[:, 1] * M_TO_MM,
            mode='lines',
            fill='toself',
            fillcolor=self._layup._cathode._formulation._color,
            line=dict(color='black', width=0.5),
            name='Cathode b-side Coating'
        )

    @property
    def cathode_current_collector_right_left_trace(self) -> go.Scatter:
        """Get cathode current collector trace for right-left view."""
        if 'cathode_current_collector' not in self._component_right_left_coordinates:
            return None
        coords = self._component_right_left_coordinates['cathode_current_collector']
        return go.Scatter(
            x=coords[:, 0] * M_TO_MM,
            y=coords[:, 1] * M_TO_MM,
            mode='lines',
            fill='toself',
            fillcolor=self._layup._cathode.current_collector.material._color,
            line=dict(color='black', width=0.5),
            name='Cathode Current Collector'
        )

    @property
    def cathode_a_side_coating_right_left_trace(self) -> go.Scatter:
        """Get cathode a-side coating trace for right-left view."""
        if 'cathode_a_side_coating' not in self._component_right_left_coordinates:
            return None
        coords = self._component_right_left_coordinates['cathode_a_side_coating']
        return go.Scatter(
            x=coords[:, 0] * M_TO_MM,
            y=coords[:, 1] * M_TO_MM,
            mode='lines',
            fill='toself',
            fillcolor=self._layup._cathode._formulation._color,
            line=dict(color='black', width=0.5),
            name='Cathode a-side Coating'
        )

    @property
    def bottom_separator_right_left_trace(self) -> go.Scatter:
        """Get bottom separator trace for right-left view."""
        if 'bottom_separator' not in self._component_right_left_coordinates:
            return None
        coords = self._component_right_left_coordinates['bottom_separator']
        return go.Scatter(
            x=coords[:, 0] * M_TO_MM,
            y=coords[:, 1] * M_TO_MM,
            mode='lines',
            fill='toself',
            fillcolor=self._layup.bottom_separator.material._color,
            line=dict(color='black', width=0.5),
            name='Bottom Separator'
        )

    @property
    def anode_b_side_coating_right_left_trace(self) -> go.Scatter:
        """Get anode b-side coating trace for right-left view."""
        if 'anode_b_side_coating' not in self._component_right_left_coordinates:
            return None
        coords = self._component_right_left_coordinates['anode_b_side_coating']
        return go.Scatter(
            x=coords[:, 0] * M_TO_MM,
            y=coords[:, 1] * M_TO_MM,
            mode='lines',
            fill='toself',
            fillcolor=self._layup._anode._formulation._color,
            line=dict(color='black', width=0.5),
            name='Anode b-side Coating'
        )

    @property
    def anode_current_collector_right_left_trace(self) -> go.Scatter:
        """Get anode current collector trace for right-left view."""
        if 'anode_current_collector' not in self._component_right_left_coordinates:
            return None
        coords = self._component_right_left_coordinates['anode_current_collector']
        return go.Scatter(
            x=coords[:, 0] * M_TO_MM,
            y=coords[:, 1] * M_TO_MM,
            mode='lines',
            fill='toself',
            fillcolor=self._layup._anode.current_collector.material._color,
            line=dict(color='black', width=0.5),
            name='Anode Current Collector'
        )

    @property
    def anode_a_side_coating_right_left_trace(self) -> go.Scatter:
        """Get anode a-side coating trace for right-left view."""
        if 'anode_a_side_coating' not in self._component_right_left_coordinates:
            return None
        coords = self._component_right_left_coordinates['anode_a_side_coating']
        return go.Scatter(
            x=coords[:, 0] * M_TO_MM,
            y=coords[:, 1] * M_TO_MM,
            mode='lines',
            fill='toself',
            fillcolor=self._layup._anode._formulation._color,
            line=dict(color='black', width=0.5),
            name='Anode a-side Coating'
        )

    @property
    def top_separator_right_left_trace(self) -> go.Scatter:
        """Get top separator trace for right-left view."""
        if 'top_separator' not in self._component_right_left_coordinates:
            return None
        coords = self._component_right_left_coordinates['top_separator']
        return go.Scatter(
            x=coords[:, 0] * M_TO_MM,
            y=coords[:, 1] * M_TO_MM,
            mode='lines',
            fill='toself',
            fillcolor=self._layup.top_separator.material._color,
            line=dict(color='black', width=0.5),
            name='Top Separator'
        )

    @property
    def tape_right_left_trace(self) -> go.Scatter:
        """Get tape trace for right-left view."""
        if 'tape' not in self._component_right_left_coordinates:
            return None
        coords = self._component_right_left_coordinates['tape']
        return go.Scatter(
            x=coords[:, 0] * M_TO_MM,
            y=coords[:, 1] * M_TO_MM,
            mode='lines',
            fill='toself',
            fillcolor=self._tape._material._color,
            line=dict(color='black', width=0.5),
            name='Tape'
        )

    @property
    def cathode_tab_right_left_trace(self) -> go.Scatter:
        """Get cathode tab trace for right-left view."""
        if 'cathode_tab' not in self._component_right_left_coordinates:
            return None
        if not isinstance(self._layup._cathode._current_collector, TabWeldedCurrentCollector):
            return None
        coords = self._component_right_left_coordinates['cathode_tab']
        return go.Scatter(
            x=coords[:, 0] * M_TO_MM,
            y=coords[:, 1] * M_TO_MM,
            mode='lines',
            fill='toself',
            fillcolor=self._layup._cathode._current_collector._weld_tab._material._color,
            line=dict(color='black', width=0.5),
            name='Cathode Tab'
        )

    @property
    def anode_tab_right_left_trace(self) -> go.Scatter:
        """Get anode tab trace for right-left view."""
        if 'anode_tab' not in self._component_right_left_coordinates:
            return None
        if not isinstance(self._layup._anode._current_collector, TabWeldedCurrentCollector):
            return None
        coords = self._component_right_left_coordinates['anode_tab']
        return go.Scatter(
            x=coords[:, 0] * M_TO_MM,
            y=coords[:, 1] * M_TO_MM,
            mode='lines',
            fill='toself',
            fillcolor=self._layup._anode._current_collector._weld_tab._material._color,
            line=dict(color='black', width=0.5),
            name='Anode Tab'
        )

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
        return self._layup.total_length

    @property
    def datum(self) -> Tuple[float, float, float]:
        """Return the jelly roll datum point.
        
        Returns
        -------
        Tuple[float, float, float]
            (x, y, z) coordinates of the jelly roll datum in millimeters
        """
        return tuple(round(d * M_TO_MM, 2) for d in self._datum)
    
    @datum.setter
    def datum(self, value: Tuple[float, float, float]) -> None:
        
        # validate
        self.validate_datum(value)

        # current datum
        _current_datum = self._datum

        # translation vector
        _value = tuple(v * MM_TO_M for v in value)
        _translation_vector = (
            _value[0] - _current_datum[0],
            _value[1] - _current_datum[1],
            _value[2] - _current_datum[2]
        )
        translation_vector = tuple(t * M_TO_MM for t in _translation_vector)

        # translate spirals
        self._translate_spirals_xz(_translation_vector[0], _translation_vector[2])

        # translate top-down coordinates
        self._translate_top_down_coordinates(_translation_vector[0], _translation_vector[1])

        # translate right-left coordinates
        self._translate_right_left_coordinates(_translation_vector[1], _translation_vector[2])

        # translate mandrel
        self._mandrel.datum = (
            self._mandrel.datum[0] + translation_vector[0],
            self._mandrel.datum[1] + translation_vector[1],
            self._mandrel.datum[2] + translation_vector[2],
        )

        # translate the layup
        self._layup.datum = (
            self._layup.datum[0] + translation_vector[0],
            self._layup.datum[1] + translation_vector[1],
            self._layup.datum[2] + translation_vector[2],
        )

        # set datum
        self._datum = tuple(d * MM_TO_M for d in value)

    @tape_length_driver.setter
    def tape_length_driver(self, value: TapeDriver) -> None:
        """Set the tape length driver mode.
        
        Parameters
        ----------
        value : TapeDriver
            Driver mode to set
            
        Raises
        ------
        TypeError
            If value is not a TapeDriver enum
        """
        if not isinstance(value, TapeDriver):
            raise TypeError(f"tape_length_driver must be TapeDriver enum, got {type(value)}")
        self._tape_length_driver = value

    @collector_tab_crumple_factor.setter
    @calculate_coordinates
    def collector_tab_crumple_factor(self, value: float) -> None:
        """Set the collector tab crumple factor and recalculate properties.
        
        Parameters
        ----------
        value : float
            The new crumple factor for the collector tabs
            
        Raises
        ------
        ValueError
            If value is negative or greater than 1
        """
        self.validate_percentage(value, "collector_tab_crumple_factor")
        self._collector_tab_crumple_factor = value / 100.0

    @additional_tape_wraps.setter
    @calculate_bulk_properties
    @calculate_tape_properties
    def additional_tape_wraps(self, value: float) -> None:
        """Set the number of additional tape wraps and recalculate properties.
        
        Parameters
        ----------
        value : float
            The new number of additional tape wraps
            
        Raises
        ------
        ValueError
            If value is negative
        """
        self.validate_positive_float(value, "additional_tape_wraps")
        self._additional_tape_wraps = value
        self._tape_length_driver = TapeDriver.JELLY_ROLL_DRIVEN

    @tape.setter
    @calculate_bulk_properties
    @calculate_tape_properties
    def tape(self, value: Tape) -> None:
        """Set the tape and recalculate properties.
        
        Parameters
        ----------
        value : Tape
            The new tape to use
            
        Raises
        ------
        TypeError
            If value is not a Tape instance
        """
        if value is None:
            self._tape = None
            return

        # validate type
        self.validate_type(value, Tape, "tape")
    
        # set the tape width to at least the current collector y-foil length
        if value._width is None or value._width < self._layup._anode._current_collector._y_foil_length:
            value.width = self._layup._anode._current_collector._y_foil_length * M_TO_MM

        # Set the tape width range to match the layup width
        value._set_width_range(self)

        # set the tape datum
        _cathode_max_y = self._get_cathode_tab_y_position()
        _anode_min_y = self._get_anode_tab_y_position()
        _middle_y = (_cathode_max_y + _anode_min_y) / 2
        value.datum = (0.0, _middle_y * M_TO_MM, 0.0)

        self._tape = value

        if self._update_properties:
            self._tape_length_driver = TapeDriver.TAPE_DRIVEN

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

        if hasattr(self, '_layup'):
            self._layup = self.position_layup_on_mandrel(self._layup, self._mandrel)

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

        # position the layup on the mandrel
        value = self.position_layup_on_mandrel(value, self._mandrel)

        # set to self
        self._layup = value

        # adjust the tape width range
        if hasattr(self, '_tape') and self._tape is not None:
            self._tape._set_width_range(self)


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
            mandrel: RoundMandrel,
            tape: Tape = None,
            additional_tape_wraps: float = 0,
            collector_tab_crumple_factor: float = 50.0,
            name: str = "Wound Jelly Roll"
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
            tape=tape,
            additional_tape_wraps=additional_tape_wraps,
            collector_tab_crumple_factor=collector_tab_crumple_factor,
            name=name
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
        spirals = [s for s in self._extruded_spirals.values()]
        spirals = np.concatenate(spirals, axis=0)
        spirals_x_z = np.column_stack((spirals[:, X_COORD_COL], spirals[:, Z_COORD_COL]))
        radius, center = self.get_radius_of_points(spirals_x_z)

        self._radius = radius
        self._diameter = self._radius * 2
        self._calculate_radius_range()
        self._calculate_total_height()

        return self._radius, self._diameter, self._radius_range

    def _calculate_total_height(self) -> float:
        y_coords = [c[:, 1] for c in self._component_top_down_coordinates.values()]
        min_vals = [np.min(y) for y in y_coords]
        max_vals = [np.max(y) for y in y_coords]
        self._min_y_point = min(min_vals)
        self._max_y_point = max(max_vals)
        self._mid_y_point = (self._min_y_point + self._max_y_point) / 2
        self._total_height = self._max_y_point - self._min_y_point
        return self._total_height, self._min_y_point, self._max_y_point

    def _calculate_radius_range(self) -> Tuple[float, float]:
        """Calculate the valid range of radii for this jelly roll configuration.
        
        This method determines the minimum and maximum possible radii by:
        1. Creating layups with minimum and maximum lengths
        2. Calculating spirals for each case
        3. Finding the bounding circle radius for each configuration
        4. Adding the final layer thickness to account for the outermost surface
        
        Returns
        -------
        Tuple[float, float]
            (minimum_radius, maximum_radius) in meters
            
        Notes
        -----
        The minimum radius is constrained by the mandrel circumference and
        the layup's minimum length. The maximum radius uses the layup's
        hard maximum length limit.
        """

        # get the minimum layup length 
        mandrel_circumference = 2 * 2 * np.pi * self._mandrel._radius
        min_layup_length = max(mandrel_circumference, self._layup.length_range[0])

        # get the radius minimum bound
        small_layup = deepcopy(self._layup)
        small_layup.length = min_layup_length
        small_layup = self.position_layup_on_mandrel(small_layup, self._mandrel)
        small_layup.calculate_flattened_center_lines()
        small_spiral = SpiralCalculator.calculate_variable_thickness_spiral(small_layup, self._mandrel._radius)
        small_spiral_coords_2d = np.column_stack((small_spiral[:, X_COORD_COL],small_spiral[:, Z_COORD_COL]))
        small_radius, _ = self.get_radius_of_points(small_spiral_coords_2d)
        small_radius = small_radius + small_layup.get_thickness_at_x(small_layup._total_length)

        # get the radius maximum bound
        big_layup = deepcopy(self._layup)
        big_layup.length = big_layup.length_hard_range[1]
        big_layup = self.position_layup_on_mandrel(big_layup, self._mandrel)
        big_layup.calculate_flattened_center_lines()
        big_spiral = SpiralCalculator.calculate_variable_thickness_spiral(big_layup, self._mandrel._radius)
        big_spiral_coords_2d = np.column_stack((big_spiral[:, X_COORD_COL],big_spiral[:, Z_COORD_COL]))
        big_radius, _ = self.get_radius_of_points(big_spiral_coords_2d)
        big_radius = big_radius + big_layup.get_thickness_at_x(big_layup._total_length)

        self._radius_range = (small_radius, big_radius)

        return self._radius_range

    def _calculate_variable_thickness_spiral(self, **kwargs) -> np.ndarray:
        """Calculate the base spiral path for variable thickness layup.
        
        Delegates to SpiralCalculator to create the fundamental spiral geometry
        that accounts for varying component thicknesses throughout the layup.
        
        Parameters
        ----------
        **kwargs
            Additional arguments passed to the spiral calculation method
            
        Returns
        -------
        np.ndarray
            Base spiral coordinates [theta, x_unwrapped, r, x, z, turns]
        """

        self._spiral = SpiralCalculator.calculate_variable_thickness_spiral(
            laminate=self._layup,
            start_radius=self._mandrel._radius,
            **kwargs
        )

        return self._spiral
    
    def _get_tape_geometry_parameters(self, spirals_x_z: np.ndarray) -> Dict[str, Any]:
        """Get geometry parameters for round tape calculation.
        
        Parameters
        ----------
        spirals_x_z : np.ndarray
            Combined X-Z coordinates of all existing spirals
            
        Returns
        -------
        Dict[str, Any]
            Dictionary containing radius and center for round geometry
        """
        radius, center = self.get_radius_of_points(spirals_x_z)
        return {'start_radius': radius,'center': center}

    def _calculate_tape_spiral(self, tape_params: Dict[str, Any], **kwargs) -> np.ndarray:
        """Calculate tape spiral using round geometry.
        
        Parameters
        ----------
        tape_params : Dict[str, Any]
            Contains start_radius and other parameters
        **kwargs
            Additional arguments passed to spiral calculation
            
        Returns
        -------
        np.ndarray
            Tape spiral coordinates
        """
        if self._tape_length_driver == TapeDriver.JELLY_ROLL_DRIVEN:
            return SpiralCalculator.calculate_simple_spiral(
                n_turns=self._additional_tape_wraps,
                start_radius=tape_params['start_radius'],
                thickness=self._tape._thickness,
                **kwargs
            )
        elif self._tape_length_driver == TapeDriver.TAPE_DRIVEN:
            return SpiralCalculator.calculate_simple_spiral(
                start_radius=tape_params['start_radius'],
                thickness=self._tape._thickness,
                target_length=self._tape._length,
                **kwargs
            )
        else:
            raise ValueError(f"Invalid tape length driver: {self._tape_length_driver}")

    def _build_tape_extruded_spiral(self, tape_spiral: np.ndarray) -> Dict[str, np.ndarray]:
        """Build extruded tape spiral for round geometry.
        
        Parameters
        ----------
        tape_spiral : np.ndarray
            Tape spiral coordinates
            
        Returns
        -------
        Dict[str, np.ndarray]
            Dictionary with 'tape' key containing extruded spiral
        """
        return SpiralCalculator.build_extruded_component_spirals(
            component_spirals={'tape': tape_spiral},
            component_thicknesses={'tape': self._tape._thickness},
        )

    def _get_high_resolution_params(self) -> Dict[str, Any]:
        """Get high-resolution parameters for round geometry.
        
        Returns
        -------
        Dict[str, Any]
            Dictionary containing round geometry high-resolution parameters
        """
        return {
            'dtheta': 0.1  # 0.1° angular spacing for spiral calculation
        }

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
            layup=self._layup,
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
        component_thicknesses = {
            'top_separator': self._layup.top_separator._thickness,
            'anode_a_side_coating': self._layup.anode._coating_thickness,
            'anode_current_collector': self._layup.anode.current_collector._thickness,
            'anode_b_side_coating': self._layup.anode._coating_thickness,
            'bottom_separator': self._layup.bottom_separator._thickness,
            'cathode_a_side_coating': self._layup.cathode._coating_thickness,
            'cathode_current_collector': self._layup.cathode.current_collector._thickness,
            'cathode_b_side_coating': self._layup.cathode._coating_thickness,
        }

        self._extruded_spirals = SpiralCalculator.build_extruded_component_spirals(
            component_spirals=self._component_spirals,
            component_thicknesses=component_thicknesses,
        )

        return self._extruded_spirals

    def _center_spirals(self) -> None:
        """Center all spiral geometries around their geometric center.
        
        This method:
        1. Combines all component spirals to find the geometric center
        2. Calculates the center point of the bounding circle
        3. Translates all spirals to center them around the origin
        
        This centering is important for visualization and ensures consistent
        coordinate systems across different jelly roll configurations.
        
        Returns
        -------
        Tuple[np.ndarray, Dict[str, np.ndarray], Dict[str, np.ndarray]]
            Centered (spiral, component_spirals, extruded_spirals)
        """
        
        spirals = [s for s in self._component_spirals.values()]
        spirals = np.concatenate(spirals, axis=0)
        spirals_x_z = np.column_stack((spirals[:, X_COORD_COL], spirals[:, Z_COORD_COL]))
        _, center = self.get_radius_of_points(spirals_x_z)

        center_x, center_z = center

        self._spiral, self._component_spirals, self._extruded_spirals = self._translate_spirals_xz(
            x_shift = -center_x,
            z_shift = -center_z
        )

        return self._spiral, self._component_spirals, self._extruded_spirals

    @classmethod
    def from_flat_wound_jelly_roll(
            cls,
            flat_jelly_roll: 'FlatWoundJellyRoll',
        ) -> 'WoundJellyRoll':
        """Create a WoundJellyRoll from an existing FlatWoundJellyRoll.
        
        This method takes a flat wound jelly roll and creates a cylindrical wound
        jelly roll using the same layup structure. A round mandrel is automatically
        created based on the flat mandrel's properties.
        
        Parameters
        ----------
        flat_jelly_roll : FlatWoundJellyRoll
            The flat wound jelly roll to convert from
            
        Returns
        -------
        WoundJellyRoll
            A new wound jelly roll with the same layup as the flat jelly roll
            
        Raises
        ------
        TypeError
            If flat_jelly_roll is not a FlatWoundJellyRoll instance
            
        Examples
        --------
        >>> flat_roll = FlatWoundJellyRoll(layup, flat_mandrel)
        >>> wound_roll = WoundJellyRoll.from_FlatWoundJellyRoll(flat_roll)
        """        
        # Validate inputs
        cls.validate_type(flat_jelly_roll, FlatWoundJellyRoll, "flat_jelly_roll")
        
        # Create a deep copy of the layup to avoid modifying the original
        layup_copy = deepcopy(flat_jelly_roll.layup)
        
        # Create a round mandrel based on the flat mandrel properties
        flat_mandrel = deepcopy(flat_jelly_roll._mandrel)
        
        # Use the flat mandrel's radius (height/2) as the round mandrel's radius
        # and preserve the length and material properties
        round_mandrel = RoundMandrel(
            diameter=flat_mandrel.height,  # Use height as diameter to maintain radius
            length=flat_mandrel.length,
            datum=flat_mandrel.datum,
            material=flat_mandrel.material
        )
        
        # Create new WoundJellyRoll instance
        wound_jelly_roll = cls(
            laminate=layup_copy,
            mandrel=round_mandrel,
            tape=flat_jelly_roll.tape,
            additional_tape_wraps=flat_jelly_roll.additional_tape_wraps,
            name=flat_jelly_roll.name
        )
        
        return wound_jelly_roll

    @property
    def total_height(self) -> float:
        """Return the total height of the wound jelly roll in mm.
        
        Returns
        -------
        float
            Total height in millimeters, rounded to 2 decimal places
        """
        return np.round(self._total_height * M_TO_MM, 2)

    @property
    def radius(self) -> float:
        """Return the outer radius of the wound jelly roll in mm.
        
        Returns
        -------
        float
            Outer radius in millimeters, rounded to 2 decimal places
        """
        return np.round(self._radius * M_TO_MM, 2)

    @property
    def radius_range(self) -> Tuple[float, float]:
        return (
            np.round(self._radius_range[0] * M_TO_MM, 2),
            np.round(self._radius_range[1] * M_TO_MM, 2)
        )
    
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

        return (round(min_radius, 2), np.round(max_radius, 2))

    @property
    def diameter(self) -> float:
        """Return the outer diameter of the wound jelly roll in mm.
        
        Returns
        -------
        float
            Outer diameter in millimeters, rounded to 2 decimal places
        """
        return np.round(self._diameter * M_TO_MM, 2)
    
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

        return (round(min_diameter, 2), np.round(max_diameter, 2))
    
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

        return (round(min_diameter, 2), np.round(max_diameter, 2))

    @diameter.setter
    def diameter(self, target_diameter: float) -> None:
        """Set diameter by optimizing layup length to achieve target diameter.
        
        Parameters
        ----------
        target_diameter : float
            Target diameter in millimeters
            
        Raises
        ------
        ValueError
            If target diameter is invalid
        """
        # Validate input
        self.validate_positive_float(target_diameter, "diameter")

        # Convert diameter to radius
        target_radius = target_diameter / 2.0

        # Set radius using the radius setter
        self.radius = target_radius

    @radius.setter
    @calculate_all_properties
    def radius(self, target_radius: float) -> None:
        """Set radius by optimizing layup length to achieve target radius.
        
        Uses Brent's method for robust root finding to determine the layup length
        that produces the desired radius.
        
        Parameters
        ----------
        target_radius : float
            Target radius in millimeters
            
        Raises
        ------
        ValueError
            If target radius is invalid or optimization fails
        """
        # Validate input
        self.validate_positive_float(target_radius, "radius")
        
        def objective_function(length: float) -> float:
            """Objective function: difference between actual and target."""
            # Create copy of layup to avoid modifying original during optimization
            assembly_copy = deepcopy(self)
            assembly_copy._layup.length = length
            assembly_copy.layup = assembly_copy._layup
            return assembly_copy.radius - target_radius

        # Use Brent's method for robust root finding
        optimal_length = brentq(
            objective_function,
            self._layup.length_range[0],
            self._layup.length_hard_range[1],
            xtol=1e-3,    
            rtol=1e-3,    
            maxiter=20 
        )
        
        # Set the optimized length
        self._layup.length = optimal_length
        self.layup = self._layup


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
            tape: Tape = None,
            additional_tape_wraps: float = 0,
            collector_tab_crumple_factor: float = 50.0,
            name: str = "Flat Wound Jelly Roll"
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
            mandrel=mandrel,
            tape=tape,
            additional_tape_wraps=additional_tape_wraps,
            collector_tab_crumple_factor=collector_tab_crumple_factor,
            name=name
        )

        self._calculate_all_properties()
        self._update_properties = True

    def _calculate_all_properties(self, **kwargs) -> Tuple[Dict[str, np.ndarray], Dict[str, np.ndarray]]:
        """Calculate all properties with hot-pressing simulation.
        
        Extends the base calculation to first simulate the hot-pressing process
        that flattens the racetrack mandrel geometry before performing standard
        jelly roll calculations.
        
        Parameters
        ----------
        **kwargs
            Additional arguments passed to property calculation methods
            
        Returns
        -------
        Tuple[Dict[str, np.ndarray], Dict[str, np.ndarray]]
            Updated (component_spirals, extruded_spirals) after all calculations
        """
        self._calculate_pressed_racetrack()
        return super()._calculate_all_properties(**kwargs)

    def _calculate_roll(self, laminate_x_spacing=0.004, **kwargs):
        super()._calculate_roll(laminate_x_spacing, **kwargs)
        self._rotate_spirals_to_minimize_thickness()
        self._center_spirals()

    def _get_tape_geometry_parameters(self, spirals_x_z: np.ndarray) -> Dict[str, Any]:
        """Get geometry parameters for racetrack tape calculation.
        
        Parameters
        ----------
        spirals_x_z : np.ndarray
            Combined X-Z coordinates of all existing spirals
            
        Returns
        -------
        Dict[str, Any]
            Dictionary containing thickness, center, and racetrack parameters
        """
        thickness = SpiralCalculator.get_thickness_of_racetrack(spirals_x_z)
        start_radius = thickness / 2
        width = SpiralCalculator.get_width_of_racetrack(spirals_x_z)
        straight_length = width - thickness
        _, center = self.get_radius_of_points(spirals_x_z)
        
        return {
            'start_radius': start_radius,
            'center': center,
            'thickness': thickness,
            'straight_length': straight_length,
            'pressed_radius': self._pressed_radius
        }

    def _calculate_tape_spiral(self, tape_params: Dict[str, Any], **kwargs) -> np.ndarray:
        """Calculate tape spiral using racetrack geometry.
        
        Parameters
        ----------
        tape_params : Dict[str, Any]
            Contains start_radius, straight_length and other parameters
        **kwargs
            Additional arguments passed to spiral calculation
            
        Returns
        -------
        np.ndarray
            Tape spiral coordinates
        """
        if self._tape_length_driver == TapeDriver.JELLY_ROLL_DRIVEN:
            return SpiralCalculator.calculate_simple_racetrack(
                n_turns=self._additional_tape_wraps,
                start_radius=tape_params['start_radius'],
                straight_length=tape_params['straight_length'],
                thickness=self._tape._thickness,
                **kwargs
            )
        
        elif self._tape_length_driver == TapeDriver.TAPE_DRIVEN:
            return SpiralCalculator.calculate_simple_racetrack(
                start_radius=tape_params['start_radius'],
                straight_length=tape_params['straight_length'],
                thickness=self._tape._thickness,
                target_length=self._tape._length,
                **kwargs
            )
        else:
            raise ValueError(f"Invalid tape length driver: {self._tape_length_driver}")

    def _build_tape_extruded_spiral(self, tape_spiral: np.ndarray) -> Dict[str, np.ndarray]:
        """Build extruded tape spiral for racetrack geometry.
        
        Parameters
        ----------
        tape_spiral : np.ndarray
            Tape spiral coordinates
            
        Returns
        -------
        Dict[str, np.ndarray]
            Dictionary with 'tape' key containing extruded spiral
        """
        return SpiralCalculator.build_extruded_component_racetracks(
            component_spirals={'tape': tape_spiral},
            component_thicknesses={'tape': self._tape._thickness},
            mandrel_radius=self._pressed_radius,
            straight_length=self._pressed_straight_length
        )

    def _apply_tape_pre_centering_transforms(self, tape_params: Dict[str, Any]) -> None:
        """Apply racetrack-specific transforms before final centering.
        
        For racetrack geometry, we need to translate all spirals to account
        for the thickness offset before applying final centering.
        
        Parameters
        ----------
        tape_params : Dict[str, Any]
            Contains thickness, center and other geometry parameters
        """
        center = tape_params['center']
        thickness = tape_params['thickness']
        
        center_x = center[0]
        center_z = center[1]

        self._spiral, self._component_spirals, self._extruded_spirals = self._translate_spirals_xz(
            x_shift = -center_x,
            z_shift = -center_z + thickness / 2
        )

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
        # Combine all component coordinates to find overall envelope
        all_coords = []
        
        for _, spiral_data in self._component_spirals.items():
            coords_2d = spiral_data[:, [X_COORD_COL, Z_COORD_COL]]
            all_coords.append(coords_2d)
        
        # Concatenate all coordinates
        combined_coords = np.vstack(all_coords)
        
        # Calculate dimensions using the utility functions
        self._thickness = SpiralCalculator.get_thickness_of_racetrack(combined_coords)
        self._width = SpiralCalculator.get_width_of_racetrack(combined_coords)
        self._calculate_thickness_width_range()

        return self._thickness, self._width

    def _calculate_thickness_width_range(self) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """Calculate the valid ranges of thickness and width for this jelly roll.
        
        This method determines the minimum and maximum possible dimensions by:
        1. Creating layups with minimum and maximum lengths
        2. Calculating racetrack spirals for each case using pressed geometry
        3. Finding the bounding dimensions for each configuration
        4. Adding final layer thickness to account for outermost surfaces
        
        Returns
        -------
        Tuple[Tuple[float, float], Tuple[float, float]]
            ((min_thickness, max_thickness), (min_width, max_width)) in meters
            
        Notes
        -----
        Uses the pressed mandrel geometry rather than the original mandrel
        to properly account for hot-pressing effects on the final dimensions.
        """

        # get the minimum length of the layup
        mandrel_circumference = 2 * (TWO_PI * self._mandrel._radius + 2 * self._mandrel._straight_length)
        min_layup_length = max(mandrel_circumference, self._layup.length_range[0])

        # cache some values for later
        radius = self._pressed_radius
        straight_length = self._pressed_straight_length

        # get the thickness minimum bound
        small_layup = deepcopy(self._layup)
        small_layup.length = min_layup_length
        small_layup = self.position_layup_on_mandrel(small_layup, self._mandrel)
        small_layup.calculate_flattened_center_lines()
        small_pressed_racetrack = SpiralCalculator.calculate_variable_thickness_racetrack(small_layup, radius, straight_length)
        small_racetrack_coords_2d = np.column_stack((small_pressed_racetrack[:, X_COORD_COL],small_pressed_racetrack[:, Z_COORD_COL]))
        small_width = SpiralCalculator.get_width_of_racetrack(small_racetrack_coords_2d)
        small_width = small_width + 2 * small_layup.get_thickness_at_x(small_layup._total_length)
        small_thickness = SpiralCalculator.get_thickness_of_racetrack(small_racetrack_coords_2d)
        small_thickness = small_thickness + 2 * small_layup.get_thickness_at_x(small_layup._total_length)

        # get the thickness maximum bound
        big_layup = deepcopy(self._layup)
        big_layup.length = big_layup.length_hard_range[1]
        big_layup = self.position_layup_on_mandrel(big_layup, self._mandrel)
        big_layup.calculate_flattened_center_lines()
        big_pressed_racetrack = SpiralCalculator.calculate_variable_thickness_racetrack(big_layup, radius, straight_length)
        big_racetrack_coords_2d = np.column_stack((big_pressed_racetrack[:, X_COORD_COL],big_pressed_racetrack[:, Z_COORD_COL]))
        big_width = SpiralCalculator.get_width_of_racetrack(big_racetrack_coords_2d)
        big_width = big_width + 2 * big_layup.get_thickness_at_x(big_layup._total_length)
        big_thickness = SpiralCalculator.get_thickness_of_racetrack(big_racetrack_coords_2d)
        big_thickness = big_thickness + 2 * big_layup.get_thickness_at_x(big_layup._total_length)
        
        self._thickness_range = (small_thickness, big_thickness)
        self._width_range = (small_width, big_width)

        return self._thickness_range, self._width_range

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
        original_circumference = 2 * np.pi * original_radius + 2 * original_straight_length
        
        # Create new mandrel geometry with pressed height
        pressed_radius = pressed_height / 2  # New radius from pressed height
        
        # Calculate new straight length to maintain same circumference
        # Circumference = 2 * π * radius + 2 * straight_length
        # Solve for new straight_length: straight_length = (circumference - 2 * π * radius) / 2
        new_straight_length = (original_circumference - TWO_PI * pressed_radius) / 2

        self._pressed_radius = pressed_radius
        self._pressed_straight_length = new_straight_length

        return self._pressed_radius, self._pressed_straight_length

    def _build_component_spirals(self):
        """Build component spirals using hot-pressed racetrack geometry.
        
        Maps individual electrode and separator components from the layup onto
        the racetrack spiral geometry, using the pressed mandrel dimensions
        rather than the original mandrel to account for hot-pressing effects.
        
        Returns
        -------
        Dict[str, np.ndarray]
            Component spirals keyed by component name, mapped to racetrack geometry
        """
        
        # Build component spirals for the hot-pressed geometry
        self._component_spirals = SpiralCalculator.build_component_racetracks(
            base_spiral=self._spiral, 
            layup=self._layup,
            mandrel_radius=self._pressed_radius, 
            straight_length=self._pressed_straight_length,
            original_mandrel_radius=self._mandrel._radius
        )

        return self._component_spirals
        
    def _build_extruded_component_spirals(self):
        """Build extruded component spirals for racetrack visualization.
        
        Creates filled thickness shapes for each component by extruding the
        center line spirals radially. Uses the pressed mandrel geometry for
        proper racetrack shape generation.
        
        Returns
        -------
        Dict[str, np.ndarray]
            Extruded component spirals for 3D racetrack visualization
        """

        component_thicknesses = {
            'top_separator': self._layup.top_separator._thickness,
            'anode_a_side_coating': self._layup.anode._coating_thickness,
            'anode_current_collector': self._layup.anode.current_collector._thickness,
            'anode_b_side_coating': self._layup.anode._coating_thickness,
            'bottom_separator': self._layup.bottom_separator._thickness,
            'cathode_a_side_coating': self._layup.cathode._coating_thickness,
            'cathode_current_collector': self._layup.cathode.current_collector._thickness,
            'cathode_b_side_coating': self._layup.cathode._coating_thickness,
        }

        # Build extruded component spirals for the hot-pressed geometry
        self._extruded_spirals = SpiralCalculator.build_extruded_component_racetracks(
            component_spirals=self._component_spirals, 
            component_thicknesses=component_thicknesses,
            mandrel_radius=self._pressed_radius, 
            straight_length=self._pressed_straight_length
        )

        return self._extruded_spirals

    def _calculate_variable_thickness_spiral(self, **kwargs) -> np.ndarray:
        """Calculate the base racetrack spiral path for variable thickness layup.
        
        Uses the hot-pressed mandrel geometry to create a racetrack spiral that
        accounts for the flattened geometry after hot pressing. This differs
        from the original mandrel geometry.
        
        Parameters
        ----------
        **kwargs
            Additional arguments passed to the racetrack spiral calculation method
            
        Returns
        -------
        np.ndarray
            Base racetrack spiral coordinates [theta, x_unwrapped, r, x, z, turns]
        """

        # Calculate new spiral with pressed mandrel geometry (no mandrel modification needed)
        self._spiral = SpiralCalculator.calculate_variable_thickness_racetrack(
            laminate=self._layup,
            mandrel_radius=self._pressed_radius, 
            straight_length=self._pressed_straight_length,
            **kwargs
        )
        
        return self._spiral
    
    def _center_spirals(
            self
        ) -> None:
        """Center all racetrack spiral geometries for proper visualization.
        
        Centers the racetrack spirals by:
        1. Finding the geometric center and thickness of all component spirals
        2. Translating all spirals to center them horizontally
        3. Adjusting vertically to position the bottom at z=0
        
        This centering ensures consistent coordinate systems and proper
        visualization alignment for racetrack geometries.
        
        Returns
        -------
        Tuple[np.ndarray, Dict[str, np.ndarray], Dict[str, np.ndarray]]
            Centered (spiral, component_spirals, extruded_spirals)
        """

        spirals = [s for s in self._component_spirals.values()]
        spirals = np.concatenate(spirals, axis=0)
        spirals_x_z = np.column_stack((spirals[:, X_COORD_COL], spirals[:, Z_COORD_COL]))
        spirals_x_z = spirals_x_z[~np.isnan(spirals_x_z).any(axis=1)]  # Remove NaN values if any

        max_z = np.max(spirals_x_z[:, 1])
        min_z = np.min(spirals_x_z[:, 1])
        max_x = np.max(spirals_x_z[:, 0])
        min_x = np.min(spirals_x_z[:, 0])

        # calculate shift so as to make max and mix values the same distance from center
        center_x = (max_x + min_x) / 2
        center_z = (max_z + min_z) / 2

        self._spiral, self._component_spirals, self._extruded_spirals = self._translate_spirals_xz(
            x_shift = -center_x,
            z_shift = -center_z
        )

        return self._spiral, self._component_spirals, self._extruded_spirals

    def _rotate_spirals_to_minimize_thickness(self, use_extruded: bool = True) -> float:
        """Rotate spirals in x-z plane to minimize overall thickness.

        Uses Brent's method to find the rotation angle that minimizes the
        vertical extent (thickness = max(z) - min(z)). The rotation is applied
        in-place to:
        - `self._spiral`
        - `self._component_spirals`
        - `self._extruded_spirals`

        Parameters
        ----------
        use_extruded : bool, optional
            If True, compute the rotation using all extruded component points
            (more representative for thickness). If False, use component
            centerline spirals. Default is True.

        Returns
        -------
        float
            Rotation angle in radians applied (counterclockwise, about centroid).

        Notes
        -----
        - Rotation is performed about the centroid of the combined points.
        - Optimization searches over [0, π) since thickness is symmetric about π.
        """
        # Choose which spiral set to use for optimization
        if use_extruded and hasattr(self, '_extruded_spirals') and self._extruded_spirals:
            spiral_dict = self._extruded_spirals
        elif hasattr(self, '_component_spirals') and self._component_spirals:
            spiral_dict = self._component_spirals
        else:
            return 0.0

        # Collect all spiral dictionaries to rotate together
        all_spirals = {}
        if hasattr(self, '_spiral') and isinstance(self._spiral, np.ndarray):
            all_spirals['_base'] = self._spiral
        if hasattr(self, '_component_spirals') and isinstance(self._component_spirals, dict):
            all_spirals.update({f'comp_{k}': v for k, v in self._component_spirals.items()})
        if hasattr(self, '_extruded_spirals') and isinstance(self._extruded_spirals, dict):
            all_spirals.update({f'ext_{k}': v for k, v in self._extruded_spirals.items()})

        # Rotate all spirals using the helper function from SpiralCalculator
        _, optimal_angle = SpiralCalculator.rotate_spiral_to_minimize_thickness(all_spirals)

        return optimal_angle
    
    def _get_high_resolution_params(self) -> Dict[str, Any]:
        """Get high-resolution parameters for racetrack geometry.
        
        Returns
        -------
        Dict[str, Any]
            Dictionary containing racetrack geometry high-resolution parameters
        """
        return {
            'ds_target': 0.0002  # 0.2mm target spacing for racetrack calculation
        }

    @classmethod
    def from_round_jelly_roll(
            cls,
            round_jelly_roll: 'WoundJellyRoll',
        ) -> 'FlatWoundJellyRoll':
        """Create a FlatWoundJellyRoll from an existing WoundJellyRoll.
        
        This method takes a wound jelly roll and creates a flat wound jelly roll
        using the same layup structure. A flat mandrel is automatically created
        based on the round mandrel's properties.
        
        Parameters
        ----------
        round_jelly_roll : WoundJellyRoll
            The wound jelly roll to convert from
            
        Returns
        -------
        FlatWoundJellyRoll
            A new flat wound jelly roll with the same layup as the wound jelly roll
            
        Raises
        ------
        TypeError
            If round_jelly_roll is not a WoundJellyRoll instance
            
        Examples
        --------
        >>> wound_roll = WoundJellyRoll(layup, round_mandrel)
        >>> flat_roll = FlatWoundJellyRoll.from_round_jelly_roll(wound_roll)
        """        
        # Validate inputs
        cls.validate_type(round_jelly_roll, WoundJellyRoll, "round_jelly_roll")
        
        # Create a deep copy of the layup to avoid modifying the original
        layup_copy = deepcopy(round_jelly_roll._layup)
        
        # Create a flat mandrel based on the round mandrel properties
        round_mandrel = deepcopy(round_jelly_roll._mandrel)
        
        # Use the round mandrel's diameter as the flat mandrel's height to maintain radius
        # Set a default straight length (can be adjusted based on requirements)
        default_straight_length = round_mandrel.diameter * 10  # Default: 2x diameter for reasonable aspect ratio
        
        flat_mandrel = FlatMandrel(
            height=round_mandrel.diameter,  # Use diameter as height to maintain radius
            width=round_mandrel.diameter + default_straight_length,  # Width = height + straight section
            length=round_mandrel.length,
            datum=round_mandrel.datum,
            material=round_mandrel.material
        )
        
        # Create new FlatWoundJellyRoll instance
        flat_jelly_roll = cls(
            laminate=layup_copy,
            mandrel=flat_mandrel,
            tape=round_jelly_roll._tape,
            additional_tape_wraps=round_jelly_roll._additional_tape_wraps,
            name=round_jelly_roll.name
        )
        
        return flat_jelly_roll

    @property
    def pressed_radius(self) -> float:
        """Return the pressed mandrel radius in mm.
        
        Returns
        -------
        float
            Pressed mandrel radius in millimeters, rounded to 2 decimal places
        """
        return np.round(self._pressed_radius * M_TO_MM, 2)
    
    @property
    def pressed_straight_length(self) -> float:
        """Return the pressed mandrel straight length in mm.
        
        Returns
        -------
        float
            Pressed mandrel straight length in millimeters, rounded to 2 decimal places
        """
        return np.round(self._pressed_straight_length * M_TO_MM, 2)
    
    @property
    def thickness(self) -> float:
        """Return the overall jelly roll thickness in millimeters.
        
        Returns
        -------
        float
            Overall thickness in millimeters, rounded to 2 decimal places
        """
        return np.round(self._thickness * M_TO_MM, 2)

    @property
    def width(self) -> float:
        """Return the overall jelly roll width in millimeters.
        
        Returns
        -------
        float
            Overall width in millimeters, rounded to 2 decimal places
        """
        return np.round(self._width * M_TO_MM, 2)

    @property
    def thickness_hard_range(self) -> Tuple[float, float]:
        return self.thickness_range
    
    @property
    def width_hard_range(self) -> Tuple[float, float]:
        return self.width_range

    @property
    def thickness_range(self) -> Tuple[float, float]:
        """Return the thickness range (min, max) of the flat wound jelly roll in mm.
        
        Returns
        -------
        Tuple[float, float]
            (min_thickness, max_thickness) in millimeters, rounded to 2 decimal places
        """
        return (
            np.round(self._thickness_range[0] * M_TO_MM, 2),
            np.round(self._thickness_range[1] * M_TO_MM, 2)
        )
    
    @property
    def width_range(self) -> Tuple[float, float]:
        """Return the width range (min, max) of the flat wound jelly roll in mm.
        
        Returns
        -------
        Tuple[float, float]
            (min_width, max_width) in millimeters, rounded to 2 decimal places
        """
        return (
            np.round(self._width_range[0] * M_TO_MM, 2),
            np.round(self._width_range[1] * M_TO_MM, 2)
        )
    
    @thickness.setter
    @calculate_all_properties
    def thickness(self, target_thickness: float) -> None:
        """Set thickness by optimizing layup length to achieve target thickness.
        
        Uses Brent's method for robust root finding to determine the layup length
        that produces the desired thickness.
        
        Parameters
        ----------
        target_thickness : float
            Target thickness in millimeters
            
        Raises
        ------
        ValueError
            If target thickness is invalid or optimization fails
        """
        # Validate input
        self.validate_positive_float(target_thickness, "thickness")
        
        def objective_function(length: float) -> float:
            """Objective function: difference between actual and target."""
            # Create copy of layup to avoid modifying original during optimization
            assembly_copy = deepcopy(self)
            assembly_copy._layup.length = length
            assembly_copy.layup = assembly_copy._layup
            return assembly_copy.thickness - target_thickness

        # Use Brent's method for robust root finding
        optimal_length = brentq(
            objective_function,
            self._layup.length_range[0],
            self._layup.length_hard_range[1],
            xtol=1e-3,    
            rtol=1e-3,    
            maxiter=20 
        )
        
        # Set the optimized length
        self._layup.length = optimal_length
        self.layup = self._layup

    @width.setter
    @calculate_all_properties
    def width(self, target_width: float) -> None:
        """Set width by optimizing layup length to achieve target width.
        
        Uses Brent's method for robust root finding to determine the layup length
        that produces the desired width.
        
        Parameters
        ----------
        target_width : float
            Target width in millimeters
            
        Raises
        ------
        ValueError
            If target width is invalid or optimization fails
        """
        # Validate input
        self.validate_positive_float(target_width, "width")
        
        def objective_function(length: float) -> float:
            """Objective function: difference between actual and target."""
            # Create copy of layup to avoid modifying original during optimization
            assembly_copy = deepcopy(self)
            assembly_copy._layup.length = length
            assembly_copy.layup = assembly_copy._layup
            return assembly_copy.width - target_width

        # Use Brent's method for robust root finding
        optimal_length = brentq(
            objective_function,
            self._layup.length_range[0],
            self._layup.length_hard_range[1],
            xtol=1e-3,    
            rtol=1e-3,    
            maxiter=20 
        )
        
        # Set the optimized length
        self._layup.length = optimal_length
        self.layup = self._layup
 
