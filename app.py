import io
import os
import base64
import time

import hvsrpy
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output, State
from flask import Flask
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Agg')


# Style Settings
default_span_style = {"cursor": "context-menu",
                      "padding": "1px", "margin-top": "0em"}
default_p_style = {"margin-top": "1em", "margin-bottom": 0}

# Bootstrap Layout:
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
            dbc.Tooltip(
                "Length of each time window in seconds. "
                "For specific guidance on an appropriate window length refer to the SESAME (2004) guidelines.",
                target="windowlength-tooltip-target",
            ),
            dbc.Input(id="windowlength-input", type="number",
                      value=60, min=0, max=600, step=1),
            # html.P(""),

            # Width of cosine taper
            html.P([
                html.Span(
                    "Width of Cosine Taper:",
                    id="width-tooltip-target",
                    style=default_span_style,
                ),
            ], style=default_p_style),
            dbc.Tooltip(
                "Fraction of each time window to be cosine tapered. "
                "0.1 is recommended.",
                target="width-tooltip-target",
            ),
            dbc.Input(id="width-input", type="number",
                      value=0.1, min=0., max=1.0, step=0.1),
            # html.P(""),

            # Butterworth Filter
            html.P([
                html.Span(
                    "Apply Butterworth Filter?",
                    id="butterworth-tooltip-target",
                    style=default_span_style,
                ),
            ], style=default_p_style),
            dbc.Tooltip(
                "Select whether a Butterworth bandpass filter is applied to the time-domain singal. "
                "Geopsy does not apply a bandpass filter.",
                target="butterworth-tooltip-target",
            ),
            dbc.Select(
                id="butterworth-input",
                options=[
                    {"label": "Yes", "value": "True"},
                    {"label": "No", "value": "False"},
                ], value="False"),
            # html.P(""),

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
                # html.P(""),

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
                # html.P(""),

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
                # html.P(""),
                # html.Hr(style={"border-top": "0.5px solid #bababa"}),
            ], className="ml-2 mr-0", id="bandpass-options"),
        ]),
    className="mt-3",
)

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
            dbc.Tooltip(
                "Bandwidth coefficient (b) for Konno and Ohmachi (1998) smoothing, "
                "40 is recommended.",
                target="bandwidth-tooltip-target",
            ),
            dbc.Input(id="bandwidth-input", type="number",
                      value=40, min=0, max=600, step=1),
            # html.P(""),
            # html.Hr(style={"border-top": "1px solid #bababa"}),

            html.P("Resampling:"),
            dbc.Container([
                # Resampling: Minumum Frequency
                html.P([
                    html.Span(
                        "Minimum Frequency (Hz):",
                        id="minf-tooltip-target",
                        style=default_span_style,
                    ),
                ], style=default_p_style),
                dbc.Tooltip(
                    "Minimum frequency considered when resampling.",
                    target="minf-tooltip-target",
                ),
                dbc.Input(id="minf-input", type="number",
                          value=0.2, min=0.2, max=10, step=0.1),
                # html.P(""),

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
                # html.P(""),

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
                          value=512, min=2, max=10000, step=1),
                # html.P(""),

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
        ]),
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
            dbc.Tooltip(
                "Geometric-Mean is recommended. "
                "Geopsy uses the Squared-Average. ",
                target="method-tooltip-target",
            ),
            dbc.Select(
                id="method-input",
                options=[
                    {"label": "Squared-Average", "value": "squared-average"},
                    {"label": "Geometric-Mean", "value": "geometric-mean"},
                ],
                value="geometric-mean",
            ),
            # html.P(" "),

            # Distribution of f0
            html.P([
                html.Span(
                    ["Distribution of ", html.Div(['f', html.Sub('0')], style={
                                                  "display": "inline"}), ":"],
                    id="distribution_f0-tooltip-target",
                    style=default_span_style,
                ),
            ], style=default_p_style),
            dbc.Tooltip(
                "Lognormal is recommended. "
                "Geopsy uses Normal.",
                target="distribution_f0-tooltip-target",
            ),
            dbc.Select(
                id="distribution_f0-input",
                options=[
                    {"label": "Lognormal", "value": "log-normal"},
                    {"label": "Normal", "value": "normal"},
                ], value='log-normal'),
            # html.P(""),

            # Distribution of Median Curve
            html.P([
                html.Span(
                    "Distribution of Median Curve:",
                    id="distribution_mc-tooltip-target",
                    style=default_span_style,
                ),
            ], style=default_p_style),
            dbc.Tooltip(
                "Lognormal is recommended. "
                "Geopsy uses Lognormal",
                target="distribution_mc-tooltip-target",
            ),
            dbc.Select(
                id="distribution_mc-input",
                options=[
                    {"label": "Lognormal", "value": "log-normal"},
                    {"label": "Normal", "value": "normal"},
                ], value="log-normal"),
            # html.P(""),

            # Frequency-Domain Window-Rejection Algorithm
            html.P([
                html.Span(
                    "Apply Frequency-Domain Window-Rejection?",
                    id="rejection_bool-tooltip-target",
                    style=default_span_style,
                ),
            ], style=default_p_style),
            dbc.Tooltip(
                "Select whether the frequency-domain window-rejection algorithm proposed "
                "by Cox et al. (2020) is applied. Geopsy does not offer this functionality.",
                target="rejection_bool-tooltip-target",
            ),
            dbc.Select(
                id="rejection_bool-input",
                options=[
                    {"label": "Yes", "value": "True"},
                    {"label": "No", "value": "False"},
                ], value="True"),
            # html.P(""),

            dbc.Container([
                # Number of Standard Deviations
                html.P([
                    html.Span(
                        "Number of Standard Deviations (n):",
                        id="n-tooltip-target",
                        style=default_span_style,
                    ),
                ], style=default_p_style),
                dbc.Tooltip(
                    "Number of standard deviations to consider during rejection. "
                    "Smaller values will tend to reject more windows than larger values. "
                    "2 is recommended.",
                    target="n-tooltip-target",
                ),
                dbc.Input(id="n-input", type="number",
                          value=2, min=1, max=4, step=0.5),
                # html.P(""),

                # Maximum Number of Iterations
                html.P([
                    html.Span(
                        "Maximum Number of Allowed Iterations:",
                        id="n_iteration-tooltip-target",
                        style=default_span_style,
                    ),
                ], style=default_p_style),
                dbc.Tooltip(
                    "Maximum number of iterations of the rejection algorithm. "
                    "50 is recommended.",
                    target="n_iteration-tooltip-target",
                ),
                dbc.Input(id="n_iteration-input", type="number",
                          value=50, min=5, max=75, step=1),
                # html.P(""),
            ],
                className="ml-2 mr-0",
                id="rejection-options"),
        ]),
    className="mt-3",
)

