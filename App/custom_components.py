from SteerEnergyStorage.Materials.ElectrodeMaterials import CathodeMaterial, AnodeMaterial, Binder, ConductiveAdditive

from dash.development.base_component import Component
import numpy as np
import dash as ds
from styles import *


class SliderWithTextInput(Component):

    def __init__(self,
                 id: dict, 
                 min_val: float, 
                 max_val: float, 
                 default_val: float | list[float], 
                 step: float,
                 mark_interval: float,
                 property_name: str,
                 title: str,
                 with_slider_titles: bool = True,
                 div_width: str = '30%',
                 **kwargs: dict
                 ):
            
            super().__init__(**kwargs)
    
            self.id = id
            self.min_val = min_val
            self.max_val = max_val
            self.default_val = default_val
            self.step = step
            self.mark_interval = mark_interval
            self.property_name = property_name
            self.with_slider_titles = with_slider_titles
            self.title = title
            self.div_width = div_width

            self.slider, self.input = self.make_slider_and_input(self.property_name, self.min_val, self.max_val, self.default_val, self.step, self.mark_interval)
            self.div = self.make_slider_div(self.title, self.slider, self.input)

    def make_slider_and_input(self, property_name, min_val, max_val, default_val, step, mark_interval):

        slider_id = self.id.copy()
        slider_id.update({'subtype': 'slider', 'property': property_name})

        slider = ds.dcc.Slider(
            id=slider_id,
            min=min_val,
            max=max_val,
            value=default_val,
            step=step,
            marks={float(i): "" for i in np.arange(min_val, max_val + mark_interval, mark_interval)}
        )

        input_id = self.id.copy()
        input_id.update({'subtype': 'input', 'property': property_name})

        input_field = ds.dcc.Input(
            id=input_id,
            type='number',
            min=min_val,
            max=max_val,
            value=default_val,
            step=step,
            style={'margin-left': '20px'}
        )

        return ds.html.Div([slider], style={'margin-bottom': '-18px'}), input_field
    
    def make_slider_div(self, title, slider, input_field):

        slider_title = title if self.with_slider_titles else "\u00A0"

        return ds.html.Div([
            ds.html.P(slider_title, style={'margin-left': '20px', 'margin-bottom': '0px'}),
            slider, 
            input_field,
        ], style={'width': self.div_width, 'margin-left': '-20px'})

    def render(self):
        return self.div


class CheckboxWithSlider(Component):

    def __init__(self,
                 id: dict,
                 min_val: float,
                 max_val: float,
                 default_check: bool,
                 default_val: float,
                 step: float,
                 mark_interval: float,
                 property_name: str,
                 title: str,
                 with_slider_titles: bool = True,
                 div_width: str = '30%',
                 checkbox_label: str = "",
                 **kwargs: dict
                 ):
        super().__init__(**kwargs)

        self.id = id
        self.min_val = min_val
        self.max_val = max_val
        self.default_check = default_check
        self.default_val = default_val
        self.step = step
        self.mark_interval = mark_interval
        self.property_name = property_name
        self.with_slider_titles = with_slider_titles
        self.title = title
        self.div_width = div_width
        self.checkbox_label = checkbox_label

        self.make_checkbox()
        self.slider_div = SliderWithTextInput(
            self.id, self.min_val, self.max_val, self.default_val,
            self.step, self.mark_interval, self.property_name,
            self.title, self.with_slider_titles, self.div_width
        ).render()

    def make_checkbox(self):

        checkbox_id = self.id.copy()
        checkbox_id.update({'subtype': 'checkbox', 'property': self.property_name})

        self.checkbox = ds.dcc.Checklist(
            id=checkbox_id,
            options=[{'label': self.checkbox_label, 'value': True}],
            value=[True] if self.default_check else [False],
            style={
                'margin': '0 10px 0 0',
                'display': 'flex',
                'alignItems': 'center',
                'height': '40px',
                'width': '40px'
            },
            inputStyle={
                'marginRight': '6px',
                'transform': 'scale(2)', 
                'WebkitTransform': 'scale(2)',  # For Safari support
            }
        )

    def make_div(self):
        self.div = ds.html.Div([
            self.checkbox,
            self.slider_div
        ], style={
            'display': 'flex',
            'alignItems': 'center',
            'flexDirection': 'row',
            'gap': '0px', 
            'width': self.div_width,
            'minHeight': '50px',
            'marginLeft': '20px'
        })

    def render(self):
        self.make_div()
        return self.div


