from SteerEnergyStorage.Formulations.ElectrodeFormulations import ElectrodeFormulation
from SteerEnergyStorage.Materials.CurrentCollectors import CurrentCollector

import pandas as pd
import numpy as np
from typing import Dict, Any
import plotly.express as px

MG_TO_KG = 1e-6
CM_TO_M = 1e-2
KG_TO_MG = 1e6
M_TO_CM = 1e2
G_TO_KG = 1e-3
KG_TO_G = 1e3
M_TO_UM = 1e6
S_TO_H = 1/3600


class _Electrode:

    def __init__(self, 
                 formulation: ElectrodeFormulation,
                 mass_loading: float,
                 current_collector: CurrentCollector,
                 calender_density: float,
                 name: str = 'Electrode'):
        """
        Initialize an object that represents an electrode.

        :param formulation: Formulation of the electrode.
        :param mass_loading: Mass loading of the electrode in mg/cm^2.
        :param current_collector: Current collector used in the electrode.
        :param calender_density: Density of the electrode after calendering in g/cm^3.
        :param name: Name of the electrode.
        """
        self._check_name(name)
        self._check_formulation(formulation)
        self._check_current_collector(current_collector)
        self._check_mass_loading(mass_loading)
        self._check_calender_density(calender_density)

        self._calculate_porosity()
        self._calculate_mass_properties()
        self._calculate_thickness_properties()
        self._calculate_mass_breakdown()
        self._calculate_cost_breakdown()

    def _check_name(self, name: str) -> None:

        if not isinstance(name, str):
            raise TypeError("Name must be a string")
        
        self._name = name

    def _check_formulation(self, formulation: ElectrodeFormulation) -> None:

        if not isinstance(formulation, ElectrodeFormulation):
            raise TypeError("Formulation must be an ElectrodeFormulation object")

        self._formulation = formulation

    def _check_current_collector(self, current_collector: CurrentCollector) -> None:

        if not isinstance(current_collector, CurrentCollector):
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
        self._single_sided_area = self._current_collector._coated_area
        self._coating_mass = self._single_sided_area * self._mass_loading * 2
        self._mass = self._coating_mass + self._current_collector._mass

    def _calculate_thickness_properties(self) -> None:
        """
        Calculate the thickness properties of the electrode.
        """
        self._material_thickness = self._mass_loading / self._calender_density
        self._material_volume = self._single_sided_area * self._material_thickness * 2
        self._thickness = self._material_thickness * 2 + self._current_collector._thickness
        self._pore_volume = self._material_volume * self._porosity

    def _calculate_mass_breakdown(self) -> None:
        """
        Calculate the mass breakdown of the electrode.
        """
        self._mass_breakdown = {'current_collector': self._current_collector._mass}
        self._mass_breakdown.update(self._calculate_component_breakdown(self._formulation._active_materials, 'active_materials'))
        self._mass_breakdown.update(self._calculate_component_breakdown(self._formulation._binders, 'binders'))
        self._mass_breakdown.update(self._calculate_component_breakdown(self._formulation._conductive_additives, 'conductive_additives'))

        active_material_mass = sum(self._mass_breakdown['active_materials'].values())
        binder_mass = sum(self._mass_breakdown['binders'].values())
        conductive_additive_mass = sum(self._mass_breakdown['conductive_additives'].values())
        current_collector_mass = self._current_collector._mass
        self._mass = active_material_mass + binder_mass + conductive_additive_mass + current_collector_mass

    def _calculate_cost_breakdown(self) -> None:
        """
        Calculate the cost breakdown of the electrode.
        """
        self._cost_breakdown = {'current_collector': self._current_collector._cost}
        self._cost_breakdown.update(self._calculate_component_cost_breakdown(self._formulation._active_materials, 'active_materials'))
        self._cost_breakdown.update(self._calculate_component_cost_breakdown(self._formulation._binders, 'binders'))
        self._cost_breakdown.update(self._calculate_component_cost_breakdown(self._formulation._conductive_additives, 'conductive_additives'))
        
        active_material_cost = sum(self._cost_breakdown['active_materials'].values())
        binder_cost = sum(self._cost_breakdown['binders'].values())
        conductive_additive_cost = sum(self._cost_breakdown['conductive_additives'].values())
        current_collector_cost = self._current_collector._cost
        self._cost = active_material_cost + binder_cost + conductive_additive_cost + current_collector_cost

    def _calculate_component_breakdown(self, components: Dict[Any, float], component_type: str) -> Dict[str, Dict[Any, float]]:
        """
        Calculate the mass breakdown for a given component type.

        :param components: Dictionary of components and their mass fractions.
        :param component_type: Type of component (e.g., 'active_materials').
        :return: Dictionary of mass breakdown for the given component type.
        """
        return {component_type: {component: fraction * self._coating_mass for component, fraction in components.items()}}

    def _calculate_component_cost_breakdown(self, components: Dict[Any, float], component_type: str) -> Dict[str, Dict[Any, float]]:
        """
        Calculate the cost breakdown for a given component type.

        :param components: Dictionary of components and their mass fractions.
        :param component_type: Type of component (e.g., 'active_materials').
        :return: Dictionary of cost breakdown for the given component type.
        """
        return {component_type: {component: fraction * self._coating_mass * component._specific_cost for component, fraction in components.items()}}

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
        
        self._porosity = 1 - (theoretical_specific_volume * self._calender_density)
    
    def _calculate_half_cell_curve(self, grid_n: int) -> None:
        """
        Calculate the half cell curve of the electrode.

        :param grid_n: Number of points to interpolate the curve on.
        """
        data = self._calculate_capacity_curves()
        data = data.groupby('active_material', group_keys=True).apply(lambda df: df.pipe(self._order_and_clean_curves)).reset_index(drop=True)
        data = data.groupby('direction', group_keys=True).apply(lambda df: df.pipe(self._linear_interpolate_on_voltage, grid_n)).reset_index(drop=False)
        data = data.groupby(['direction', 'voltage'], group_keys=True).agg({'capacity': 'sum'}).reset_index(drop=False)
        data = self._flip_and_shift_curves(data)
        self._half_cell_curve = data
        reversible_capacity = self._half_cell_curve.query("direction == 'discharge'")['capacity'].max()
        self._areal_capacity = reversible_capacity / (self._single_sided_area * 2)

    def _calculate_capacity_curves(self) -> pd.DataFrame:
        """
        Calculate the capacity curves of the electrode.

        :return: DataFrame containing the capacity curves.
        """
        half_cell_curve = []
        for am in self._formulation._active_materials.keys():
            am_mass = self._coating_mass * self._formulation._active_materials[am]
            irrev_scale = am._irreversible_capacity_scaling
            rev_scaling = am._reversible_capacity_scaling
            data = am._half_cell_curve.copy()
            data['capacity'] = data['specific_capacity'] * am_mass

            data['capacity'] = [c * irrev_scale if d == 'charge' 
                                           else c * irrev_scale * rev_scaling
                                           for c, d in zip(data['capacity'], data['direction'])]
            
            data = (data
                    .filter(['voltage', 'capacity', 'direction'])
                    .sort_values(by=['direction', 'capacity'])
                    .assign(active_material=am)
                    )

            half_cell_curve.append(data)

        return pd.concat(half_cell_curve)

    def _linear_interpolate_on_voltage(self, data: pd.DataFrame, grid_n: int) -> pd.DataFrame:
        """
        Cubic spline interpolate the curves on voltage.

        :param data: DataFrame containing the capacity curves.
        :param grid_n: Number of points to interpolate the curve on.
        :return: DataFrame containing the interpolated curves.
        """
        data = data.sort_values('voltage')
        interpolated_curves = []
        v_min = data['voltage'].min()
        v_max = data['voltage'].max()
        voltage_grid = np.linspace(v_min, v_max, grid_n)
        for am, df in data.groupby('active_material'):
            x = df['voltage']
            y = df['capacity']
            new_y = np.interp(voltage_grid, x, y)
            new_data = pd.DataFrame({'voltage': voltage_grid, 'capacity': new_y, 'active_material': am})
            interpolated_curves.append(new_data)

        new_data = pd.concat(interpolated_curves)

        return new_data

    def _flip_and_shift_curves(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Flip and shift the curves.

        :param data: DataFrame containing the interpolated curves.
        :return: DataFrame containing the flipped and shifted curves.
        """
        data = (data
                .assign(max_capacity=lambda x: x['capacity'].max())
                .assign(capacity=lambda x: [-c + m if d == 'discharge' else c for c, d, m in zip(x['capacity'], x['direction'], x['max_capacity'])])
                .reset_index(drop=True)
                .drop(columns=['max_capacity'])
                )
                
        charge_curve = data.query("direction == 'charge'").sort_values('capacity', ascending=True)
        discharge_curve = data.query("direction == 'discharge'").sort_values('capacity', ascending=False)
        return pd.concat([charge_curve, discharge_curve]).reset_index(drop=True)

    def plot_half_cell_curve(self, grid_n: int = 100, **kwargs) -> None:
        """
        Plot the half cell curve of the electrode.

        :param grid_n: Number of points to interpolate the curve on.
        """
        if not hasattr(self, '_half_cell_curve'):
            self._calculate_half_cell_curve(grid_n)

        fig = px.line(self.half_cell_curve, y='Voltage (V)', x='Capacity (Ah)', color='Direction',
                      title='Capacity vs Voltage', line_shape='spline', template='presentation', **kwargs)

        return fig    

    @property
    def cost_breakdown(self) -> Dict[str, Any]:
        """
        Get the cost breakdown of the electrode.

        :return: Dictionary containing the cost breakdown.
        """
        return self._format_breakdown(self._cost_breakdown)

    @property
    def mass_breakdown(self) -> Dict[str, Any]:
        """
        Get the mass breakdown of the electrode.

        :return: Dictionary containing the mass breakdown.
        """
        return self._format_breakdown(self._mass_breakdown)

    def _format_breakdown(self, breakdown: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format the breakdown dictionary.

        :param breakdown: Dictionary containing the breakdown.
        :return: Formatted breakdown dictionary.
        """
        formatted_breakdown = {}
        for key, value in breakdown.items():
            if isinstance(value, dict):
                value = {k: round(v, 5) for k, v in value.items()}
            else:
                value = round(value, 5)
            key = key.replace('_', ' ').title()
            formatted_breakdown[key] = value

        return formatted_breakdown

    @property
    def half_cell_curve(self) -> pd.DataFrame:
        """
        Get the half cell curve of the electrode.

        :return: DataFrame containing the half cell curve.
        """
        if not hasattr(self, '_half_cell_curve'):
            raise ValueError("Half cell curve not calculated. Call _calculate_half_cell_curve() first.")

        return (self
                ._half_cell_curve
                .assign(capacity=lambda x: x['capacity'] * S_TO_H)
                .rename(columns={'capacity': 'Capacity (Ah)', 
                                 'voltage': 'Voltage (V)', 
                                 'direction': 'Direction'})
                )

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
    def formulation(self) -> ElectrodeFormulation:
        """
        Get the formulation of the electrode.

        :return: Formulation of the electrode.
        """
        return self._formulation

    @property
    def mass_loading(self) -> float:
        """
        Get the mass loading of the electrode.

        :return: Mass loading of the electrode.
        """
        return round(self._mass_loading * (KG_TO_MG / M_TO_CM**2), 2)

    @property
    def current_collector(self) -> CurrentCollector:
        """
        Get the current collector of the electrode.

        :return: Current collector of the electrode.
        """
        return self._current_collector

    @property
    def single_sided_area(self) -> float:
        """
        Get the single-sided area of the electrode.

        :return: Single-sided area of the electrode.
        """
        return round(self._single_sided_area, 2)

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
    def material_thickness(self) -> float:
        """
        Get the material thickness of the electrode.

        :return: Material thickness of the electrode.
        """
        return round(self._material_thickness * M_TO_UM, 2)

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

    def __str__(self) -> str:
        return self._name
    
    def __repr__(self) -> str:
        return self.__str__()


class Anode(_Electrode):
    
    def __init__(self, 
                 formulation: ElectrodeFormulation,
                 mass_loading: float,
                 current_collector: CurrentCollector,
                 calender_density: float,
                 name: str = 'Anode',
                 anode_free = False):
        """
        Initialize an object that represents an anode.

        :param formulation: Formulation of the anode.
        :param mass_loading: Mass loading of the anode in mg/cm^2.
        :param current_collector: Current collector used in the anode.
        :param calender_density: Density of the anode after calendering in g/cm^3.
        :param name: Name of the anode.
        """
        super().__init__(formulation=formulation,
                         mass_loading=mass_loading,
                         current_collector=current_collector,
                         calender_density=calender_density,
                         name=name)
        
        self._anode_free = anode_free
        self._current_collector._anode = True
        
    def _order_and_clean_curves(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Order and clean the curves ready for interpolation.

        :param data: DataFrame containing the capacity curves.
        :return: DataFrame containing the ordered and cleaned curves.
        """
        charge_data = (data
                       .query("direction == 'charge'")
                       .sort_values('capacity', ascending=True)
                       .assign(min_vol=lambda x: x['voltage'].cummin())
                       .query("voltage >= min_vol")
                       )
        
        discharge_data = (data
                          .query("direction == 'discharge'")
                          .sort_values('capacity', ascending=False)
                          .assign(min_vol=lambda x: x['voltage'].cummin())
                          .query("voltage <= min_vol")
                          )

        return pd.concat([charge_data, discharge_data]).reset_index(drop=True)


class Cathode(_Electrode):
    
    def __init__(self, 
                 formulation: ElectrodeFormulation,
                 mass_loading: float,
                 current_collector: CurrentCollector,
                 calender_density: float,
                 name: str = 'Cathode'):
        """
        Initialize an object that represents a cathode.

        :param formulation: Formulation of the cathode.
        :param mass_loading: Mass loading of the cathode in mg/cm^2.
        :param current_collector: Current collector used in the cathode.
        :param calender_density: Density of the cathode after calendering in g/cm^3.
        :param name: Name of the cathode.
        """
        super().__init__(formulation=formulation,
                         mass_loading=mass_loading,
                         current_collector=current_collector,
                         calender_density=calender_density,
                         name=name)
        
    def _order_and_clean_curves(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Order and clean the curves ready for interpolation.

        :param data: DataFrame containing the capacity curves.
        :return: DataFrame containing the ordered and cleaned curves.
        """
        charge_data = (data
                       .query("direction == 'charge'")
                       .sort_values('capacity', ascending=True)
                       .assign(max_vol=lambda x: x['voltage'].cummax())
                       .query("voltage >= max_vol")
                       )
        
        discharge_data = (data
                          .query("direction == 'discharge'")
                          .sort_values('capacity', ascending=False)
                          .assign(max_vol=lambda x: x['voltage'].cummax())
                          .query("voltage <= max_vol")
                          )

        return pd.concat([charge_data, discharge_data]).reset_index(drop=True).drop(columns=['max_vol'])



