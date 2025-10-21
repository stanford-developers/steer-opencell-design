from steer_opencell_design.Components.other import Laminate, Tape, Terminal
from steer_opencell_design.Components.Electrodes import Cathode, Anode
from steer_opencell_design.Components.Separators import Separator
from steer_opencell_design.Constructions.ElectrodeAssemblies import Stack

from steer_opencell_design.DataManager import DataManager
from steer_opencell_design.Constants import *

from pathlib import Path
from copy import deepcopy
import numpy as np
import plotly.graph_objects as go
import pandas as pd


class Pouch:
    def __init__(
        self,
        positive_terminal: Terminal,
        negative_terminal: Terminal,
        heat_seal_size_sides: float,
        heat_seal_size_top: float,
        laminate: Laminate,
        tape: Tape,
        name: str = "Pouch",
    ):
        """
        Class representing a pouch used for a pouch cell.

        :param positive_terminal: Terminal: positive terminal of the pouch
        :param negative_terminal: Terminal: negative terminal of the pouch
        :param heat_seal_size_sides: float: size of the heat seal on the sides of the pouch in mm
        :param heat_seal_size_top: float: size of the heat seal on the top of the pouch in mm
        :param laminate: Laminate: laminate used in the pouch
        :param tape: Tape: tape used in the pouch
        :param name: str: name of the pouch
        """
        self._check_positive_terminal(positive_terminal)
        self._check_negative_terminal(negative_terminal)
        self._check_heat_seal_size_sides(heat_seal_size_sides)
        self._check_heat_seal_size_top(heat_seal_size_top)
        self._check_laminate(laminate)
        self._check_tape(tape)
        self._check_name(name)

    def _check_positive_terminal(self, positive_terminal: Terminal):
        if not isinstance(positive_terminal, Terminal):
            raise TypeError("Positive terminal must be a Terminal")

        self._positive_terminal = deepcopy(positive_terminal)

    def _check_negative_terminal(self, negative_terminal: Terminal):
        if not isinstance(negative_terminal, Terminal):
            raise TypeError("Negative terminal must be a Terminal")

        self._negative_terminal = deepcopy(negative_terminal)

    def _check_heat_seal_size_sides(self, heat_seal_size_sides: float):
        if not isinstance(heat_seal_size_sides, (int, float)):
            raise TypeError("Heat seal size sides must be a number")

        if heat_seal_size_sides <= 0:
            raise ValueError("Heat seal size sides must be positive")

        self._heat_seal_size_sides = heat_seal_size_sides * MM_TO_M

    def _check_heat_seal_size_top(self, heat_seal_size_top: float):
        if not isinstance(heat_seal_size_top, (int, float)):
            raise TypeError("Heat seal size top must be a number")

        if heat_seal_size_top <= 0:
            raise ValueError("Heat seal size top must be positive")

        self._heat_seal_size_top = heat_seal_size_top * MM_TO_M

    def _check_laminate(self, laminate: Laminate):
        if not isinstance(laminate, Laminate):
            raise TypeError("Laminate must be a Laminate")

        self._laminate = laminate

    def _check_tape(self, tape: Tape):
        if not isinstance(tape, Tape):
            raise TypeError("Tape must be a Tape")

        self._tape = tape

    def _check_name(self, name: str):
        if not isinstance(name, str):
            raise TypeError("Name must be a string")

        if len(name) == 0:
            raise ValueError("Name cannot be empty")

        self._name = name

    def _calculate_properties(self, stack: Stack):
        self._width = stack._width + 2 * self._heat_seal_size_sides
        self._length = stack._length + self._heat_seal_size_top
        self._area = self._width * self._length
        self._mass = self._area * self._laminate._areal_mass * 2 + self._positive_terminal._mass + self._negative_terminal._mass
        self._cost = self._area * self._laminate._areal_cost * 2 + self._positive_terminal._cost + self._negative_terminal._cost

    @property
    def name(self) -> str:
        return self._name

    @property
    def area(self) -> float:
        if hasattr(self, "_area"):
            return round(self._area * M_TO_CM**2, 2)
        else:
            raise AttributeError("The pouch needs to be used in a pouch cell to calculate its dimensions")

    @property
    def mass(self) -> float:
        if hasattr(self, "_mass"):
            return round(self._mass * KG_TO_G, 2)
        else:
            raise AttributeError("The pouch needs to be used in a pouch cell to calculate its mass")

    @property
    def cost(self) -> float:
        if hasattr(self, "_cost"):
            return round(self._cost, 2)
        else:
            raise AttributeError("The pouch needs to be used in a pouch cell to calculate its cost")

    @property
    def length(self) -> float:
        if hasattr(self, "_length"):
            return round(self._length * M_TO_MM, 2)
        else:
            raise AttributeError("The pouch needs to be used in a pouch cell to calculate its dimensions")

    @property
    def width(self) -> float:
        if hasattr(self, "_width"):
            return round(self._width * M_TO_MM, 2)
        else:
            raise AttributeError("The pouch needs to be used in a pouch cell to calculate its dimensions")

    @property
    def tape(self) -> Tape:
        return self._tape

    @property
    def laminate(self) -> Laminate:
        return self._laminate

    @property
    def heat_seal_size_sides(self) -> float:
        return round(self._heat_seal_size_sides * M_TO_MM, 2)

    @property
    def heat_seal_size_top(self) -> float:
        return round(self._heat_seal_size_top * M_TO_MM, 2)

    @property
    def positive_terminal(self) -> Terminal:
        return self._positive_terminal

    @property
    def negative_terminal(self) -> Terminal:
        return self._negative_terminal

    def __str__(self) -> str:
        return self.name

    def __repr__(self):
        return self.__str__()


