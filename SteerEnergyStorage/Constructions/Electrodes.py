from SteerEnergyStorage.Formulations.ElectrodeFormulations import CathodeFormulation, AnodeFormulation, _ElectrodeFormulation
from SteerEnergyStorage.Materials.CurrentCollectors import _CurrentCollector
from SteerEnergyStorage.Materials.RawMaterials import InsulationMaterial

from SteerEnergyStorage.Constants import *
from SteerEnergyStorage.Utils import *

import pandas as pd
import numpy as np
from typing import Dict, Any
import plotly.express as px
import plotly.graph_objects as go


class _Electrode:
    """
    Base class for electrodes, representing the common properties and methods of an electrode.
    """
    def __init__(
            self, 
            formulation: _ElectrodeFormulation,
            mass_loading: float,
            current_collector: _CurrentCollector,
            calender_density: float,
            insulation_material: InsulationMaterial = None,
            insulation_thickness: float = 0.0,
            name: str = 'Electrode'
        ):
        """
        Initialize an object that represents an electrode.

        Parameters:
        ----------
        formulation : _ElectrodeFormulation
            The formulation of the electrode, which includes active materials, binders, and conductive additives.
        mass_loading : float
            The mass loading of the electrode in mg/cm^2.
        current_collector : _CurrentCollector
            The current collector used in the electrode.
        calender_density : float
            The density of the electrode coating after calendering in g/cm^3.
        insulation_material : InsulationMaterial, optional
            The insulation material used in the electrode (default is None).
        insulation_thickness : float, optional
            The thickness of the insulation material in micrometers (default is 0.0).
        name : str, optional
            The name of the electrode (default is 'Electrode').
        ----------
        """
        self._check_name(name)
        self._check_formulation(formulation)
        self._check_current_collector(current_collector)
        self._check_mass_loading(mass_loading)
        self._check_calender_density(calender_density)
        self._check_insulation_material(insulation_material)
        self._check_insulation_thickness(insulation_thickness)

        self._calculate_porosity()
        self._calculate_thickness_properties()
        self._calculate_mass_properties()
        self._calculate_cost_properties()

    def _check_insulation_material(self, insulation_material: InsulationMaterial) -> None:
        """
        Check if the insulation material is valid.

        Parameters:
        ----------
        insulation_material : InsulationMaterial
            The insulation material to check.

        Raises:
        -------
        TypeError: If the insulation material is not an InsulationMaterial object.
        ValueError: If the insulation material is not provided when the current collector has an insulation width.
        ----------
        """
        if insulation_material is not None and not isinstance(insulation_material, InsulationMaterial):
            raise TypeError("Insulation material must be an InsulationMaterial object")
        
        if self._current_collector._insulation_area != 0 and insulation_material is None:
            raise ValueError("Insulation material must be provided if the current collector has an insulation width")
        
        if self._current_collector._insulation_area == 0 and insulation_material is not None:
            raise ValueError("Insulation material cannot be provided if the current collector does not have an insulation area")
        
        self._insulation_material = insulation_material

    def _check_insulation_thickness(self, insulation_thickness: float) -> None:
        """
        Check if the insulation thickness is valid.

        Parameters:
        ----------
        insulation_thickness : float
            The thickness of the insulation material in micrometers.
        
        Raises:
        -------
        TypeError: If the insulation thickness is not a number.
        ValueError: If the insulation thickness is less than zero.
        ----------
        """
        if not isinstance(insulation_thickness, (int, float)):
            raise TypeError("Insulation thickness must be a number")
        
        if insulation_thickness < 0:
            raise ValueError("Insulation thickness must be greater than or equal to zero")
        
        if self._insulation_material is not None and insulation_thickness == 0:
            raise ValueError("Insulation thickness must be greater than zero if insulation material is provided")
        
        self._insulation_thickness = insulation_thickness * UM_TO_M

    def _check_name(self, name: str) -> None:

        if not isinstance(name, str):
            raise TypeError("Name must be a string")
        
        self._name = name

    def _check_formulation(self, formulation: _ElectrodeFormulation) -> None:

        if not isinstance(formulation, _ElectrodeFormulation):
            raise TypeError("Formulation must be an ElectrodeFormulation object")

        self._formulation = formulation

    def _check_current_collector(self, current_collector: _CurrentCollector) -> None:

        if not isinstance(current_collector, _CurrentCollector):
            raise TypeError("Current collector must be a CurrentCollector object")

        self._current_collector = current_collector

    def _check_mass_loading(self, mass_loading: float) -> None:

        if not isinstance(mass_loading, (int, float)):
            raise TypeError("Mass loading must be a number")

        if mass_loading <= 0:
            raise ValueError("Mass loading must be greater than zero")
        
        self._mass_loading = mass_loading * (MG_TO_KG / CM_TO_M**2)

    def _check_calender_density(self, calender_density: float) -> None:

        if not isinstance(calender_density, (int, float)):
            raise TypeError("Calender density must be a number")

        if calender_density <= 0:
            raise ValueError("Calender density must be greater than zero")

        self._calender_density = calender_density * (G_TO_KG / CM_TO_M**3)

    def _calculate_mass_properties(self) -> None:
        """
        Calculate the mass properties of the electrode.
        """
        self._coating_mass = self._current_collector._coated_area * self._mass_loading
        self._insulator_mass = self._current_collector._insulation_area * self._insulation_material._density * self._insulation_thickness if self._insulation_material else 0.0
        self._mass = self._coating_mass + self._current_collector._mass + self._insulator_mass

        self._mass_breakdown = (
            {k: float(v * self._minimum_coating_volume) for k, v in self._formulation._density_breakdown.items()} | 
            {self._current_collector.name: self._current_collector._mass} |
            ({self._insulation_material.name: self._insulator_mass} if self._insulation_material else {})
        )

    def _calculate_cost_properties(self) -> None:
        """
        Calculate the cost properties of the electrode.
        """
        self._coating_cost = self._coating_mass * self._formulation._specific_cost
        self._insulator_cost = self._insulator_mass * self._insulation_material._specific_cost if self._insulation_material else 0.0
        self._cost = self._coating_cost + self._current_collector._cost + self._insulator_cost

        self._cost_breakdown = (
            {k: float(v * self._coating_mass) for k, v in self._formulation._specific_cost_breakdown.items()} |
            {self._current_collector.name: self._current_collector.cost} |
            ({self._insulation_material.name: self._insulator_cost * self._insulator_mass} if self._insulation_material else {})
        )

    def _calculate_thickness_properties(self) -> None:
        """
        Calculate the thickness properties of the electrode.
        """
        self._minimum_coating_thickness = self._mass_loading / self._formulation._density
        self._minimum_coating_volume = self._current_collector._coated_area * self._minimum_coating_thickness

        self._coating_thickness = self._mass_loading / self._calender_density
        self._coating_volume = self._current_collector._coated_area * self._coating_thickness
        self._thickness = self._coating_thickness * 2 + self._current_collector._thickness
        self._pore_volume = self._coating_volume * self._porosity

        if self._insulation_thickness > self._coating_thickness:
            raise ValueError(f"""Insulation thickness of {self.insulation_thickness} um cannot be 
                             greater than coating thickness of {self.coating_thickness}. Increase 
                             your mass loading or decrease insulation thickness.""")
        
        if self._coating_thickness < self._minimum_coating_thickness:
            raise ValueError(f"""Your caldender density of {self.calender_density} g/cm^3 is too high, 
                             leading to negative porosity. Decrease your calender density below 
                             {self._formulation._density} g/cm^3.""")

    def _calculate_porosity(self) -> None:
        """
        Calculate the overall porosity of the electrode formulation.
        """
        active_mass_fractions = [v for v in self._formulation._active_materials.values()]
        active_mass_densities = [am._density for am in self._formulation._active_materials.keys()]
        
        conductive_aids_fractions = [v for v in self._formulation._conductive_additives.values()]
        conductive_aids_densities = [ca._density for ca in self._formulation._conductive_additives.keys()]

        binder_fractions = [v for v in self._formulation._binders.values()]
        binder_densities = [b._density for b in self._formulation._binders.keys()]

        theoretical_specific_volume = sum(amf / amd for amf, amd in zip(active_mass_fractions, active_mass_densities)) + \
                                      sum(caf / cad for caf, cad in zip(conductive_aids_fractions, conductive_aids_densities)) + \
                                      sum(bf / bd for bf, bd in zip(binder_fractions, binder_densities))
        
        porosity = 1 - (theoretical_specific_volume * self._calender_density)

        if porosity < 0:
            raise ValueError("Porosity cannot be negative. Check the mass fractions and densities of the components.")

        self._porosity = porosity

    def _get_top_down_view(self, side: str = 'a', **kwargs) -> pd.DataFrame:
        """
        Helper method to get a top-down view of the electrode.
        """
        if side == 'a':
            figure = self._current_collector.get_a_side_view(**kwargs)
        elif side == 'b':
            figure = self._current_collector.get_b_side_view(**kwargs)
        else:
            raise ValueError("Side must be either 'a' or 'b'.")
        
        for trace in figure.data:

            if trace.name == "Coated Area":
                trace.name = self._formulation.name
                trace.fill = 'toself'
                trace.fillcolor = self._formulation._color
                trace.fillpattern = None

            elif trace.name == "Insulation Strip":
                trace.name = self._insulation_material.name if self._insulation_material else 'No Insulation'
                trace.fill = 'toself'
                trace.fillcolor = self._insulation_material._color if self._insulation_material else 'rgba(0,0,0,0)'
                trace.fillpattern = None

        return figure

    def plot_half_cell_curve(self, areal: bool = False, **kwargs) -> None:
        """
        Plot the half cell curve of the electrode.

        Parameters
        ----------
        areal : bool, optional
            If True, plot the areal capacity instead of the specific capacity (default is False).
        """
        if not hasattr(self, '_half_cell_curve'):
            raise ValueError(f"A half cell curve for {self.name} has not been calculated yet. Please set a voltage cutoff before plotting.")

        x = 'Capacity (Ah)' if not areal else 'Areal Capacity (mAh/cm²)'

        fig = px.line(
            self.half_cell_curve, 
            y='Voltage (V)', 
            x=x, 
            line_shape='spline', 
            template='presentation', 
            **kwargs
        )

        fig.update_traces(
            line=dict(color=self._formulation._color),
        )

        return fig    

    def get_a_side_view(self, **kwargs) -> go.Figure:
        """
        Get a side view of the electrode.
        """
        figure = self._get_top_down_view(side='a', **kwargs)
        return figure

    def get_b_side_view(self, **kwargs) -> go.Figure:
        """
        Get a side view of the electrode.
        """
        figure = self._get_top_down_view(side='b', **kwargs)
        return figure

    def get_end_view(self, **kwargs) -> go.Figure:
        """
        Get a side view of the electrode, including coatings and insulation.
        """
        figure = self._current_collector.get_end_view(**kwargs)

        def add_patch(trace, y_base, y_thickness, material, showlegend):

            y_data = trace.y
            df = build_square_df(
                x=min(y_data),
                y=y_base,
                x_width=max(y_data) - min(y_data),
                y_width=y_thickness
            )
            figure.add_trace(
                go.Scatter(
                    x=df['x'],
                    y=df['y'],
                    fill='toself',
                    fillcolor=material._color,
                    mode='lines',
                    name=material.name,
                    line=dict(color='black', width=0.5),
                    showlegend=showlegend,
                    legendgroup=material.name
                )
            )

        # Add coatings
        add_patch(
            self._current_collector._a_side_coated_area_trace,
            self._current_collector._datum[2] + self._current_collector._thickness / 2,
            self._coating_thickness,
            self._formulation,
            showlegend=True
        )
        add_patch(
            self._current_collector._b_side_coated_area_trace,
            self._current_collector._datum[2] - self._current_collector._thickness / 2,
            -self._coating_thickness,
            self._formulation,
            showlegend=False
        )

        # Add insulation if present
        if self._insulation_material:
            add_patch(
                self._current_collector._a_side_insulation_area_trace,
                self._current_collector._datum[2] + self._current_collector._thickness / 2,
                self._insulation_thickness,
                self._insulation_material,
                showlegend=True
            )
            add_patch(
                self._current_collector._b_side_insulation_area_trace,
                self._current_collector._datum[2] - self._current_collector._thickness / 2,
                -self._insulation_thickness,
                self._insulation_material,
                showlegend=False
            )

        return figure

    @property
    def voltage_cutoff(self) -> float:
        """
        Get the maximum voltage of the half cell curves.
        
        :return: float: maximum voltage of the half cell curves
        """
        return round(float(self.half_cell_curves['Maximum Voltage (V)'].max()), 3)

    @voltage_cutoff.setter
    def voltage_cutoff(self, voltage: float):
        """
        Set the voltage cutoff for the half cell curves.
        
        :param voltage: float: maximum voltage of the half cell curves
        """
        self._formulation.voltage_cutoff = voltage
        self._voltage_cutoff = voltage
        
        data = (
            self
            ._formulation
            ._half_cell_curve
            .assign(
                capacity = lambda x: x['specific_capacity'] * self._coating_mass,
                areal_capacity = lambda x: x['capacity'] / (self._current_collector._coated_area),
            ).drop(
                columns=['specific_capacity_max', 'voltage_at_max_capacity', 'specific_capacity']
            )
        )

        self._half_cell_curve = data

    @property
    def properties(self) -> Dict[str, Any]:
        """
        Get the properties of the electrode.

        :return: Dictionary containing the properties of the electrode.
        """
        return {
            'Mass': f"{self.mass} g",
            'Coating mass': f"{self.coating_mass} g",
            'Total thickness': f"{self.thickness} um",
            'Coating thickness': f"{self.coating_thickness} um",
            'Porosity': f"{self.porosity} %",
            'Cost': f"$ {self.cost}",
        }

    @property
    def insulation_thickness(self) -> float:
        """
        Get the insulation thickness of the electrode.

        :return: Insulation thickness of the electrode in micrometers.
        """
        return round(self._insulation_thickness * M_TO_UM, 2)

    @property
    def coating_thickness(self) -> float:
        """
        Get the coating thickness of the electrode.

        :return: Coating thickness of the electrode in micrometers.
        """
        return round(self._coating_thickness * M_TO_UM, 2)

    @property
    def cost_breakdown(self) -> Dict[str, Any]:
        """
        Get the cost breakdown of the electrode.

        :return: Dictionary containing the cost breakdown.
        """
        return {k: round(v, 2) for k, v in self._cost_breakdown.items()}

    @property
    def mass_breakdown(self) -> Dict[str, Any]:
        """
        Get the mass breakdown of the electrode.

        :return: Dictionary containing the mass breakdown.
        """
        return {k: round(v * KG_TO_G, 2) for k, v in self._mass_breakdown.items()}

    @property
    def half_cell_curve(self) -> pd.DataFrame:

        if not hasattr(self, '_half_cell_curve'):
            raise ValueError(f"A half cell curve for {self.name} has not been calculated yet. Please set a voltage cutoff or a maximum specific capacity before accessing this property.")

        data = (self
                ._half_cell_curve
                .assign(
                    capacity = lambda x: x['capacity'] * (S_TO_H),
                    areal_capacity = lambda x: x['areal_capacity'] * ((S_TO_H * A_TO_mA)/M_TO_CM**2),
                ).filter(
                    items=['capacity', 'voltage', 'direction', 'areal_capacity']
                )
                .rename(
                    columns={
                        'capacity': 'Capacity (Ah)', 
                        'voltage': 'Voltage (V)', 
                        'direction': 'Direction',
                        'areal_capacity': 'Areal Capacity (mAh/cm²)'
                        }
                    )
                )
        
        return data

    @property
    def porosity(self) -> float:
        """
        Get the porosity of the electrode.

        :return: Porosity of the electrode.
        """
        return round(self._porosity * 100, 2)
    
    @property
    def calender_density(self) -> float:
        """
        Get the calender density of the electrode.

        :return: Calender density of the electrode.
        """
        return round(self._calender_density * (KG_TO_G / M_TO_CM**3), 2)

    @property
    def mass_loading(self) -> float:
        """
        Get the mass loading of the electrode.

        :return: Mass loading of the electrode.
        """
        return round(self._mass_loading * (KG_TO_MG / M_TO_CM**2), 2)

    @property
    def current_collector(self) -> _CurrentCollector:
        """
        Get the current collector of the electrode.

        :return: Current collector of the electrode.
        """
        return self._current_collector

    @property
    def name(self) -> str:
        """
        Get the name of the electrode.

        :return: Name of the electrode.
        """
        return self._name

    @property
    def coating_mass(self) -> float:
        """
        Get the coating mass of the electrode.

        :return: Coating mass of the electrode.
        """
        return round(self._coating_mass * KG_TO_G, 2)

    @property
    def mass(self) -> float:
        """
        Get the mass of the electrode.

        :return: Mass of the electrode.
        """
        return round(self._mass * KG_TO_G, 2)

    @property
    def thickness(self) -> float:
        """
        Get the thickness of the electrode.

        :return: Thickness of the electrode.
        """
        return round(self._thickness * M_TO_UM, 2)

    @property
    def cost(self) -> float:
        """
        Get the cost of the electrode.

        :return: Cost of the electrode.
        """
        return round(self._cost, 2)

    @property
    def formulation(self) -> _ElectrodeFormulation:
        """
        Get the formulation of the electrode.

        :return: Formulation of the electrode.
        """
        return self._formulation

    def __str__(self) -> str:
        return self._name
    
    def __repr__(self) -> str:
        return self.__str__()