button_style = {"width": "100%"}
results_tab = dbc.Card(
    dbc.CardBody(
        [
            dbc.Row([
                dbc.Col([
                    html.A(
                        dbc.Button("Save Figure", color="primary",
                                   id="save_figure-button", style=button_style),
                        id='figure-download', download="", href="", target="_blank"),
                ]),
                dbc.Col([
                    html.A(
                        dbc.Button("Save as hvsrpy", color="primary",
                                   id="save_hvsrpy-button", style=button_style),
                        id="hv-download", download="", href="", target="_blank"),
                    dbc.Tooltip(
                        "Save results in the hvsrpy-style text format.",
                        target="save_hvsrpy-button"),
                ]),
                dbc.Col([
                    html.A(
                        dbc.Button("Save as geopsy", color="primary",
                                   id="save_geopsy-button", style=button_style),
                        id="geopsy-download", download="", href="", target="_blank"),
                    dbc.Tooltip(
                        "Save results in the geopsy-style text format.",
                        target="save_geopsy-button"),
                ]),
            ]),

            # html.P(""),
            html.Div(id='window-information-table',
                     style={"font-size": "12px"}),
            html.Div(id='before-rejection-table',
                     style={"font-size": "12px"}),
            # html.P(""),
            html.Div(id='after-rejection-table',
                     style={"font-size": "12px"}),
        ]),
    className="mt-3",
)