class CylindricalLidAssembly:
    def __init__(self, cost: float, mass: float, thickness: float):
        """
        Class representing a lid assembly used for a cylindrical cell.

        :param cost: float: cost of the lid assembly in $
        :param mass: float: mass of the lid assembly in g
        :param thickness: float: thickness of the lid assembly in mm
        """
        self._check_cost(cost)
        self._check_mass(mass)
        self._check_thickness(thickness)

    def _check_cost(self, cost: float):
        if not isinstance(cost, (int, float)):
            raise TypeError("Cost must be a number")

        if cost < 0:
            raise ValueError("Cost cannot be negative")

        self._cost = cost

    def _check_mass(self, mass: float):
        if not isinstance(mass, (int, float)):
            raise TypeError("Mass must be a number")

        if mass < 0:
            raise ValueError("Mass cannot be negative")

        self._mass = mass * G_TO_KG

    def _check_thickness(self, thickness: float):
        if not isinstance(thickness, (int, float)):
            raise TypeError("Thickness must be a number")

        if thickness <= 0:
            raise ValueError("Thickness must be positive")

        self._thickness = thickness * MM_TO_M

    @property
    def cost(self) -> float:
        return round(self._cost, 2)

    @property
    def mass(self) -> float:
        return round(self._mass * KG_TO_G, 2)

    @property
    def thickness(self) -> float:
        return round(self._thickness * M_TO_MM, 2)

    def __str__(self) -> str:
        return "Cylindrical Lid Assembly"

    def __repr__(self):
        return self.__str__()


class CylindricalTerminalConnector:
    def __init__(
        self,
        formula: str,
        diameter: float,
        thickness: float,
        fill_factor: float = 1,
        specific_cost: float = None,
        density: float = None,
    ):
        """
        Class representing a cylindrical terminal connector used for a cylindrical cell.

        :param formula: str: formula of the terminal connector
        :param radius: float: radius of the terminal connector in mm
        :param thickness: float: thickness of the terminal connector in mm
        :param fill_factor: float: fill factor of the terminal connector
        :param specific_cost: float: specific cost of the terminal connector in $/kg
        :param density: float: density of the terminal connector in g/cm^3
        """
        self._check_formula(formula)
        self._check_diameter(diameter)
        self._check_thickness(thickness)
        self._check_fill_factor(fill_factor)
        self._set_properties_from_database()
        self._check_specific_cost(specific_cost)
        self._check_density(density)
        self._calculate_properties()
        self._calculate_footprint()

    def _check_formula(self, formula: str):
        if not isinstance(formula, str):
            raise TypeError("Formula must be a string")

        if len(formula) == 0:
            raise ValueError("Formula cannot be empty")

        self._formula = formula

    def _check_fill_factor(self, fill_factor: float):
        if not isinstance(fill_factor, (int, float)):
            raise TypeError("Fill factor must be a number")

        if fill_factor <= 0 or fill_factor > 1:
            raise ValueError("Fill factor must be between 0 and 1")

        self._fill_factor = fill_factor

    def _check_diameter(self, diameter: float):
        if not isinstance(diameter, (int, float)):
            raise TypeError("Diameter must be a number")

        if diameter <= 0:
            raise ValueError("Diameter must be positive")

        self._diameter = diameter * MM_TO_M

    def _check_thickness(self, thickness: float):
        if not isinstance(thickness, (int, float)):
            raise TypeError("Thickness must be a number")

        if thickness <= 0:
            raise ValueError("Thickness must be positive")

        self._thickness = thickness * MM_TO_M

    def _set_properties_from_database(self):
        """
        Retrieve the properties of the tab material.
        """
        data_path = (Path(__file__).parent / "../../Data/materials_properties.db").resolve()
        materials_database = DataManager(data_path)
        available_materials = materials_database.get_unique_values("current_collectors", "formula")

        if self._formula not in available_materials:
            raise ValueError(f"{self._formula} is not available in the materials database. Allowed values are: {available_materials}")

        data = materials_database.get_data(
            "current_collectors",
            condition=f"formula='{self._formula}'",
            latest_column="date",
        )

        self._name = data["name"].values[0]
        self._specific_cost = float(data["specific_cost"].values[0])
        self._density = float(data["density"].values[0])

    def _check_specific_cost(self, specific_cost: float):
        if specific_cost is not None:
            if not isinstance(specific_cost, (int, float)):
                raise TypeError("Specific cost must be a number.")

            if specific_cost < 0:
                raise ValueError("Specific cost cannot be negative.")

            self._specific_cost = float(specific_cost)

    def _check_density(self, density: float):
        if density is not None:
            if not isinstance(density, (int, float)):
                raise TypeError("Density must be a number.")

            if density <= 0:
                raise ValueError("Density must be positive.")

            self._density = float(density) * G_TO_KG / CM_TO_M**3

    def _calculate_properties(self):
        """
        Calculate the properties of the terminal connector.
        """
        self._radius = self._diameter / 2
        self._mass = np.pi * (self._radius**2) * self._thickness * self._density * self._fill_factor
        self._cost = self._mass * self._specific_cost

    def _calculate_footprint(self):
        self._circle = pd.DataFrame({"theta": np.linspace(0, 2 * np.pi, 30), "radius": self._radius}).assign(x=lambda x: x["radius"] * np.cos(x["theta"])).assign(y=lambda x: x["radius"] * np.sin(x["theta"])).sort_values(by="theta", ascending=True).drop(columns=["theta", "radius"])

    @property
    def circle(self) -> pd.DataFrame:
        return self._circle.assign(x=lambda x: x["x"] * M_TO_MM).assign(y=lambda x: x["y"] * M_TO_MM).rename(columns={"x": "X [mm]", "y": "Y [mm]"})

    @property
    def mass(self) -> float:
        return round(self._mass * KG_TO_G, 2)

    @property
    def cost(self) -> float:
        return round(self._cost, 2)

    @property
    def name(self) -> str:
        return self._name

    @property
    def formula(self) -> str:
        return self._formula

    @property
    def radius(self) -> float:
        return round(self._radius * M_TO_MM, 2)

    @property
    def thickness(self) -> float:
        return round(self._thickness * M_TO_MM, 2)

    @property
    def fill_factor(self) -> float:
        return round(self._fill_factor, 2)

    @property
    def specific_cost(self) -> float:
        return self._specific_cost

    @property
    def density(self) -> float:
        return self._density * KG_TO_G / M_TO_CM**3

    def __str__(self) -> str:
        return f"{self.name} ({self.formula})"

    def __repr__(self):
        return self.__str__()


