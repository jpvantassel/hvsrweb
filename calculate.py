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

# Bootstrap Layout:
# TIME DOMAIN SETTINGS TAB
tab1_content = dbc.Card(
    dbc.CardBody(
        [
            # Window Length
            html.P([
                html.Span(
                    "Window length (s):",
                    id="windowlength-tooltip-target",
                    style={"textDecoration": "underline", "cursor": "context-menu", "padding":"5px"},
                ),
            ]),
            dbc.Tooltip(
                "In general low frequency peaks require longer window lengths. "
                "See the SESAME guidelines for specific window length recommendations.",
                target="windowlength-tooltip-target",
            ),
            dbc.Input(id="windowlength-input", type="number", value=30, min=0, max=600, step=1),
            html.P(""),
            html.Hr(style={"border-top": "1px solid #bababa"}),

            # Butterworth Filter
            html.P([
                html.Span(
                    "Apply Butterworth Filter?",
                    id="butterworth-tooltip-target",
                    style={"textDecoration": "underline", "cursor": "context-menu", "padding":"5px"},
                ),
            ]),
            dbc.Tooltip(
                "Boolean to control whether Butterworth filter is applied. "
                "Geopsy does not apply a bandpass filter.",
                target="butterworth-tooltip-target",
            ),
            dbc.Select(
                id="butterworth-input",
                options=[
                    {"label": "True", "value": "True"},
                    {"label": "False", "value": "False"},
                    # {"label": "Disabled option", "value": "3", "disabled": True},
                ], value="True"),
            html.P(""), # used for styling purposes only

            # fLow for bandpass filter
            html.P([
                html.Span(
                    "Low-cut frequency for bandpass filter:",
                    id="flow-tooltip-target",
                    style={"textDecoration": "underline", "cursor": "context-menu", "padding":"5px"},
                ),
            ]),
            dbc.Tooltip(
                "Do we even really need "
                "a tooltip for this one?",
                target="flow-tooltip-target",
            ),
            dbc.Input(id="flow-input", type="number", value=0.1, min=0, max=1000, step=0.01),
            html.P(""), # used for styling purposes only

            # fHigh for bandpass filter
            html.P([
                html.Span(
                    "High-cut frequency for bandpass filter:",
                    id="fhigh-tooltip-target",
                    style={"textDecoration": "underline", "cursor": "context-menu", "padding":"5px"},
                ),
            ]),
            dbc.Tooltip(
                "Do we even really need "
                "a tooltip for this one?",
                target="fhigh-tooltip-target",
            ),
            dbc.Input(id="fhigh-input", type="number", value=30, min=0, max=600, step=1),
            html.P(""), # used for styling purposes only

            # fOrder for bandpass filter
            html.P([
                html.Span(
                    "Filter order:",
                    id="forder-tooltip-target",
                    style={"textDecoration": "underline", "cursor": "context-menu", "padding":"5px"},
                ),
            ]),
            dbc.Tooltip(
                "Do we even really need "
                "a tooltip for this one?",
                target="forder-tooltip-target",
            ),
            dbc.Input(id="forder-input", type="number", value=5, min=0, max=600, step=1),
            html.P(""), # used for styling purposes only
            html.Hr(style={"border-top": "0.5px solid #bababa"}),# used for styling purposes only

            # Width of cosine taper
            html.P([
                html.Span(
                    "Cosine taper width:",
                    id="width-tooltip-target",
                    style={"textDecoration": "underline", "cursor": "context-menu", "padding":"5px"},
                ),
            ]),
            dbc.Tooltip(
                "Geopsy default of 0.05 is equal to 0.1. "
                "0.1 is recommended.",
                target="width-tooltip-target",
            ),
            dbc.Input(id="width-input", type="number", value=0.1, min=0.1, max=1.0, step=0.1),

            # dbc.Button("Click here", color="success")]

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
                    "Bandwith:",
                    id="bandwidth-tooltip-target",
                    style={"textDecoration": "underline", "cursor": "context-menu", "padding":"5px"},
                ),
            ]),
            dbc.Tooltip(
                "Konno and Ohmachi smoothing constant. "
                "40 is recommended.",
                target="bandwidth-tooltip-target",
            ),
            dbc.Input(id="bandwidth-input", type="number", value=40, min=0, max=600, step=1),
            html.P(""),
            html.Hr(style={"border-top": "1px solid #bababa"}),

            # Minumum frequency
            html.P("After Resampling:"),
            html.P([
                html.Span(
                    "Min frequency:",
                    id="minf-tooltip-target",
                    style={"textDecoration": "underline", "cursor": "context-menu", "padding":"5px"},
                ),
            ]),
            dbc.Tooltip(
                "Do we even really need "
                "a tooltip for this one?",
                target="minf-tooltip-target",
            ),
            dbc.Input(id="minf-input", type="number", value=0.1, min=0, max=1000, step=0.01),
            html.P(""),

            # Maximum frequency
            html.P([
                html.Span(
                    "Max frequency:",
                    id="maxf-tooltip-target",
                    style={"textDecoration": "underline", "cursor": "context-menu", "padding":"5px"},
                ),
            ]),
            dbc.Tooltip(
                "Do we even really need "
                "a tooltip for this one?",
                target="maxf-tooltip-target",
            ),
            dbc.Input(id="maxf-input", type="number", value=20, min=0, max=600, step=1),
            html.P(""),

            # Number of frequencies
            html.P([
                html.Span(
                    "Number of frequencies:",
                    id="nf-tooltip-target",
                    style={"textDecoration": "underline", "cursor": "context-menu", "padding":"5px"},
                ),
            ]),
            dbc.Tooltip(
                "Do we even really need "
                "a tooltip for this one?",
                target="nf-tooltip-target",
            ),
            dbc.Input(id="nf-input", type="number", value=2048, min=0, max=10000, step=1),
            html.P(""),

            # Resampling type
            html.P([
                html.Span(
                    "Resampling type:",
                    id="res_type-tooltip-target",
                    style={"textDecoration": "underline", "cursor": "context-menu", "padding":"5px"},
                ),
            ]),
            dbc.Tooltip(
                "Boolean to control whether Butterworth filter is applied. "
                "Geopsy does not apply a bandpass filter.",
                target="res_type-tooltip-target",
            ),
            dbc.Select(
                id="res_type-input",
                options=[
                    {"label": "log", "value": "log"},
                    {"label": "linear", "value": "linear"},
                ], value="log",
            ),
            # dbc.Button("Click here", color="success")]
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
                    "Method for combining horizontal components:",
                    id="method-tooltip-target",
                    style={"textDecoration": "underline", "cursor": "context-menu", "padding":"5px"},
                ),
            ]),
            dbc.Tooltip(
                "Method for combining horizontal components. Geopsy default is 'squared-average'. "
                "'Geometric-mean' is recommended.",
                target="method-tooltip-target",
            ),
            dbc.Select(
                id="method-input",
                options=[
                    {"label": "squared-average", "value": "squared-average"},
                    {"label": "geometric-mean", "value": "geometric-mean"},
                ], value="geometric-mean",
            ),
            html.P(" "),
            html.Hr(style={"border-top": "1px solid #bababa"}),

            # Frequency domain rejection
            html.P([
                html.Span(
                    "Apply frequency domain rejection?",
                    id="rejection_bool-tooltip-target",
                    style={"textDecoration": "underline", "cursor": "context-menu", "padding":"5px"},
                ),
            ]),
            dbc.Tooltip(
                "Boolean to control whether frequency domain rejection proposed "
                "by Cox et al. (in review) is applied. Geopsy does not offer this functionality.",
                target="rejection_bool-tooltip-target",
            ),
            dbc.Select(
                id="rejection_bool-input",
                options=[
                    {"label": "True", "value": "True"},
                    {"label": "False", "value": "False"},
                    # {"label": "Disabled option", "value": "3", "disabled": True},
                ], value="True"),
            html.P(""),

            # Standard deviations to consider
            html.P([
                html.Span(
                    "Standard deviations:",
                    id="n-tooltip-target",
                    style={"textDecoration": "underline", "cursor": "context-menu", "padding":"5px"},
                ),
            ]),
            dbc.Tooltip(
                "Number of standard deviations to consider during rejection. "
                "Smaller values will reject more windows. 2 is recommended. ",
                target="n-tooltip-target",
            ),
            dbc.Input(id="n-input", type="number", value=2, min=0, max=600, step=1),
            html.P(""),

            # Max iterations
            html.P([
                html.Span(
                    "Iterations during rejection:",
                    id="n_iteration-tooltip-target",
                    style={"textDecoration": "underline", "cursor": "context-menu", "padding":"5px"},
                ),
            ]),
            dbc.Tooltip(
                "Number of iterations to perform during rejection. "
                "50 is recommended.",
                target="n_iteration-tooltip-target",
            ),
            dbc.Input(id="n_iteration-input", type="number", value=50, min=0, max=600, step=1),
            html.P(""),
            html.Hr(style={"border-top": "0.5px solid #bababa"}),

            # Distribution of f0
            html.P([
                html.Span(
                    "Distribution of f0:",
                    id="distribution_f0-tooltip-target",
                    style={"textDecoration": "underline", "cursor": "context-menu", "padding":"5px"},
                ),
            ]),
            dbc.Tooltip(
                "Geopsy default 'normal'. 'log-normal' is recommended.",
                target="distribution_f0-tooltip-target",
            ),
            dbc.Select(
                id="distribution_f0-input",
                options=[
                    {"label": "log-normal", "value": "log-normal"},
                    {"label": "normal", "value": "normal"},
                    # {"label": "Disabled option", "value": "3", "disabled": True},
                ], value='log-normal'),
            html.P(""),

            # Distribution of mean curve
            html.P([
                html.Span(
                    "Distribution of mean curve:",
                    id="distribution_mc-tooltip-target",
                    style={"textDecoration": "underline", "cursor": "context-menu", "padding":"5px"},
                ),
            ]),
            dbc.Tooltip(
                "Geopsy default 'log-normal'. 'log-normal' is recommended.",
                target="distribution_mc-tooltip-target",
            ),
            dbc.Select(
                id="distribution_mc-input",
                options=[
                    {"label": "log-normal", "value": "log-normal"},
                    {"label": "normal", "value": "normal"},
                    # {"label": "Disabled option", "value": "3", "disabled": True},
                ], value="log-normal"),
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
                md=9,
            style={"padding-bottom": "20px",}),
            # Column2_2
            dbc.Col([
                    dbc.Button("Calculate", id="calculate-button", outline=True, color="success", className="mr-1", size="lg"),
                ], md=2, ),
            dbc.Col([
                    html.Div(id="spinner")
                    #dbc.Spinner(color="success", className="mt-2 pl-0"),
                ], md=1, ),
        ]),
        # Row1.5
        dbc.Row([html.Div(id="filename-reference")], className="mt-1 ml-4 mb-1"),
        # Row2
        dbc.Row([
                # Column2_1
                dbc.Col(
                    [
                        html.H4("Settings"),
                        dbc.Tabs([
                            dbc.Tab(tab1_content, label="Time Domain"),
                            dbc.Tab(tab2_content, label="Frequency Domain"),
                            dbc.Tab(tab3_content, label="  H/V  ")
                        ]),
                        # dbc.Button("View details", color="secondary"),
                        # html.P(id="total-time"),
                        # dbc.Button("Save Figure", color="primary", id="save_figure-button", className="mr-2"),
                        # dbc.Button("Save .hv", color="dark", id="save_hv-button"),
                        # html.Div(id="intermediate-value"),
                        # html.P(id="figure_status"),
                        dbc.Row([
                            html.Div(id="stat-table"),
                        ], className="mt-2 ml-2"),
                    ],
                    md=5,
                ),
                # Column2_2
                dbc.Col([
                    # Row2_2_1
                    dbc.Row([
                        html.Div([html.Img(id = 'cur_plot', src = '')], id='plot_div')#id="figure-div")
                    ]),
                ], md=7)
            ]),
        dbc.Row([
            html.Div(id='rejection-tables')#id="figure-div")
        ], className="mt-2 ml-2"),
    ], className="mt-4", fluid=True)

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
    style={"max-width": "1200px"},
)


