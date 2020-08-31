import io
import os
import base64
import time

import numpy as np
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_table
from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output, State
from flask import Flask
import matplotlib
from matplotlib import cm
from mpl_toolkits.mplot3d.axes3d import get_test_data
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.pyplot as plt

import hvsrpy

matplotlib.use('Agg')

# Style Settings
default_span_style = {"cursor": "context-menu",
                      "padding": "1px", "margin-top": "0em"}
default_p_style = {"margin-top": "0.5em", "margin-bottom": "0em"}
default_cardbody_style = {"min-height": "65vh"}

intro_tab = dbc.Card(
    dbc.CardBody(
        dcc.Markdown("""
            # Welcome to HVSRweb

            HVSRweb is a web application for horizontal-to-vertical spectral
            ratio (HVSR) processing. HVSRweb utilizes _hvsrpy_
            (Vantassel, 2020) behind Dash (Plotly, 2017) to allow
            processing of ambient noise data in the cloud, with no
            installation required.

            # Getting Started

            1. Load your own ambient noise data using the upload bar or press
            __Demo__ to load a data file provided by us.
            2. Explore the processing settings tabs (Time, Frequency,
            and H/V) and make any desired changes.
            3. When done, press __Calculate__ and go to the Results tab for
            more information.

            # Citation

            If you use HVSRweb in your research or consulting we ask you
            please cite the following:

            Vantassel, J.P., Cox, B.R., Brannon, D.M. (2021). HVSRweb: An
            Open-Source, Web-Based Application for Horizontal-to-Vertical
            Spectral Ratio Processing. (Submitted).

            Additional information concerning the implementation of
            the HVSR calculation can be found on the _hvsrpy_
            [GitHub](https://github.com/jpvantassel/hvsrpy).

            # Additional References

            Background information concerning the HVSR statistics and
            the terminology can be found in the following references:

            Cox, B. R., Cheng, T., Vantassel, J. P., and Manuel, L. (2020).
            “A statistical representation and frequency-domain
            window-rejection algorithm for single-station HVSR measurements.”
            Geophysical Journal International, 221(3), 2170-2183.

            Cheng, T., Cox, B. R., Vantassel, J. P., and Manuel, L. (2020).
            "A statistical approach to account for azimuthal variability in
            single-station HVSR measurements." Geophysical Journal
            International, Accepted.

            """),
        style=default_cardbody_style),
    className="mt-3",
)

time_tab = dbc.Card(
    dbc.CardBody(
        [
            # Window Length
            html.P([
                html.Span(
                    "Window Length (s):",
                    id="windowlength-tooltip-target",
                    style=default_span_style,
                ),
            ], style=default_p_style),
            dbc.Tooltip("""
                        Length of each time window in seconds. For specific
                        guidance on an appropriate window length refer to the
                        SESAME (2004) guidelines.
                        """,
                        target="windowlength-tooltip-target",
                        ),
            dbc.Input(id="windowlength-input", type="number",
                      value=60, min=30, max=600, step=1),

            # Width of cosine taper
            html.P([
                html.Span(
                    "Cosine Taper Width:",
                    id="width-tooltip-target",
                    style=default_span_style,
                ),
            ], style=default_p_style),
            dbc.Tooltip("""
                        Fraction of each time window to be cosine tapered.
                        0.1 (i.e., 5% off either end) is recommended.
                        """,
                        target="width-tooltip-target",
                        ),
            dbc.Input(id="width-input", type="number",
                      value=0.1, min=0., max=1.0, step=0.1),

            # Butterworth Filter
            html.P([
                html.Span(
                    "Apply Butterworth Filter?",
                    id="butterworth-tooltip-target",
                    style=default_span_style,
                ),
            ], style=default_p_style),
            dbc.Tooltip("""
                        Select whether a Butterworth bandpass filter is applied
                        to the time-domain singal. Geopsy does not apply a
                        bandpass filter.
                        """,
                        target="butterworth-tooltip-target",
                        ),
            dbc.Select(
                id="butterworth-input",
                options=[
                    {"label": "Yes", "value": "True"},
                    {"label": "No", "value": "False"},
                ], value="False"),

            dbc.Container([
                # Butterworth Filter: Low Frequency
                html.P([
                    html.Span(
                        "Low-cut Frequency (Hz):",
                        id="flow-tooltip-target",
                        style=default_span_style,
                    ),
                ], style=default_p_style),
                dbc.Tooltip(
                    "Frequencies below that specified are filtered.",
                    target="flow-tooltip-target",
                ),
                dbc.Input(id="flow-input", type="number",
                          value=0.1, min=0, max=1000, step=0.01),

                # Butterworth Filter: High Frequency
                html.P([
                    html.Span(
                        "High-cut Frequency (Hz):",
                        id="fhigh-tooltip-target",
                        style=default_span_style,
                    ),
                ], style=default_p_style),
                dbc.Tooltip(
                    "Frequencies above that specified are filtered.",
                    target="fhigh-tooltip-target",
                ),
                dbc.Input(id="fhigh-input", type="number",
                          value=30, min=0, max=600, step=1),

                # Butterworth Filter: Filter Order
                html.P([
                    html.Span(
                        "Filter Order:",
                        id="forder-tooltip-target",
                        style=default_span_style,
                    ),
                ], style=default_p_style),
                dbc.Tooltip(
                    "Order of Butterworth filter, 5 is recommended.",
                    target="forder-tooltip-target",
                ),
                dbc.Input(id="forder-input", type="number",
                          value=5, min=0, max=600, step=1),
            ], className="ml-2 mr-0", id="bandpass-options",),
        ], style=default_cardbody_style),
    className="mt-3",
)