class CylindricalCanister:
    def __init__(
        self,
        formula: str,
        outer_diameter: float,
        wall_thickness: float,
        length: float,
        specific_cost: float = None,
        density: float = None,
    ):
        """
        Class representing a canister used for a cylindrical cell.

        :param formula: str: formula of the canister
        :param outer_diameter: float: outer diameter of the canister in mm
        :param wall_thickness: float: thickness of the canister wall in mm
        :param length: float: length of the canister in mm
        """
        self._check_formula(formula)
        self._check_outer_diameter(outer_diameter)
        self._check_wall_thickness(wall_thickness)
        self._check_length(length)
        self._set_properties_from_database()
        self._check_specific_cost(specific_cost)
        self._check_density(density)
        self._calculate_properties()

    def _check_formula(self, formula: str):
        if not isinstance(formula, str):
            raise TypeError("Formula must be a string")

        if len(formula) == 0:
            raise ValueError("Formula cannot be empty")

        self._formula = formula

    def _check_outer_diameter(self, outer_diameter: float):
        if not isinstance(outer_diameter, (int, float)):
            raise TypeError("Outer diameter must be a number")

        if outer_diameter <= 0:
            raise ValueError("Outer diameter must be positive")

        self._outer_diameter = outer_diameter * MM_TO_M

    def _check_wall_thickness(self, wall_thickness: float):
        if not isinstance(wall_thickness, (int, float)):
            raise TypeError("Wall thickness must be a number")

        if wall_thickness <= 0:
            raise ValueError("Wall thickness must be positive")

        self._wall_thickness = wall_thickness * MM_TO_M

    def _check_length(self, length: float):
        if not isinstance(length, (int, float)):
            raise TypeError("Length must be a number")

        if length <= 0:
            raise ValueError("Length must be positive")

        self._length = length * MM_TO_M

    def _set_properties_from_database(self):
        """
        Retrieve the properties of the tab material.
        """
        data_path = (Path(__file__).parent / "../../Data/materials_properties.db").resolve()
        materials_database = DataManager(data_path)
        available_materials = materials_database.get_unique_values("current_collectors", "formula")

        if self._formula not in available_materials:
            raise ValueError(f"{self._formula} is not available in the materials database. Allowed values are: {available_materials}")

        data = materials_database.get_data(
            "current_collectors",
            condition=f"formula='{self._formula}'",
            latest_column="date",
        )

        self._name = data["name"].values[0]
        self._specific_cost = float(data["specific_cost"].values[0])
        self._density = float(data["density"].values[0])

    def _check_specific_cost(self, specific_cost: float):
        if specific_cost is not None:
            if not isinstance(specific_cost, (int, float)):
                raise TypeError("Specific cost must be a number.")

            if specific_cost < 0:
                raise ValueError("Specific cost cannot be negative.")

            self._specific_cost = float(specific_cost)

    def _check_density(self, density: float):
        if density is not None:
            if not isinstance(density, (int, float)):
                raise TypeError("Density must be a number.")

            if density <= 0:
                raise ValueError("Density must be positive.")

            self._density = float(density) * G_TO_KG / CM_TO_M**3

    def _calculate_properties(self):
        """
        Calculate the properties of the canister.
        """
        self._inner_radius = self._outer_diameter / 2 - self._wall_thickness
        self._inner_diameter = self._outer_diameter - 2 * self._wall_thickness
        self._outer_radius = self._outer_diameter / 2

        base_plate_volume = np.pi * self._outer_diameter**2 * self._wall_thickness
        sides_volume = np.pi * (self._outer_radius**2 - self._inner_radius**2) * (self._length - self._wall_thickness)

        self._volume = base_plate_volume + sides_volume
        self._mass = self._volume * self._density
        self._cost = self._mass * self._specific_cost

    @property
    def inner_radius(self) -> float:
        return round(self._inner_radius * M_TO_MM, 2)

    @property
    def inner_diameter(self) -> float:
        return round(self._inner_diameter * M_TO_MM, 2)

    @property
    def outer_radius(self) -> float:
        return round(self._outer_radius * M_TO_MM, 2)

    @property
    def outer_diameter(self) -> float:
        return round(self._outer_diameter * M_TO_MM, 2)

    @property
    def wall_thickness(self) -> float:
        return round(self._wall_thickness * M_TO_MM, 2)