@app.callback(
    [Output('filename-reference', 'children')],
    [Input('upload-bar', 'filename')])
def store_filename(filename):
    return [filename]
'''
@app.callback(
    Output('spinner', 'children'),
    [Input('calculate-button', 'n_clicks')])
def update_spinner(n_clicks):
    if n_clicks == None:
        return html.P("")
    else:
        return dbc.Spinner(color="success")

@app.callback(
    Output('hidden-div', 'children'),
    [Input('save_hv-button', 'n_clicks'),
    Input('cur_plot', 'src')])
def save_figure(n_clicks, src):
    if n_clicks == None:
        return html.P("")
    else:

        out_img = BytesIO()
        in_fig.savefig(out_img, format='png', **save_args)
        if close_all:
            in_fig.clf()
        return html.P("")
 '''
def parse_data(filename):
    try:
        return hvsrpy.Sensor3c.from_mseed(filename)
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
    return "data:image/png;base64,{}".format(encoded)

def generate_table(hv, distribution_f0):
    table_header = [html.Thead(html.Tr([html.Th("Parameter"), html.Th("Distribution"), html.Th("Mean"), html.Th("Median"), html.Th("Standard Deviation")]))]
    if distribution_f0 == "log-normal":
        row1 = html.Tr([html.Td("f0"), html.Td("Log-normal"), html.Td("-"), html.Td(str(hv.mean_f0_frq(distribution_f0))[:4]+" Hz"), html.Td(str(hv.std_f0_frq(distribution_f0))[:4])])
        row2 = html.Tr([html.Td("T0"), html.Td("Log-normal"), html.Td("-"), html.Td(str(1/hv.mean_f0_frq(distribution_f0))[:4]+" s"), html.Td(str(-1*hv.std_f0_frq(distribution_f0))[:5])])
    else:
        row1 = html.Tr([html.Td("f0"), html.Td("Normal"), html.Td(str(self.std_f0_frq(distribution_f0))[:4]), html.Td("-"), html.Td(str(hv.std_f0_frq(distribution_f0))[:4])])
        row2 = html.Tr([html.Td("T0"), html.Td("Normal"), html.Td("-"), html.Td("-"), html.Td("-")])
    table_body = [html.Tbody([row1, row2])]
    table = dbc.Table(table_header + table_body, bordered=True)
    return table