mod_span_style = dict(default_span_style)
mod_span_style["padding"] = "0"
frequency_tab = dbc.Card(
    dbc.CardBody(
        [
            # Bandwidth
            html.P([
                html.Span(
                    "Konno and Ohmachi Smoothing Coefficient:",
                    id="bandwidth-tooltip-target",
                    style=default_span_style,
                ),
            ], style=default_p_style),
            dbc.Tooltip("""
                        Bandwidth coefficient (b) for Konno and Ohmachi (1998)
                        smoothing a value of 40 is recommended.
                        """,
                        target="bandwidth-tooltip-target",
                        ),
            dbc.Input(id="bandwidth-input", type="number",
                      value=40, min=10, max=100, step=5),

            html.P("Resampling:", style=default_p_style),
            dbc.Container([
                # Resampling: Minimum Frequency
                html.P([
                    html.Span(
                        "Minimum Frequency (Hz):",
                        id="minf-tooltip-target",
                        style=mod_span_style,
                    ),
                ], style=default_p_style),
                dbc.Tooltip(
                    "Minimum frequency considered when resampling.",
                    target="minf-tooltip-target",
                ),
                dbc.Input(id="minf-input", type="number",
                          value=0.2, min=0.01, max=30, step=0.01),

                # Resampling: Maximum Frequency
                html.P([
                    html.Span(
                        "Maximum Frequency (Hz):",
                        id="maxf-tooltip-target",
                        style=default_span_style,
                    ),
                ], style=default_p_style),
                dbc.Tooltip(
                    "Maximum frequency considered when resampling.",
                    target="maxf-tooltip-target",
                ),
                dbc.Input(id="maxf-input", type="number",
                          value=20, min=1, max=100, step=1),

                # Resampling: Number of Frequencies
                html.P([
                    html.Span(
                        "Number of Frequency Points:",
                        id="nf-tooltip-target",
                        style={"cursor": "context-menu", "padding": "5px"},
                    ),
                ], style=default_p_style),
                dbc.Tooltip(
                    "Number of frequency points after resampling.",
                    target="nf-tooltip-target",
                ),
                dbc.Input(id="nf-input", type="number",
                          value=128, min=32, max=4096, step=1),

                # Resampling: Type
                html.P([
                    html.Span(
                        "Type:",
                        id="res_type-tooltip-target",
                        style=default_span_style,
                    ),
                ], style=default_p_style),
                dbc.Tooltip(
                    "Distribution of frequency samples.",
                    target="res_type-tooltip-target",
                ),
                dbc.Select(
                    id="res_type-input",
                    options=[
                        {"label": "Logarithmic", "value": "log"},
                        {"label": "Linear", "value": "linear"},
                    ],
                    value="log",
                )],
                className="ml-2 mr-0"),
        ], style=default_cardbody_style),
    className="mt-3",
)

hv_tab = dbc.Card(
    dbc.CardBody(
        [
            # Method for combining
            html.P([
                html.Span(
                    "Define Horizontal Component with:",
                    id="method-tooltip-target",
                    style=default_span_style,
                ),
            ], style=default_p_style),
            dbc.Tooltip("""
                        Geometric-Mean is recommended.
                        Geopsy uses the Squared-Average by default.
                        """,
                        target="method-tooltip-target",
                        ),
            dbc.Select(
                id="method-input",
                options=[
                    {"label": "Geometric-Mean", "value": "geometric-mean"},
                    {"label": "Squared-Average", "value": "squared-average"},
                    {"label": "Single-Azimuth", "value": "azimuth"},
                    {"label": "Multiple-Azimuths", "value": "rotate"}
                ],
                value="geometric-mean",
            ),

            dbc.Container([
                # Azimuth degrees
                html.P([
                    html.Span(
                        "Azimuth:",
                        id="azimuth-tooltip-target",
                        style=default_span_style,
                    ),
                ], style=default_p_style),
                dbc.Tooltip("""
                            Azimuth measured in degrees clockwise from North
                            (sensor is assumed to be oriented due North).
                            """,
                            target="azimuth-tooltip-target",
                            ),
                dbc.Input(id="azimuth-input", type="number",
                          value=90, min=0, max=179, step=1),
            ],
                className="ml-2 mr-0",
                id="azimuth-options"),

            dbc.Container([
                # Rotate degrees
                html.P([
                    html.Span(
                        "Azimuthal Interval:",
                        id="rotate-tooltip-target",
                        style=default_span_style,
                    ),
                ], style=default_p_style),
                dbc.Tooltip("""
                            Spacing in degrees between considered azimuths.
                            15 is recommended.
                            """,
                            target="rotate-tooltip-target",
                            ),
                dbc.Input(id="rotate-input", type="number",
                          value=15, min=0, max=45, step=1),
            ],
                className="ml-2 mr-0",
                id="rotate-options"),

            # Distribution of f0
            html.P([
                html.Span(
                    ["Distribution of ", html.Div(['f', html.Sub('0')], style={
                                                  "display": "inline"}), ":"],
                    id="distribution_f0-tooltip-target",
                    style=default_span_style,
                ),
            ], style=default_p_style),
            dbc.Tooltip("""
                        Lognormal is recommended.
                        Geopsy uses Normal.
                        """,
                        target="distribution_f0-tooltip-target",
                        ),
            dbc.Select(
                id="distribution_f0-input",
                options=[
                    {"label": "Lognormal", "value": "log-normal"},
                    {"label": "Normal", "value": "normal"},
                ], value='log-normal'),

            # Distribution of Median Curve
            html.P([
                html.Span(
                    "Distribution of Median Curve:",
                    id="distribution_mc-tooltip-target",
                    style=default_span_style,
                ),
            ], style=default_p_style),
            dbc.Tooltip("""
                        Lognormal is recommended.
                        Geopsy uses Lognormal
                        """,
                        target="distribution_mc-tooltip-target",
                        ),
            dbc.Select(
                id="distribution_mc-input",
                options=[
                    {"label": "Lognormal", "value": "log-normal"},
                    {"label": "Normal", "value": "normal"},
                ], value="log-normal"),

            # Frequency-Domain Window-Rejection Algorithm
            html.P([
                html.Span(
                    "Apply Frequency-Domain Window-Rejection?",
                    id="rejection_bool-tooltip-target",
                    style=default_span_style,
                ),
            ], style=default_p_style),
            dbc.Tooltip("""
                        Select whether the frequency-domain window-rejection
                        algorithm proposed by Cox et al. (2020) is applied.
                        Geopsy does not offer this functionality.
                        """,
                        target="rejection_bool-tooltip-target",
                        ),
            dbc.Select(
                id="rejection_bool-input",
                options=[
                    {"label": "Yes", "value": "True"},
                    {"label": "No", "value": "False"},
                ], value="True"),

            dbc.Container([
                # Number of Standard Deviations
                html.P([
                    html.Span(
                        "Number of Standard Deviations (n):",
                        id="n-tooltip-target",
                        style=default_span_style,
                    ),
                ], style=default_p_style),
                dbc.Tooltip("""
                            Number of standard deviations to consider during
                            rejection. Smaller values will tend to reject more
                            windows than larger values. 2 is recommended.
                            """,
                            target="n-tooltip-target",
                            ),
                dbc.Input(id="n-input", type="number",
                          value=2, min=1, max=4, step=0.5),

                # Maximum Number of Iterations
                html.P([
                    html.Span(
                        "Maximum Number of Allowed Iterations:",
                        id="n_iteration-tooltip-target",
                        style=default_span_style,
                    ),
                ], style=default_p_style),
                dbc.Tooltip("""
                            Maximum number of iterations of the rejection
                            algorithm. 50 is recommended.
                            """,
                            target="n_iteration-tooltip-target",
                            ),
                dbc.Input(id="n_iteration-input", type="number",
                          value=50, min=5, max=75, step=1),
            ],
                className="ml-2 mr-0",
                id="rejection-options"),
        ], style=default_cardbody_style),
    className="mt-3",
)

