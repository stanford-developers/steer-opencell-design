from steer_opencell_design.Constructions.ElectrodeAssemblies import (
    Stack,
    CylindricalJellyRoll,
    FlatJellyRoll,
    _JellyRoll,
)
from steer_opencell_design.Components.Electrolytes import Electrolyte
from steer_opencell_design.Components.Containers import (
    Pouch,
    PrismaticCase,
    CylindricalCase,
)

from App.general.styles import *
from steer_opencell_design.Constants import *
from steer_opencell_design.Decorators import get_colorway

import pandas as pd
import numpy as np

import plotly.express as px
import plotly.graph_objects as go
from copy import deepcopy
from scipy.interpolate import CubicSpline


class _Cell:
    def __init__(
        self,
        electrode_assembly: Stack | CylindricalJellyRoll | FlatJellyRoll,
        n_electrode_assembly: int,
        electrolyte: Electrolyte,
        electrolyte_overfill: float,
        encapsulation: Pouch | PrismaticCase | CylindricalCase,
        reversible_capacity: float,
        irreversible_capacity: float,
        grid_n: int = 100,
        name: str = "cell",
    ):
        """
        Initiate an object that represents an electrochemical cell.

        :param electrode_assembly: Electrode assembly used in the cell
        :param n_electrode_assembly: Number of electrode assemblies in the cell
        :param electrolyte: Electrolyte used in the cell
        :param electrolyte_overfill: Overfill of the electrolyte in the cell (%)
        :param encapsulation: Encapsulation of the cell
        :param reversible_capacity: Reversible capacity of the cell in Ah
        :param irreversible_capacity: Irreversible capacity of the cell in Ah
        :param grid_n: Number of points to interpolate the half cell curves
        :param name: Name of the cell
        """
        self._check_and_copy_encapsulation(encapsulation)
        self._check_and_copy_electrode_assembly(electrode_assembly, n_electrode_assembly)
        self._check_and_copy_electrolyte(electrolyte, electrolyte_overfill)
        self._check_anode_free(electrode_assembly)

        self._check_name(name)
        self._check_reversible_capacity(reversible_capacity)
        self._check_irreversible_capacity(irreversible_capacity)
        self._check_grid_n(grid_n)

        self._calculate_electrolyte_quantities()
        self._calculate_half_cell_curve()
        self._calculate_full_cell_curve()
        self._get_effective_areal_capacity()  # TODO

        self._calculate_mass_breakdown()
        self._calculate_cost_breakdown()
        self._calculate_geometry_properties()
        self._calculate_energy_properties()

    def _calculate_geometry_properties(self):
        pass

    def _calculate_electrolyte_quantities(self):
        """
        Function to calculate the electrolyte quantities in the cell
        """
        self._electrolyte._volume = sum([s._pore_volume for s in self._electrode_assemblies]) * (1 + self._electrolyte_overfill)
        self._electrolyte._mass = self._electrolyte._volume * self._electrolyte._density
        self._electrolyte._cost = (self._electrolyte._mass) * self._electrolyte._specific_cost

    def _check_anode_free(self, electrode_assembly: Stack | CylindricalJellyRoll | FlatJellyRoll) -> None:
        if electrode_assembly._anode_free:
            self._anode_free = True
        else:
            self._anode_free = False

    def _check_and_copy_electrode_assembly(
        self,
        electrode_assembly: Stack | CylindricalJellyRoll | FlatJellyRoll,
        n_electrode_assembly: int,
    ) -> None:
        """
        Function to validate the electrode assembly and copy it n times

        :param electrode_assembly: Electrode assembly to validate
        :param n_electrode_assembly: Number of times to copy the electrode assembly
        """
        if not isinstance(electrode_assembly, (Stack, CylindricalJellyRoll, FlatJellyRoll)):
            raise ValueError("Electrode assembly must be an instance of Stack, CylindricalJellyRoll or FlatJellyRoll")

        if not isinstance(n_electrode_assembly, int):
            raise ValueError("Number of electrode assembly must be an integer")

        if n_electrode_assembly <= 0:
            raise ValueError("Number of electrode assembly must be greater than 0")

        self._electrode_assemblies = [deepcopy(electrode_assembly) for _ in range(n_electrode_assembly)]

    def _check_and_copy_electrolyte(self, electrolyte: Electrolyte, electrolyte_overfill: float):
        """
        Function to validate and copy electrolyte
        """
        if not isinstance(electrolyte, Electrolyte):
            raise ValueError("Electrolyte must be an instance of Electrolyte")

        if not (0 <= electrolyte_overfill <= 100):
            raise ValueError("Electrolyte_overfill percentage must be between 0 and 100")

        self._electrolyte = deepcopy(electrolyte)
        self._electrolyte_overfill = electrolyte_overfill / 100

    def _check_and_copy_encapsulation(self, encapsulation: Pouch | PrismaticCase | CylindricalCase) -> None:
        """
        Function to validate and copy encapsulation

        :param encapsulation: Encapsulation to validate
        """
        if not isinstance(encapsulation, (Pouch, PrismaticCase, CylindricalCase)):
            raise ValueError("Encapsulation must be an instance of Pouch, PrismaticCase or CylindricalShell")

        self._encapsulation = deepcopy(encapsulation)

    def _check_name(self, name: str) -> None:
        """
        Function to validate name

        :param name: Name to validate
        """
        if not isinstance(name, str):
            raise ValueError("Name must be a string")

        self._name = name

    def _check_reversible_capacity(self, reversible_capacity: float) -> None:
        """
        Function to validate reversible capacity

        :param reversible_capacity: Reversible capacity to validate
        """
        if not isinstance(reversible_capacity, (int, float)):
            raise ValueError("Reversible capacity must be a number")

        if reversible_capacity <= 0:
            raise ValueError("Reversible capacity must be greater than 0")

        self._reversible_capacity = reversible_capacity * H_TO_S

    def _check_irreversible_capacity(self, irreversible_capacity: float) -> None:
        """
        Function to validate irreversible capacity

        :param irreversible_capacity: Irreversible capacity to validate
        """
        if not isinstance(irreversible_capacity, (int, float)):
            raise ValueError("Irreversible capacity must be a number")

        if irreversible_capacity < 0:
            raise ValueError("Irreversible capacity must be greater than 0")

        self._irreversible_capacity = irreversible_capacity * H_TO_S

    def _check_grid_n(self, grid_n: int) -> None:
        """
        Function to validate grid_n

        :param grid_n: Number of points to interpolate the half cell curves
        """
        if not isinstance(grid_n, int):
            raise ValueError("Grid_n must be an integer")

        if grid_n <= 20:
            raise ValueError("Grid_n must be greater than 20")

        self._grid_n = grid_n

    def _add_to_dict(self, dictionary_1: dict, dictionary_2: dict | float | int):
        for key, value in dictionary_2.items():
            if key in dictionary_1:
                dictionary_1[key] += value
            else:
                dictionary_1[key] = value

        return dictionary_1

    def _calculate_half_cell_curve(self):
        """
        Function to calculate the half cell curve of the stack from the half cell curves of the anode and cathode active materials
        """
        for s in self._electrode_assemblies:
            s._calculate_half_cell_curve(grid_n=self._grid_n)

        cathode_half_cell = (
            pd.concat([s._cathode_half_cell_curve for c in self._electrode_assemblies])
            .groupby(["direction", "voltage"], as_index=False)["capacity"]
            .sum()
            .groupby("direction", as_index=False)
            .apply(
                lambda x: x.sort_values(
                    "capacity",
                    ascending=True if x["direction"].values[0] == "charge" else False,
                )
            )
        )

        self._cathode_half_cell_curve = cathode_half_cell

        if not self._anode_free:
            anode_half_cell = (
                pd.concat([s._anode_half_cell_curve for s in self._electrode_assemblies])
                .groupby(["direction", "voltage"], as_index=False)["capacity"]
                .sum()
                .groupby("direction", as_index=False)
                .apply(
                    lambda x: x.sort_values(
                        "capacity",
                        ascending=True if x["direction"].values[0] == "charge" else False,
                    )
                )
            )

            self._anode_half_cell_curve = anode_half_cell

    def _calculate_full_cell_curve(self):
        """
        Function to calculate the full cell curves of the stack
        """
        for s in self._electrode_assemblies:
            s._calculate_full_cell_curve()

        full_cell_curve = pd.concat([s._full_cell_curve for s in self._electrode_assemblies]).groupby(["direction", "voltage"], as_index=False)["capacity"].sum().sort_values(["direction", "capacity"])

        charge_curve = full_cell_curve.query("direction == 'charge'")
        discharge_curve = full_cell_curve.query("direction == 'discharge'")

        # interpolate charge_curve on capacity
        min_cap = charge_curve["capacity"].min()
        top_cap = self._reversible_capacity + self._irreversible_capacity
        max_cap = top_cap if top_cap < charge_curve["capacity"].max() else charge_curve["capacity"].max()
        cap_grid = np.linspace(min_cap, max_cap, self._grid_n)
        cs = CubicSpline(charge_curve["capacity"], charge_curve["voltage"])
        new_voltage = cs(cap_grid)
        charge_curve = pd.DataFrame({"capacity": cap_grid, "voltage": new_voltage, "direction": "charge"})

        # interpolate discharge_curve on capacity
        max_cap = top_cap if top_cap < charge_curve["capacity"].max() else charge_curve["capacity"].max()
        min_cap = self._irreversible_capacity if self._irreversible_capacity > discharge_curve["capacity"].min() else discharge_curve["capacity"].min()
        cap_grid = np.linspace(min_cap, max_cap, self._grid_n)
        cs = CubicSpline(discharge_curve["capacity"], discharge_curve["voltage"])
        new_voltage = cs(cap_grid)
        discharge_curve = pd.DataFrame({"capacity": cap_grid, "voltage": new_voltage, "direction": "discharge"})

        self._full_cell_curve = (
            pd.concat([charge_curve, discharge_curve])
            .groupby("direction", as_index=False)
            .apply(
                lambda x: x.sort_values(
                    "capacity",
                    ascending=True if x["direction"].values[0] == "charge" else False,
                )
            )
        )

    def _get_effective_areal_capacity(self) -> None:
        """
        Function to calculate the effective areal capacity of the stacks
        """
        self._effective_areal_capacity = self._reversible_capacity / sum([s._areal_capacity for s in self._electrode_assemblies])

    def _linear_interpolate_on_voltage(self, df) -> pd.DataFrame:
        direction = df["direction"].iloc[0]
        electrode = df["electrode"].iloc[0]

        if direction == "discharge" and electrode == "cathode":
            df = df.sort_values(by="capacity", ascending=False)
        elif direction == "charge" and electrode == "anode":
            df = df.sort_values(by="capacity", ascending=False)

        x_max = df["voltage"].max()
        x_min = df["voltage"].min()
        x = df["voltage"]
        y = df["capacity"]
        y_new = np.interp(self._v_grid, x, y)

        return pd.DataFrame({"capacity": y_new, "voltage": self._v_grid}).query("voltage >= @x_min and voltage <= @x_max")

    def _linear_interpolate_on_capacity(self, df) -> pd.DataFrame:
        df = df.sort_values(by="capacity", ascending=True)
        x_max = df["capacity"].max()
        x_min = df["capacity"].min()
        x = df["capacity"]
        y = df["voltage"]
        y_new = np.interp(self._c_grid, x, y)

        return pd.DataFrame({"voltage": y_new, "capacity": self._c_grid}).query("capacity >= @x_min and capacity <= @x_max")

    def _get_color_map(self):
        color_map = {
            "Electrolyte": "#3465A4",
            "Encapsulation": CURRENT_COLLECTOR_COLOR,
            "Cathode": CATHODE_COLOR,
            "Anode": ANODE_COLOR,
            "Separator": SEPARATOR_COLOR,
        }

        items = [
            "active_materials",
            "binders",
            "conductive_additives",
            "current_collectors",
        ]
        color_tups = [
            ("#D7263D", "#FF758F"),
            ("#007F5F", "#2BB673"),
            ("#F49D37", "#FFD166"),
            ("#3A86FF", "#A0C4FF"),
        ]

        for item, color_tup in zip(items, color_tups):
            anode_items = [a.name for a in list(self._anode_mass_breakdown[item].keys())]
            anode_colors = get_colorway(color_tup[0], color_tup[1], len(anode_items))
            anode_map = {item: color for item, color in zip(anode_items, anode_colors)}
            color_map.update(anode_map)

            cathode_items = [c.name for c in list(self._cathode_mass_breakdown[item].keys())]
            cathode_colors = get_colorway(color_tup[0], color_tup[1], len(cathode_items))
            cathode_map = {item: color for item, color in zip(cathode_items, cathode_colors)}
            color_map.update(cathode_map)

        return color_map

    def _get_mass_breakdown_plot_pie(self, **kwargs):
        mass_breakdown = self.mass_breakdown
        electrode_assembly_mass_breakdown = self.electrode_assembly_mass_breakdown
        mass_breakdown.pop("Electrode Assemblies")
        mass_breakdown.update(electrode_assembly_mass_breakdown)
        mass_breakdown = pd.DataFrame(mass_breakdown.items(), columns=["component", "mass"]).assign(level="Cell")

        anode_mass_breakdown = self.anode_mass_breakdown
        anode_mass_breakdown = {obj: value for innder_dict in anode_mass_breakdown.values() for obj, value in innder_dict.items()}
        anode_mass_breakdown = pd.DataFrame(anode_mass_breakdown.items(), columns=["component", "mass"]).assign(level="Anode").assign(component=lambda x: x["component"].apply(lambda y: y.name))

        cathode_mass_breakdown = self.cathode_mass_breakdown
        cathode_mass_breakdown = {obj: value for innder_dict in cathode_mass_breakdown.values() for obj, value in innder_dict.items()}
        cathode_mass_breakdown = pd.DataFrame(cathode_mass_breakdown.items(), columns=["component", "mass"]).assign(level="Cathode").assign(component=lambda x: x["component"].apply(lambda y: y.name))

        color_map = self._get_color_map()
        data = pd.concat([mass_breakdown, anode_mass_breakdown, cathode_mass_breakdown])

        figure = px.pie(
            data,
            values="mass",
            names="component",
            title="Mass Breakdown",
            facet_col="level",
            color="component",
            color_discrete_map=color_map,
        )
        figure.update_traces(
            textposition="inside",
            textinfo="percent+label",
            marker=dict(line=dict(color="#000000", width=2)),
        )
        figure.for_each_annotation(lambda a: a.update(text=a.text.split("=")[1]))

        return figure

    def _get_cost_breakdown_plot_pie(self, **kwargs):
        cost_breakdown = self.cost_breakdown
        electrode_assembly_cost_breakdown = self.electrode_assembly_cost_breakdown
        cost_breakdown.pop("Electrode Assemblies")
        cost_breakdown.update(electrode_assembly_cost_breakdown)
        cost_breakdown = pd.DataFrame(cost_breakdown.items(), columns=["component", "cost"]).assign(level="Cell")

        anode_cost_breakdown = self.anode_cost_breakdown
        anode_cost_breakdown = {obj: value for innder_dict in anode_cost_breakdown.values() for obj, value in innder_dict.items()}
        anode_cost_breakdown = pd.DataFrame(anode_cost_breakdown.items(), columns=["component", "cost"]).assign(level="Anode").assign(component=lambda x: x["component"].apply(lambda y: y.name))

        cathode_cost_breakdown = self.cathode_cost_breakdown
        cathode_cost_breakdown = {obj: value for innder_dict in cathode_cost_breakdown.values() for obj, value in innder_dict.items()}
        cathode_cost_breakdown = pd.DataFrame(cathode_cost_breakdown.items(), columns=["component", "cost"]).assign(level="Cathode").assign(component=lambda x: x["component"].apply(lambda y: y.name))

        color_map = self._get_color_map()
        data = pd.concat([cost_breakdown, anode_cost_breakdown, cathode_cost_breakdown])

        figure = px.pie(
            data,
            values="cost",
            names="component",
            title="Cost Breakdown",
            facet_col="level",
            color="component",
            color_discrete_map=color_map,
        )
        figure.update_traces(
            textposition="inside",
            textinfo="percent+label",
            marker=dict(line=dict(color="#000000", width=2)),
        )
        figure.for_each_annotation(lambda a: a.update(text=a.text.split("=")[1]))

        return figure

    def _get_cost_breakdown_plot_sunburst(self, background_color="white", **kwargs):
        cost_breakdown = pd.DataFrame(self.cost_breakdown.items(), columns=["level_1", "cost"]).query('level_1 != "Electrode Assemblies"').assign(level_2=None).assign(level_0="Cell")

        electrode_assembly_cost_breakdown = (
            pd.DataFrame(
                self.electrode_assembly_cost_breakdown.items(),
                columns=["level_1", "cost"],
            )
            .query('level_1 != "Anode" and level_1 != "Cathode"')
            .assign(level_0="Cell")
            .assign(level_2=None)
        )

        anode_cost_breakdown = self.anode_cost_breakdown
        anode_cost_breakdown = {obj: value for innder_dict in anode_cost_breakdown.values() for obj, value in innder_dict.items()}
        anode_cost_breakdown = pd.DataFrame(anode_cost_breakdown.items(), columns=["level_2", "cost"]).assign(level_1="Anode").assign(level_0="Cell").assign(level_2=lambda x: x["level_2"].apply(lambda y: y.name))

        cathode_cost_breakdown = self.cathode_cost_breakdown
        cathode_cost_breakdown = {obj: value for innder_dict in cathode_cost_breakdown.values() for obj, value in innder_dict.items()}
        cathode_cost_breakdown = pd.DataFrame(cathode_cost_breakdown.items(), columns=["level_2", "cost"]).assign(level_1="Cathode").assign(level_0="Cell").assign(level_2=lambda x: x["level_2"].apply(lambda y: y.name))

        color_map = self._get_color_map()

        data = pd.concat(
            [
                cost_breakdown,
                anode_cost_breakdown,
                cathode_cost_breakdown,
                electrode_assembly_cost_breakdown,
            ]
        ).drop(columns=["level_0"])

        figure = px.sunburst(
            data,
            path=["level_1", "level_2"],
            values="cost",
            color="level_1",
            color_discrete_map=color_map,
            **kwargs,
        )
        figure.update_traces(textinfo="percent parent+label")
        figure.for_each_annotation(lambda a: a.update(text=a.text.split("=")[1]))
        
        figure.update_layout(
            plot_bgcolor=background_color,
            paper_bgcolor=background_color,
            margin=dict(t=20, l=80, r=80, b=80),
        )

        return figure

    def _get_mass_breakdown_plot_sunburst(self, background_color="white", **kwargs):
        mass_breakdown = pd.DataFrame(self.mass_breakdown.items(), columns=["level_1", "mass"]).query('level_1 != "Electrode Assemblies"').assign(level_2=None).assign(level_0="Cell")

        electrode_assembly_mass_breakdown = (
            pd.DataFrame(
                self.electrode_assembly_mass_breakdown.items(),
                columns=["level_1", "mass"],
            )
            .query('level_1 != "Anode" and level_1 != "Cathode"')
            .assign(level_0="Cell")
            .assign(level_2=None)
        )

        anode_mass_breakdown = self.anode_mass_breakdown
        anode_mass_breakdown = {obj: value for innder_dict in anode_mass_breakdown.values() for obj, value in innder_dict.items()}
        anode_mass_breakdown = pd.DataFrame(anode_mass_breakdown.items(), columns=["level_2", "mass"]).assign(level_1="Anode").assign(level_0="Cell").assign(level_2=lambda x: x["level_2"].apply(lambda y: y.name))

        cathode_mass_breakdown = self.cathode_mass_breakdown
        cathode_mass_breakdown = {obj: value for innder_dict in cathode_mass_breakdown.values() for obj, value in innder_dict.items()}
        cathode_mass_breakdown = pd.DataFrame(cathode_mass_breakdown.items(), columns=["level_2", "mass"]).assign(level_1="Cathode").assign(level_0="Cell").assign(level_2=lambda x: x["level_2"].apply(lambda y: y.name))

        color_map = self._get_color_map()

        data = pd.concat(
            [
                mass_breakdown,
                anode_mass_breakdown,
                cathode_mass_breakdown,
                electrode_assembly_mass_breakdown,
            ]
        ).drop(columns=["level_0"])

        figure = px.sunburst(
            data,
            path=["level_1", "level_2"],
            values="mass",
            color="level_1",
            color_discrete_map=color_map,
            **kwargs,
        )
        figure.update_traces(textinfo="percent parent+label")
        figure.for_each_annotation(lambda a: a.update(text=a.text.split("=")[1]))
        figure.update_layout(
            plot_bgcolor=background_color,
            paper_bgcolor=background_color,
            margin=dict(t=20, l=80, r=80, b=80),
        )

        return figure

    def _calculate_mass_breakdown(self):
        self._mass_breakdown = {
            "electrode_assemblies": sum([s._mass for s in self._electrode_assemblies]),
            "electrolyte": self._electrolyte._mass,
            "encapsulation": self._encapsulation._mass,
        }

        self._electrode_assembly_mass_breakdown = {
            "cathode": sum([s._mass_breakdown["cathode"] for s in self._electrode_assemblies]),
            "anode": sum([s._mass_breakdown["anode"] for s in self._electrode_assemblies]),
            "separator": sum([s._mass_breakdown["separator"] for s in self._electrode_assemblies]),
        }

        anode_mass_breakdown = {
            "active_materials": {},
            "binders": {},
            "conductive_additives": {},
            "current_collectors": {},
        }
        cathode_mass_breakdown = {
            "active_materials": {},
            "binders": {},
            "conductive_additives": {},
            "current_collectors": {},
        }

        for s in self._electrode_assemblies:
            for key in anode_mass_breakdown.keys():
                anode_mass_breakdown[key] = self._add_to_dict(anode_mass_breakdown[key], s._anode_mass_breakdown[key])
            for key in cathode_mass_breakdown.keys():
                cathode_mass_breakdown[key] = self._add_to_dict(cathode_mass_breakdown[key], s._cathode_mass_breakdown[key])

        self._anode_mass_breakdown = anode_mass_breakdown
        self._cathode_mass_breakdown = cathode_mass_breakdown

        self._mass = sum(self._mass_breakdown.values())

    def _calculate_cost_breakdown(self):
        self._cost_breakdown = {
            "electrode_assemblies": sum([s._cost for s in self._electrode_assemblies]),
            "electrolyte": self._electrolyte._cost,
            "encapsulation": self._encapsulation._cost,
        }

        self._electrode_assembly_cost_breakdown = {
            "cathode": sum([s._cost_breakdown["cathode"] for s in self._electrode_assemblies]),
            "anode": sum([s._cost_breakdown["anode"] for s in self._electrode_assemblies]),
            "separator": sum([s._cost_breakdown["separator"] for s in self._electrode_assemblies]),
        }

        anode_cost_breakdown = {
            "active_materials": {},
            "binders": {},
            "conductive_additives": {},
            "current_collectors": {},
        }
        cathode_cost_breakdown = {
            "active_materials": {},
            "binders": {},
            "conductive_additives": {},
            "current_collectors": {},
        }

        for s in self._electrode_assemblies:
            for key in anode_cost_breakdown.keys():
                anode_cost_breakdown[key] = self._add_to_dict(anode_cost_breakdown[key], s._anode_cost_breakdown[key])
            for key in cathode_cost_breakdown.keys():
                cathode_cost_breakdown[key] = self._add_to_dict(cathode_cost_breakdown[key], s._cathode_cost_breakdown[key])

        self._anode_cost_breakdown = anode_cost_breakdown
        self._cathode_cost_breakdown = cathode_cost_breakdown

        self._cost = sum(self._cost_breakdown.values())

    def _calculate_energy_properties(self):
        self._energy = -np.trapezoid(
            self._full_cell_curve.query("direction == 'discharge'")["voltage"],
            self._full_cell_curve.query("direction == 'discharge'")["capacity"],
        )

        self._specific_energy = self._energy / self._mass
        self._energy_density = self._energy / self._volume
        self._normalized_cost = self._cost / self._energy

    def get_capacity_voltage_plot(
        self,
        background_color="white",
        upper_v_limit=None,
        lower_v_limit=None,
        n_p_ratio=None,
        **kwargs,
    ):
        cathode_curve = self.cathode_half_cell_curve.copy().assign(Electrode="Cathode")
        anode_curve = self.anode_half_cell_curve.copy().assign(Electrode="Anode") if not self._anode_free else None
        full_curves = self.full_cell_curve.copy().assign(Electrode="Full Cell")

        data = pd.concat([cathode_curve, anode_curve, full_curves])
        upper_cap_limit = self.reversible_capacity + self.irreversible_capacity
        lower_cap_limit = self.irreversible_capacity

        color_map = {"Cathode": "blue", "Anode": "red", "Full Cell": "black"}

        figure = px.line(
            data,
            x="Capacity (Ah)",
            y="Voltage (V)",
            color="Electrode",
            title="Capacity vs Voltage",
            line_shape="spline",
            template="presentation",
            color_discrete_map=color_map,
            **kwargs,
        )

        y_max = data["Voltage (V)"].max()
        y_min = data["Voltage (V)"].min()
        y_range = y_max - y_min
        y_plot_range = [y_min - y_range * 0.1, y_max + y_range * 0.1]

        if n_p_ratio is not None:
            n_p_ratio_value = upper_cap_limit * n_p_ratio
            x_max = data["Capacity (Ah)"].max() if data["Capacity (Ah)"].max() > n_p_ratio_value else n_p_ratio_value
        else:
            x_max = data["Capacity (Ah)"].max()

        x_min = data["Capacity (Ah)"].min()
        x_range = x_max - x_min
        x_plot_range = [x_min - x_range * 0.1, x_max + x_range * 0.1]

        # add capacity lines
        figure.add_traces(
            go.Scatter(
                x=[upper_cap_limit, upper_cap_limit],
                y=y_plot_range,
                mode="lines",
                line=dict(color="orange", width=2, dash="dash"),
                name="Upper Capacity Limit",
            )
        )
        figure.add_traces(
            go.Scatter(
                x=[lower_cap_limit, lower_cap_limit],
                y=y_plot_range,
                mode="lines",
                line=dict(color="royalblue", width=2, dash="dash"),
                name="Lower Capacity Limit",
            )
        )

        if upper_v_limit is not None:
            figure.add_traces(
                go.Scatter(
                    x=x_plot_range,
                    y=[upper_v_limit, upper_v_limit],
                    mode="lines",
                    line=dict(color="firebrick", width=2, dash="dot"),
                    name="Upper Voltage Limit",
                )
            )
        if lower_v_limit is not None:
            figure.add_traces(
                go.Scatter(
                    x=x_plot_range,
                    y=[lower_v_limit, lower_v_limit],
                    mode="lines",
                    line=dict(color="seagreen", width=2, dash="dashdot"),
                    name="Lower Voltage Limit",
                )
            )
        if n_p_ratio is not None:
            figure.add_traces(
                go.Scatter(
                    x=[n_p_ratio_value, n_p_ratio_value],
                    y=y_plot_range,
                    mode="lines",
                    line=dict(color="black", width=2.5, dash="longdash"),
                    name="n/p Ratio",
                )
            )

        figure.update_layout(
            plot_bgcolor=background_color,
            paper_bgcolor=background_color,
            legend=dict(title_text=""),
        )

        return figure

    def get_mass_breakdown_plot(self, mode: str = "sunburst", **kwargs):
        if mode.lower() == "pie":
            figure = self._get_mass_breakdown_plot_pie(**kwargs)
        elif mode.lower() == "sunburst":
            figure = self._get_mass_breakdown_plot_sunburst(**kwargs)
        else:
            raise ValueError("Plot mode not recognized. Please choose between ['pie', 'sunburst']")

        return figure

    def get_cost_breakdown_plot(self, mode: str = "sunburst", **kwargs):
        if mode.lower() == "pie":
            figure = self._get_cost_breakdown_plot_pie(**kwargs)
        elif mode.lower() == "sunburst":
            figure = self._get_cost_breakdown_plot_sunburst(**kwargs)
        else:
            raise ValueError("Plot mode not recognized. Please choose between ['pie', 'sunburst']")

        return figure

    @property
    def electrolyte_overfill(self) -> float:
        return self._electrolyte_overfill * 100

    @property
    def full_cell_curve(self):
        if not hasattr(self, "_full_cell_curve"):
            raise AttributeError("Full cell curves have not been calculated yet")

        data = self._full_cell_curve.assign(capacity=lambda x: x["capacity"] * S_TO_H).rename(
            columns={
                "capacity": "Capacity (Ah)",
                "voltage": "Voltage (V)",
                "direction": "Direction",
            }
        )

        return data

    @property
    def name(self) -> str:
        return self._name

    @property
    def reversible_capacity(self) -> float:
        return round(self._reversible_capacity * S_TO_H, 2)

    @property
    def irreversible_capacity(self) -> float:
        return round(self._irreversible_capacity * S_TO_H, 2)

    @property
    def cost_breakdown(self) -> dict:
        if not hasattr(self, "_cost_breakdown"):
            raise AttributeError("Cost breakdown has not been calculated yet")
        return {item.replace("_", " ").title(): round(value, 3) for item, value in self._cost_breakdown.items()}

    @property
    def electrode_assembly_mass_breakdown(self) -> dict:
        if not hasattr(self, "_electrode_assembly_mass_breakdown"):
            raise AttributeError("Stacks cost breakdown has not been calculated yet")
        return {item.replace("_", " ").title(): round(value * KG_TO_G, 3) for item, value in self._electrode_assembly_mass_breakdown.items()}

    @property
    def electrode_assembly_cost_breakdown(self) -> dict:
        if not hasattr(self, "_electrode_assembly_cost_breakdown"):
            raise AttributeError("Stacks cost breakdown has not been calculated yet")
        return {item.replace("_", " ").title(): round(value, 3) for item, value in self._electrode_assembly_cost_breakdown.items()}

    @property
    def anode_cost_breakdown(self) -> dict:
        if not hasattr(self, "_anode_cost_breakdown"):
            raise AttributeError("Anode cost breakdown has not been calculated yet")

        cost_breakdown = {key.replace("_", " ").title(): {obj: round(value, 3) for obj, value in inner.items()} for key, inner in self._anode_cost_breakdown.items()}

        return cost_breakdown

    @property
    def cathode_cost_breakdown(self) -> dict:
        if not hasattr(self, "_cathode_cost_breakdown"):
            raise AttributeError("Cathode cost breakdown has not been calculated yet")

        cost_breakdown = {key.replace("_", " ").title(): {obj: round(value, 3) for obj, value in inner.items()} for key, inner in self._cathode_cost_breakdown.items()}

        return cost_breakdown

    @property
    def cost(self) -> float:
        if not hasattr(self, "_cost"):
            raise AttributeError("Cost has not been calculated yet")
        return round(self._cost, 2)

    @property
    def mass(self) -> float:
        if not hasattr(self, "_mass"):
            raise AttributeError("Mass has not been calculated yet")
        return round(self._mass * KG_TO_G, 2)

    @property
    def mass_breakdown(self) -> dict:
        if not hasattr(self, "_mass_breakdown"):
            raise AttributeError("Mass breakdown has not been calculated yet")
        return {item.replace("_", " ").title(): round(value * KG_TO_G, 3) for item, value in self._mass_breakdown.items()}

    @property
    def stacks_mass_breakdown(self) -> dict:
        if not hasattr(self, "_stacks_mass_breakdown"):
            raise AttributeError("Stacks mass breakdown has not been calculated yet")
        return {item.replace("_", " ").title(): round(value * KG_TO_G, 3) for item, value in self._stacks_mass_breakdown.items()}

    @property
    def anode_mass_breakdown(self) -> dict:
        if not hasattr(self, "_anode_mass_breakdown"):
            raise AttributeError("Anode mass breakdown has not been calculated yet")

        mass_breakdown = {key.replace("_", " ").title(): {obj: round(value * KG_TO_G, 3) for obj, value in inner.items()} for key, inner in self._anode_mass_breakdown.items()}

        return mass_breakdown

    @property
    def cathode_mass_breakdown(self) -> dict:
        if not hasattr(self, "_cathode_mass_breakdown"):
            raise AttributeError("Cathode mass breakdown has not been calculated yet")

        mass_breakdown = {key.replace("_", " ").title(): {obj: round(value * KG_TO_G, 3) for obj, value in inner.items()} for key, inner in self._cathode_mass_breakdown.items()}

        return mass_breakdown

    @property
    def volume(self) -> float:
        if not hasattr(self, "_volume"):
            raise AttributeError("Volume has not been calculated yet")
        return round(self._volume * M_TO_CM**3, 2)

    @property
    def height(self) -> float:
        if not hasattr(self, "_height"):
            raise AttributeError("Height has not been calculated yet")
        return round(self._height * M_TO_MM, 2)

    @property
    def width(self) -> float:
        if not hasattr(self, "_width"):
            raise AttributeError("Width has not been calculated yet")
        return round(self._width * M_TO_MM, 2)

    @property
    def length(self) -> float:
        if not hasattr(self, "_length"):
            raise AttributeError("Length has not been calculated yet")
        return round(self._length * M_TO_MM, 2)

    @property
    def energy(self) -> float:
        if not hasattr(self, "_energy"):
            raise AttributeError("Energy has not been calculated yet")
        return round(self._energy * S_TO_H, 2)

    @property
    def specific_energy(self) -> float:
        if not hasattr(self, "_specific_energy"):
            raise AttributeError("Specific energy has not been calculated yet")
        return round(self._specific_energy * S_TO_H, 2)

    @property
    def energy_density(self) -> float:
        if not hasattr(self, "_energy_density"):
            raise AttributeError("Energy density has not been calculated yet")
        return round(self._energy_density * S_TO_H / M_TO_DM**3, 2)

    @property
    def normalized_cost(self) -> float:
        if not hasattr(self, "_normalized_cost"):
            raise AttributeError("Normalized cost has not been calculated yet")
        return round(self._normalized_cost / (S_TO_H * W_TO_KW), 2)

    @property
    def cathode_half_cell_curve(self) -> pd.DataFrame:
        """
        Get the half cell curve of the electrode.

        :return: DataFrame containing the half cell curve.
        """
        if not hasattr(self, "_cathode_half_cell_curve"):
            raise AttributeError("Half cell curves have not been calculated yet")

        return self._cathode_half_cell_curve.assign(capacity=lambda x: x["capacity"] * S_TO_H).rename(
            columns={
                "capacity": "Capacity (Ah)",
                "voltage": "Voltage (V)",
                "direction": "Direction",
            }
        )

    @property
    def anode_half_cell_curve(self) -> pd.DataFrame:
        """
        Get the half cell curve of the electrode.

        :return: DataFrame containing the half cell curve.
        """
        if not hasattr(self, "_anode_half_cell_curve"):
            raise AttributeError("Half cell curves have not been calculated yet")

        return self._anode_half_cell_curve.assign(capacity=lambda x: x["capacity"] * S_TO_H).rename(
            columns={
                "capacity": "Capacity (Ah)",
                "voltage": "Voltage (V)",
                "direction": "Direction",
            }
        )

    @property
    def effective_areal_capacity(self) -> float:
        return round(self._effective_areal_capacity * (S_TO_H * A_TO_mA / M_TO_CM**2), 6)

    def __str__(self) -> str:
        return self._name

    def __repr__(self) -> str:
        return self.__str__()