class CylindricalCase:
    def __init__(
        self,
        canister: CylindricalCanister,
        lid_assembly: CylindricalLidAssembly,
        cathode_terminal_connector: CylindricalTerminalConnector,
        anode_terminal_connector: CylindricalTerminalConnector,
        name: str = "cylindrical_case",
    ):
        """
        Class representing a casing used for a cylindrical cell.

        :param shell: CylindricalShell: shell of the case
        :param positive_terminal: Terminal: positive terminal of the case
        :param negative_terminal: Terminal: negative terminal of the case
        :param name: str: name of the case
        """
        self._check_canister(canister)
        self._check_lid_assembly(lid_assembly)
        self._check_cathode_terminal_connector(cathode_terminal_connector)
        self._check_anode_terminal_connector(anode_terminal_connector)

        self._check_name(name)
        self._calculate_properties()
        self._calculate_footprint()

    def _check_canister(self, canister: CylindricalCanister):
        if not isinstance(canister, CylindricalCanister):
            raise TypeError("Canister must be a CylindricalCanister")

        self._canister = deepcopy(canister)

    def _check_lid_assembly(self, lid_assembly: CylindricalLidAssembly):
        if not isinstance(lid_assembly, CylindricalLidAssembly):
            raise TypeError("Lid assembly must be a CylindricalLidAssembly")

        self._lid_assembly = deepcopy(lid_assembly)

    def _check_cathode_terminal_connector(self, cathode_terminal_connector: CylindricalTerminalConnector):
        if not isinstance(cathode_terminal_connector, CylindricalTerminalConnector):
            raise TypeError("Cathode terminal connector must be a CylindricalTerminalCollector")

        if cathode_terminal_connector._radius > self._canister._inner_radius:
            raise ValueError(f"Cathode terminal connector radius ({cathode_terminal_connector.radius} mm) must be smaller than canister inner radius ({self._canister.inner_radius} mm)")

        self._cathode_terminal_connector = deepcopy(cathode_terminal_connector)

    def _check_anode_terminal_connector(self, anode_terminal_connector: CylindricalTerminalConnector):
        if not isinstance(anode_terminal_connector, CylindricalTerminalConnector):
            raise TypeError("Anode terminal connector must be a CylindricalTerminalCollector")

        if anode_terminal_connector._radius > self._canister._inner_radius:
            raise ValueError(f"Anode terminal connector radius ({anode_terminal_connector.radius} mm) must be smaller than canister inner radius ({self._canister.inner_radius} mm)")

        self._anode_terminal_connector = deepcopy(anode_terminal_connector)

    def _check_name(self, name: str):
        if not isinstance(name, str):
            raise TypeError("Name must be a string")

        if len(name) == 0:
            raise ValueError("Name cannot be empty")

        self._name = name

    def _calculate_properties(self):
        self._cost = self._canister._cost + self._lid_assembly._cost + self._cathode_terminal_connector._cost + self._anode_terminal_connector._cost
        self._mass = self._canister._mass + self._lid_assembly._mass + self._cathode_terminal_connector._mass + self._anode_terminal_connector._mass

        self._length = self._canister._length
        self._outer_radius = self._canister._outer_radius
        self._outer_diameter = self._canister._outer_diameter
        self._closed_volume = self._length * np.pi * (self._outer_radius**2)

        self._inner_radius = self._canister._inner_radius
        self._inner_height = self._length - self._lid_assembly._thickness - self._cathode_terminal_connector._thickness - self._anode_terminal_connector._thickness - self._canister._wall_thickness
        self._inner_volume = np.pi * (self._inner_radius**2) * self._inner_height

    def _calculate_footprint(self):
        self._inner_circle = pd.DataFrame({"theta": np.linspace(0, 2 * np.pi, 30), "radius": self._inner_radius}).assign(x=lambda x: x["radius"] * np.cos(x["theta"])).assign(y=lambda x: x["radius"] * np.sin(x["theta"])).sort_values(by="theta", ascending=True).drop(columns=["theta", "radius"])

        self._outer_circle = pd.DataFrame({"theta": np.linspace(0, 2 * np.pi, 30), "radius": self._outer_radius}).assign(x=lambda x: x["radius"] * np.cos(x["theta"])).assign(y=lambda x: x["radius"] * np.sin(x["theta"])).sort_values(by="theta", ascending=False).drop(columns=["theta", "radius"])

    def get_top_down_view(
        self,
        paper_bgcolor="white",
        plot_bgcolor="white",
        title=None,
        with_base=True,
        **kwargs,
    ):
        """
        Get a top down view of the cylindrical case
        """
        # canister wall
        outer_circle = self.outer_circle.copy()
        inner_circle = self.inner_circle.copy()
        data = pd.concat([outer_circle, inner_circle])
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=data["X [mm]"],
                y=data["Y [mm]"],
                mode="lines",
                name="Canister Wall",
                line=dict(width=0, shape="spline"),
                fillcolor="black",
                fill="toself",
            )
        )

        if with_base:
            fig.add_trace(
                go.Scatter(
                    x=inner_circle["X [mm]"],
                    y=inner_circle["Y [mm]"],
                    mode="lines",
                    name="Canister Base",
                    line=dict(width=0, shape="spline"),
                    fillcolor="grey",
                    fill="toself",
                )
            )
            anode_circle = self._anode_terminal_connector.circle.copy()
            fill_factor = self._anode_terminal_connector.fill_factor
            fig.add_trace(
                go.Scatter(
                    x=anode_circle["X [mm]"],
                    y=anode_circle["Y [mm]"],
                    mode="lines",
                    name="Anode Collector",
                    line=dict(width=0, shape="spline"),
                    fillcolor=ANODE_COLOR,
                    fill="toself",
                    opacity=fill_factor,
                )
            )

        title = title if title is not None else f"{self.name} top down view"

        fig.update_layout(
            title=title,
            xaxis=dict(showgrid=False, zeroline=False, scaleanchor="y", title="X [mm]"),
            yaxis=dict(showgrid=False, zeroline=False, title="Y [mm]"),
            paper_bgcolor=paper_bgcolor,
            plot_bgcolor=plot_bgcolor,
            **kwargs,
        )

        return fig

    def get_bottom_up_view(self, paper_bgcolor="white", plot_bgcolor="white", title=None, **kwargs):
        """
        Get a bottom up view of the cylindrical case
        """
        # canister wall
        outer_circle = self.outer_circle.copy()
        inner_circle = self.inner_circle.copy()
        data = pd.concat([outer_circle, inner_circle])
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=data["X [mm]"],
                y=data["Y [mm]"],
                mode="lines",
                name="Canister Wall",
                line=dict(width=0, shape="spline"),
                fillcolor="black",
                fill="toself",
            )
        )

        # lid assembly
        fig.add_trace(
            go.Scatter(
                x=inner_circle["X [mm]"],
                y=inner_circle["Y [mm]"],
                mode="lines",
                name="Lid assembly",
                line=dict(width=0, shape="spline"),
                fillcolor="#338DFF",
                fill="toself",
            )
        )

        # cathode terminal connector
        cathode_circle = self._cathode_terminal_connector.circle.copy()
        fill_factor = self._cathode_terminal_connector.fill_factor
        fig.add_trace(
            go.Scatter(
                x=cathode_circle["X [mm]"],
                y=cathode_circle["Y [mm]"],
                mode="lines",
                name="Cathode Collector",
                line=dict(width=0, shape="spline"),
                fillcolor=CATHODE_COLOR,
                fill="toself",
                opacity=fill_factor,
            )
        )

        title = title if title is not None else f"{self.name} bottom up view"

        fig.update_layout(
            title=title,
            xaxis=dict(showgrid=False, zeroline=False, scaleanchor="y", title="X [mm]"),
            yaxis=dict(showgrid=False, zeroline=False, title="Y [mm]"),
            paper_bgcolor=paper_bgcolor,
            plot_bgcolor=plot_bgcolor,
            **kwargs,
        )

        return fig

    def get_side_view(self, plot_bgcolor="white", paper_bgcolor="white", **kwargs):
        """
        Get a side view of the cylindrical case
        """
        fig = go.Figure()

        # anode terminal connector
        pos_y = -self.inner_height / 2
        neg_y = -self.inner_height / 2 - self._anode_terminal_connector.thickness
        anode_x = [
            -self._anode_terminal_connector.radius,
            self._anode_terminal_connector.radius,
            self._anode_terminal_connector.radius,
            -self._anode_terminal_connector.radius,
            -self._anode_terminal_connector.radius,
        ]
        anode_y = [neg_y, neg_y, pos_y, pos_y, neg_y]
        fig.add_trace(
            go.Scatter(
                x=anode_x,
                y=anode_y,
                mode="lines",
                name="Anode Terminal Collector",
                line=dict(width=0),
                fillcolor=ANODE_COLOR,
                fill="toself",
            )
        )

        # cathode terminal connector
        pos_y = self.inner_height / 2 + self._cathode_terminal_connector.thickness
        neg_y = self.inner_height / 2
        cathode_x = [
            -self._cathode_terminal_connector.radius,
            self._cathode_terminal_connector.radius,
            self._cathode_terminal_connector.radius,
            -self._cathode_terminal_connector.radius,
            -self._cathode_terminal_connector.radius,
        ]
        cathode_y = [neg_y, neg_y, pos_y, pos_y, pos_y]
        fig.add_trace(
            go.Scatter(
                x=cathode_x,
                y=cathode_y,
                mode="lines",
                name="Cathode Terminal Collector",
                line=dict(width=0),
                fillcolor=CATHODE_COLOR,
                fill="toself",
            )
        )

        # lid assembly
        pos_y = self.inner_height / 2 + self._cathode_terminal_connector.thickness + self._lid_assembly.thickness
        neg_y = self.inner_height / 2 + self._cathode_terminal_connector.thickness
        lid_x = [
            -self.inner_radius,
            self.inner_radius,
            self.inner_radius,
            -self.inner_radius,
            -self.inner_radius,
        ]
        lid_y = [neg_y, neg_y, pos_y, pos_y, neg_y]
        fig.add_trace(
            go.Scatter(
                x=lid_x,
                y=lid_y,
                mode="lines",
                name="Lid Assembly",
                line=dict(width=0),
                fillcolor=LID_COLOR,
                fill="toself",
            )
        )

        # canister
        pos_y = self.inner_height / 2 + self._cathode_terminal_connector.thickness + self._lid_assembly.thickness
        neg_y = -self.inner_height / 2 - self._anode_terminal_connector.thickness - self._canister.wall_thickness
        canister_x = [
            -self.outer_radius,
            self.outer_radius,
            self.outer_radius,
            self.inner_radius,
            self.inner_radius,
            -self.inner_radius,
            -self.inner_radius,
            -self.outer_radius,
            -self.outer_radius,
        ]
        canister_y = [
            neg_y,
            neg_y,
            pos_y,
            pos_y,
            neg_y + self._canister.wall_thickness,
            neg_y + self._canister.wall_thickness,
            pos_y,
            pos_y,
            neg_y,
        ]
        fig.add_trace(
            go.Scatter(
                x=canister_x,
                y=canister_y,
                mode="lines",
                name="Canister",
                line=dict(width=0),
                fillcolor="black",
                fill="toself",
            )
        )

        fig.update_layout(
            xaxis=dict(showgrid=False, zeroline=False, scaleanchor="y", title="X [mm]"),
            yaxis=dict(showgrid=False, zeroline=False, title="Y [mm]"),
            paper_bgcolor=paper_bgcolor,
            plot_bgcolor=plot_bgcolor,
            **kwargs,
        )

        return fig

    @property
    def inner_circle(self) -> pd.DataFrame:
        return self._inner_circle.assign(x=lambda x: x["x"] * M_TO_MM).assign(y=lambda x: x["y"] * M_TO_MM).rename(columns={"x": "X [mm]", "y": "Y [mm]"})

    @property
    def outer_circle(self) -> pd.DataFrame:
        return self._outer_circle.assign(x=lambda x: x["x"] * M_TO_MM).assign(y=lambda x: x["y"] * M_TO_MM).rename(columns={"x": "X [mm]", "y": "Y [mm]"})

    @property
    def cost(self) -> float:
        return round(self._cost, 2)

    @property
    def mass(self) -> float:
        return round(self._mass * KG_TO_G, 2)

    @property
    def inner_radius(self) -> float:
        return round(self._inner_radius * M_TO_MM, 2)

    @property
    def inner_height(self) -> float:
        return round(self._inner_height * M_TO_MM, 2)

    @property
    def outer_radius(self) -> float:
        return round(self._outer_radius * M_TO_MM, 2)

    @property
    def length(self) -> float:
        return round(self._length * M_TO_MM, 2)

    @property
    def inner_volume(self) -> float:
        return round(self._inner_volume * M_TO_CM**3, 2)

    @property
    def closed_volume(self) -> float:
        return round(self._closed_volume * M_TO_CM**3, 2)

    @property
    def name(self) -> str:
        return self._name.replace("_", " ").title()