body = dbc.Container([
    # Row for Upload Bar and Calc/Demo Buttons
    dbc.Row([
            # Column1_1
            dbc.Col([
                    dcc.Upload(
                        id="upload-bar",
                        children=html.Div(
                            ["Drag and drop or click to select a file to upload."]
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
                        # Allow multiple files to be uploaded
                        # TODO (jpv): Changing from True to False will change back to True at some point.
                        multiple=False,
                    ),
                    ],
                    md=10,
                    style={"padding-bottom": "10px", }),
            # Column2_2
            dbc.Col([
                    dbc.Button("Calculate", id="calculate-button", color="primary",
                               size="lg"),
                    dbc.Tooltip(
                        "Perform HVSR calculation with the current file and settings",
                        target="calculate-button",
                    ),
                    ], md=1, ),
            dbc.Col([
                    dbc.Button("Demo", id="demo-button", color="secondary",
                               size="lg", className="ml-1"),
                    dbc.Tooltip(
                        "Load a file supplied by us!",
                        target="demo-button",
                    ),
                    ], md=1, ),
            ]),
    # Row for Current File, Settings, and Figure
    dbc.Row([
        # SETTINGS
        dbc.Col(
            [
                html.Div([
                         html.H5("Current File:", style={"display": "inline"}),
                         html.P(id="filename-reference"),
                         ], className="mb-2"),
                dbc.Tabs([
                    dbc.Tab(time_tab, label="Time"),
                    dbc.Tab(frequency_tab, label="Frequency"),
                    dbc.Tab(hv_tab, label="H/V"),
                    dbc.Tab(results_tab, label="Results",
                            id="results-tab", disabled=True),
                ]),
            ],
            md=4,
        ),
        # FIGURE
        dbc.Col([
            dbc.Row([
                html.Div([html.Img(id='cur_plot', src='', style={
                         "width": "95%"})], id='plot_div')
            ]),
        ], md=5),
    ]),

    html.Div(id='hidden-file-contents', style={"display": "none"}),
], className="mt-4 mr-0", style={"margin-top":"0"}, fluid=True)

server = Flask(__name__)
app = dash.Dash(server=server, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.title = 'hvsrpy-app'
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
            children=[html.Img(src=app.get_asset_url("hvsr_app_logo.png"))],
        ),
        body,
        html.Footer("© 2019-2020 Dana M. Brannon & Joseph P. Vantassel")
    ],
)


@app.callback(Output('no_file_warn', 'displayed'),
              [Input('calculate-button', 'n_clicks'),
               Input('filename-reference', 'children')])
def display_no_file_warn(n_clicks, filename):
    """Warn user if they click CALCULATE without having uploaded a data file."""
    if (filename == "No file has been uploaded.") and (n_clicks):
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
    if filename:
        return [filename, {"color": "#34a1eb", "padding": "4px", "margin-left": "4px", "display": "inline"}, contents]
    if n_clicks != None:
        return ["Demo file loaded, press calculate to continue!", {"color": "#34a1eb", "padding": "4px", "margin-left": "4px", "display": "inline"}, "data/UT.STN12.A2_C150.miniseed"]
    else:
        return ["No file has been uploaded.", {"color": "gray", "padding": "4px", "margin-left": "4px", "display": "inline"}, "No contents."]

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


def parse_data(contents, filename):
    """Parse uploaded data and return a Sensor3c object."""
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'miniseed' in filename:
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