class _PouchCell(_Cell):
    def __init__(
        self,
        electrode_assembly: Stack | CylindricalJellyRoll | FlatJellyRoll,
        n_electrode_assembly: int,
        electrolyte: Electrolyte,
        electrolyte_overfill: float,
        encapsulation: Pouch,
        reversible_capacity: float,
        irreversible_capacity: float,
        grid_n: int = 100,
        name: str = "pouch_cell",
    ):
        """
        Class to represent a pouch cell.

        :param electrode_assembly: Electrode assembly used in the cell
        :param electrolyte: Electrolyte used in the cell
        :param electrolyte_overfill: Overfill of the electrolyte in the cell (%)
        :param encapsulation: Pouch used in the cell
        :param reversible_capacity: Reversible capacity of the cell in mAh
        :param irreversible_capacity: Irreversible capacity of the cell in mAh
        :param grid_n: Number of points to interpolate the half and full cell curves
        :param name: Name of the cell
        """
        super().__init__(
            electrode_assembly=electrode_assembly,
            n_electrode_assembly=n_electrode_assembly,
            electrolyte=electrolyte,
            electrolyte_overfill=electrolyte_overfill,
            encapsulation=encapsulation,
            reversible_capacity=reversible_capacity,
            irreversible_capacity=irreversible_capacity,
            grid_n=grid_n,
            name=name,
        )

    def _check_and_copy_encapsulation(self, encapsulation: Pouch) -> None:
        """
        Function to validate and copy encapsulation

        :param encapsulation: Encapsulation to validate
        """
        if not isinstance(encapsulation, Pouch):
            raise ValueError("Encapsulation must be an instance of Pouch")

        self._encapsulation = deepcopy(encapsulation)

    @property
    def pouch(self) -> Pouch:
        return self._encapsulation