class MaterialSelector0(Component):

    def __init__(self, 
                 id: dict, 
                 materials: list,
                 with_slider_titles: bool,
                 density_default: float,
                 specific_cost_default: float,
                 formula_default: str,
                 slider_div_width: str,
                 dropdown_placeholder: str,
                 **kwargs: dict
                 ):
        
        super().__init__(**kwargs)

        self.id = id
        self.with_slider_titles = with_slider_titles
        self.density_default = density_default
        self.specific_cost_default = specific_cost_default
        self.slider_div_width = slider_div_width
        self.materials = materials
        self.dropdown_placeholder = dropdown_placeholder
        self.formula_default = formula_default

        self.make_text_input()

        self.density_div = SliderWithTextInput(self.id, 0, 12, self.density_default, 0.01, 1, 'density', 'Density (g/cm³)', self.with_slider_titles, self.slider_div_width).render()
        self.specific_cost_div = SliderWithTextInput(self.id, 0, 30, self.specific_cost_default, 0.01, 5, 'specific_cost', 'Specific Cost ($/kg)', self.with_slider_titles, self.slider_div_width).render()


    def make_text_input(self):

        dropdown_id = self.id.copy()
        dropdown_id.update({'subtype': 'text_input', 'property': 'name'})

        self.text_input = ds.dcc.Dropdown(
            id=dropdown_id,
            options=[{'label': material, 'value': material} for material in self.materials] if self.materials else [],
            placeholder=self.dropdown_placeholder,
            style={'width': '200px', 'margin-right': '40px'},
            value=self.formula_default
        )

    def make_div(self):
        
        self.div = ds.html.Div([
            self.text_input,
            self.density_div,
            self.specific_cost_div,
        ], style={'display': 'flex', 'align-items': 'center', 'flex-direction': 'row', 'width': '160%'})

    def render(self):
        self.make_div()
        return self.div


class CurrentCollectorSelector(MaterialSelector0):

    def __init__(self, 
                 id: dict, 
                 materials: list,
                 with_slider_titles: bool = True,
                 density_default: float = 4,
                 specific_cost_default: float = 15,
                 slider_div_width: str = '300px',
                 dropdown_placeholder: str = 'Select Material',
                 formula_default: str = 'Al',
                 **kwargs: dict
                 ):
        
        super().__init__(id=id, 
                         materials=materials,
                         with_slider_titles=with_slider_titles, 
                         density_default=density_default, 
                         specific_cost_default=specific_cost_default, 
                         slider_div_width=slider_div_width, 
                         dropdown_placeholder=dropdown_placeholder,
                         formula_default=formula_default,
                         **kwargs)
        

class MaterialSelector1(MaterialSelector0):

    def __init__(self, 
                 id: dict, 
                 with_slider_titles: bool,
                 weight_default: float,
                 density_default: float,
                 specific_cost_default: float,
                 formula_default: str,
                 slider_div_width: str,
                 materials: list,
                 dropdown_placeholder: str = 'Select Material',
                 **kwargs: dict
                 ):
        
        super().__init__(
            id=id,
            with_slider_titles=with_slider_titles,
            density_default=density_default,
            specific_cost_default=specific_cost_default,
            formula_default=formula_default,
            slider_div_width=slider_div_width,
            materials=materials,
            dropdown_placeholder=dropdown_placeholder
        )

        self.with_slider_titles = with_slider_titles
        self.weight_default = weight_default

        self.make_store()
        self.make_text_input()
        self.weight_percent_div = SliderWithTextInput(self.id, 0, 100, self.weight_default, 0.1, 20, 'weight', 'Weight (%)', self.with_slider_titles, self.slider_div_width).render()

    def make_store(self):

        store_id = self.id.copy()
        store_id.update({'subtype': 'store', 'property': 'object'})
        self.store = ds.dcc.Store(id=store_id)

    def make_text_input(self):

        input_id = self.id.copy()
        input_id.update({'subtype': 'text_input', 'property': 'name'})
        default_value = self.id['type'].replace('_', ' ').title() + " " + str(self.id['index'] + 1)

        self.text_input = ds.dcc.Input(
            id=input_id,
            type='text',
            style={'width': '200px', 'margin-right': '40px'},
            value=default_value
        )

    def make_div(self):
        
        self.div = ds.html.Div([
            self.text_input,
            self.weight_percent_div,
            self.density_div,
            self.specific_cost_div,
            self.store,
        ], style={'display': 'flex', 'align-items': 'center', 'flex-direction': 'row', 'width': '160%'})