def generate_table(hv, distribution_f0):
    """Generate output tables depending on user specifications."""
    head_style = {"font-size": "16px", "padding":"0.5px"}
    row_style = {"font-size": "16px", "padding":"0.5px"}
    # td_style = {"padding":"0px"}

    if distribution_f0 == "log-normal":
        row0 = html.Tr([
            html.Td(""),
            html.Td(html.Div(["LM"]),
                    id="log_median"),
                    # style=td_style),
            html.Td(html.Div([u"\u03c3", html.Sub('ln')]),
                    id="log_std"),
                    # style=td_style),
            dbc.Tooltip("Log-Normal Median",
                        target="log_median"),
            dbc.Tooltip("Log-Normal Standard Deviation",
                        target="log_std"),
        ], style=head_style)

        row1 = html.Tr([
            html.Td(html.Div(['f', html.Sub('0')]),
                    id="f0_lognormal"),
                    # style=td_style),
            html.Td(str(hv.mean_f0_frq(distribution_f0))[:4]+" Hz"),
                    # style=td_style),
            html.Td(str(hv.std_f0_frq(distribution_f0))[:4]),
                    # style=td_style),
            dbc.Tooltip("Fundamental Site Frequency",
                        target="f0_lognormal"),
        ], style=row_style)

        row2 = html.Tr([
            html.Td(html.Div(['T', html.Sub('0')]),
                    id="T0_lognormal"),
                    # style=td_style),
            html.Td(str((1/hv.mean_f0_frq(distribution_f0)))[:4]+" s"),
                    # style=td_style),
            html.Td(str(hv.std_f0_frq(distribution_f0))[:4]),
                    # style=td_style),
            dbc.Tooltip("Fundamental Site Period",
                        target="T0_lognormal"),
        ], style=row_style)

    elif distribution_f0 == "normal":
        row0 = html.Tr([
            html.Td(""),
            html.Td(html.Div([u"\u03bc"]),
                    id="mean"),
            html.Td(html.Div([u"\u03c3"]),
                    id="std"),
            dbc.Tooltip("Mean",
                        target="mean"),
            dbc.Tooltip("Standard Deviation",
                        target="std"),
        ], style=head_style)

        row1 = html.Tr([
            html.Td(html.Div(['f', html.Sub('0')]),
                    id="f0_normal"),
            html.Td(str(hv.mean_f0_frq(distribution_f0))[:4]+" Hz"),
            html.Td(str(hv.std_f0_frq(distribution_f0))[:4]),
            dbc.Tooltip("Fundamental Site Frequency",
                        target="f0_normal"),
        ], style=row_style)

        row2 = html.Tr([
            html.Td(html.Div(['T', html.Sub('0')]),
                    id="T0_normal"),
            html.Td("-"),
            html.Td("-"),
            dbc.Tooltip("Fundamental Site Period - Noncomputable",
                        target="T0_normal"),
        ], style=row_style)

    table_body = [html.Tbody([row1, row2])]
    table = dbc.Table([html.Thead(row0)] + table_body, bordered=True,
                      hover=True, className="mb-0", style={"padding":"0"})
    return table


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
     Output('results-tab', 'disabled')],
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
     State('n_iteration-input', 'value')]
)
def update_timerecord_plot(calc_clicked, filename, contents, filter_bool, flow, fhigh, forder, minf, maxf, nf, res_type,
                           windowlength, width, bandwidth, method, distribution_mc, rejection_bool, n, distribution_f0, n_iteration):
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

    filter_bool = True if filter_bool == "True" else False
    rejection_bool = True if rejection_bool == "True" else False

    start = time.time()

    if (contents) and (contents != "No contents."):
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

        if filename == "Demo file loaded, press calculate to continue!":
            sensor = hvsrpy.Sensor3c.from_mseed(contents)
            filename = "Demo file"
        else:
            sensor = parse_data(contents, filename)
        bp_filter = {"flag": filter_bool, "flow": flow,
                     "fhigh": fhigh, "order": forder}
        resampling = {"minf": minf, "maxf": maxf,
                      "nf": nf, "res_type": res_type}
        hv = sensor.hv(windowlength, bp_filter, width,
                       bandwidth, resampling, method)
        # TODO (dmb): Fix this so it doesn't need a monkey patch
        hv.meta["File Name"] = filename

        individual_width = 0.3
        median_width = 1.3

        for ax, title in zip([ax3, ax4], ["Before Rejection", "After Rejection"]):
            # Rejected Windows
            if title == "After Rejection":
                if hv.rejected_window_indices.size > 0:
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
                    marker='o', markersize=2.5, markerfacecolor="#ffffff", markeredgewidth=0.5, markeredgecolor='k',
                    label="" if title == "Before Rejection" and rejection_bool else r"$f_{0,i}$")

            # Peak Mean Curve
            ax.plot(hv.mc_peak_frq(distribution_mc), hv.mc_peak_amp(distribution_mc), linestyle="", zorder=4,
                    marker='D', markersize=4, markerfacecolor='#66ff33', markeredgewidth=1, markeredgecolor='k',
                    label="" if title == "Before Rejection" and rejection_bool else r"$f_{0,mc}$")

            # Mean Curve
            label = r"$LM_{curve}$" if distribution_mc == "log-normal" else "Mean Curve"
            ax.plot(hv.frq, hv.mean_curve(distribution_mc), color='k', linewidth=median_width,
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
                        hv, distribution_f0)
                    c_iter = hv.reject_windows(n, max_iterations=n_iteration,
                                               distribution_f0=distribution_f0, distribution_mc=distribution_mc)
                    # Create Window Information Table
                    row1 = html.Tr([html.Td("Window length"),
                                    html.Td(str(windowlength)+"s")], style={"font-size": "16px"})
                    row2 = html.Tr([html.Td("No. of iterations"), html.Td(
                        str(c_iter)+" of "+str(n_iteration)+" allowed.")], style={"font-size": "16px"})

                elif title == "After Rejection":
                    table_after_rejection = generate_table(hv, distribution_f0)
                    fig.legend(ncol=4, loc='lower center',
                               bbox_to_anchor=(0.51, 0), columnspacing=2)
                    row3 = html.Tr([html.Td("No. of rejected windows"), html.Td(
                        str(len(hv.rejected_window_indices)) + " of " + str(sensor.ns.n_windows))], style={"font-size": "16px"})
                    window_table = [html.Tbody([row1, row2, row3])]
            else:
                table_no_rejection = generate_table(hv, distribution_f0)
                # Create Window Information Table
                row1 = html.Tr([html.Td("Window length"),
                                html.Td(str(windowlength)+"s")])
                row2 = html.Tr([html.Td("No. of windows"),
                                html.Td(str(sensor.ns.n_windows))])
                window_table = [html.Tbody([row1, row2])]

                fig.legend(loc="upper center", bbox_to_anchor=(0.75, 0.3))
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

        save_figure = fig
        fig.tight_layout(h_pad=1, w_pad=2, rect=(0, 0.08, 1, 1))
        save_figure.tight_layout(h_pad=1, w_pad=2, rect=(0, 0.08, 1, 1))
        end = time.time()

        # User is attempting to download the demo file
        if (filename == "Demo file"):
            filename = "hvsrpy_demo"
        out_url, encoded_image = fig_to_uri(fig)
        fig_name = filename.split('.miniseed')[0] + '.png'

        # Create hrefs to send to html.A links for download
        for filetype in ["hvsrpy", "geopsy"]:
            if filetype == "hvsrpy":
                data = "".join(hv._hvsrpy_style_lines(
                    distribution_f0, distribution_mc))
            else:
                data = "".join(hv._geopsy_style_lines(
                    distribution_f0, distribution_mc))
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
                geopsy_downloadable = f'data:text/plain;base64,{encoded}'
                geopsy_name = filename.split('.miniseed')[0] + '_geopsy.hv'

        table_label_style = {"margin-top": "0.5em", "margin-bottom": "0.25em"}

        if rejection_bool:
            return (out_url,
                    (html.H6("Window Information:"), dbc.Table(window_table,
                                                               bordered=True,
                                                               hover=True)),
                    (html.H6("Statistics Before Rejection:",
                             style=table_label_style),
                     table_before_rejection),
                    (html.H6("Statistics After Rejection:",
                             style=table_label_style),
                     table_after_rejection),
                    out_url,
                    fig_name,
                    hvsrpy_downloadable,
                    hvsrpy_name,
                    geopsy_downloadable,
                    geopsy_name,
                    False)
        else:
            return (out_url,
                    (html.H6("Window Information:"), dbc.Table(window_table,
                                                               bordered=True)),
                    (html.H6("Statistics:", style=table_label_style),
                     table_no_rejection),
                    ([]),
                    out_url,
                    fig_name,
                    hvsrpy_downloadable,
                    hvsrpy_name,
                    geopsy_downloadable,
                    geopsy_name,
                    False)
    else:
        raise PreventUpdate


if __name__ == "__main__":
    # app.run_server(debug=True)#, port=8888)
    server.run("0.0.0.0")