@app.callback(
    [Output('cur_plot', 'src'),
    Output('stat-table', 'children'),
    Output('rejection-tables', 'children')],
    #  Output('calculate-button', 'color'),
    #  Output('total-time', 'children')],
    [Input('calculate-button', 'n_clicks')],
    [State('filename-reference', 'children'),
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
def update_timerecord_plot(n_clicks, filename, filter_bool, flow, fhigh, forder, minf, maxf, nf, res_type,
    windowlength, width, bandwidth, method, distribution_mc, rejection_bool, n, distribution_f0, n_iteration):
    start = time.time()

    if filename:
        print(filename)

        # TODO (jpv): Check that filename is iterable/sliceable
        # filename = filename

        sensor = parse_data(filename)
        bp_filter = {"flag":filter_bool, "flow":flow, "fhigh":fhigh, "order":forder}
        resampling = {"minf":minf, "maxf":maxf, "nf":nf, "res_type":res_type}
        hv = sensor.hv(windowlength, bp_filter, width, bandwidth, resampling, method)

        fig = plt.figure(figsize=(6,6), dpi=150)
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
            if title=="After Rejection":
                for amp in hv.amp[hv.rejected_window_indices]:
                    ax.plot(hv.frq, amp, color='#00ffff', linewidth=individual_width, zorder=2)
                ax.plot(hv.frq, amp, color='#00ffff', linewidth=individual_width, label="Rejected")
            for amp in hv.amp[hv.valid_window_indices]:
                ax.plot(hv.frq, amp, color='#888888', linewidth=individual_width)

            ax.plot(hv.frq, amp, color='#888888', linewidth=individual_width,
                    label = "Accepted" if title=="Before Rejection" else "")

            ax.plot(hv.frq, hv.mean_curve(distribution_mc), color='k', linewidth=median_width,
                    label="" if title=="Before Rejection" and rejection_bool else "Mean Curve")

            # Window Peaks
            ax.plot(hv.peak_frq, hv.peak_amp, linestyle="", zorder=2,
                    marker='o', markersize=2.5, markerfacecolor="#ffffff", markeredgewidth=0.5, markeredgecolor='k',
                    label="" if title=="Before Rejection" and rejection_bool else r"$f_{0,i}$")

            # Mean Curve
            ax.plot(hv.frq, hv.nstd_curve(-1, distribution_mc),
                    color='k', linestyle='--', linewidth=median_width, zorder=3,
                    label = "" if title=="Before Rejection" and rejection_bool else "Mean ± 1 STD")
            ax.plot(hv.frq, hv.nstd_curve(+1, distribution_mc),
                    color='k', linestyle='--', linewidth=median_width, zorder=3)

            # Peak Mean Curve
            ax.plot(hv.mc_peak_frq(distribution_mc), hv.mc_peak_amp(distribution_mc), linestyle="", zorder=4,
                    marker='D', markersize=5, markerfacecolor='#66ff33', markeredgewidth=1, markeredgecolor='k',
                    label = "" if title=="Before Rejection" and rejection_bool else r"$f_{0,mc}$")

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
            # n_spaces = 19
            if rejection_bool:
                if title=="Before Rejection":
                    table_before = generate_table(hv, distribution_f0)
                    c_iter = hv.reject_windows(n, max_iterations=n_iteration,
                                               distribution_f0=distribution_f0, distribution_mc=distribution_mc)
                elif title=="After Rejection":
                    fig.legend(ncol=4, loc='lower center', bbox_to_anchor=(0.51, 0))
                    table_after = generate_table(hv, distribution_f0)
            else:
                n_spaces += 9
                '''
                print()
                print(f"Window length :  {str(windowlength)}s")
                print(f"No. of windows : {sensor.ns.n_windows}")
                print()
                print(f"*{'*'*n_spaces} Statistics{'*'*n_spaces}")
                hv.print_stats(distribution_f0)
                print()
                '''
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
        save_figure.tight_layout(h_pad=1, w_pad=2, rect=(0,0.07,1,1))
        # figure_name_out = "test.png" #"example_hvsr_figure.png"
        # save_figure.savefig(figure_name_out, dpi=300, bbox_inches='tight')
        # renderer = PlotlyRenderer()
        # exporter = mplexporter.Exporter(renderer)
        # exporter.run(fig)
        # renderer.layout
        # renderer.data
        # plotly_fig = mpl_to_plotly(fig)

        # TODO (jpv): Reintroduce statistics table after async thread issue.
        # Rejection Statistics Table
        row1 = html.Tr([html.Td("Window length"), html.Td(str(windowlength)+"s")])
        row2 = html.Tr([html.Td("No. of windows"), html.Td(str(sensor.ns.n_windows))])
        row3 = html.Tr([html.Td("No. of iterations to convergence"), html.Td(str(c_iter)+" of "+str(n_iteration)+" allowed.")])
        row4 = html.Tr([html.Td("No. of rejected windows"), html.Td(str(len(hv.rejected_window_indices)))])
        table_body = [html.Tbody([row1, row2, row3, row4])]

        end = time.time()
        time_elapsed = str(end-start)[0:4]
        # return (dcc.Graph(figure=plotly_fig), html.P("Before Rejection:"), table_before, dbc.Table(table_body, bordered=True), html.P("After Rejection:"), table_after), "success", html.P("Total time elapsed (s): "+time_elapsed)
        # print(plotly_fig.data)
        # print("\n"*5)

        # print(plotly_fig.layout)
        # print("\n"*5)

        # print(plotly_fig.data)
        # raise RuntimeError

        # return {"data":plotly_fig.data, "layout":plotly_fig.layout}

        # return dcc.Graph(figure=plotly_fig)
        out_url = fig_to_uri(fig)
        return out_url, dbc.Table(table_body, bordered=True), (html.P("Before Rejection:"), table_before, html.P("After Rejection:"), table_after)
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
