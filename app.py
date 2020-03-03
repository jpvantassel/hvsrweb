import base64
from io import BytesIO
import os
from urllib.parse import quote as urlquote
import json

from flask import Flask, send_from_directory
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

import dash_table
import pandas as pd
import datetime
import io
import plotly.graph_objs as go
from dash.exceptions import PreventUpdate
# import plotly.matplotlylib.renderer.PlotlyRenderer as PlotlyRenderer
# import plotly.matplotlylib.mplexporter as mplexporter

from plotly.matplotlylib import mplexporter, PlotlyRenderer

from plotly.tools import mpl_to_plotly
import plotly

# print(dir(plotly))


# HVSRPY IMPORTS
import hvsrpy
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import time

import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Style Settings
default_style = {"cursor": "context-menu", "padding":"5px"}

# Bootstrap Layout:
# TIME DOMAIN SETTINGS TAB
tab1_content = dbc.Card(
    dbc.CardBody(
        [
            # Window Length
            html.P([
                html.Span(
                    "Window Length (s):",
                    id="windowlength-tooltip-target",
                    style=default_style,
                ),
            ]),
            dbc.Tooltip(
                "Length of each time window in seconds. "
                "For specific guidance on an appropriate window length refer to the SESAME (2004) guidelines.",
                target="windowlength-tooltip-target",
            ),
            dbc.Input(id="windowlength-input", type="number", value=60, min=0, max=600, step=1),
            html.P(""),

            # Width of cosine taper
            html.P([
                html.Span(
                    "Width of Cosine Taper:",
                    id="width-tooltip-target",
                    style=default_style,
                ),
            ]),
            dbc.Tooltip(
                "Fraction of each time window to be cosine tapered. "
                "0.1 is recommended.",
                target="width-tooltip-target",
            ),
            dbc.Input(id="width-input", type="number", value=0.1, min=0., max=1.0, step=0.1),
            html.P(""), # used for styling purposes only

            # Butterworth Filter
            html.P([
                html.Span(
                    "Apply Butterworth Filter?",
                    id="butterworth-tooltip-target",
                    style=default_style,
                ),
            ]),
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
            html.P(""), # used for styling purposes only

            dbc.Container([
                # Butterworth Filter: Low Frequency
                html.P([
                    html.Span(
                        "Low-cut Frequency (Hz):",
                        id="flow-tooltip-target",
                        style=default_style,
                    ),
                ]),
                dbc.Tooltip(
                    "Frequencies below that specified are filtered.",
                    target="flow-tooltip-target",
                ),
                dbc.Input(id="flow-input", type="number", value=0.1, min=0, max=1000, step=0.01),
                html.P(""), # used for styling purposes only

                # Butterworth Filter: High Frequency
                html.P([
                    html.Span(
                        "High-cut Frequency (Hz):",
                        id="fhigh-tooltip-target",
                        style=default_style,
                    ),
                ]),
                dbc.Tooltip(
                    "Frequencies above that specified are filtered.",
                    target="fhigh-tooltip-target",
                ),
                dbc.Input(id="fhigh-input", type="number", value=30, min=0, max=600, step=1),
                html.P(""), # used for styling purposes only

                # Butterworth Filter: Filter Order
                html.P([
                    html.Span(
                        "Filter Order:",
                        id="forder-tooltip-target",
                        style=default_style,
                    ),
                ]),
                dbc.Tooltip(
                    "Order of Butterworth filter, 5 is recommended.",
                    target="forder-tooltip-target",
                ),
                dbc.Input(id="forder-input", type="number", value=5, min=0, max=600, step=1),
                html.P(""), # used for styling purposes only
                html.Hr(style={"border-top": "0.5px solid #bababa"}),# used for styling purposes only
                ], className="ml-2 mr-0", id="bandpass-options"),
    ]),
    className="mt-3",
)