class BinderSelector(MaterialSelector1):

    def __init__(self, 
                 id: dict, 
                 with_slider_titles: bool = True,
                 weight_default: float = 0,
                 density_default: float = 1.7,
                 specific_cost_default: float = 10,
                 formula_default: str = None,
                 slider_div_width: str = '220px',
                 materials: list = [],
                 dropdown_placeholder: str = ' ',
                 **kwargs: dict
                 ):
        
        super().__init__(
            id=id, 
            with_slider_titles=with_slider_titles, 
            weight_default=weight_default, 
            density_default=density_default, 
            specific_cost_default=specific_cost_default, 
            slider_div_width=slider_div_width, 
            formula_default=formula_default,
            materials=materials,
            dropdown_placeholder=dropdown_placeholder,
            **kwargs
        )


class ConductiveAdditiveSelector(MaterialSelector1):

    def __init__(self, 
                 id: dict, 
                 with_slider_titles: bool = True,
                 weight_default: float = 0,
                 density_default: float = 1.9,
                 specific_cost_default: float = 9,
                 slider_div_width: str = '220px',
                 formula_default: str = None,
                 materials: list = [],
                 dropdown_placeholder: str = ' ',
                 **kwargs: dict
                 ):
        
        super().__init__(
            id=id, 
            with_slider_titles=with_slider_titles, 
            weight_default=weight_default, 
            density_default=density_default, 
            specific_cost_default=specific_cost_default, 
            formula_default=formula_default,
            slider_div_width=slider_div_width, 
            materials=materials,
            dropdown_placeholder=dropdown_placeholder,
            **kwargs
        )


class RangeSliderWithTextInput(SliderWithTextInput):

    def __init__(self,
                 id: dict, 
                 min_val: float, 
                 max_val: float, 
                 default_val: list[float], 
                 step: float,
                 mark_interval,
                 property_name: str,
                 title: str,
                 with_slider_titles: bool = True,
                 div_width: str = '800px',
                 **kwargs: dict
                 ):
            
            super().__init__(**kwargs, 
                             id=id, 
                             min_val=min_val, 
                             max_val=max_val, 
                             default_val=default_val, 
                             step=step, 
                             mark_interval=mark_interval, 
                             property_name=property_name, 
                             title=title, 
                             with_slider_titles=with_slider_titles, 
                             div_width=div_width)

    def make_slider_and_input(self, property_name, min_val, max_val, default_val, step, mark_interval):

        slider_id = self.id.copy()
        slider_id.update({'subtype': 'range_slider', 'property': property_name})

        slider = ds.dcc.RangeSlider(
            id=slider_id,
            min=min_val,
            max=max_val,
            value=default_val,
            step=step,
            marks={i: "" for i in range(min_val, max_val + 1, mark_interval)}
        )

        input_id_min = self.id.copy()
        input_id_min.update({'subtype': 'input', 'property': property_name, 'select_value': 'min'})

        input_field_min = ds.dcc.Input(
            id=input_id_min,
            type='number',
            min=min_val,
            max=max_val,
            value=default_val[0],
            step=step
        )

        input_id_min = self.id.copy()
        input_id_min.update({'subtype': 'input', 'property': property_name, 'select_value': 'max'})

        input_field_max = ds.dcc.Input(
            id=input_id_min,
            type='number',
            min=min_val,
            max=max_val,
            value=default_val[1],
            step=step
        )

        input_div = ds.html.Div([
            input_field_min, 
            ds.html.P("to", style={'margin': '0 10px', 'align-self': 'center'}), 
            input_field_max
        ], style={'display': 'flex', 'align-items': 'center', 'flex-direction': 'row', 'margin-left': '20px'})

        return ds.html.Div([slider], style={'margin-bottom': '-18px'}), input_div
    