button_style = {"padding": "5px", "width": "100%"}
col_style = {"padding": "5px"}
results_tab = dbc.Card(
    dbc.CardBody(
        [
            dbc.Row([
                dbc.Col([
                    html.A(
                        dbc.Button("Save Figure", color="primary",
                                   id="save_figure-button", style=button_style),
                        id='figure-download', download="", href="", target="_blank"),
                ], style=col_style),
                dbc.Col([
                    html.A(
                        dbc.Button("Save as hvsrpy", color="primary",
                                   id="save_hvsrpy-button", style=button_style),
                        id="hv-download", download="", href="", target="_blank"),
                    dbc.Tooltip(
                        "Save results in the hvsrpy-style text format.",
                        target="save_hvsrpy-button"),
                ], style=col_style),
                dbc.Col([
                    html.A(
                        dbc.Button("Save as geopsy", color="primary",
                                   id="save_geopsy-button", style=button_style),
                        id="geopsy-download", download="", href="", target="_blank"),
                    html.Div(id="geopsy-button-tooltip"),
                ], style=col_style),
            ], className="mb-2"),
            html.Div(id='window-information-table'),
            html.Div(id='before-rejection-table'),
            html.Div(id='after-rejection-table'),
            html.Div(id="tooltips"),
            html.Div([
                html.P("Looking for more information? Refer to the references back in the Intro tab.",
                       style=dict(**default_p_style, **{"display": "inline", "color": "#495057"})),
            ]),
            html.Div([
                html.P("Looking for more functionality? Checkout ",
                       style=dict(**default_p_style, **{"display": "inline", "color": "#495057"})),
                html.A("hvsrpy.",
                       href="https://github.com/jpvantassel/hvsrpy")
            ]),
            html.Div([
                html.P("Want to access an earlier version of HVSRweb? Find instructions ",
                       style=dict(**default_p_style, **{"display": "inline", "color": "#495057"})),
                html.A("here.",
                       href="https://github.com/jpvantassel/hvsrweb")
            ]),
        ], style=default_cardbody_style),
    className="mt-3",
)

body = dbc.Container([
    dbc.Row([
            # Demo and Calculate buttons
            dbc.Col([
                    dbc.Button("Demo", id="demo-button", color="secondary",
                               size="lg", style={"padding-left": "30px", "padding-right": "30px"}),
                    dbc.Tooltip(
                        "Load ambient noise data provided by us.",
                        target="demo-button",
                    ),
                    ], md=1, ),
            dbc.Col([
                    dbc.Button("Calculate", id="calculate-button", color="primary",
                               size="lg"),
                    dbc.Tooltip(
                        "Perform HVSR calculation with the current file and settings.",
                        target="calculate-button",
                    ),
                    ], md=1, ),

            # Upload bar
            dbc.Col([
                    dcc.Upload(
                        id="upload-bar",
                        children=html.Div(
                            ["Drag and drop or click to select a 3-component miniSEED (*.miniseed or *.mseed) file to upload."]
                        ),
                        style={
                            "height": "50px",
                            "lineHeight": "45px",
                            "textAlign": "center",
                            "cursor": "pointer",
                            "background-color": "white",
                            "color": "black",
                            "border": "1px solid #dedede",
                            "border-radius": "8px",
                        },
                        multiple=False,
                    ),
                    ],
                    md=10,
                    style={"padding-bottom": "10px"}),
            ]),
    # Row for Settings and Figure
    dbc.Row([
        # Settings
        dbc.Col(
            [
                html.Div([
                         html.H5("Current File:", style={"display": "inline"}),
                         html.P(id="filename-reference"),
                         ], className="mb-2"),
                dbc.Tabs([
                    dbc.Tab(intro_tab, label="Intro"),
                    dbc.Tab(time_tab, label="Time"),
                    dbc.Tab(frequency_tab, label="Frequency"),
                    dbc.Tab(hv_tab, label="H/V"),
                    dbc.Tab(results_tab, label="Results",
                            id="results-tab", disabled=True),
                ], ),
            ],
            md=4,
        ),
        # Figure
        dbc.Col([
            dbc.Row([
                html.Div([html.Img(id='cur_plot', src='', style={"width": "90%", "text-align": "center"})],
                         id='plot_div')
            ]),
        ], md=5),
    ]),
    html.Div(id='hidden-file-contents', style={"display": "none"}),
], className="mt-4 mr-0", style={"margin-top": "0"}, fluid=True)