class _PrismaticCell(_Cell):
    def __init__(
        self,
        electrode_assembly: Stack | CylindricalJellyRoll | FlatJellyRoll,
        n_electrode_assembly: int,
        electrolyte: Electrolyte,
        electrolyte_overfill: float,
        encapsulation: Pouch,
        reversible_capacity: float,
        irreversible_capacity: float,
        grid_n: int = 100,
        name: str = "prismatic_cell",
    ):
        """
        Class to represent a prismatic cell.

        :param electrode_assembly: Electrode assembly used in the cell
        :param electrolyte: Electrolyte used in the cell
        :param electrolyte_overfill: Overfill of the electrolyte in the cell (%)
        :param encapsulation: Pouch used in the cell
        :param reversible_capacity: Reversible capacity of the cell in mAh
        :param irreversible_capacity: Irreversible capacity of the cell in mAh
        :param grid_n: Number of points to interpolate the half and full cell curves
        :param name: Name of the cell
        """
        super().__init__(
            electrode_assembly=electrode_assembly,
            n_electrode_assembly=n_electrode_assembly,
            electrolyte=electrolyte,
            electrolyte_overfill=electrolyte_overfill,
            encapsulation=encapsulation,
            reversible_capacity=reversible_capacity,
            irreversible_capacity=irreversible_capacity,
            grid_n=grid_n,
            name=name,
        )

    def _check_and_copy_encapsulation(self, encapsulation: Pouch) -> None:
        """
        Function to validate and copy encapsulation

        :param encapsulation: Encapsulation to validate
        """
        if not isinstance(encapsulation, PrismaticCase):
            raise ValueError("Encapsulation must be an instance of PrismaticCase")

        self._encapsulation = deepcopy(encapsulation)

    def _calculate_geometry_properties(self):
        self._height = self._encapsulation._external_height
        self._width = self._encapsulation._external_width
        self._length = self._encapsulation._external_length
        self._volume = self._encapsulation._external_volume

    @property
    def prismatic_case(self) -> PrismaticCase:
        return self._encapsulation