class PrismaticShell:
    def __init__(
        self,
        cost: float,
        mass: float,
        internal_width: float,
        internal_length: float,
        internal_height: float,
        wall_thickness: float,
        name: str = "Prismatic Shell",
    ):
        """
        Class representing a shell used for a prismatic cell.

        :param cost: float: cost of the shell in $
        :param mass: float: mass of the shell in g
        :param internal_width: float: internal width of the shell in mm
        :param internal_length: float: internal length of the shell in mm
        :param internal_height: float: internal height of the shell in mm
        :param wall_thickness: float: thickness of the shell wall in mm
        """
        self._check_cost(cost)
        self._check_mass(mass)
        self._check_internal_width(internal_width)
        self._check_internal_length(internal_length)
        self._check_internal_height(internal_height)
        self._check_wall_thickness(wall_thickness)
        self._check_name(name)
        self._calculate_properties()

    def _calculate_properties(self):
        self._external_width = self._internal_width + 2 * self._wall_thickness
        self._external_length = self._internal_length + 2 * self._wall_thickness
        self._external_height = self._internal_height + 2 * self._wall_thickness
        self._external_volume = self._external_width * self._external_length * self._external_height
        self._internal_volume = self._internal_width * self._internal_length * self._internal_height

    def _check_cost(self, cost: float):
        if not isinstance(cost, (int, float)):
            raise TypeError("Cost must be a number")

        if cost < 0:
            raise ValueError("Cost cannot be negative")

        self._cost = cost

    def _check_mass(self, mass: float):
        if not isinstance(mass, (int, float)):
            raise TypeError("Mass must be a number")

        if mass < 0:
            raise ValueError("Mass cannot be negative")

        self._mass = mass * G_TO_KG

    def _check_internal_width(self, internal_width: float):
        if not isinstance(internal_width, (int, float)):
            raise TypeError("Internal width must be a number")

        if internal_width <= 0:
            raise ValueError("Internal width must be positive")

        self._internal_width = internal_width * MM_TO_M

    def _check_internal_length(self, internal_length: float):
        if not isinstance(internal_length, (int, float)):
            raise TypeError("Internal length must be a number")

        if internal_length <= 0:
            raise ValueError("Internal length must be positive")

        self._internal_length = internal_length * MM_TO_M

    def _check_internal_height(self, internal_height: float):
        if not isinstance(internal_height, (int, float)):
            raise TypeError("Internal height must be a number")

        if internal_height <= 0:
            raise ValueError("Internal height must be positive")

        self._internal_height = internal_height * MM_TO_M

    def _check_wall_thickness(self, wall_thickness: float):
        if not isinstance(wall_thickness, (int, float)):
            raise TypeError("Wall thickness must be a number")

        if wall_thickness <= 0:
            raise ValueError("Wall thickness must be positive")

        self._wall_thickness = wall_thickness * MM_TO_M

    def _check_name(self, name: str):
        if not isinstance(name, str):
            raise TypeError("Name must be a string")

        if len(name) == 0:
            raise ValueError("Name cannot be empty")

        self._name = name

    @property
    def external_width(self) -> float:
        return round(self._external_width * M_TO_MM, 2)

    @property
    def external_length(self) -> float:
        return round(self._external_length * M_TO_MM, 2)

    @property
    def external_height(self) -> float:
        return round(self._external_height * M_TO_MM, 2)

    @property
    def internal_volume(self) -> float:
        return round(self._internal_volume * M_TO_CM**3, 2)

    @property
    def external_volume(self) -> float:
        return round(self._external_volume * M_TO_CM**3, 2)

    @property
    def internal_width(self) -> float:
        return round(self._internal_width * M_TO_MM, 2)

    @property
    def internal_length(self) -> float:
        return round(self._internal_length * M_TO_MM, 2)

    @property
    def internal_height(self) -> float:
        return round(self._internal_height * M_TO_MM, 2)

    @property
    def wall_thickness(self) -> float:
        return round(self._wall_thickness * M_TO_MM, 2)

    @property
    def cost(self) -> float:
        return round(self._cost, 2)

    @property
    def mass(self) -> float:
        return round(self._mass * KG_TO_G, 2)

    @property
    def name(self) -> str:
        return self._name

    def __str__(self) -> str:
        return self.name

    def __repr__(self):
        return self.__str__()


