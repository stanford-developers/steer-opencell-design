import dash as ds
import numpy as np
from typing import Union, Optional


class SliderWithTextInput:

    def __init__(
        self,
        id_base: dict,
        min_val: float,
        max_val: float,
        step: float,
        mark_interval: float,
        property_name: str,
        title: str,
        default_val: Union[float, list[float]] = None,
        with_slider_titles: bool = True,
        slider_disable: bool = False,
        div_width: str = 'calc(90%)',
    ):

        self.id_base = id_base
        self.min_val = min_val
        self.max_val = max_val
        self.default_val = default_val
        self.step = step
        self.mark_interval = mark_interval
        self.property_name = property_name
        self.title = title
        self.with_slider_titles = with_slider_titles
        self.div_width = div_width
        self.slider_disable = slider_disable

        self.slider_id = self._make_id('slider')
        self.input_id = self._make_id('input')

    def _make_id(self, subtype: str):
        return {**self.id_base, 'subtype': subtype, 'property': self.property_name}

    def _make_slider(self):

        return ds.dcc.Slider(
            id=self.slider_id,
            min=self.min_val,
            max=self.max_val,
            value=self.default_val,
            step=self.step,
            disabled=self.slider_disable,
            marks={int(i): "" for i in np.arange(self.min_val, self.max_val + self.mark_interval, self.mark_interval)},
            updatemode='mouseup'
        )

    def _make_input(self):

        return ds.dcc.Input(
            id=self.input_id,
            type='number',
            value=self.default_val,
            step=self.step,
            style={'margin-left': '20px'},
            disabled=self.slider_disable,
        )

    def __call__(self):

        slider_title = self.title if self.with_slider_titles else "\u00A0"

        return ds.html.Div([
            ds.html.P(slider_title, style={'margin-left': '20px', 'margin-bottom': '0px'}),
            ds.html.Div([self._make_slider()], style={'margin-bottom': '-18px'}),
            self._make_input(),
            ds.html.Br(), ds.html.Br()
        ], style={'width': self.div_width, 'margin-left': '-20px'})

    @property
    def components(self):
        return {'slider': self.slider_id, 'input': self.input_id}
    

class RangeSliderWithTextInput:

    def __init__(
        self,
        id_base: dict,
        min_val: float,
        max_val: float,
        step: float,
        mark_interval: float,
        property_name: str,
        title: str,
        default_val: Union[list[float], None] = None,
        with_slider_titles: bool = True,
        slider_disable: bool = False,
        div_width: str = 'calc(90%)',
    ):

        self.id_base = id_base
        self.min_val = min_val
        self.max_val = max_val
        self.default_val = default_val or [min_val, max_val]
        self.step = step
        self.mark_interval = mark_interval
        self.property_name = property_name
        self.title = title
        self.with_slider_titles = with_slider_titles
        self.div_width = div_width
        self.slider_disable = slider_disable

        self.slider_id = self._make_id('rangeslider')
        self.input_min_id = self._make_id('input_min')
        self.input_max_id = self._make_id('input_max')

    def _make_id(self, subtype: str):
        return {**self.id_base, 'subtype': subtype, 'property': self.property_name}

    def _make_range_slider(self):
        return ds.dcc.RangeSlider(
            id=self.slider_id,
            min=self.min_val,
            max=self.max_val,
            value=self.default_val,
            step=self.step,
            disabled=self.slider_disable,
            marks={int(i): "" for i in np.arange(self.min_val, self.max_val + self.mark_interval, self.mark_interval)},
            updatemode='mouseup'
        )

    def _make_min_input(self):
        return ds.dcc.Input(
            id=self.input_min_id,
            type='number',
            value=self.default_val[0],
            step=self.step,
            style={'margin-left': '20px', 'width': '80px'},
            disabled=self.slider_disable,
        )

    def _make_max_input(self):
        return ds.dcc.Input(
            id=self.input_max_id,
            type='number',
            value=self.default_val[1],
            step=self.step,
            style={'margin-left': '10px', 'width': '80px'},
            disabled=self.slider_disable,
        )

    def __call__(self):
        slider_title = self.title if self.with_slider_titles else "\u00A0"

        return ds.html.Div([
            ds.html.P(slider_title, style={'margin-left': '20px', 'margin-bottom': '0px'}),
            ds.html.Div([self._make_range_slider()], style={'margin-bottom': '-18px'}),
            ds.html.Div([
                ds.html.Span("Min:", style={'margin-left': '20px', 'margin-right': '5px'}),
                self._make_min_input(),
                ds.html.Span("Max:", style={'margin-left': '15px', 'margin-right': '5px'}),
                self._make_max_input(),
            ], style={'display': 'flex', 'align-items': 'center'}),
            ds.html.Br(), ds.html.Br()
        ], style={'width': self.div_width, 'margin-left': '-20px'})

    @property
    def components(self):
        return {
            'rangeslider': self.slider_id, 
            'input_min': self.input_min_id, 
            'input_max': self.input_max_id
        }