class _StackedCell(_Cell):
    def __init__(
        self,
        electrode_assembly: Stack,
        electrolyte: Electrolyte,
        electrolyte_overfill: float,
        encapsulation: Pouch | PrismaticCase | CylindricalCase,
        reversible_capacity: float,
        irreversible_capacity: float,
        n_electrode_assembly: int = 1,
        grid_n: int = 100,
        name: str = "stacked_cell",
    ):
        """
        A class that represents a stacked cell.

        :param electrode_assembly: Stack within the cell
        :param electrolyte: Electrolyte used in the cell
        :param electrolyte_overfill: Overfill of the electrolyte in the cell (%)
        :param encapsulation: Encapsulation of the cell
        :param positive_terminal: Positive terminal of the cell
        :param negative_terminal: Negative terminal of the cell
        :param reversible_capacity: Reversible capacity of the cell in mAh
        :param irreversible_capacity: Irreversible capacity of the cell in mAh
        :param n_electrode_assembly: Number of stacks in the cell
        :param grid_n: Number of points to interpolate the half cell curves
        :param name: Name of the cell
        """
        super().__init__(
            electrode_assembly=electrode_assembly,
            n_electrode_assembly=n_electrode_assembly,
            electrolyte=electrolyte,
            electrolyte_overfill=electrolyte_overfill,
            encapsulation=encapsulation,
            reversible_capacity=reversible_capacity,
            irreversible_capacity=irreversible_capacity,
            grid_n=grid_n,
            name=name,
        )

    def _check_and_copy_electrode_assembly(self, electrode_assembly: Stack, n_electrode_assembly: int) -> None:
        """
        Function to validate the electrode assembly and copy it n times

        :param electrode_assembly: Electrode assembly to validate
        :param n_electrode_assembly: Number of times to copy the electrode assembly
        """
        if not isinstance(electrode_assembly, Stack):
            raise ValueError("Electrode assembly must be an instance of Stack")

        if not isinstance(n_electrode_assembly, int):
            raise ValueError("Number of electrode assembly must be an integer")

        if n_electrode_assembly <= 0:
            raise ValueError("Number of electrode assembly must be greater than 0")

        self._electrode_assemblies = [deepcopy(electrode_assembly) for _ in range(n_electrode_assembly)]

    @property
    def stacks(self) -> Stack:
        return self._electrode_assemblies