class PrismaticLid:
    def __init__(
        self,
        cost: float,
        mass: float,
        internal_width: float,
        external_width: float,
        name: str = "Prismatic Lid",
    ):
        """
        Class representing a lid used for a prismatic cell.

        :param cost: float: cost of the lid in $
        :param mass: float: mass of the lid in g
        :param internal_width: float: internal width of the lid in mm
        :param external_width: float: external width of the lid in mm
        :param name: str: name of the lid
        """
        self._check_cost(cost)
        self._check_mass(mass)
        self._check_internal_width(internal_width)
        self._check_external_width(external_width)
        self._check_name(name)

    def _check_cost(self, cost: float):
        if not isinstance(cost, (int, float)):
            raise TypeError("Cost must be a number")

        if cost < 0:
            raise ValueError("Cost cannot be negative")

        self._cost = cost

    def _check_mass(self, mass: float):
        if not isinstance(mass, (int, float)):
            raise TypeError("Mass must be a number")

        if mass < 0:
            raise ValueError("Mass cannot be negative")

        self._mass = mass * G_TO_KG

    def _check_internal_width(self, internal_width: float):
        if not isinstance(internal_width, (int, float)):
            raise TypeError("Internal width must be a number")

        if internal_width <= 0:
            raise ValueError("Internal width must be positive")

        self._internal_width = internal_width * MM_TO_M

    def _check_external_width(self, external_width: float):
        if not isinstance(external_width, (int, float)):
            raise TypeError("External width must be a number")

        if external_width <= 0:
            raise ValueError("External width must be positive")

        self._external_width = external_width * MM_TO_M

    def _check_name(self, name: str):
        if not isinstance(name, str):
            raise TypeError("Name must be a string")

        if len(name) == 0:
            raise ValueError("Name cannot be empty")

        self._name = name

    @property
    def internal_width(self) -> float:
        return round(self._internal_width * M_TO_MM, 2)

    @property
    def external_width(self) -> float:
        return round(self._external_width * M_TO_MM, 2)

    @property
    def cost(self) -> float:
        return round(self._cost, 2)

    @property
    def mass(self) -> float:
        return round(self._mass * KG_TO_G, 2)

    @property
    def name(self) -> str:
        return self._name

    def __str__(self) -> str:
        return self.name

    def __repr__(self):
        return self.__str__()