class MaterialSelector2(MaterialSelector1):

    def __init__(self, 
                 id: dict, 
                 dropdown_placeholder: str,
                 materials: list,
                 with_slider_titles: bool,
                 weight_default: float,
                 density_default: float,
                 specific_cost_default: float,
                 formula_default: str,
                 slider_div_width: str,
                 name_default: str,
                 irreversible_capacity_scaling_default: float = 1,
                 reversible_capacity_scaling_default: float = 1,
                 **kwargs: dict
                 ):
        
        self.dropdown_placeholder = dropdown_placeholder
        self.materials = materials
        self.name_default = name_default
        self.irreversible_capacity_scaling_default = irreversible_capacity_scaling_default
        self.reversible_capacity_scaling_default = reversible_capacity_scaling_default

        super().__init__(
            id=id, 
            with_slider_titles=with_slider_titles, 
            weight_default=weight_default, 
            density_default=density_default, 
            specific_cost_default=specific_cost_default, 
            slider_div_width=slider_div_width, 
            formula_default=formula_default,
            materials=materials,
            dropdown_placeholder=dropdown_placeholder,
            **kwargs
        )

        self.reversible_capacity_div = SliderWithTextInput(self.id, 0.5, 1.5, self.reversible_capacity_scaling_default, 0.01, 0.1, 'reversible_capacity', 'Rev. Cap. Scaling', self.with_slider_titles, self.slider_div_width).render()
        self.irreversible_capacity_div = SliderWithTextInput(self.id, 0.5, 1.5, self.irreversible_capacity_scaling_default, 0.01, 0.1, 'irreversible_capacity', 'Irrev. Cap. Scaling', self.with_slider_titles, self.slider_div_width).render()

    def make_text_input(self):

        dropdown_id = self.id.copy()
        dropdown_id.update({'subtype': 'text_input', 'property': 'name'})

        self.text_input = ds.dcc.Dropdown(
            id=dropdown_id,
            options=[{'label': material, 'value': material} for material in self.materials] if self.materials else [],
            placeholder=self.dropdown_placeholder,
            style={'width': '380px', 'margin-right': '40px'},
            value=self.name_default
        )

    def make_div(self):
        self.div = ds.html.Div([
            self.text_input,
            self.weight_percent_div,
            self.density_div,
            self.specific_cost_div,
            self.reversible_capacity_div,
            self.irreversible_capacity_div,
            self.store,
        ], style={'display': 'flex', 'align-items': 'center', 'flex-direction': 'row', 'width': '160%'})


class CathodeMaterialSelector(MaterialSelector2):

    def __init__(self, 
                 id: dict, 
                 materials: list,
                 dropdown_placeholder: str = 'Select Material',
                 with_slider_titles: bool = True,
                 weight_default: float = 100,
                 density_default: float = 4.4,
                 specific_cost_default: float = 11,
                 slider_div_width: str = '220px',
                 name_default=None,
                 irreversible_capacity_scaling_default: float = 1,
                 reversible_capacity_scaling_default: float = 1,
                 **kwargs: dict
                 ):
        
        super().__init__(id=id, 
                         dropdown_placeholder=dropdown_placeholder, 
                         materials=materials, 
                         with_slider_titles=with_slider_titles, 
                         weight_default=weight_default, 
                         density_default=density_default, 
                         specific_cost_default=specific_cost_default, 
                         formula_default=None,
                         slider_div_width=slider_div_width, 
                         name_default=name_default,
                         irreversible_capacity_scaling_default=irreversible_capacity_scaling_default,
                         reversible_capacity_scaling_default=reversible_capacity_scaling_default,
                         **kwargs)
        
        dens_cost_slider_id = self.id.copy() 
        dens_cost_slider_id['logic'] = 'match'

        self.density_div = SliderWithTextInput(dens_cost_slider_id, 0, 12, self.density_default, 0.01, 1, 'density', 'Density (g/cm³)', self.with_slider_titles, self.slider_div_width).render()
        self.specific_cost_div = SliderWithTextInput(dens_cost_slider_id, 0, 500, self.specific_cost_default, 0.01, 50, 'specific_cost', 'Specific Cost ($/kg)', self.with_slider_titles, self.slider_div_width).render()

    
class AnodeMaterialSelector(MaterialSelector2):

    def __init__(self, 
                 id: dict, 
                 materials: list,
                 dropdown_placeholder: str = 'Select Material',
                 with_slider_titles: bool = True,
                 weight_default: float = 100,
                 density_default: float = 1.5,
                 specific_cost_default: float = 7,
                 slider_div_width: str = '220px',
                 name_default=None,
                 irreversible_capacity_scaling_default: float = 1,
                 reversible_capacity_scaling_default: float = 1,
                 **kwargs: dict
                 ):
        
        super().__init__(id=id, 
                         dropdown_placeholder=dropdown_placeholder, 
                         materials=materials, 
                         with_slider_titles=with_slider_titles, 
                         weight_default=weight_default, 
                         density_default=density_default, 
                         specific_cost_default=specific_cost_default, 
                         formula_default=None,
                         slider_div_width=slider_div_width, 
                         name_default=name_default,
                         irreversible_capacity_scaling_default=irreversible_capacity_scaling_default,
                         reversible_capacity_scaling_default=reversible_capacity_scaling_default,
                         **kwargs)
        
        dens_cost_slider_id = self.id.copy() 
        dens_cost_slider_id['logic'] = 'match'
        
        self.density_div = SliderWithTextInput(dens_cost_slider_id, 0, 12, self.density_default, 0.01, 1, 'density', 'Density (g/cm³)', self.with_slider_titles, self.slider_div_width).render()
        self.specific_cost_div = SliderWithTextInput(dens_cost_slider_id, 0, 500, self.specific_cost_default, 0.01, 50, 'specific_cost', 'Specific Cost ($/kg)', self.with_slider_titles, self.slider_div_width).render()