class _JellyRollCell(_Cell):
    def __init__(
        self,
        electrode_assembly: _JellyRoll,
        electrolyte: Electrolyte,
        electrolyte_overfill: float,
        encapsulation: Pouch | PrismaticCase | CylindricalCase,
        reversible_capacity: float,
        irreversible_capacity: float,
        n_electrode_assembly: int = 1,
        grid_n: int = 100,
        name: str = "stacked_cell",
    ):
        """
        A class that represents a jelly roll cell.

        :param electrode_assembly: Stack within the cell
        :param electrolyte: Electrolyte used in the cell
        :param electrolyte_overfill: Overfill of the electrolyte in the cell (%)
        :param encapsulation: Encapsulation of the cell
        :param reversible_capacity: Reversible capacity of the cell in mAh
        :param irreversible_capacity: Irreversible capacity of the cell in mAh
        :param n_electrode_assembly: Number of stacks in the cell
        :param grid_n: Number of points to interpolate the half cell curves
        :param name: Name of the cell
        """

        super().__init__(
            electrode_assembly=electrode_assembly,
            n_electrode_assembly=n_electrode_assembly,
            electrolyte=electrolyte,
            electrolyte_overfill=electrolyte_overfill,
            encapsulation=encapsulation,
            reversible_capacity=reversible_capacity,
            irreversible_capacity=irreversible_capacity,
            grid_n=grid_n,
            name=name,
        )

    def _check_and_copy_electrode_assembly(self, electrode_assembly: _JellyRoll, n_electrode_assembly: int) -> None:
        """
        Function to validate the electrode assembly and copy it n times

        :param electrode_assembly: Electrode assembly to validate
        :param n_electrode_assembly: Number of times to copy the electrode assembly
        """
        if not isinstance(electrode_assembly, _JellyRoll):
            raise ValueError("Electrode assembly must be an instance of a Jelly Roll")

        if not isinstance(n_electrode_assembly, int):
            raise ValueError("Number of electrode assembly must be an integer")

        if n_electrode_assembly <= 0:
            raise ValueError("Number of electrode assembly must be greater than 0")

        self._electrode_assemblies = [deepcopy(electrode_assembly) for _ in range(n_electrode_assembly)]

    @property
    def jelly_roll(self) -> _JellyRoll:
        return self._electrode_assemblies[0]