# FREQUENCY DOMAIN SETTINGS TAB
tab2_content = dbc.Card(
    dbc.CardBody(
        [
            # Bandwidth
            html.P([
                html.Span(
                    "Konno and Ohmachi Smoothing Coefficient:",
                    id="bandwidth-tooltip-target",
                    style=default_style,
                ),
            ]),
            dbc.Tooltip(
                "Bandwidth coefficient (b) for Konno and Ohmachi (1998) smoothing, "
                "40 is recommended.",
                target="bandwidth-tooltip-target",
            ),
            dbc.Input(id="bandwidth-input", type="number", value=40, min=0, max=600, step=1),
            html.P(""),
            # html.Hr(style={"border-top": "1px solid #bababa"}),

            html.P("Resampling:"),
            dbc.Container([
                # Resampling: Minumum Frequency
                html.P([
                    html.Span(
                        "Minimum Frequency:",
                        id="minf-tooltip-target",
                        style=default_style,
                    ),
                ]),
                dbc.Tooltip(
                    "Minimum frequency considered when resampling.",
                    target="minf-tooltip-target",
                ),
                dbc.Input(id="minf-input", type="number", value=0.2, min=0.2, max=10, step=0.1),
                html.P(""),

                # Resampling: Maximum Frequency
                html.P([
                    html.Span(
                        "Maximum Frequency:",
                        id="maxf-tooltip-target",
                        style=default_style,
                    ),
                ]),
                dbc.Tooltip(
                    "Maximum frequency considered when resampling.",
                    target="maxf-tooltip-target",
                ),
                dbc.Input(id="maxf-input", type="number", value=20, min=1, max=100, step=1),
                html.P(""),

                # Resampling: Number of Frequencies
                html.P([
                    html.Span(
                        "Number of Frequency Points:",
                        id="nf-tooltip-target",
                        style={"cursor": "context-menu", "padding":"5px"},
                    ),
                ]),
                dbc.Tooltip(
                    "Number of frequency points after resampling.",
                    target="nf-tooltip-target",
                ),
                dbc.Input(id="nf-input", type="number", value=512, min=2, max=10000, step=1),
                html.P(""),

                # Resampling: Type
                html.P([
                    html.Span(
                        "Type:",
                        id="res_type-tooltip-target",
                        style=default_style,
                    ),
                ]),
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

# H/V SETTINGS TAB
tab3_content = dbc.Card(
    dbc.CardBody(
        [
            # Method for combining
            html.P([
                html.Span(
                    "Method for Combining the Horizontal Components:",
                    id="method-tooltip-target",
                    style=default_style,
                ),
            ]),
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
            html.P(" "),

            # Distribution of f0
            html.P([
                html.Span(
                    "Distribution of f0:",
                    id="distribution_f0-tooltip-target",
                    style=default_style,
                ),
            ]),
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
            html.P(""),

            # Distribution of Median Curve
            html.P([
                html.Span(
                    "Distribution of Median Curve:",
                    id="distribution_mc-tooltip-target",
                    style=default_style,
                ),
            ]),
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
            html.P(""),

            # Frequency-Domain Window-Rejection Algorithm
            html.P([
                html.Span(
                    "Apply Frequency-Domain Window-Rejection?",
                    id="rejection_bool-tooltip-target",
                    style=default_style,
                ),
            ]),
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
            html.P(""),

            dbc.Container([
                # Number of Standard Deviations
                html.P([
                    html.Span(
                        "Number of Standard Deviations (n):",
                        id="n-tooltip-target",
                        style=default_style,
                    ),
                ]),
                dbc.Tooltip(
                    "Number of standard deviations to consider during rejection. "
                    "Smaller values will tend to reject more windows than larger values. "
                    "2 is recommended.",
                    target="n-tooltip-target",
                ),
                dbc.Input(id="n-input", type="number", value=2, min=1, max=4, step=0.5),
                html.P(""),

                # Maximum Number of Iterations
                html.P([
                    html.Span(
                        "Maximum Number of Allowed Iterations:",
                        id="n_iteration-tooltip-target",
                        style=default_style,
                    ),
                ]),
                dbc.Tooltip(
                    "Maximum number of iterations of the rejection algorithm. "
                    "50 is recommended.",
                    target="n_iteration-tooltip-target",
                ),
                dbc.Input(id="n_iteration-input", type="number", value=50, min=5, max=75, step=1),
                html.P(""),
            ],
            className="ml-2 mr-0",
            id="rejection-options"),
    ]),
    className="mt-3",
)

body = dbc.Container([
        # Row1
        dbc.Row([
            # Column1_1
            dbc.Col([
                    # html.H2("Graph"),
                    dcc.Upload(
                        id="upload-bar",
                        children=html.Div(
                            ["Drag and drop or click to select a file to upload."]
                        ),
                        style={
                            #"width": "100%",
                            "height": "50px",
                            "lineHeight": "45px",
                            "textAlign": "center",
                            "cursor": "pointer",
                            #"margin": "10px",
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
                md=11,
            style={"padding-bottom": "20px",}),
            # Column2_2
            dbc.Col([
                    dbc.Button("Calculate", id="calculate-button", outline=True, color="success", size="lg"),
                ], md=1, ),
        ]),
        # Row1.5
        dbc.Row([
            html.H4("Current File:"),
            html.P(id="filename-reference")
            #html.Div(id="filename-reference", style={"padding":"4px", "margin-left":"4px"})
        ], className="mt-1", style={"margin-left":"0px"}),
        # Row2
        dbc.Row([
                # Column2_1
                dbc.Col(
                    [
                        html.H4("Settings"),
                        dbc.Tabs([
                            dbc.Tab(tab1_content, label="Time Domain"),
                            dbc.Tab(tab2_content, label="Frequency Domain"),
                            dbc.Tab(tab3_content, label="H/V Options")
                        ]),
                        # dbc.Button("View details", color="secondary"),
                        html.P(""),
                        dbc.Button("Save Figure", color="primary", id="save_figure-button", className="mr-2"),
                        html.Div(id="hidden-figure-div", style={"display":"none"}),
                        html.Div(id="save-figure-status"),
                        # dbc.Button("Save .hv", color="dark", id="save_hv-button"),
                        # html.Div(id="intermediate-value"),
                        # html.P(id="figure_status"),
                        #dbc.Row([
                        #    html.Div(id="stat-table"),
                        #], className="mt-2 ml-2"),
                    ],
                    md=3,
                ),
                # Column2_2
                dbc.Col([
                    # Row2_2_1
                    dbc.Row([
                        html.Div([html.Img(id = 'cur_plot', src = '', style={"width":"50%"})], id='plot_div')#id="figure-div")
                    ]),
                ], md=6)
            ]),
        dbc.Row([
            dbc.Col([
                html.Div(id='window-information-table'),
            ], md=4),
            dbc.Col([
                html.Div(id='before-rejection-table'),
            ], md=4),
            dbc.Col([
                html.Div(id='after-rejection-table'),
            ], md=4),
            #html.Div(id='rejection-tables')#id="figure-div")
        ], className="mt-5 ml-4 mb-2", id="tables"),
        html.Div(id='hidden-file-contents', style={"display":"none"}),
    ], className="mt-4 mr-0", fluid=True)

# TODO (jpv): Need to change the below lines when deplyed on Heroku.
UPLOAD_DIRECTORY = "/project/app_uploaded_files"
if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

# Normally, Dash creates its own Flask server internally. By creating our own,
# we can create a route for downloading files directly:
server = Flask(__name__)
app = dash.Dash(server=server, external_stylesheets=[dbc.themes.BOOTSTRAP])
@server.route("/download/<path:path>")
def download(path):
    """Serve a file from the upload directory."""
    return send_from_directory(UPLOAD_DIRECTORY, path, as_attachment=True)
'''
INSTEAD OF:
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
'''

app.layout = html.Div(
    [
        body,
    ],
    style={"max-width":"97%"},
)


@app.callback(
    [Output('filename-reference', 'children'),
    Output('filename-reference', 'style'),
    Output('hidden-file-contents', 'children')],
    [Input('upload-bar', 'contents'),
    Input('upload-bar', 'filename')])
def store_filename(contents, filename):
    if filename:
        return [filename, {"color":"#34a1eb", "padding":"4px", "margin-left":"4px"}, contents]
    else:
        return ["No file has been uploaded.", {"color":"gray", "padding":"4px", "margin-left":"4px"}, "No contents."]
'''
@app.callback(
    Output('spinner', 'children'),
    [Input('calculate-button', 'n_clicks')])
def update_spinner(n_clicks):
    if n_clicks == None:
        return html.P("")
    else:
        return dbc.Spinner(color="success")
'''
@app.callback(
    Output('save-figure-status', 'children'),
    [Input('save_figure-button', 'n_clicks'),
     Input('hidden-figure-div', 'children'),
     Input('filename-reference', 'children')])
def save_figure(n_clicks, image_data, filename):
    if n_clicks == None:
        return html.P("Nothing saved yet.")
    else:
        encoded_image_bytes = bytearray(image_data[0], 'utf-8')
        img_title = filename.split('.miniseed')[0] + '_figure.png'
        with open(img_title, "wb") as fh:
            fh.write(base64.decodebytes(encoded_image_bytes))
        return html.P("Figure saved!")

# Show/hide bandpass filter options depending on user input
@app.callback(Output('bandpass-options', 'style'),
             [Input('butterworth-input', 'value')])
def set_bandpass_options_style(value):
    # Enable butterworth options if user wants to apply the filter
    if value == "True":
        return {'display': 'block'}
    # Disable butterworth options if user doesn't want to apply the filter
    elif value == "False":
        return {'display': 'none'}

# Show/hide window rejection options depending on user input
@app.callback(Output('rejection-options', 'style'),
             [Input('rejection_bool-input', 'value')])
def set_rejection_options_style(value):
    # Enable rejection options if user wants to apply the filter
    if value == "True":
        return {'display': 'block'}
    # Disable rejection options if user doesn't want to apply the filter
    elif value == "False":
        return {'display': 'none'}

def parse_data(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'miniseed' in filename:
            #print("It tried miniseed")
            stringio_obj = io.BytesIO(decoded)
            #st = obspy.read(stringio_obj)
            #print(st)
            return hvsrpy.Sensor3c.from_mseed(stringio_obj)
            #print(sensor)
    # TODO (jpv): Fix logic. Does not make sense to return exception to caller.
    except Exception as e:
        raise PreventUpdate
        # print(e)
        # return html.Div([
        #     'There was an error processing this file.'
        # ])
def fig_to_uri(in_fig, close_all=True, **save_args):
    # type: (plt.Figure) -> str
    """
    Save a figure as a URI
    :param in_fig:
    :return:
    """
    out_img = BytesIO()
    in_fig.savefig(out_img, format='png', **save_args)
    if close_all:
        in_fig.clf()
        plt.close('all')
    out_img.seek(0)  # rewind file
    encoded = base64.b64encode(out_img.read()).decode("ascii").replace("\n", "")
    return "data:image/png;base64,{}".format(encoded), encoded

def generate_table(hv, distribution_f0):
    if distribution_f0 == "log-normal":
        table_header = [html.Thead(html.Tr([html.Th("Name"), html.Th("Log-Normal Median"), html.Th("Log-Normal Standard Deviation")]))]
        row1 = html.Tr([
            html.Td("Fundamental Site Frequency, f0"),
            html.Td(str(hv.mean_f0_frq(distribution_f0))[:4]+" Hz"),
            html.Td(str(hv.std_f0_frq(distribution_f0))[:4])
        ])
        row2 = html.Tr([
            html.Td("Fundamental Site Period, T0"),
            html.Td(str((1/hv.mean_f0_frq(distribution_f0)))[:4]+" s"),
            html.Td(str(hv.std_f0_frq(distribution_f0))[:4])
        ])
    elif distribution_f0 == "normal":
        table_header = [html.Thead(html.Tr([html.Th("Name"), html.Th("Mean"), html.Th("Standard Deviation")]))]
        row1 = html.Tr([
            html.Td("Fundamental Site Frequency, f0"),
            html.Td(str(hv.mean_f0_frq(distribution_f0))[:4]+" Hz"),
            html.Td(str(hv.std_f0_frq(distribution_f0))[:4])
        ])
        row2 = html.Tr([
            html.Td("Fundamental Site Period, T0"),
            html.Td("-"),
            html.Td("-")
        ])

    table_body = [html.Tbody([row1, row2])]
    table = dbc.Table(table_header + table_body, bordered=True, hover=True)
    return table

@app.callback(
    [Output('cur_plot', 'src'),
    Output('window-information-table', 'children'),
    Output('before-rejection-table', 'children'),
    Output('after-rejection-table', 'children'),
    Output('tables', 'style'),
    Output('hidden-figure-div', 'children')],
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
def update_timerecord_plot(n_clicks, filename, contents, filter_bool, flow, fhigh, forder, minf, maxf, nf, res_type,
    windowlength, width, bandwidth, method, distribution_mc, rejection_bool, n, distribution_f0, n_iteration):

    # print(filter_bool)
    # print(flow)
    # print(fhigh)
    # print(forder)
    # print(minf)
    # print(maxf)
    # print(nf)
    # print(windowlength)
    # print(width)
    # print(bandwidth)
    # print(method)
    # print(distribution_mc)
    # print(rejection_bool)
    # print(n)
    # print(distribution_f0)
    # print(n_iteration)

    filter_bool = True if filter_bool=="True" else False
    rejection_bool = True if rejection_bool=="True" else False

    start = time.time()
    # print(filename)
    # print(data)
    if contents:
        #contents = contents[0]
        #filename = filename[0]

        # TODO (jpv): Check that filename is iterable/sliceable
        # filename = filename

        fig = plt.figure(figsize=(6,6), dpi=150)
        gs = fig.add_gridspec(nrows=6,ncols=6)

        ax0 = fig.add_subplot(gs[0:2, 0:3])
        ax1 = fig.add_subplot(gs[2:4, 0:3])
        ax2 = fig.add_subplot(gs[4:6, 0:3])

        if rejection_bool:
            ax3 = fig.add_subplot(gs[0:3, 3:6])
            ax4 = fig.add_subplot(gs[3:6, 3:6])
        else:
            ax3 = fig.add_subplot(gs[1:4, 3:6])
            ax4 = False

        sensor = parse_data(contents, filename)
        bp_filter = {"flag":filter_bool, "flow":flow, "fhigh":fhigh, "order":forder}
        resampling = {"minf":minf, "maxf":maxf, "nf":nf, "res_type":res_type}
        hv = sensor.hv(windowlength, bp_filter, width, bandwidth, resampling, method)


        individual_width = 0.3
        median_width = 1.3

        for ax, title in zip([ax3, ax4], ["Before Rejection", "After Rejection"]):
            # Rejected Windows
            if title=="After Rejection":
                if hv.rejected_window_indices.size>0:
                    label = "Rejected"
                    for amp in hv.amp[hv.rejected_window_indices]:
                        ax.plot(hv.frq, amp, color='#00ffff', linewidth=individual_width, zorder=2, label=label)
                        label=None

            # Accepted Windows
            label="Accepted"
            for amp in hv.amp[hv.valid_window_indices]:
                ax.plot(hv.frq, amp, color='#888888', linewidth=individual_width,
                        label = label if title=="Before Rejection" else "")
                label=None

            # Window Peaks
            ax.plot(hv.peak_frq, hv.peak_amp, linestyle="", zorder=2,
                    marker='o', markersize=2.5, markerfacecolor="#ffffff", markeredgewidth=0.5, markeredgecolor='k',
                    label="" if title=="Before Rejection" and rejection_bool else r"$f_{0,i}$")

            # Peak Mean Curve
            ax.plot(hv.mc_peak_frq(distribution_mc), hv.mc_peak_amp(distribution_mc), linestyle="", zorder=4,
                    marker='D', markersize=4, markerfacecolor='#66ff33', markeredgewidth=1, markeredgecolor='k',
                    label = "" if title=="Before Rejection" and rejection_bool else r"$f_{0,mc}$")

            # Mean Curve
            label = r"$LM_{curve}$" if distribution_mc=="log-normal" else "Mean Curve"
            ax.plot(hv.frq, hv.mean_curve(distribution_mc), color='k', linewidth=median_width,
                    label="" if title=="Before Rejection" and rejection_bool else label)

            # Mean +/- Curve
            label = r"$LM_{curve}$"+" ± 1 STD" if distribution_mc=="log-normal" else "Mean ± 1 STD"
            ax.plot(hv.frq, hv.nstd_curve(-1, distribution_mc),
                    color='k', linestyle='--', linewidth=median_width, zorder=3,
                    label = "" if title=="Before Rejection" and rejection_bool else label)
            ax.plot(hv.frq, hv.nstd_curve(+1, distribution_mc),
                    color='k', linestyle='--', linewidth=median_width, zorder=3)

            label = r"$LM_{f0}$"+" ± 1 STD" if distribution_f0=="log-normal" else "Mean f0 ± 1 STD"
            ymin, ymax = ax.get_ylim()
            ax.plot([hv.mean_f0_frq(distribution_f0)]*2, [ymin, ymax], linestyle="-.", color="#000000")
            ax.fill([hv.nstd_f0_frq(-1, distribution_f0)]*2 + [hv.nstd_f0_frq(+1, distribution_f0)]*2, [ymin, ymax, ymax, ymin],
                    color = "#ff8080",
                    label="" if title=="Before Rejection" and rejection_bool else label)

            ax.set_ylim((ymin, ymax))
            ax.set_xscale('log')
            ax.set_xlabel("Frequency (Hz)")
            ax.set_ylabel("HVSR Ampltidue")

            if rejection_bool:
                if title=="Before Rejection":
                    table_before_rejection = generate_table(hv, distribution_f0)
                    c_iter = hv.reject_windows(n, max_iterations=n_iteration,
                                       distribution_f0=distribution_f0, distribution_mc=distribution_mc)
                    # Create Window Information Table
                    row1 = html.Tr([html.Td("Window length"), html.Td(str(windowlength)+"s")])
                    row2 = html.Tr([html.Td("No. of windows"), html.Td(str(sensor.ns.n_windows))])
                    row3 = html.Tr([html.Td("No. of iterations to convergence"), html.Td(str(c_iter)+" of "+str(n_iteration)+" allowed.")])

                elif title=="After Rejection":
                    fig.legend(ncol=4, loc='lower center', bbox_to_anchor=(0.51, 0), columnspacing=2)
                    table_after_rejection = generate_table(hv, distribution_f0)
                    row4 = html.Tr([html.Td("No. of rejected windows"), html.Td(str(len(hv.rejected_window_indices)))])
                    window_information_table_body = [html.Tbody([row1, row2, row3, row4])]
            else:
                table_no_rejection = generate_table(hv, distribution_f0)
                # Create Window Information Table
                row1 = html.Tr([html.Td("Window length"), html.Td(str(windowlength)+"s")])
                row2 = html.Tr([html.Td("No. of windows"), html.Td(str(sensor.ns.n_windows))])
                row3 = html.Tr([html.Td("No. of iterations to convergence"), html.Td(str(c_iter)+" of "+str(n_iteration)+" allowed.")])
                window_information_table_body = [html.Tbody([row1, row2, row3])]

                fig.legend(loc="upper center", bbox_to_anchor=(0.75, 0.3))
                break
            ax.set_title(title)

        norm_factor = sensor.normalization_factor
        for ax, timerecord, name in zip([ax0,ax1,ax2], [sensor.ns, sensor.ew, sensor.vt], ["NS", "EW", "VT"]):
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
                ax.plot(ctime[window_index], amp[window_index], linewidth=0.2, color="cyan")

        # TODO (jpv): Reintroduce save figure after async thread issue.
        save_figure = fig
        fig.tight_layout(h_pad=1, w_pad=2, rect=(0,0.08,1,1))
        save_figure.tight_layout(h_pad=1, w_pad=2, rect=(0,0.08,1,1))
        # figure_name_out = "test.png" #"example_hvsr_figure.png"
        # save_figure.savefig(figure_name_out, dpi=300, bbox_inches='tight')
        # renderer = PlotlyRenderer()
        # exporter = mplexporter.Exporter(renderer)
        # exporter.run(fig)
        # renderer.layout
        # renderer.data
        # plotly_fig = mpl_to_plotly(fig)



        end = time.time()
        # return (dcc.Graph(figure=plotly_fig), html.P("Before Rejection:"), table_before, dbc.Table(table_body, bordered=True), html.P("After Rejection:"), table_after), "success", html.P("Total time elapsed (s): "+time_elapsed)
        # print(plotly_fig.data)
        # print("\n"*5)

        # print(plotly_fig.layout)
        # print("\n"*5)

        # print(plotly_fig.data)
        # raise RuntimeError

        # return {"data":plotly_fig.data, "layout":plotly_fig.layout}

        # return dcc.Graph(figure=plotly_fig)
        out_url, encoded_image = fig_to_uri(fig)
        if rejection_bool:
            return out_url, (html.H5("Window Information:"), dbc.Table(window_information_table_body, bordered=True, striped=True, hover=True, dark=True)), (html.H5("Statistics Before Rejection:"), table_before_rejection), (html.H5("Statistics After Rejection:"), table_after_rejection), ({"border": "2px solid #73AD21", "border-radius":"20px", "padding":"15px"}), [encoded_image]
        else:
            return out_url, dbc.Table(window_information_table_body, bordered=True), (html.P("Statistics:"), table_no_rejection), ({"border": "2px solid #73AD21", "border-radius":"20px", "padding":"15px"})
    else:
        raise PreventUpdate

    # return ([])
    # return (""), "success", ("")


'''
# Below is information from the example at: https://docs.faculty.ai/user-guide/apps/examples/dash_file_upload_download.html
# It may be useful for downloading information we have created later.
@app.callback(Output('output-data-upload', 'children'),
            [
                Input('upload-data', 'contents'),
                Input('upload-data', 'filename')
            ])
def update_table(contents, filename):
    table = html.Div()

    if contents:
        contents = contents[0]
        filename = filename[0]
        df = parse_data(contents, filename)

        table = html.Div([
            html.H5(filename),
            dash_table.DataTable(
                data=df.to_dict('rows'),
                columns=[{'name': i, 'id': i} for i in df.columns]
            ),
            html.Hr(style={"border-top": "1px solid #bababa"}),
            html.Div('Raw Content'),
            html.Pre(contents[0:200] + '...', style={
                'whiteSpace': 'pre-wrap',
                'wordBreak': 'break-all'
            })
        ])

    return table

def save_file(name, content):
    """Decode and store a file uploaded with Plotly Dash."""
    data = content.encode("utf8").split(b";base64,")[1]
    with open(os.path.join(UPLOAD_DIRECTORY, name), "wb") as fp:
        fp.write(base64.decodebytes(data))

def uploaded_files():
    """List the files in the upload directory."""
    files = []
    for filename in os.listdir(UPLOAD_DIRECTORY):
        path = os.path.join(UPLOAD_DIRECTORY, filename)
        if os.path.isfile(path):
            files.append(filename)
    return files

def file_download_link(filename):
    """Create a Plotly Dash 'A' element that downloads a file from the app."""
    location = "/download/{}".format(urlquote(filename))
    return html.A(filename, href=location)

@app.callback(
    Output("file-list", "children"),
    [Input("upload-data", "filename"), Input("upload-data", "contents")],
)
def update_output(uploaded_filenames, uploaded_file_contents):
    """Save uploaded files and regenerate the file list."""

    if uploaded_filenames is not None and uploaded_file_contents is not None:
        for name, data in zip(uploaded_filenames, uploaded_file_contents):
            save_file(name, data)

    files = uploaded_files()
    if len(files) == 0:
        return [html.Li("No files yet!")]
    else:
        return [html.Li(file_download_link(filename)) for filename in files]
'''

if __name__ == "__main__":
    app.run_server(debug=True)#, port=8888)