class Anode(_Electrode):
    """
    A class representing an anode in a battery system, inheriting from the _Electrode base class.
    """
    def __init__(
            self, 
            formulation: AnodeFormulation,
            mass_loading: float,
            current_collector: _CurrentCollector,
            calender_density: float,
            insulation_material: InsulationMaterial = None,
            insulation_thickness: float = 0.0,
            name: str = 'Anode'
        ):
        """
        Initialize an object that represents an anode.

        Parameters:
        ----------
        formulation : AnodeFormulation
            The formulation of the anode.
        mass_loading : float
            The mass loading of the anode in mg/cm^2.
        current_collector : _CurrentCollector
            The current collector used in the anode.
        calender_density : float
            The density of the anode after calendering in g/cm^3.
        insulation_material : InsulationMaterial, optional
            The insulation material used in the anode (default is None).
        insulation_thickness : float, optional
            The thickness of the insulation material in micrometers (default is 0.0).
        name : str, optional
            The name of the anode (default is 'Anode').
        ----------
        """
        super().__init__(
            formulation=formulation,
            mass_loading=mass_loading,
            current_collector=current_collector,
            calender_density=calender_density,
            name=name,
            insulation_material=insulation_material,
            insulation_thickness=insulation_thickness
        )

        
class Cathode(_Electrode):
    """
    A class representing a cathode in a battery system, inheriting from the _Electrode base class.
    """
    def __init__(
            self, 
            formulation: CathodeFormulation,
            mass_loading: float,
            current_collector: _CurrentCollector,
            calender_density: float,
            insulation_material: InsulationMaterial = None,
            insulation_thickness: float = 0.0,
            name: str = 'Cathode'
        ):
        """
        Initialize an object that represents a cathode.

        Parameters
        ----------
        formulation : CathodeFormulation
            The formulation of the cathode.
        mass_loading : float
            The mass loading of the cathode in mg/cm².
        current_collector : _CurrentCollector
            The current collector used in the cathode.
        calender_density : float
            The density of the cathode after calendering in g/cm³.
        insulation_material : InsulationMaterial, optional
            The insulation material used in the cathode (default is None).
        insulation_thickness : float, optional
            The thickness of the insulation in micrometers (default is 0.0).
        name : str, optional
            The name of the cathode (default is 'Cathode').
        """
        super().__init__(
            formulation=formulation,
            mass_loading=mass_loading,
            current_collector=current_collector,
            calender_density=calender_density,
            name=name,
            insulation_material=insulation_material,
            insulation_thickness=insulation_thickness
        )



    