class StackedPouchCell(_PouchCell, _StackedCell):
    def __init__(
        self,
        stack: Stack,
        pouch: Pouch,
        electrolyte: Electrolyte,
        electrolyte_overfill: float,
        reversible_capacity: float,
        irreversible_capacity: float,
        n_stacks: int = 1,
        grid_n: int = 100,
        name: str = "stacked_pouch_cell",
    ):
        """
        A class that represents a stacked pouch cell.

        :param stack: Stack within the cell
        :param pouch: Pouch used in the cell
        :param electrolyte: Electrolyte used in the cell
        :param electrolyte_overfill: Overfill of the electrolyte in the cell (%)
        :param positive_terminal: Positive terminal of the cell
        :param negative_terminal: Negative terminal of the cell
        :param reversible_capacity: Reversible capacity of the cell in mAh
        :param irreversible_capacity: Irreversible capacity of the cell in mAh
        :param grid_n: Number of points to interpolate the half cell curves
        :param name: Name of the cell
        """
        pouch._calculate_properties(stack)

        super().__init__(
            electrode_assembly=stack,
            n_electrode_assembly=n_stacks,
            electrolyte=electrolyte,
            electrolyte_overfill=electrolyte_overfill,
            encapsulation=pouch,
            reversible_capacity=reversible_capacity,
            irreversible_capacity=irreversible_capacity,
            grid_n=grid_n,
            name=name,
        )

    def _calculate_geometry_properties(self):
        self._width = self._encapsulation._width
        self._length = self._encapsulation._length
        self._height = sum([s._thickness for s in self._electrode_assemblies]) + self._encapsulation._laminate._thickness * 2
        self._volume = self._encapsulation._length * self._encapsulation._width * self._height