application = Flask(__name__)
app = dash.Dash(server=application, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.title = 'HVSRweb: A web application for HVSR processsing'
app.layout = html.Div(
    [
        html.Div([
            dcc.ConfirmDialog(
                id='no_file_warn',
                message='Please upload a file before clicking calculate.',
                displayed=False,
            )]),
        html.Div(
            id="banner",
            className="banner",
            children=[html.Img(src=app.get_asset_url("hvsrweb_logo.png")),
                      html.H2("HVSRweb: A web application for HVSR processing")]
        ),
        body,
        html.Footer(dbc.Container(html.Span(
            "HVSRweb v0.2.0 © 2019-2020 Dana M. Brannon & Joseph P. Vantassel", className="text-muted")), className="footer")
    ],
)


@app.callback(Output('no_file_warn', 'displayed'),
              [Input('calculate-button', 'n_clicks'),
               Input('filename-reference', 'children')])
def display_no_file_warn(n_clicks, filename):
    """Warn user if they click Calculate without a data file."""
    if filename == "No file has been uploaded." and n_clicks:
        return True
    return False


@app.callback(
    [Output('filename-reference', 'children'),
     Output('filename-reference', 'style'),
     Output('hidden-file-contents', 'children')],
    [Input('upload-bar', 'contents'),
     Input('upload-bar', 'filename'),
     Input('demo-button', 'n_clicks')])
def store_filename(contents, filename, n_clicks):
    """Display the uploaded filename and store its contents."""
    defaults = {"color": "gray", "padding": "4px",
                "margin-left": "4px", "display": "inline"}
    if filename:
        return [filename, {**defaults, "color": "#34a1eb"}, contents]
    if n_clicks != None:
        return ["File loaded, press calculate to continue.",
                {**defaults, "color": "#34a1eb", "font-weight": "bold"},
                "data/UT.STN11.A2_C150.miniseed"]
    else:
        return ["No file has been uploaded.", {**defaults}, "No contents."]

@app.callback(Output('bandpass-options', 'style'),
              [Input('butterworth-input', 'value')])
def set_bandpass_options_style(value):
    """Show/hide Bandpass Filter options depending on user input."""
    if value == "True":
        return {'display': 'block'}
    elif value == "False":
        return {'display': 'none'}

@app.callback(Output('rejection-options', 'style'),
              [Input('rejection_bool-input', 'value')])
def set_rejection_options_style(value):
    """Show/hide Window Rejection options depending on user input."""
    if value == "True":
        return {'display': 'block'}
    elif value == "False":
        return {'display': 'none'}

@app.callback(Output('azimuth-options', 'style'),
              [Input('method-input', 'value')])
def set_azimuth_options_style(value):
    """Show/hide Azimuth options depending on user input."""
    if value == "azimuth":
        return {'display': 'block'}
    else:
        return {'display': 'none'}

@app.callback(Output('rotate-options', 'style'),
              [Input('method-input', 'value')])
def set_azimuth_options_style(value):
    """Show/hide Rotate options depending on user input."""
    if value == "rotate":
        return {'display': 'block'}
    else:
        return {'display': 'none'}


def parse_data(contents, filename):
    """Parse uploaded data and return a Sensor3c object."""
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if filename.endswith("miniseed") or filename.endswith("mseed"):
            bytesio_obj = io.BytesIO(decoded)
            return hvsrpy.Sensor3c.from_mseed(bytesio_obj)
    except Exception as e:
        raise PreventUpdate


def fig_to_uri(in_fig, close_all=True, **save_args):
    """Save matplotlib figure for use as html.Img source and for downloading purposes."""
    out_img = io.BytesIO()
    in_fig.savefig(out_img, format='png', **save_args)
    if close_all:
        in_fig.clf()
        plt.close('all')
    out_img.seek(0)
    encoded = base64.b64encode(out_img.read()).decode(
        "ascii").replace("\n", "")
    return "data:image/png;base64,{}".format(encoded), encoded


def generate_table(hv, distribution_f0, method):
    """Generate output tables depending on user specifications."""
    head_style = {"font-size": "16px", "padding": "0.5px"}
    row_style = {"font-size": "16px", "padding": "0.5px"}

    def prep(x): return str(np.round(x, decimals=2))

    if method == "rotate":
        sub_letters = "AZ"
    elif method == "azimuth":
        sub_letters = u"\u03B1"
    elif method == "geometric-mean":
        sub_letters = "GM"
    elif method == "squared-average":
        sub_letters = "SA"
    else:
        sub_letters = ""

    f0 = hv.mean_f0_frq(distribution_f0)
    t0 = prep(1/f0) + "s"
    f0 = prep(f0)
    f0_std = prep(hv.std_f0_frq(distribution_f0))
    t0_std = f0_std

    if distribution_f0 == "log-normal":
        row0 = html.Tr([html.Td(""),
                        html.Td(html.Div(["LM"]), id="med"),
                        html.Td(html.Div([u"\u03c3", html.Sub('ln')]), id="std")],
                       style=head_style)
    elif distribution_f0 == "normal":
        row0 = html.Tr([html.Td(""),
                        html.Td(html.Div([u"\u03bc"]), id="med"),
                        html.Td(html.Div([u"\u03c3"]), id="std")],
                       style=head_style)
        t0 = "-"
        t0_std = "-"
    else:
        raise ValueError

    sub = f"0,{sub_letters}"
    row1 = html.Tr([html.Td(html.Div(["f", html.Sub(sub)]), id="f0"),
                    html.Td(f"{f0} Hz"),
                    html.Td(f0_std)],
                   style=row_style)

    row2 = html.Tr([html.Td(html.Div(["T", html.Sub(sub)]), id="t0"),
                    html.Td(f"{t0}"),
                    html.Td(t0_std)],
                   style=row_style)

    table = dbc.Table([html.Thead(row0), html.Tbody([row1, row2])],
                      bordered=True, hover=True, className="mb-0",
                      style={"padding": "0", "color": "#495057"})
    return table


def create_hrefs(hv, distribution_f0, distribution_mc, filename, rotate_flag):
    """Generate hrefs to be put inside hv-download and geopsy-download."""
    for filetype in ["hvsrpy", "geopsy"]:
        if filetype == "hvsrpy":
            data = "".join(hv._hvsrpy_style_lines(distribution_f0,
                                                  distribution_mc))
        else:
            if rotate_flag:
                pass
            else:
                data = "".join(hv._geopsy_style_lines(distribution_f0,
                                                      distribution_mc))
        bytesIO = io.BytesIO()
        bytesIO.write(bytearray(data, 'utf-8'))
        bytesIO.seek(0)
        encoded = base64.b64encode(bytesIO.read()).decode(
            "utf-8").replace("\n", "")
        bytesIO.close()
        if filetype == "hvsrpy":
            hvsrpy_downloadable = f'data:text/plain;base64,{encoded}'
            hvsrpy_name = filename.split('.miniseed')[0] + '.hv'
        else:
            if rotate_flag:
                geopsy_downloadable = "#"
                geopsy_name = "null.hv"
            else:
                geopsy_downloadable = f'data:text/plain;base64,{encoded}'
                geopsy_name = filename.split('.miniseed')[0] + '_geopsy.hv'
    return (hvsrpy_downloadable, hvsrpy_name, geopsy_downloadable, geopsy_name)


@app.callback(
    [Output('cur_plot', 'src'),
     Output('window-information-table', 'children'),
     Output('before-rejection-table', 'children'),
     Output('after-rejection-table', 'children'),
     Output('figure-download', 'href'),
     Output('figure-download', 'download'),
     Output('hv-download', 'href'),
     Output('hv-download', 'download'),
     Output('geopsy-download', 'href'),
     Output('geopsy-download', 'download'),
     Output('results-tab', 'disabled'),
     Output('tooltips', 'children'),
     Output('geopsy-button-tooltip', 'children'),
     Output('save_geopsy-button', 'disabled')],
    [Input('calculate-button', 'n_clicks')],
    [State('filename-reference', 'children'),
     State('hidden-file-contents', 'children'),
     State('butterworth-input', 'value'),
     State('flow-input', 'value'),
     State('fhigh-input', 'value'),
     State('forder-input', 'value'),
     State('minf-input', 'value'),
     State('maxf-input', 'value'),
     State('nf-input', 'value'),
     State('res_type-input', 'value'),
     State('windowlength-input', 'value'),
     State('width-input', 'value'),
     State('bandwidth-input', 'value'),
     State('method-input', 'value'),
     State('distribution_mc-input', 'value'),
     State('rejection_bool-input', 'value'),
     State('n-input', 'value'),
     State('distribution_f0-input', 'value'),
     State('n_iteration-input', 'value'),
     State('azimuth-input', 'value'),
     State('rotate-input', 'value')]
)
def update_timerecord_plot(calc_clicked, filename, contents,
                           filter_bool, flow, fhigh, forder,
                           minf, maxf, nf, res_type,
                           windowlength, width, bandwidth, method,
                           distribution_mc, rejection_bool, n, distribution_f0,
                           n_iteration, azimuth_degrees, azimuthal_interval):
    """Create figure and tables from user-uploaded file.

    Determine if user is requesting a demo or uploading a file. Run calculation and create figure and
    tables based on demo or uploaded file. Return the figure, tables, and download information.

    Parameters
    ----------
    calc_clicked : int
        Number of clicks (initiates function via callback).
    demo_clicked : int
        Number of clicks (initiates function via callback).
    filename : str
        The name of the user-uploaded file.
    contents : str
        The contents of the user-uploaded file (as a base64 encoded string.)
    filter_bool : str
        User-specified value.
    flow : float
        User-specified value.
    fhigh : float
        User-specified value.
    forder : float
        User-specified value.
    minf : float
        User-specified value.
    maxf: float
        User-specified value.
    nf : float
        User-specified value.
    res_type : str
        User-specified value.
    windowlength : float
        User-specified value.
    width : float
        User-specified value.
    bandwith : float
        User-specified value.
    method : str
        User-specified value.
    distribution_mc : str
        User-specified value.
    rejection_bool : str
        User-specified value.
    n : float
        User-specified value.
    distribution_f0 : str
        User-specified value.
    n_iteration : float
        User-specified value.

    Returns
    -------
    bool
        True if successful, False otherwise.

    .. _PEP 484:
        https://www.python.org/dev/peps/pep-0484/

    """

    if method == "rotate":
        azimuth = np.arange(0, 180, azimuthal_interval)
    elif method == "azimuth":
        azimuth = azimuth_degrees
    else:
        azimuth = None

    filter_bool = True if filter_bool == "True" else False
    rejection_bool = True if rejection_bool == "True" else False

    start = time.time()

    if (contents) and (contents != "No contents."):
        if filename == "File loaded, press calculate to continue.":
            sensor = hvsrpy.Sensor3c.from_mseed(contents)
            filename = "Demo file"
        else:
            sensor = parse_data(contents, filename)
        bp_filter = {"flag": filter_bool, "flow": flow,
                     "fhigh": fhigh, "order": forder}
        resampling = {"minf": minf, "maxf": maxf,
                      "nf": nf, "res_type": res_type}
        hv = sensor.hv(windowlength, bp_filter, width,
                       bandwidth, resampling, method, azimuth=azimuth)
        hv.meta["File Name"] = filename

        individual_width = 0.3
        median_width = 1.3

        # Azimuth Code
        if method == "rotate":
            if rejection_bool:
                hv.reject_windows(n=n, max_iterations=n_iteration,
                                  distribution_f0=distribution_f0,
                                  distribution_mc=distribution_mc)
                f0mc_after = hv.mc_peak_frq(distribution_mc)
                table_after_rejection = generate_table(hv, distribution_f0,
                                                       method)
            else:
                table_before_rejection = generate_table(hv, distribution_f0,
                                                        method)
                f0mc_before = hv.mc_peak_frq(distribution_mc)

            azimuths = [*hv.azimuths, 180.]
            mesh_frq, mesh_azi = np.meshgrid(hv.frq, azimuths)
            mesh_amp = hv.mean_curves(distribution=distribution_mc)
            mesh_amp = np.vstack((mesh_amp, mesh_amp[0]))
            end = time.time()
            print(f"Elapsed Time: {str(end-start)[0:4]} seconds")

            # Layout
            fig = plt.figure(figsize=(6, 5), dpi=150)
            gs = fig.add_gridspec(nrows=2, ncols=2, wspace=0.3,
                                  hspace=0.1, width_ratios=(1.2, 0.8))
            ax0 = fig.add_subplot(gs[0:2, 0:1], projection='3d')
            ax1 = fig.add_subplot(gs[0:1, 1:2])
            ax2 = fig.add_subplot(gs[1:2, 1:2])
            fig.subplots_adjust(bottom=0.21)

            # Settings
            individual_width = 0.3
            median_width = 1.3

            # 3D Median Curve
            ax = ax0
            ax.plot_surface(np.log10(mesh_frq), mesh_azi, mesh_amp, rstride=1,
                            cstride=1, cmap=cm.plasma, linewidth=0,
                            antialiased=False)
            for coord in list("xyz"):
                getattr(ax, f"w_{coord}axis").set_pane_color((1, 1, 1))
            ax.set_xticks(np.log10(np.array([0.01, 0.1, 1, 10, 100])))
            ax.set_xticklabels(["$10^{"+str(x)+"}$" for x in range(-2, 3)])
            ax.set_xlim(np.log10((0.1, 30)))
            ax.view_init(elev=30, azim=245)
            ax.dist = 12
            ax.set_yticks(np.arange(0, 180+45, 45))
            ax.set_ylim(0, 180)
            ax.set_xlabel("Frequency (Hz)")
            ax.set_ylabel("Azimuth (deg)")
            ax.set_zlabel("HVSR Amplitude")
            pfrqs, pamps = hv.mean_curves_peak(distribution=distribution_mc)
            pfrqs = np.array([*pfrqs, pfrqs[0]])
            pamps = np.array([*pamps, pamps[0]])
            ax.scatter(np.log10(pfrqs), azimuths, pamps*1.01,
                       marker="s", c="w", edgecolors="k", s=9)

            # 2D Median Curve
            ax = ax1
            contour = ax.contourf(mesh_frq, mesh_azi, mesh_amp,
                                  cmap=cm.plasma, levels=10)
            ax.set_xscale("log")
            ax.set_xticklabels([])
            ax.set_ylabel("Azimuth (deg)")
            ax.set_yticks(np.arange(0, 180+30, 30))
            ax.set_ylim(0, 180)
            divider = make_axes_locatable(ax)
            cax = divider.append_axes("top", size="5%", pad=0.05)
            fig.colorbar(contour, cax=cax, orientation="horizontal")
            cax.xaxis.set_ticks_position("top")

            ax.plot(pfrqs, azimuths, marker="s", color="w", linestyle="",
                    markersize=3, markeredgecolor="k",
                    label=r"$f_{0,mc,\alpha}$")

            # 2D Median Curve
            ax = ax2

            # Accepted Windows
            label = "Accepted"
            for amps in hv.amp:
                for amp in amps:
                    ax.plot(hv.frq, amp, color="#888888",
                            linewidth=individual_width, zorder=2, label=label)
                    label = None

            # Mean Curve
            label = r"$LM_{curve,AZ}$" if distribution_mc == "log-normal" else r"$Mean_{curve,AZ}$"
            ax.plot(hv.frq, hv.mean_curve(distribution_mc), color='k',
                    label=label, linewidth=median_width, zorder=4)

            # Mean +/- Curve
            label = r"$LM_{curve,AZ}$" + \
                " ± 1 STD" if distribution_mc == "log-normal" else r"$Mean_{curve,AZ}$"+" ± 1 STD"
            ax.plot(hv.frq, hv.nstd_curve(-1, distribution=distribution_mc),
                    color="k", linestyle="--", linewidth=median_width,
                    zorder=4, label=label)
            ax.plot(hv.frq, hv.nstd_curve(+1, distribution=distribution_mc),
                    color="k", linestyle="--", linewidth=median_width,
                    zorder=4)

            # Window Peaks
            label = r"$f_{0,i,\alpha}$"
            for frq, amp in zip(hv.peak_frq, hv.peak_amp):
                ax.plot(frq, amp, linestyle="", zorder=3, marker='o',
                        markersize=2.5, markerfacecolor="#ffffff",
                        markeredgewidth=0.5, markeredgecolor='k', label=label)
                label = None

            # Peak Mean Curve
            ax.plot(hv.mc_peak_frq(distribution_mc),
                    hv.mc_peak_amp(distribution_mc), linestyle="", zorder=5,
                    marker='D', markersize=4, markerfacecolor='#66ff33',
                    markeredgewidth=1, markeredgecolor='k',
                    label=r"$f_{0,mc,AZ}$")

            # f0,az
            label = r"$LM_{f0,AZ}$"+" ± 1 STD" if distribution_f0 == "log-normal" else "Mean " + \
                r"$f_{0,AZ}$"+" ± 1 STD"
            ymin, ymax = ax.get_ylim()
            ax.plot([hv.mean_f0_frq(distribution_f0)]*2, [ymin, ymax],
                    linestyle="-.", color="#000000", zorder=6)
            ax.fill([hv.nstd_f0_frq(-1, distribution_f0)]*2 + [hv.nstd_f0_frq(+1, distribution_f0)]*2, [ymin, ymax, ymax, ymin],
                    color="#ff8080", label=label, zorder=1)
            ax.set_ylim((ymin, ymax))

            # Limits and labels
            ax.set_xscale("log")
            ax.set_xlabel("Frequency (Hz)")
            ax.set_ylabel("HVSR Amplitude")
            for spine in ["top", "right"]:
                ax.spines[spine].set_visible(False)

            # Lettering
            xs, ys = [0.45, 0.85, 0.85], [0.81, 0.81, 0.47]
            for x, y, letter in zip(xs, ys, list("abc")):
                fig.text(x, y, f"({letter})", fontsize=12)

            # Legend
            handles, labels = [], []
            for ax in [ax2, ax1, ax0]:
                _handles, _labels = ax.get_legend_handles_labels()
                handles += _handles
                labels += _labels
            new_handles, new_labels = [], []
            for index in [0, 5, 1, 2, 3, 4, 6]:
                new_handles.append(handles[index])
                new_labels.append(labels[index])
            fig.legend(new_handles, new_labels, loc="lower center",
                       bbox_to_anchor=(0.47, 0), ncol=4, columnspacing=0.5,
                       handletextpad=0.4)
            end = time.time()

            # User is attempting to download the demo file
            if (filename == "Demo file"):
                filename = "hvsrpy_demo"
            out_url, encoded_image = fig_to_uri(fig)
            fig_name = filename.split('.miniseed')[0] + '.png'

            # Create hrefs to send to html.A links for download
            hrefs = create_hrefs(hv, distribution_f0, distribution_mc,
                                 filename, rotate_flag=True)

            if distribution_f0 == "log-normal":
                med_title = "Log-Normal Median"
                std_title = "Log-Normal Standard Deviation"
            else:
                med_title = "Mean"
                std_title = "Standard Deviation"
            tooltips = [dbc.Tooltip("Fundamental Site Frequency",
                                    id="f0_tt", target="f0"),
                        dbc.Tooltip("Fundamental Site Period",
                                    id="t0_tt", target="t0"),
                        dbc.Tooltip(med_title, id="med_tt", target="med"),
                        dbc.Tooltip(std_title, id="std_tt", target="std")]

            mc_style = {"font-size": "16px", "color": "#495057"}
            if distribution_mc == "normal":
                fmc_txt = "Peak frequency of mean curve, f"
            else:
                fmc_txt = "Peak frequency of median curve, f"

            if rejection_bool:
                stats = (html.P("Statistics After Rejection:", className="mb-1"),
                         table_after_rejection,
                         html.Div([fmc_txt, html.Sub("0,mc,AZ"),  ": ", str(f0mc_after)[:4]], style=mc_style, className="mb-2"))
            else:
                stats = (html.P("Statistics Without Rejection:", className="mb-1"),
                         table_before_rejection,
                         html.Div([fmc_txt, html.Sub("0,mc,AZ"),  ": ", str(f0mc_before)[:4]], style=mc_style, className="mb-2"))

            return (out_url,
                    ([]),
                    ([]),
                    stats,
                    out_url,
                    fig_name,
                    *hrefs,
                    False,
                    tooltips,
                    dbc.Tooltip(
                        "Geopsy does not offer a multi-azimuth output file.",
                        target="save_geopsy-button"),
                    True)

        # No rotate
        else:
            fig = plt.figure(figsize=(6, 6), dpi=150)
            gs = fig.add_gridspec(nrows=6, ncols=6)

            ax0 = fig.add_subplot(gs[0:2, 0:3])
            ax1 = fig.add_subplot(gs[2:4, 0:3])
            ax2 = fig.add_subplot(gs[4:6, 0:3])

            if rejection_bool:
                ax3 = fig.add_subplot(gs[0:3, 3:6])
                ax4 = fig.add_subplot(gs[3:6, 3:6])
            else:
                ax3 = fig.add_subplot(gs[1:4, 3:6])
                ax4 = False

            individual_width = 0.3
            median_width = 1.3
            for ax, title in zip([ax3, ax4], ["Before Rejection", "After Rejection"]):
                # Rejected Windows
                if title == "After Rejection":
                    if len(hv.rejected_window_indices):
                        label = "Rejected"
                        for amp in hv.amp[hv.rejected_window_indices]:
                            ax.plot(hv.frq, amp, color='#00ffff',
                                    linewidth=individual_width, zorder=2, label=label)
                            label = None

                # Accepted Windows
                label = "Accepted"
                for amp in hv.amp[hv.valid_window_indices]:
                    ax.plot(hv.frq, amp, color='#888888', linewidth=individual_width,
                            label=label if title == "Before Rejection" else "")
                    label = None

                # Window Peaks
                ax.plot(hv.peak_frq, hv.peak_amp, linestyle="", zorder=2,
                        marker='o', markersize=2.5, markerfacecolor="#ffffff",
                        markeredgewidth=0.5, markeredgecolor='k',
                        label="" if title == "Before Rejection" and rejection_bool else r"$f_{0,i}$")

                # Peak Mean Curve
                ax.plot(hv.mc_peak_frq(distribution_mc),
                        hv.mc_peak_amp(distribution_mc), linestyle="",
                        zorder=4, marker='D', markersize=4,
                        markerfacecolor='#66ff33', markeredgewidth=1,
                        markeredgecolor='k',
                        label="" if title == "Before Rejection" and rejection_bool else r"$f_{0,mc}$")

                # Mean Curve
                label = r"$LM_{curve}$" if distribution_mc == "log-normal" else "Mean Curve"
                ax.plot(hv.frq, hv.mean_curve(distribution_mc), color='k',
                        linewidth=median_width,
                        label="" if title == "Before Rejection" and rejection_bool else label)

                # Mean +/- Curve
                label = r"$LM_{curve}$" + \
                    " ± 1 STD" if distribution_mc == "log-normal" else "Mean ± 1 STD"
                ax.plot(hv.frq, hv.nstd_curve(-1, distribution_mc),
                        color='k', linestyle='--', linewidth=median_width, zorder=3,
                        label="" if title == "Before Rejection" and rejection_bool else label)
                ax.plot(hv.frq, hv.nstd_curve(+1, distribution_mc),
                        color='k', linestyle='--', linewidth=median_width, zorder=3)

                label = r"$LM_{f0}$" + \
                    " ± 1 STD" if distribution_f0 == "log-normal" else "Mean f0 ± 1 STD"
                ymin, ymax = ax.get_ylim()
                ax.plot([hv.mean_f0_frq(distribution_f0)]*2,
                        [ymin, ymax], linestyle="-.", color="#000000")
                ax.fill([hv.nstd_f0_frq(-1, distribution_f0)]*2 + [hv.nstd_f0_frq(+1, distribution_f0)]*2, [ymin, ymax, ymax, ymin],
                        color="#ff8080",
                        label="" if title == "Before Rejection" and rejection_bool else label)

                ax.set_ylim((ymin, ymax))
                ax.set_xscale('log')
                ax.set_xlabel("Frequency (Hz)")
                ax.set_ylabel("HVSR Ampltidue")

                if rejection_bool:
                    if title == "Before Rejection":
                        table_before_rejection = generate_table(
                            hv, distribution_f0, method)
                        c_iter = hv.reject_windows(n, max_iterations=n_iteration,
                                                   distribution_f0=distribution_f0, distribution_mc=distribution_mc)
                        # Create Window Information Table
                        row1 = html.Tr([html.Td("Window length"),
                                        html.Td(str(windowlength)+"s")], style={"font-size": "16px"})
                        row2 = html.Tr([html.Td("No. of iterations"), html.Td(
                            str(c_iter)+" of "+str(n_iteration)+" allowed.")], style={"font-size": "16px"})
                        f0mc_before = hv.mc_peak_frq(distribution_mc)

                    elif title == "After Rejection":
                        table_after_rejection = generate_table(
                            hv, distribution_f0, method)
                        fig.legend(ncol=4, loc='lower center',
                                   bbox_to_anchor=(0.51, 0), columnspacing=2)
                        rej_str = f"{len(hv.rejected_window_indices)} of {sensor.ns.n_windows}"
                        row3 = html.Tr([html.Td("No. of rejected windows"),
                                        html.Td(rej_str)],
                                       style={"font-size": "16px"})
                        window_table = [html.Tbody([row1, row2, row3])]
                        f0mc_after = hv.mc_peak_frq(distribution_mc)
                else:
                    f0mc_before = hv.mc_peak_frq(distribution_mc)
                    table_no_rejection = generate_table(
                        hv, distribution_f0, method)
                    # Create Window Information Table
                    row1 = html.Tr([html.Td("Window length"),
                                    html.Td(str(windowlength)+"s")])
                    row2 = html.Tr([html.Td("No. of windows"),
                                    html.Td(str(sensor.ns.n_windows))])
                    window_table = [html.Tbody([row1, row2])]

                    fig.legend(loc="upper center", bbox_to_anchor=(0.77, 0.4))
                    break
                ax.set_title(title)

            norm_factor = sensor.normalization_factor
            for ax, timerecord, name in zip([ax0, ax1, ax2], [sensor.ns, sensor.ew, sensor.vt], ["NS", "EW", "VT"]):
                ctime = timerecord.time
                amp = timerecord.amp/norm_factor
                ax.plot(ctime.T, amp.T, linewidth=0.2, color='#888888')
                ax.set_title(f"Time Records ({name})")
                ax.set_yticks([-1, -0.5, 0, 0.5, 1])
                ax.set_xlim(0, windowlength*timerecord.n_windows)
                ax.set_ylim(-1, 1)
                ax.set_xlabel('Time (s)')
                ax.set_ylabel('Normalized Amplitude')
                for window_index in hv.rejected_window_indices:
                    ax.plot(ctime[window_index], amp[window_index],
                            linewidth=0.2, color="cyan")

            if rejection_bool:
                axs = [ax0, ax3, ax1, ax4, ax2]
            else:
                axs = [ax0, ax3, ax1, ax2]

            for ax, letter in zip(axs, list("abcde")):
                ax.text(0.97, 0.97, f"({letter})", ha="right",
                        va="top", transform=ax.transAxes, fontsize=12)
                for spine in ["top", "right"]:
                    ax.spines[spine].set_visible(False)
            fig.tight_layout(h_pad=1, w_pad=2, rect=(0, 0.08, 1, 1))
            end = time.time()

            # User is attempting to download the demo file
            if (filename == "Demo file"):
                filename = "hvsrpy_demo"
            out_url, encoded_image = fig_to_uri(fig)
            fig_name = filename.split('.miniseed')[0] + '.png'

            # Create hrefs to send to html.A links for download
            hrefs = create_hrefs(hv, distribution_f0, distribution_mc,
                                 filename, rotate_flag=False)

            if distribution_f0 == "log-normal":
                med_title = "Log-Normal Median"
                std_title = "Log-Normal Standard Deviation"
            else:
                med_title = "Mean"
                std_title = "Standard Deviation"
            tooltips = [dbc.Tooltip("Fundamental Site Frequency",
                                    id="f0_tt", target="f0"),
                        dbc.Tooltip("Fundamental Site Period",
                                    id="t0_tt", target="t0"),
                        dbc.Tooltip(med_title, id="med_tt", target="med"),
                        dbc.Tooltip(std_title, id="std_tt", target="std")
                        ]

            mc_style = {"font-size": "16px", "color": "#495057"}
            if distribution_mc == "normal":
                fmc_txt = "Peak frequency of mean curve, f"
            else:
                fmc_txt = "Peak frequency of median curve, f"

            if rejection_bool:
                stats = ((html.P("Statistics Before Rejection:", className="mb-1"),
                          table_before_rejection,
                          html.Div([fmc_txt, html.Sub("0,mc"), ": ", str(f0mc_before)[:4]], style=mc_style, className="mb-2")),
                         (html.P("Statistics After Rejection:", className="mb-1"),
                          table_after_rejection,
                          html.Div([fmc_txt, html.Sub("0,mc"),  ": ", str(f0mc_after)[:4]], style=mc_style, className="mb-2")),
                         )
            else:
                stats = ((html.P("Statistics:", className="mb-1"),
                          table_no_rejection,
                          html.Div([fmc_txt, html.Sub("0,mc"),  ": ", str(f0mc_before)[:4]], style=mc_style, className="mb-2")),
                         ([]))

            return (out_url,
                    (html.P("Window Information:", className="mb-1"),
                     dbc.Table(window_table, bordered=True, hover=True, style={"color": "#495057"})),
                    *stats,
                    out_url,
                    fig_name,
                    *hrefs,
                    False,
                    tooltips,
                    dbc.Tooltip(
                        "Save results in the geopsy-style text format.",
                        target="save_geopsy-button"),
                    False)

    else:
        raise PreventUpdate


if __name__ == "__main__":
    app.run_server(debug=True)
