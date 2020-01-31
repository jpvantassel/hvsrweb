import base64
import os
from urllib.parse import quote as urlquote

from flask import Flask, send_from_directory
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

import dash_table
import pandas as pd
import datetime
import io
import plotly.graph_objs as go

from plotly.tools import mpl_to_plotly

# HVSRPY IMPORTS
import hvsrpy
import numpy as np
import matplotlib.pyplot as plt
import time

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# NEED TO CHANGE THE BELOW LINES WHEN DEPLOYED ON HEROKU
UPLOAD_DIRECTORY = "/project/app_uploaded_files"
if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

# Normally, Dash creates its own Flask server internally. By creating our own,
# we can create a route for downloading files directly:
server = Flask(__name__)
app = dash.Dash(server=server, external_stylesheets=external_stylesheets)
@server.route("/download/<path:path>")
def download(path):
    """Serve a file from the upload directory."""
    return send_from_directory(UPLOAD_DIRECTORY, path, as_attachment=True)
'''
INSTEAD OF:
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
'''

# STYLING
colors = {
    "graphBackground": "#F5F5F5",
    "background": "#ffffff",
    "text": "#000000"
}
app.layout = html.Div(
    [
        html.H1("HVSR Calculation"),
        html.H2("Upload a file"),
        dcc.Upload(
            id="upload-data",
            children=html.Div(
                ["Drag and drop or click to select a file to upload."]
            ),
            style={
                "width": "100%",
                "height": "60px",
                "lineHeight": "60px",
                "borderWidth": "1px",
                "borderStyle": "dashed",
                "borderRadius": "5px",
                "textAlign": "center",
                "margin": "10px",
            },
            # Allow multiple files to be uploaded
            multiple=True,
        ),
        #html.H2("File List (click to download)"),
        #html.Ul(id="file-list"),

        # Time Domain Settings
        html.Div([
            html.P('Window length in seconds. In general low frequency peaks require longer window lengths. See the SESAME guidelines for specific window length recommendations.'),
            dcc.Input(id='windowlength', value=60, type='number'),

            html.P('Boolean to control whether Butterworth filter is applied. Geopsy does not apply a bandpass filter.'),
            dcc.Dropdown(
                id='filter_bool',
                options=[
                    {'label': 'True', 'value': 'True'},
                    {'label': 'False', 'value': 'False'}
                    ],
                value="False"
            ),
            html.P('Low-cut frequency for bandpass filter.'),
            dcc.Input(id='flow', value=0.1, type='number'),
            html.P('High-cut frequency for bandpass filter.'),
            dcc.Input(id='fhigh', value=45, type='number'),
            html.P('Filter order.'),
            dcc.Input(id='forder', value=5, type='number'),

            html.P('Width of cosine taper {0. - 1.}. Geopsy default of 0.05 is equal to 0.1 -> 0.1 is recommended.'),
            dcc.Input(id="width", value=0.1, type="number"),
        ],
        style={'width': '100%', 'display': 'inline-block'}),

        # Frequency Domain Settings
        html.Div([
            html.P('Konno and Ohmachi smoothing constant. 40 is recommended.'),
            dcc.Input(id='bandwidth', value=40, type='number'),

            html.P('Minimum frequency after resampling.'),
            dcc.Input(id='minf', value=0.3, type='number'),
            html.P('Maximum frequency after resampling.'),
            dcc.Input(id='maxf', value=40, type='number'),
            html.P('Number of frequencies after resampling.'),
            dcc.Input(id='nf', value=2048, type='number'),
            html.P('Type of resampling.'),
            dcc.Dropdown(
                id='res_type',
                options=[
                    {'label': 'log', 'value': 'log'},
                    {'label': 'linear', 'value': 'linear'}
                    ],
                value='log'
            ),
        ],
        style={'width': '100%', 'display': 'inline-block'}),

        # H/V Settings
        html.Div([
            html.P('Method for combining horizontal components. Geopsy default is "squared-average". "Geometric-mean" is recommended.'),
            dcc.Dropdown(
                id='method',
                options=[
                    {'label': 'squared-average', 'value': 'squared-average'},
                    {'label': 'geometric-mean', 'value': 'geometric-mean'}
                    ],
                value='geometric-mean'
            ),

            html.P('Boolean to control whether frequency domain rejection proposed by Cox et al. (in review) is applied. Geopsy does not offer this functionality.'),
            dcc.Dropdown(
                id='rejection_bool',
                options=[
                    {'label': 'True', 'value': 'True'},
                    {'label': 'False', 'value': 'False'}
                    ],
                value='True'
            ),
            html.P('Number of standard deviations to consider during rejection. Smaller values will reject more windows -> 2 is recommended.'),
            dcc.Input(id='n', value=2, type='number'),
            html.P('Maximum number of iterations to perform for rejection -> 50 is recommended'),
            dcc.Input(id='n_iteration', value=50, type='number'),

            html.P('Distribution of f0 {"log-normal", "normal"}. Geopsy default "normal" -> "log-normal" is recommended.'),
            dcc.Dropdown(
                id='distribution_f0',
                options=[
                    {'label': 'log-normal', 'value': 'log-normal'},
                    {'label': 'normal', 'value': 'normal'}
                    ],
                value='log-normal'
            ),
            html.P('Distribution of mean curve {"log-normal", "normal"}. Geopsy default "log-normal" -> "log-normal" is recommended.'),
            dcc.Dropdown(
                id='distribution_mc',
                options=[
                    {'label': 'log-normal', 'value': 'log-normal'},
                    {'label': 'normal', 'value': 'normal'}
                    ],
                value='log-normal'
            ),
        ],
        style={'width': '100%', 'display': 'inline-block'}),

        html.Table([
            html.Tr([html.Td(['Window length (s):']), html.Td(id='calc_window_length')]),
            html.Tr([html.Td(['No. of Windows :']), html.Td(id='calc_n_windows')]),
            html.Tr([html.Td(['No. of Rejected Windows :']), html.Td(id='calc_n_rejected_windows')]),
        ]),

        dcc.Graph(id='Mygraph'),

        html.Div(id='output-data-upload')
    ],
    style={"max-width": "1000px"},
)