class StackedPrismaticCell(_PrismaticCell, _StackedCell):
    def __init__(
        self,
        stack: Stack,
        prismatic_case: PrismaticCase,
        electrolyte: Electrolyte,
        electrolyte_overfill: float,
        reversible_capacity: float,
        irreversible_capacity: float,
        n_stacks: int = 1,
        grid_n: int = 100,
        name: str = "stacked_prismatic_cell",
    ):
        """
        A class that represents a stacked prismatic cell.

        :param stack: Stack within the cell
        :param prismatic_case: Prismatic case used in the cell
        :param electrolyte: Electrolyte used in the cell
        :param electrolyte_overfill: Overfill of the electrolyte in the cell (%)
        :param reversible_capacity: Reversible capacity of the cell in mAh
        :param irreversible_capacity: Irreversible capacity of the cell in mAh
        :param n_stacks: Number of stacks in the cell
        :param grid_n: Number of points to interpolate the half cell curves
        :param name: Name of the cell
        """

        self._check_encapsulation(stack, prismatic_case, n_stacks)

        super().__init__(
            electrode_assembly=stack,
            n_electrode_assembly=n_stacks,
            electrolyte=electrolyte,
            electrolyte_overfill=electrolyte_overfill,
            encapsulation=prismatic_case,
            reversible_capacity=reversible_capacity,
            irreversible_capacity=irreversible_capacity,
            grid_n=grid_n,
            name=name,
        )

    def _check_encapsulation(self, stack: Stack, prismatic_case: PrismaticCase, n_stacks: int) -> None:
        # Check stack is small enough to fit in the prismatic case
        if stack._thickness * n_stacks > prismatic_case._internal_height:
            raise ValueError("Stack thickness cannot be greater than the internal height of the prismatic case")
        if stack._width > prismatic_case._internal_width:
            raise ValueError("Stack width cannot be greater than the internal width of the prismatic case")
        if stack._length > prismatic_case._internal_length:
            raise ValueError("Stack length cannot be greater than the internal length of the prismatic case")