class PrismaticCase:
    def __init__(self, shell: PrismaticShell, lid: PrismaticLid, name: str = "Prismatic Case"):
        """
        Class representing a casing used for a prismatic cell.

        :param shell: PrismaticShell: shell of the case
        :param lid: PrismaticLid: lid of the case
        :param name: str: name of the case
        """
        self._check_shell(shell)
        self._check_lid(lid)
        self._check_name(name)
        self._calculate_properties()

    def _calculate_properties(self):
        self._cost = self._shell._cost + self._lid._cost
        self._mass = self._shell._mass + self._lid._mass

        self._internal_width = self._shell._internal_width + self._lid._internal_width
        self._internal_length = self._shell._internal_length
        self._internal_height = self._shell._internal_height
        self._internal_volume = self._internal_height * self._internal_length * self._internal_width

        self._external_width = self._shell._external_width + self._lid._external_width
        self._external_length = self._shell._external_length
        self._external_height = self._shell._external_height
        self._external_volume = self._external_height * self._external_length * self._external_width

    def _check_shell(self, shell: PrismaticShell):
        if not isinstance(shell, PrismaticShell):
            raise TypeError("Shell must be a PrismaticShell")

        self._shell = shell

    def _check_lid(self, lid: PrismaticLid):
        if not isinstance(lid, PrismaticLid):
            raise TypeError("Lid must be a PrismaticLid")

        self._lid = lid

    def _check_name(self, name: str):
        if not isinstance(name, str):
            raise TypeError("Name must be a string")

        if len(name) == 0:
            raise ValueError("Name cannot be empty")

        self._name = name

    def get_optimized_stack(
        self,
        anode: Anode,
        cathode: Cathode,
        separator: Separator,
        n_stacks: int = 1,
        **kwargs,
    ) -> Stack:
        """
        Function to get the optimized stack for the prismatic case.

        :param anode: Anode: anode used in the cell
        :param cathode: Cathode: cathode used in the cell
        :param separator: Separator: separator used in the cell
        :return: tuple: optimized stack
        """
        # Check stack is small enough to fit in the prismatic case
        if anode.current_collector._width > self._internal_width:
            raise ValueError("Anode current collector width is too large for the prismatic case")
        if anode.current_collector._length > self._internal_length:
            raise ValueError("Anode current collector length is too large for the prismatic case")

        target_stack_height = self._internal_height / n_stacks
        stack_layers = 2
        stack = Stack(
            anode=anode,
            cathode=cathode,
            separator=separator,
            n_layers=stack_layers,
            **kwargs,
        )

        if stack._length > self._internal_length:
            raise ValueError("Stack length is too large for the prismatic case. Reduce your current collector lengths.")
        if stack._width > self._internal_width:
            raise ValueError("Stack width is too large for the prismatic case. Reduce your current collector widths.")
        if stack._thickness > target_stack_height:
            raise ValueError("Stack is too thick for the prismatic case even with one layer. Check your inputs.")

        initial_layer_guess = int(target_stack_height // (stack._thickness / 2))
        stack = Stack(
            anode=anode,
            cathode=cathode,
            separator=separator,
            n_layers=initial_layer_guess,
            **kwargs,
        )

        if stack._thickness > target_stack_height:
            while stack._thickness > target_stack_height:
                initial_layer_guess -= 1
                stack = Stack(
                    anode=anode,
                    cathode=cathode,
                    separator=separator,
                    n_layers=initial_layer_guess,
                    **kwargs,
                )
        elif stack._thickness < target_stack_height:
            while stack._thickness < target_stack_height:
                initial_layer_guess += 1
                stack = Stack(
                    anode=anode,
                    cathode=cathode,
                    separator=separator,
                    n_layers=initial_layer_guess,
                    **kwargs,
                )
            stack = Stack(
                anode=anode,
                cathode=cathode,
                separator=separator,
                n_layers=initial_layer_guess - 1,
                **kwargs,
            )

        return stack

    @property
    def internal_width(self) -> float:
        return round(self._internal_width * M_TO_MM, 2)

    @property
    def internal_length(self) -> float:
        return round(self._internal_length * M_TO_MM, 2)

    @property
    def internal_height(self) -> float:
        return round(self._internal_height * M_TO_MM, 2)

    @property
    def internal_volume(self) -> float:
        return round(self._internal_volume * M_TO_CM**3, 2)

    @property
    def external_width(self) -> float:
        return round(self._external_width * M_TO_MM, 2)

    @property
    def external_length(self) -> float:
        return round(self._external_length * M_TO_MM, 2)

    @property
    def external_height(self) -> float:
        return round(self._external_height * M_TO_MM, 2)

    @property
    def external_volume(self) -> float:
        return round(self._external_volume * M_TO_CM**3, 2)

    @property
    def shell(self) -> PrismaticShell:
        return self._shell

    @property
    def lid(self) -> PrismaticLid:
        return self._lid

    @property
    def cost(self) -> float:
        return round(self._cost, 2)

    @property
    def mass(self) -> float:
        return round(self._mass * KG_TO_G, 2)

    @property
    def name(self) -> str:
        return self._name

    def __str__(self) -> str:
        return self.name

    def __repr__(self):
        return self.__str__()