def parse_data(filename):
    try:
        sensor = hvsrpy.Sensor3c.from_mseed(filename)
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])
    return sensor

@app.callback(
    [Output('Mygraph', 'figure'),
     Output('calc_window_length', 'children'),
     Output('calc_n_windows', 'children'),
     Output('calc_n_rejected_windows', 'children')],
    [Input('upload-data', 'contents'), #UNHASHED THIS ONE
     Input('upload-data', 'filename'),
     Input('filter_bool', 'value'),
     Input('flow', 'value'),
     Input('fhigh', 'value'),
     Input('forder', 'value'),
     Input('minf', 'value'),
     Input('maxf', 'value'),
     Input('nf', 'value'),
     Input('res_type', 'value'),
     Input('windowlength', 'value'),
     Input('width', 'value'),
     Input('bandwidth', 'value'),
     Input('method', 'value'),
     Input('rejection_bool', 'value'),
     Input('distribution_mc', 'value'),
     Input('distribution_f0', 'value'),
     Input('n', 'value'),
     Input('n_iteration', 'value')])
def update_graph(contents, filename, filter_bool, flow, fhigh, forder, minf, maxf, nf, res_type,
    windowlength, width, bandwidth, method, rejection_bool, distribution_mc, distribution_f0, n, n_iteration):
    plotly_fig = {
        'layout': go.Layout(
            plot_bgcolor=colors["graphBackground"],
            paper_bgcolor=colors["graphBackground"])
    }
    n_windows = 0
    n_rejected_windows = 0

    if filename:
        contents = contents[0]
        filename = filename[0]

        # Perform calculation and create figure
        start = time.time()
        sensor = parse_data(filename)
        bp_filter = {"flag":True if filter_bool == 'True' else False,
                    "flow":flow,
                    "fhigh":fhigh,
                    "order":forder}
        resampling = {"minf":minf,
                    "maxf":maxf,
                    "nf":nf,
                    "res_type":res_type}
        hv = sensor.hv(windowlength, bp_filter, width, bandwidth, resampling, method)
        end = time.time()

        fig = plt.figure(figsize=(6,6))
        gs = fig.add_gridspec(nrows=6,ncols=6)

        ax0 = fig.add_subplot(gs[0:2, 0:3])
        ax1 = fig.add_subplot(gs[2:4, 0:3])
        ax2 = fig.add_subplot(gs[4:6, 0:3])

        if rejection_bool == 'True':
            ax3 = fig.add_subplot(gs[0:3, 3:6])
            ax4 = fig.add_subplot(gs[3:6, 3:6])
        else:
            ax3 = fig.add_subplot(gs[1:4, 3:6])
            ax4 = False

        for ax, title in zip([ax3, ax4], ["Before Rejection", "After Rejection"]):
            if title=="After Rejection":
                for amp in hv.amp[hv.rejected_window_indices]:
                    ax.plot(hv.frq, amp, color='#00ffff', linewidth=1.0, zorder=2)
                ax.plot(hv.frq, amp, color='#00ffff', linewidth=1.0, label="Rejected")
            for amp in hv.amp[hv.valid_window_indices]:
                ax.plot(hv.frq, amp, color='#cccccc', linewidth=1)
            label = "Accepted" if title=="Before Rejection" else ""
            ax.plot(hv.frq, amp, color='#cccccc', label=label, linewidth=1)
            label = "" if title=="Before Rejection" and rejection_bool else "Mean Curve"
            ax.plot(hv.frq, hv.mean_curve(distribution_mc), color='k', label=label, linewidth=1.5)
            label = "" if title=="Before Rejection" and rejection_bool else "Mean ± 1 STD"
            ax.plot(hv.frq, hv.nstd_curve(-1, distribution_mc), color='k', linestyle='--', label=label, linewidth=1.5)
            ax.plot(hv.frq, hv.nstd_curve(+1, distribution_mc), color='k', linestyle='--', linewidth=1.5)
            label = "" if title=="Before Rejection" and rejection_bool else "f0,window"
            ax.plot(hv.peak_frq, hv.peak_amp,
                    marker='o', markersize=5, markerfacecolor='white', markeredgewidth=1.0, markeredgecolor='k', linestyle="", label=label)
            label = "" if title=="Before Rejection" and rejection_bool else "f0,mc"
            ax.plot(hv.mc_peak_frq(distribution_mc), hv.mc_peak_amp(distribution_mc),
                    marker='D', markersize=5, markerfacecolor='#66ff33', markeredgewidth=1.5, markeredgecolor='k',
                    linestyle="", label=label)
            label = "LMf0 ± 1 STD" if distribution_f0=="log-normal" else "Mean f0 ± 1 STD"
            ymin, ymax = ax.get_ylim()
            ax.plot([hv.mean_f0_frq(distribution_f0)]*2, [ymin, ymax],
                    linestyle="-.", color="#000000", zorder=1, label="" if title=="Before Rejection" and rejection_bool else label )
            ax.fill([hv.nstd_f0_frq(-1, distribution_f0)]*2 + [hv.nstd_f0_frq(+1, distribution_f0)]*2, [ymin, ymax, ymax, ymin],
                    color = "#808080")
            ax.set_ylim((ymin, ymax))
            ax.set_xscale('log')
            ax.set_xlabel("Frequency (Hz)")
            ax.set_ylabel("H/V Ampltidue (#)")
            if rejection_bool:
                if title=="Before Rejection":
                    c_iter = hv.reject_windows(n, max_iterations=n_iteration, distribution_f0=distribution_f0, distribution_mc=distribution_mc)
                    print(f"Number of Iterations to Convergence: {c_iter} of {n_iteration} allowed.\n")
                elif title=="After Rejection":
                    fig.legend(ncol=4, loc='lower center', bbox_to_anchor=(0.5, 0))
            else:
                fig.legend(loc="upper center", bbox_to_anchor=(0.75, 0.3))
                break
            ax.set_title(title)

        norm_factor = sensor.normalization_factor
        for ax, timerecord, name in zip([ax0,ax1,ax2], [sensor.ns, sensor.ew, sensor.vt], ["NS", "EW", "VT"]):
            ctime = timerecord.time
            amp = timerecord.amp/norm_factor
            ax.plot(ctime.T, amp.T, linewidth=0.3, color='#cccccc')
            ax.set_title(f"Time Records ({name})")
            ax.set_yticks([-1, -0.5, 0, 0.5, 1])
            ax.set_xlim(0, windowlength*timerecord.n_windows)
            ax.set_ylim(-1, 1)
            ax.set_xlabel('Time (s)')
            ax.set_ylabel('Normalized Amplitude')
            for window_index in hv.rejected_window_indices:
                ax.plot(ctime[window_index], amp[window_index], linewidth=0.3, color="cyan")

        fig.tight_layout(h_pad=0.5, w_pad=0.5, rect=(0,0.07,1,1))

        figure_name_out = "example_hvsr_figure.png"
        fig.savefig(figure_name_out, dpi=300, bbox_inches='tight')
        file_name_out = "example_output.hv"
        hv.to_file_like_geopsy(file_name_out, distribution_f0, distribution_mc)

        plotly_fig = mpl_to_plotly(fig)
        n_windows = sensor.ns.n_windows
        n_rejected_windows = len(hv.rejected_window_indices)
        # SOURCE: https://community.plot.ly/t/is-it-possible-to-use-custom-plotly-offline-iplot-mpl-code-in-dash/6897
    return plotly_fig, windowlength, n_windows, n_rejected_windows

'''
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
            html.Hr(),
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