class CylindricalCell(_JellyRollCell):
    def __init__(
        self,
        electrode_assembly: CylindricalJellyRoll,
        electrolyte: Electrolyte,
        electrolyte_overfill: float,
        encapsulation: CylindricalCase,
        reversible_capacity: float,
        irreversible_capacity: float,
        grid_n: int = 100,
        name: str = "stacked_cell",
    ):
        """ "
        A class that represents a cylindrical cell.

        :param electrode_assembly: Electrode assembly used in the cell
        :param electrolyte: Electrolyte used in the cell
        :param electrolyte_overfill: Overfill of the electrolyte in the cell (%)
        :param encapsulation: Encapsulation of the cell
        :param positive_terminal: Positive terminal of the cell
        :param negative_terminal: Negative terminal of the cell
        :param reversible_capacity: Reversible capacity of the cell in mAh
        :param irreversible_capacity: Irreversible capacity of the cell in mAh
        :param grid_n: Number of points to interpolate the half cell curves
        :param name: Name of the cell
        """
        super().__init__(
            electrode_assembly=electrode_assembly,
            n_electrode_assembly=1,
            electrolyte=electrolyte,
            electrolyte_overfill=electrolyte_overfill,
            encapsulation=encapsulation,
            reversible_capacity=reversible_capacity,
            irreversible_capacity=irreversible_capacity,
            grid_n=grid_n,
            name=name,
        )

    def _check_and_copy_electrode_assembly(self, electrode_assembly: CylindricalJellyRoll, n_electrode_assembly: int) -> None:
        """
        Function to validate the electrode assembly and copy it n times

        :param electrode_assembly: Electrode assembly to validate
        :param n_electrode_assembly: Number of times to copy the electrode assembly
        """
        if not isinstance(electrode_assembly, CylindricalJellyRoll):
            raise ValueError("Electrode assembly must be an instance of a Jelly Roll")

        if not isinstance(n_electrode_assembly, int):
            raise ValueError("Number of electrode assembly must be an integer")

        if n_electrode_assembly <= 0:
            raise ValueError("Number of electrode assembly must be greater than 0")

        if electrode_assembly._radius > self._encapsulation._inner_radius:
            raise ValueError(f"Electrode assembly, {electrode_assembly.radius} mm,  cannot be greater than the internal radius of the cylindrical case, {self._encapsulation.inner_radius} mm")

        if electrode_assembly._width > self._encapsulation._inner_height:
            raise ValueError(f"Electrode assembly, {electrode_assembly.width} mm, cannot be greater than the internal height of the cylindrical case, {self._encapsulation.inner_height} mm")

        self._electrode_assemblies = [deepcopy(electrode_assembly) for _ in range(n_electrode_assembly)]

    def _check_and_copy_encapsulation(self, encapsulation: CylindricalCase) -> None:
        """
        Function to validate and copy encapsulation

        :param encapsulation: Encapsulation to validate
        """
        if not isinstance(encapsulation, CylindricalCase):
            raise ValueError("Encapsulation must be an instance of CylindricalCase")

        self._encapsulation = deepcopy(encapsulation)

    def _calculate_geometry_properties(self):
        self._radius = self._encapsulation._outer_radius
        self._diameter = self._radius * 2
        self._length = self._encapsulation._length
        self._volume = np.pi * self._radius**2 * self._length

    def get_top_down_view(self, background_color="white", **kwargs) -> go.Figure:
        """
        Function to get a top down view of the cylindrical cell with the jelly roll and the casing

        :param show: Whether to show the plot or not
        """
        fig = go.Figure()

        for trace in self._encapsulation.get_top_down_view().data:
            if trace.name == "Canister Wall":
                fig.add_trace(trace)

        for trace in self._electrode_assemblies[0].get_top_down_view().data:
            fig.add_trace(trace)

        fig.update_layout(
            xaxis=dict(
                showgrid=False,
                zeroline=False,
                showticklabels=False,
                scaleanchor="y",
                title="X (cm)",
            ),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, title="Y (cm)"),
            paper_bgcolor=background_color,
            plot_bgcolor=background_color,
            title=f"Top down view of cylindrical cell",
            **kwargs,
        )

        return fig

    @property
    def cylindrical_case(self) -> CylindricalCase:
        return self._encapsulation

    @property
    def radius(self) -> float:
        if not hasattr(self, "_radius"):
            raise AttributeError("Radius has not been calculated yet")
        return round(self._radius * M_TO_MM, 2)

    @property
    def diameter(self) -> float:
        if not hasattr(self, "_diameter"):
            raise AttributeError("Diameter has not been calculated yet")
        return round(self._diameter * M_TO_CM, 2)
