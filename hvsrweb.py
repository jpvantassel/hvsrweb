import io
import base64

import numpy as np
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output, State
from flask import Flask
import pandas as pd
import xgboost as xgb
from sklearn import cluster
import plotly
import plotly.subplots
import plotly.graph_objs as go
import hvsrpy

# Style Settings
default_span_style = {"cursor": "context-menu",
                      "padding": "1em", "margin-top": "0em"}
default_p_style = {"margin-top": "0.5em", "margin-bottom": "0em"}
default_cardbody_style = {"min-height": "110vh"}

COLORS = {
    "error": "#f2190a",
    "primary": "#0d6efd",
    "link": "#495057"
}

HIDE_CONTAINER = dict(display="none")
DISPLAY_CONTAINER = dict(display="block")


intro_tab = dbc.Card(
    dbc.CardBody([
        dcc.Markdown("""
            ##### Welcome to HVSRweb

            HVSRweb is a web application for horizontal-to-vertical
            spectral ratio (HVSR) processing (Vantassel et al., 2021).
            HVSRweb utilizes _hvsrpy_ (Vantassel, 2020) behind Dash
            (Plotly, 2017) to offer a cloud-based tool for HVSR
            processing. HVSRweb is hosted on computing resources
            made available through the DesignSafe-CI
            (Rathje et al., 2017).

            ##### Citation

            If you use HVSRweb in your research or consulting we ask you
            please cite the following:

            Vantassel, J.P., Cox, B.R., & Brannon, D.M. (2021). HVSRweb:
            An Open-Source, Web-Based Application for
            Horizontal-to-Vertical Spectral Ratio Processing. IFCEE
            2021. https://doi.org/10.1061/9780784483428.005.

            ##### References

            Background information concerning the HVSR statistics can be
            found in the following references:

            Cox, B. R., Cheng, T., Vantassel, J. P., & Manuel, L.
            (2020). A statistical representation and frequency-domain
            window-rejection algorithm for single-station HVSR
            measurements. Geophysical Journal International, 221(3),
            2170-2183. https://doi.org/10.1093/gji/ggaa119.

            Cheng, T., Cox, B. R., Vantassel, J. P., & Manuel, L.
            (2020). A statistical approach to account for azimuthal
            variability in single-station HVSR measurements. Geophysical
            Journal International, 223(2), 1040-1053.
            https://doi.org/10.1093/gji/ggaa342.

            ##### Getting Started

            1. Progress to the __Data__ tab to upload your data,
            HVSRweb supports many different file formats
            (e.g., miniSEED, SAF, SAC, etc.).
            2. Make your __PreProcessing__ and __Processing__ selections
            in the associated tabs.
            3. After processing review the results of your HVSR analysis
            in the __Results__, __HVSR__, and __HVSR-3D__ tabs as
            applicable. 

            ##### More Information
            """),

            dbc.Row([
                html.P("Looking for a previous version of HVSRweb?", style=default_p_style),
                html.Div([
                    html.P(" Refer to the ",
                           style={**default_p_style, "display": "inline"}),
                    html.A("HVSRweb GitHub.", href="https://github.com/jpvantassel/hvsrweb",
                           style={"display": "inline"})
                ], style={"padding-left": "2em"})
            ]),

            dbc.Row([
                html.P("Looking for more information about the HVSR calculations?", style=default_p_style),
                html.Div([
                    html.P("See the ",
                           style={**default_p_style, "display": "inline"}),
                    html.A("hvsrpy GitHub.", href="https://github.com/jpvantassel/hvsrpy",
                           style={"display": "inline"})
                ], style={"padding-left": "2em"})
            ]),
    ],
        style=default_cardbody_style),
    className="mt-3 md-4",
)

data_tab = dbc.Card(
    dbc.CardBody(
        [
            html.P([
                html.Span(
                    "Data Upload:",
                    style=default_span_style,
                ),
            ], style=default_p_style),

            dcc.Upload(
                children=html.Div(children=html.P("Drag & drop or Click to select file(s)",
                                                  style={"font-size": "1em"})),
                id="upload-bar",
                style={
                    "height": "4em",
                    "lineHeight": "4em",
                    "textAlign": "center",
                    "cursor": "pointer",
                    "background-color": "white",
                    "color": "black",
                    "border": "0.1em solid #dedede",
                    "border-radius": "0.5em",
                    # "padding":"1em",
                },
                multiple=True,
            ),

            html.P([
                html.Span(
                    "OR",
                    style=default_span_style,
                ),
            ], style={**default_p_style, "text-align": "center"}),

            dbc.Row(children=[
                    dbc.Button(children="Load Demo Data", id="demo-button",
                               color="primary", size="lg", style={"padding": "1em"}),
                    dbc.Tooltip(children="Load ambient noise data provided by us.",
                                id="demo-button-tooltip",
                                target="demo-button"),
                    ],
                    style={"text-align": "center", "margin": "1em"}),

            dbc.Row([
                html.H6(children="",
                        id="data-continue-instructions",
                        style={"display": "inline", "margin-top": "2em", "margin-bottom": "2em", "text-align": "center"}),
            ]),

        ], style=default_cardbody_style),
    className="mt-3 md-4",
)

preprocess_tab = dbc.Card(
    dbc.CardBody(
        [
            # processing-workflow
            html.P([
                html.Span(
                    "Processing Workflow:",
                    id="processing-workflow-target",
                    style=default_span_style,
                ),
            ], style=default_p_style),
            dbc.Tooltip("""
                        Workflow for processing the HVSR data.
                        """,
                        target="processing-workflow-target",
                        ),
            dbc.Select(id="processing-workflow",
                       options=[
                           dict(label="Manual", value="manual"),
                           dict(label="AutoHVSR", value="autohvsr"),
                       ],
                       ),


            # preprocess-default-container (start)
            dbc.Container([
                # trim
                html.P([
                    html.Span(
                        "Start & End Times (s):",
                        id="new-start-and-end-time-tooltip-target",
                        style=default_span_style,
                    ),
                ], style=default_p_style),
                dbc.Tooltip("""
                        New start and end times for the time-domain
                        recording in seconds.
                        """,
                            target="new-start-and-end-time-tooltip-target",
                            ),
                dbc.Row([dbc.Col([dbc.Input(id="new-start-time", type="number",
                                            value=0, min=0, max=99999, step=1),]),
                         dbc.Col([dbc.Input(id="new-end-time", type="number",
                                            value=0, min=0, max=99999, step=1),])
                         ]),
                dbc.Tooltip("New start time in seconds.",
                            target="new-start-time"),
                dbc.Tooltip("New end time in seconds.",
                            target="new-end-time"),

                # orient-to-degrees-from-north
                html.P([
                    html.Span(
                        "Rotate Sensor (degree):",
                        id="orient-to-degrees-from-north-tooltip-target",
                        style=default_span_style,
                    ),
                ], style=default_p_style),
                dbc.Tooltip("""
                        Rotate sensor to new orientation. The sensor's
                        new orientation is defined in degrees from north
                        (clockwise positive). The sensor's north
                        component will be oriented such that it is
                        aligned with the defined orientation.
                        """,
                            target="orient-to-degrees-from-north-tooltip-target",
                            ),
                dbc.Input(id="orient-to-degrees-from-north", type="number",
                          value=0, min=0, max=360, step=1),

                # butterworth-filter
                html.P([
                    html.Span(
                        "Butterworth Filter",
                        id="butterworth-filter-tooltip-target",
                        style=default_span_style,
                    ),
                ], style=default_p_style),
                dbc.Tooltip("""
                        Select type of Butterworth filter to be applied
                        to the time-domain recording.
                        """,
                            target="butterworth-filter-tooltip-target",
                            ),
                dbc.Select(
                    id="butterworth-filter",
                    options=[
                        dict(label="Bandpass", value="bandpass"),
                        dict(label="Lowpass", value="lowpass"),
                        dict(label="Highpass", value="highpass"),
                        dict(label="None", value="none"),
                    ], value="none"),

                # butterworth-filter-lower-frequency
                dbc.Container([
                    html.P([
                        html.Span(
                            "Low-cut Frequency (Hz):",
                            id="butterworth-filter-lower-frequency-tooltip-target",
                            style=default_span_style,
                        ),
                    ], style=default_p_style),
                    dbc.Tooltip(
                        "Frequencies below that specified will be filtered.",
                        target="butterworth-filter-lower-frequency-tooltip-target",
                    ),
                    dbc.Input(id="butterworth-filter-lower-frequency", type="number",
                              value=0.1, min=0, max=100, step=0.01),
                ], className="ml-2 mr-0", id="butterworth-filter-lower-frequency-container"),

                # butterworth-filter-upper-frequency
                dbc.Container([
                    html.P([
                        html.Span(
                            "High-cut Frequency (Hz):",
                            id="butterworth-filter-upper-frequency-tooltip-target",
                            style=default_span_style,
                        ),
                    ], style=default_p_style),
                    dbc.Tooltip(
                        "Frequencies above that specified will be filtered.",
                        target="butterworth-filter-upper-frequency-tooltip-target",
                    ),
                    dbc.Input(id="butterworth-filter-upper-frequency", type="number",
                              value=30, min=0, max=100, step=0.01),
                ], className="ml-2 mr-0", id="butterworth-filter-upper-frequency-container"),

            ], id="preprocess-default-container", style=HIDE_CONTAINER),
            # preprocess-default-container (end)

            # traditional-container (start)
            dbc.Container([
                # window-length
                html.P([
                    html.Span(
                        "Window Length (s):",
                        id="window-length-tooltip-target",
                        style=default_span_style,
                    ),
                ], style=default_p_style),
                dbc.Tooltip("""
                        Length of each time window in seconds.
                        SESAME (2004) recommends 10 significant cycles
                        per window.
                        """,
                            target="window-length-tooltip-target",
                            ),
                dbc.Input(id="window-length", type="number",
                          value=100, min=0, max=600, step=1),
            ], id="traditional-container", style=HIDE_CONTAINER),
            # traditional-container (end)

            # preprocess-default-container-continued (start)
            dbc.Container([
                # detrend
                html.P([
                    html.Span(
                        "Detrend:",
                        id="detrend-tooltip-target",
                        style=default_span_style,
                    ),
                ], style=default_p_style),
                dbc.Tooltip("""
                        Type of detrend to be performed.
                        """,
                            target="detrend-tooltip-target",
                            ),
                dbc.Select(id="detrend",
                           options=[
                               dict(label="Linear", value="linear"),
                               dict(label="Constant", value="constant"),
                               dict(label="None", value="none"),
                           ],
                           value="linear"),
            ], id="preprocess-default-container-continued", style=HIDE_CONTAINER),
            # preprocess-default-container-continued (end)

            # preprocess-button
            dbc.Row(
                children=[
                    dbc.Button(children="Preprocess", id="preprocess-button",
                               color="primary", size="lg", style={"padding": "1em"}),
                    dbc.Tooltip(children="Apply preprocessing settings to time-domain data.",
                                target="preprocess-button"),
                ], style={"text-align": "center", "margin": "1em"}
            ),

            # preprocess-continue-instructions
            dbc.Row([
                html.H6(children="",
                        id="preprocess-continue-instructions",
                        style={"display": "inline", "margin-top": "2em", "margin-bottom": "2em", "text-align": "center"}),
            ]),

        ], style=default_cardbody_style),
    className="mt-3",
)

process_tab = dbc.Card(
    dbc.CardBody(
        [
            # process-method
            html.P([
                html.Span(
                    "Processing Method:",
                    id="process-method-tooltip-target",
                    style=default_span_style,
                ),
            ], style=default_p_style),
            dbc.Tooltip("""
                        Select method for HVSR processing.
                        """,
                        target="process-method-tooltip-target",
                        ),
            dbc.Select(id="process-method",
                       options=[
                           dict(label="Traditional", value="traditional"),
                           dict(label="Azimuthal", value="azimuthal"),
                           dict(label="Diffuse Field", value="diffuse"),
                       ],
                       ),

            # combine-horizontals-container (start)
            dbc.Container([
                html.P([
                    html.Span(
                        "Method to Combine Horizontals:",
                        id="combine-horizontals-tooltip-target",
                        style=default_span_style,
                    ),
                ], style=default_p_style),
                dbc.Tooltip("""
                            Select a method to combine the horizontal
                            components.
                            """,
                            target="combine-horizontals-tooltip-target",
                            ),
                dbc.Select(id="combine-horizontals-select",
                           options=[
                               dict(label="Geometric Mean", value="geometric_mean"),
                               dict(label="Single Azimuth", value="single_azimuth"),
                               dict(label="RotDpp", value="rotdpp"),
                               dict(label="Arithmetic Mean", value="arithmetic_mean"),
                               dict(label="Squared Average", value="squared_average"),
                               dict(label="Quadratic Mean", value="quadratic_mean"),
                               dict(label="Total Horizontal Energy",
                                    value="total_horizontal_energy"),
                               dict(label="Maximum Horizontal Value",
                                    value="maximum_horizontal_value"),
                           ],
                           ),
            ], id="combine-horizontals-container", style=HIDE_CONTAINER),
            # combine-horizontals-container (end)

            # process-base-container (start)
            dbc.Container([

                # window-type-and-width
                html.P([
                    html.Span(
                        "Tapering Window:",
                        id="window-type-and-width-tooltip-target",
                        style=default_span_style,
                    ),
                ], style=default_p_style),
                dbc.Tooltip("""
                            Window function and associated width applied
                            to each window.
                            """,
                            target="window-type-and-width-tooltip-target",
                            ),
                dbc.Row([
                    dbc.Col([
                        dbc.Select(id="window-type",
                                   options=[dict(label="Tukey", value="tukey")],
                                   value="tukey"
                                   ),
                    ], md=8),
                    dbc.Col([
                        dbc.Input(id="window-width", type="number",
                                  value=0.1, min=0., max=1.0, step=0.1),
                    ], md=4)
                ]),

                # smoothing-operator-and-bandwidth
                html.P([
                    html.Span(
                        "Smoothing Operator:",
                        id="smoothing-operator-and-bandwidth-tooltip-target",
                        style=default_span_style,
                    ),
                ], style=default_p_style),
                dbc.Tooltip("""
                            Smoothing operator and associated bandwidth
                            to be used on the raw horizontal and
                            vertical Fourier spectra.
                            """,
                            target="smoothing-operator-and-bandwidth-tooltip-target",
                            ),
                dbc.Row([
                    dbc.Col([
                        dbc.Select(id="smoothing-operator",
                                   options=[
                                       dict(label="Konno and Ohmachi", value="konno_and_ohmachi"),
                                       dict(label="Parzen", value="parzen"),
                                       dict(label="Savitzky and Golay", value="savitzky_and_golay"),
                                       dict(label="Linear Rectangular", value="linear_rectangular"),
                                       dict(label="Log Rectangular", value="log_rectangular"),
                                       dict(label="Linear Triangular", value="linear_triangular"),
                                       dict(label="Log Triangular", value="log_triangular"),
                                   ],
                                   value="konno_and_ohmachi"
                                   ),
                    ], md=8),
                    dbc.Col([
                        dbc.Input(id="smoothing-bandwidth", type="number",
                                  value=40., min=0., max=100, step=0.01),
                    ], md=4)
                ]),
            ], id="process-base-container", style=HIDE_CONTAINER),
            # process-base-container (end)


            # frequency-sampling-container (start)
            dbc.Container([
                # frequency-sampling
                html.P([
                    html.Span(
                        "Frequency Sampling:",
                        style=default_span_style,
                    ),
                ], style=default_p_style),
                dbc.Row([
                    dbc.Col([
                        dbc.Input(id="minimum-frequency", type="number",
                                  value=0.2, min=0.001, max=999, step=0.001),
                    ]),
                    dbc.Col([
                        dbc.Input(id="maximum-frequency", type="number",
                            value=20, min=1, max=100, step=1),
                    ]),
                    dbc.Col([
                        dbc.Input(id="n-frequency", type="number",
                            value=256, min=32, max=4096, step=1),
                    ]),
                ]),

                dbc.Row([
                    dbc.Col([
                        dbc.Select(id="sampling-type-frequency",
                                   options=[
                                       {"label": "Logarithmic", "value": "log"},
                                       {"label": "Linear", "value": "linear"},
                                   ],
                                   value="log",
                                   ),
                    ]),
                ]),

                dbc.Tooltip(
                    "Minimum frequency considered when resampling in Hz.",
                    target="minimum-frequency",
                ),
                dbc.Tooltip(
                    "Maximum frequency considered when resampling in Hz.",
                    target="maximum-frequency",
                ),
                dbc.Tooltip(
                    "Number of frequency points to consider when resampling.",
                    target="n-frequency",
                ),
                dbc.Tooltip(
                    "Distribution of frequency samples.",
                    target="sampling-type-frequency",
                ),
            ], id="frequency-sampling-container", style=HIDE_CONTAINER),
            # frequency-sampling-container (end)


            # traditional-traditional (start)
            dbc.Container([

            ], id="traditional-traditional", style=HIDE_CONTAINER),
            # traditional-traditional (end)


            # traditional-single-azimuthal (start)
            dbc.Container([
                html.P([
                    html.Span(
                        "Azimuth (degree):",
                        id="traditional-single-azimuthal-tooltip-target",
                        style=default_span_style,
                    ),
                ], style=default_p_style),
                dbc.Tooltip("""
                            Azimuth direction for HVSR computation.
                            """,
                            target="traditional-single-azimuthal-tooltip-target",
                            ),
                dbc.Input(id="single-azimuth", type="number",
                          value=0, min=0., max=360., step=1.),
            ], id="traditional-single-azimuth", style=HIDE_CONTAINER),
            # traditional-single-azimuthal (end)


            # traditional-rotdpp (start)
            dbc.Container([
                # rotdpp-azimuthal-interval
                html.P([
                    html.Span(
                        "Azimuthal Interval (degree):",
                        id="rotdpp-azimuthal-interval-tooltip-target",
                        style=default_span_style,
                    ),
                ], style=default_p_style),
                dbc.Tooltip("""
                                Interval azimuth between measurements for HVSR.
                                An azimuthal interval of 5 indicates that HVSR
                                will be computed every 5 degrees between 0
                                and 180 for the determination of RotDpp.
                                """,
                            target="rotdpp-azimuthal-interval-tooltip-target",
                            ),
                dbc.Input(id="rotdpp-azimuthal-interval", type="number",
                          value=5, min=1., max=180., step=1.),

                # rotdpp-azimuthal-ppth-percentile
                html.P([
                    html.Span(
                        "ppth Percential (%):",
                        id="rotdpp-azimuthal-ppth-percentile-tooltip-target",
                        style=default_span_style,
                    ),
                ], style=default_p_style),
                dbc.Tooltip("""
                                Percentile for RotDpp computation. A value
                                of 50 would result in the computation of RotD50.
                                """,
                            target="rotdpp-azimuthal-ppth-percentile-tooltip-target",
                            ),
                dbc.Input(id="rotdpp-azimuthal-ppth-percentile", type="number",
                          value=50, min=0, max=100, step=1.),
            ], id="traditional-rotdpp", style=HIDE_CONTAINER),
            # traditional-rotdpp (end)


            # azimuthal (start)
            dbc.Container([
                # azimuthal-interval
                html.P([
                    html.Span(
                        "Azimuthal Interval (degree):",
                        id="azimuthal-interval-tooltip-target",
                        style=default_span_style,
                    ),
                ], style=default_p_style),
                dbc.Tooltip("""
                                Interval between azimuths for HVSR computation.
                                An azimuthal interval of 5 indicates that HVSR
                                will be computed every 5 degrees between 0
                                and 180.
                                """,
                            target="azimuthal-interval-tooltip-target",
                            ),
                dbc.Input(id="azimuthal-interval", type="number",
                          value=5, min=1., max=180., step=1.),
            ], id="azimuthal", style=HIDE_CONTAINER),
            # azimuthal (end)


            # statistics-container (start)
            dbc.Container([

                # distribution-resonance
                html.P([
                    html.Span(
                        "Distribution of Resonance:",
                        id="distribution-resonance-tooltip-target",
                        style=default_span_style,
                    ),
                ], style=default_p_style),
                dbc.Tooltip("""
                            Distribution of the HVSR resonance(s)
                            identified during processing. Applies in
                            terms of both frequency and amplitude.
                            """,
                            target="distribution-resonance-tooltip-target",
                            ),
                dbc.Select(id="distribution-resonance",
                           options=[
                               dict(label="Lognormal", value="lognormal"),
                               dict(label="Normal", value="normal"),
                           ],
                           value="lognormal"
                           ),

                # distribution-mean-curve
                html.P([
                    html.Span(
                        "Distribution of Mean Curve:",
                        id="distribution-mean-curve-tooltip-target",
                        style=default_span_style,
                    ),
                ], style=default_p_style),
                dbc.Tooltip("""
                            Distribution of the mean curve.
                            """,
                            target="distribution-mean-curve-tooltip-target",
                            ),
                dbc.Select(id="distribution-mean-curve",
                           options=[
                               dict(label="Lognormal", value="lognormal"),
                               dict(label="Normal", value="normal"),
                           ],
                           value="lognormal"
                           ),

            ], id="statistics-container", style=HIDE_CONTAINER),
            # statistics-container (start)


            # resonance-search-range-container (start)
            dbc.Container([
                # resonance-search-range
                html.P([
                    html.Span(
                        "Resonance Search Range:",
                        style=default_span_style,
                    ),
                ], style=default_p_style),
                dbc.Row([
                    dbc.Col([
                        dbc.Input(id="minimum-search-frequency", type="number",
                                  value=0, min=0, max=999, step=0.001),
                    ]),
                    dbc.Col([
                        dbc.Input(id="maximum-search-frequency", type="number",
                            value=100, min=0, max=999, step=0.001),
                    ]),
                ]),
                dbc.Tooltip(
                    """
                    Lowest frequency in Hz considered when searching
                    for peaks in the HVSR curve.
                    """,
                    target="minimum-search-frequency",
                ),
                dbc.Tooltip(
                    """
                    Highest frequency in Hz considered when searching
                    for peaks in the HVSR curve.
                    """,
                    target="maximum-search-frequency",
                )], id="resonance-search-range-container", style=HIDE_CONTAINER),
            # resonance-search-range-container (end)


            # rejection (start)
            dbc.Container([

                # rejection-select
                html.P([
                    html.Span(
                        "Apply Window Rejection Algorithm:",
                        id="rejection-select-tooltip-target",
                        style=default_span_style,
                    ),
                ], style=default_p_style),
                dbc.Tooltip("""
                            Select which (if any) window rejection
                            algorithm will be applied during the HVSR
                            computation.
                            """,
                            target="rejection-select-tooltip-target",
                            ),
                dbc.Select(id="rejection-select",
                           options=[
                               dict(label="No", value="False"),
                               dict(
                                   label="Frequency-Domain Window Rejection Algorithm (Cox et al., 2020)", value="fdwra"),
                           ],
                           value="fdwra"
                           ),

                # fdwra (start)
                dbc.Container([

                    # fdwra-n
                    html.P([
                        html.Span(
                            "Number of Standard Deviations:",
                            id="fdwra-n-tooltip-target",
                            style=default_span_style,
                        ),
                    ], style=default_p_style),
                    dbc.Tooltip("""
                                Number of standard deviations to consider during
                                rejection. Smaller values will tend to reject more
                                windows than larger values.
                                """,
                                target="traditional-single-azimuthal-tooltip-target",
                                ),
                    dbc.Input(id="fdwra-n", type="number",
                              value=2.5, min=0.5, max=4, step=0.5),

                    # fdwra-max-iteration
                    html.P([
                        html.Span(
                            "Maximum Number of Allowed Iterations:",
                            id="fdwra-max-iteration-tooltip-target",
                            style=default_span_style,
                        ),
                    ], style=default_p_style),
                    dbc.Tooltip("""
                                Maximum number of iterations allowed for the
                                algorithm to converge.
                                """,
                                target="fdwra-max-iteration-tooltip-target",
                                ),
                    dbc.Input(id="fdwra-max-iteration", type="number",
                              value=50, min=5., max=75., step=5.),

                ], id="fdwra"),
                # fdwra (end)

            ], id="rejection", style=HIDE_CONTAINER),
            # rejection (end)


            # diffuse (start)
            dbc.Container([

            ], id="diffuse", style=HIDE_CONTAINER),
            # diffuse (end)


            # process-button
            dbc.Row(
                children=[
                    dbc.Button(children="Process", id="process-button",
                               color="primary", size="lg", style={"padding-left": "2em", "padding-right": "2em"}),
                    dbc.Tooltip(children="Apply processing settings to compute HVSR.",
                                target="process-button"),
                ], style={"padding": "2em"}
            ),


            # process-continue-instructions
            dbc.Row([
                html.H6(children="",
                        id="process-continue-instructions",
                        style={"display": "inline", "margin-top": "2em", "margin-bottom": "2em", "text-align": "center"}),
            ]),

        ], style=default_cardbody_style),
    className="mt-3 md-4",
)

results_tab = dbc.Card(
    dbc.CardBody(
        [
            html.P([
                html.Span("General Summary:",
                          style=default_span_style),
            ], style=default_p_style),
            dbc.Row(dbc.Col(id="general-summary-table")),

            html.P([
                html.Span("Resonance Summary:",
                          style=default_span_style),
            ], style=default_p_style),
            dbc.Row(dbc.Col(id="results-table")),

            dbc.Container([
                html.P([
                    html.Span("2nd Resonance Summary:",
                          style=default_span_style),
                ], style=default_p_style),
                dbc.Row(dbc.Col(id="results-table-1")),
            ], id="results-table-1-container", style=HIDE_CONTAINER),

            dbc.Container([
                html.P([
                    html.Span("3rd Resonance Summary:",
                          style=default_span_style),
                ], style=default_p_style),
                dbc.Row(dbc.Col(id="results-table-2")),
            ], id="results-table-2-container", style=HIDE_CONTAINER),

            dbc.Container([
                html.P([
                    html.Span("4th Resonance Summary:",
                          style=default_span_style),
                ], style=default_p_style),
                dbc.Row(dbc.Col(id="results-table-3")),
            ], id="results-table-3-container", style=HIDE_CONTAINER),

            dbc.Container([
                html.P([
                    html.Span("5th Resonance Summary:",
                          style=default_span_style),
                ], style=default_p_style),
                dbc.Row(dbc.Col(id="results-table-4")),
            ], id="results-table-4-container", style=HIDE_CONTAINER),

            dbc.Container([
                html.P([
                    html.Span("6th Resonance Summary:",
                          style=default_span_style),
                ], style=default_p_style),
                dbc.Row(dbc.Col(id="results-table-5")),
            ], id="results-table-5-container", style=HIDE_CONTAINER),

            # html.P([
            #     html.Span("Download Results:",
            #               style=default_span_style),
            # ], style=default_p_style),
            dbc.Row([
                # dbc.Col([
                    html.A(
                        dbc.Button(children="Download Results", id="button-save-hvsrpy",
                                   color="primary", size="lg", style={"width": "100%", "padding-left": "2em", "padding-right": "2em", "margin": "0"}),
                        id="hvsrpy-download", download="", href="", target="_blank", style={"width": "100%", "padding": "0", "margin": "0"}),

                    # style={"padding-left": "2em", "padding-right": "2em"}

                    # ]),
                    # TODO(jpv): Skip for now
                    # dbc.Col([
                    #     html.A(
                    #         dbc.Button("Save as geopsy", color="primary", size="md",
                    #                    id="button-save-geopsy", style=dict(width="80%")),
                    #         id="geopsy-download", download="", href="", target="_blank"),
                    # ]),

                    ], style={"padding-left": "2em", "padding-right": "2em", "padding-top": "0.5em", "padding-bottom": "1em"}),

            # dbc.Tooltip(
            #     "Save results as a .",
            #     target="button-save-hvsrpy"),
            # TODO(jpv): Skip for now
            # dbc.Tooltip(
            #     "Save results in the geopsy-style text format.",
            #     target="button-save-geopsy"),

            dbc.Row([
                html.P("Looking for more information?", style=default_p_style),
                html.Div([
                    html.P("Refer to the references back in the ",
                           style={**default_p_style, "display": "inline"}),
                    html.P("Intro ",
                           style={**default_p_style, "display": "inline", "font-weight":"bold"}),
                    html.P(" tab.",
                           style={**default_p_style, "display": "inline"}),

                ], style={"padding-left": "2em"})
            ]),

            dbc.Row([
                html.P("Looking for more functionality?", style=default_p_style),
                html.Div([
                    html.P("Checkout ",
                           style={**default_p_style, "display": "inline"}),
                    html.A("hvsrpy.", href="https://github.com/jpvantassel/hvsrpy",
                           style={"display": "inline"})
                ], style={"padding-left": "2em"})
            ]),

            dbc.Row([
                html.P("Looking for an earlier version of HVSRweb?", style=default_p_style),
                html.Div([
                    html.P("Find instructions on the ",
                           style={**default_p_style, "display": "inline"}),
                    html.A("HVSRweb GitHub.",
                           href="https://github.com/jpvantassel/hvsrweb", style={"display": "inline"})
                ], style={"padding-left": "2em"})
            ]),
        ], style=default_cardbody_style),
    className="mt-3 md-4",
)

application = Flask(__name__)
app = dash.Dash(server=application, external_stylesheets=[dbc.themes.BOOTSTRAP])

tab_label_style = dict(padding="0.5em")
app.title = "HVSRweb: A web application for HVSR processsing"
app.layout = html.Div(
    [
        html.Div(
            id="banner",
            className="banner",
            children=[html.Img(src=app.get_asset_url("hvsrweb_logo.png")),
                      html.H4("HVSRweb: A web application for HVSR processing")]
        ),
        dbc.Container([

            dbc.Row([
                dbc.Col(
                    children=[
                        dbc.Tabs(children=[
                            dbc.Tab(intro_tab, id="intro-tab",
                                    label="Intro", label_style=tab_label_style),
                            dbc.Tab(data_tab, id="data-tab",
                                    label="Data", label_style=tab_label_style),
                            dbc.Tab(preprocess_tab, id="preprocess-tab",
                                    label="Preprocess", disabled=True, label_style=tab_label_style),
                            dbc.Tab(process_tab, id="process-tab",
                                    label="Process", disabled=True, label_style=tab_label_style),
                            dbc.Tab(results_tab, id="results-tab",
                                    label="Results", disabled=True, label_style=tab_label_style),
                        ]),
                    ],
                    md=4,
                ),

                dbc.Col(
                    children=[
                        dbc.Tabs(children=[
                            dbc.Tab(label="Seismic Record",
                                    children=[dbc.Card(dbc.CardBody(children=[
                                        dbc.Row(
                                            children=[
                                                html.Div([
                                                    html.H6(children="Current File:",
                                                            style={"display": "inline", "margin-top": "1em", "margin-bottom": "1em"}),
                                                    html.P(children="No file has been uploaded.",
                                                           id="filename-display",
                                                           style={"display": "inline", "padding": "0.25em", "margin-left": "0.5em"}),
                                                ]),
                                            ],
                                        ),
                                        html.Div(id="plot-seismic-record", className="p-4")], style=default_cardbody_style), className="mt-3"),
                                    ],
                                    label_style=tab_label_style),
                            dbc.Tab(label="HVSR",
                                    id="plot-hvsr-tab",
                                    disabled=True,
                                    children=[dbc.Card(dbc.CardBody(children=[
                                        dbc.Row(
                                            children=[
                                                html.Div([
                                                    html.H6(children="Current File:",
                                                            style={"display": "inline", "margin-top": "1em", "margin-bottom": "1em"}),
                                                    html.P(children="No file has been uploaded.",
                                                           id="filename-display-hvsr",
                                                           style={"display": "inline", "padding": "0.25em", "margin-left": "0.5em"}),
                                                ]),
                                            ],
                                        ),
                                        dbc.Row(
                                            html.Div(html.Div(id="plot-hvsr", style={'display': 'inline-block', 'width': '100%', 'height': "100%"}),
                                                     style={'display': 'inline-block', 'width': '100%', 'min-height': "600px"})
                                        )
                                    ], style=default_cardbody_style), className="mt-3"),
                                    ],
                                    label_style=tab_label_style),
                            dbc.Tab(label="HVSR - 3D",
                                    id="plot-hvsr-3d-tab",
                                    disabled=True,
                                    children=[dbc.Card(dbc.CardBody(children=[
                                        dbc.Row(
                                            children=[
                                                html.Div([
                                                    html.H6(children="Current File:",
                                                            style={"display": "inline", "margin-top": "1em", "margin-bottom": "1em"}),
                                                    html.P(children="No file has been uploaded.",
                                                           id="filename-display-hvsr-az",
                                                           style={"display": "inline", "padding": "0.25em", "margin-left": "0.5em"}),
                                                ]),
                                            ],
                                        ),
                                        dbc.Row(
                                            html.Div(html.Div(id="plot-hvsr-3d", style={'display': 'inline-block', 'width': '100%', 'height': "100%"}),
                                                     style={'display': 'inline-block', 'width': '100%', 'min-height': "600px"})
                                        )
                                    ],  style=default_cardbody_style), className="mt-3"),
                                    ],
                                    label_style=tab_label_style),
                        ]),
                    ],
                    md=8,
                ),
            ]),
            dcc.Store(id='srecord3c'),
            dcc.Store(id='preprocess-settings'),
            dcc.Store(id='process-settings'),
            dcc.Store(id='reset-to-preprocess-step'),
            dcc.Store(id='reset-to-process-step'),
        ], fluid=True),

        html.Footer(dbc.Container(children=[html.Div("HVSRweb v0.3.0 © 2019-2023"),
                                            html.Div("Joseph P. Vantassel & Dana M. Brannon")],
                                  className="text-muted"),
                    className="footer")
    ],
)


dbc.Tooltip(children="The preprocess tab is disabled; you must upload data first.",
            id="preprocess-tab-tooltip",
            target="preprocess-tab"),
dbc.Tooltip(children="The process tab is disabled; you must preprocess your data first.",
            id="process-tab-tooltip",
            target="process-tab"),
dbc.Tooltip(children="Results disabled; you must process your data first.",
            id="results-tab-tooltip",
            target="results-tab"),
dbc.Tooltip(children="HVSR 3D results are only available following azimuthal processing.",
            id="hvsr-3d-tooltip",
            target="hvsr-3d"),


@ app.callback(
    [Output('reset-to-preprocess-step', 'data'),
     Output('reset-to-process-step', 'data'),
    ],
    [Input('demo-button', 'n_clicks'),
     Input('upload-bar', 'filename'),
     Input("butterworth-filter", "value"),
     Input('butterworth-filter-lower-frequency', "value"),
     Input('butterworth-filter-upper-frequency', "value"),
     Input('processing-workflow', "value"),
     Input('new-start-time', "value"),
     Input('new-start-time', "value"),
     Input('orient-to-degrees-from-north', "value"),
     Input('window-length', "value"),
     Input('detrend', "value"),
     Input("process-method", "value"),
     Input("combine-horizontals-select", "value"),
     Input("window-type", "value"),
     Input("window-width", "value"),
     Input("smoothing-operator", "value"),
     Input("smoothing-bandwidth", "value"),
     Input("minimum-frequency", "value"),
     Input("maximum-frequency", "value"),
     Input("n-frequency", "value"),
     Input("sampling-type-frequency", "value"),
     Input("single-azimuth", "value"),
     Input("rotdpp-azimuthal-interval", "value"),
     Input("rotdpp-azimuthal-ppth-percentile", "value"),
     Input("azimuthal-interval", "value"),
     Input("distribution-resonance", "value"),
     Input("distribution-mean-curve", "value"),
     Input("minimum-search-frequency", "value"),
     Input("maximum-search-frequency", "value"),
     Input("rejection-select", "value"),
     Input("fdwra-n", "value"),
     Input("fdwra-max-iteration", "value"),
     ]
)
def the_listener(*args):
    """Display/Hide Tab; Keep/Remove Message"""
    triggered_id = dash.ctx.triggered_id

    # changes to data tab
    if triggered_id in ["demo-button", "upload-bar"]:
        return (
            (True, True),  # preprocessing: disable tab; disable text
            (True, True),  # processing: disable tab; disable text
        )

    # changes to preprocess tab
    if triggered_id in ["butterworth-filter",
                        "butterworth-filter-lower-frequency",
                        "butterworth-filter-upper-frequency",
                        "processing-workflow",
                        "new-start-time",
                        "new-end-time",
                        "orient-to-degrees-from-north",
                        "window-length",
                        "detrend"]:
        return (
            (True, True),  # preprocessing: disable tab; disable text
            (True, True),  # processing: disable tab; disable text
        )

    # changes to process tab
    if triggered_id in ["process-method",
                        "combine-horizontals-select",
                        "window-type",
                        "window-width",
                        "smoothing-operator",
                        "smoothing-bandwidth",
                        "minimum-frequency",
                        "maximum-frequency",
                        "n-frequency",
                        "sampling-type-frequency",
                        "single-azimuth",
                        "rotdpp-azimuthal-interval",
                        "traditional-rotdpp",
                        "azimuthal-interval",
                        "distribution-resonance",
                        "distribution-mean-curve",
                        "minimum-search-frequency",
                        "maximum-search-frequency",
                        "rejection-select",
                        "fdwra-n",
                        "fdwra-max-iteration",
                        ]:
        return (
            (False, False),   # preprocessing: disable tab; disable text
            (True, True),   # processing: disable tab; disable text
        )

    raise PreventUpdate


@ app.callback(
    [Output('filename-display', 'children'),
     Output('filename-display-hvsr', 'children'),
     Output('filename-display-hvsr-az', 'children'),
     Output('srecord3c', 'data'),
     Output('data-continue-instructions', 'children'),
     Output('data-continue-instructions', 'style'),
     Output('new-end-time', "value"),
     Output('preprocess-tab', 'disabled')],
    [Input('demo-button', 'n_clicks'),
     Input('upload-bar', 'contents')],
    [State('upload-bar', 'filename'),
     State('data-continue-instructions', 'style')])
def gather_filename_from_user(demo_button_n_clicks, upload_bar_contents,
                              upload_bar_filename, data_continue_instructions_style):
    """Acquire filename and update web components accordingly."""
    triggered_id = dash.ctx.triggered_id

    if triggered_id == "demo-button":
        srecord3c = hvsrpy.read_single("data/UT.STN11.A2_C150.miniseed")
        return ("Demo file",
                "Demo file",
                "Demo file",
                srecord3c._to_dict(),
                "Data loading complete. Continue to the Preprocess tab.",
                {**data_continue_instructions_style, "color": COLORS["primary"]},
                np.floor(srecord3c.vt.time()[-1]),
                False,
                )

    # if upload bar has been used.
    if triggered_id == "upload-bar":

        # loop across upload_bar_contents (one entry per file selected for upload).
        decoded_contents = []
        for upload_bar_content in upload_bar_contents:
            _, string = upload_bar_content.split(",")
            decoded_contents.append(base64.b64decode(string, validate=True))

        # only accept a single file or a set of three files.
        if len(decoded_contents) not in [1, 3]:
            return ("No file has been uploaded.",
                    "No file has been uploaded.",
                    "No file has been uploaded.",
                    None,
                    f"Incorrect number of files selected, must be 1 or 3.",
                    {**data_continue_instructions_style, "color": COLORS["error"]},
                    0,
                    True,
                    )

        # dash loads data as base64 encoded, but we do not know
        # whether the underlying data is from a binary format
        # (e.g., miniseed) or a text format (e.g., saf) so we need to
        # check both with nested try statements.
        try:
            file_contents = [io.BytesIO(content) for content in decoded_contents]
            file_contents = file_contents if len(file_contents) == 3 else file_contents[0]
            srecord3c = hvsrpy.read_single(file_contents)
        except Exception as e:
            try:
                file_contents = [io.StringIO(content.decode("utf-8"))
                                 for content in decoded_contents]
                file_contents = file_contents if len(file_contents) == 3 else file_contents[0]
                srecord3c = hvsrpy.read_single(file_contents)
            except Exception as e:
                return ("No file has been uploaded.",
                        "No file has been uploaded.",
                        "No file has been uploaded.",
                        None,
                        "An error occured; the selected file type is not supported. Please contact the developer if you believe this is in error.",
                        {**data_continue_instructions_style, "color": COLORS["error"]},
                        0,
                        True,
                        )

        srecord3c.meta["file name(s)"] = upload_bar_filename

        return (f"{', '.join(upload_bar_filename)}",
                f"{', '.join(upload_bar_filename)}",
                f"{', '.join(upload_bar_filename)}",
                srecord3c._to_dict(),
                "Data loading complete. Continue to the Preprocess tab.",
                {**data_continue_instructions_style, "color": COLORS["primary"]},
                np.floor(srecord3c.vt.time()[-1]),
                False,
                )

    raise PreventUpdate


def plot_srecord3c(srecord3c):
    fig = plotly.subplots.make_subplots(rows=3, cols=1, shared_xaxes=True, shared_yaxes=True,
                                        x_title="Time (s)", y_title="Amplitude (counts)", vertical_spacing=0.03)
    fig.add_trace(go.Scatter(x=srecord3c.ns.time(),
                  y=srecord3c.ns.amplitude, name="NS"), row=1, col=1)
    fig.add_trace(go.Scatter(x=srecord3c.ew.time(),
                  y=srecord3c.ew.amplitude, name="EW"), row=2, col=1)
    fig.add_trace(go.Scatter(x=srecord3c.vt.time(),
                  y=srecord3c.vt.amplitude, name="VT"), row=3, col=1)
    fig.update_layout(margin=dict(t=50, b=100, l=100, r=50),
                      height=600)
    return (dcc.Graph(figure=fig),)


def plot_preprocessed_srecord3c(records):
    """If file loads correctly, create a plot of the associated time series."""
    dt = records[0].vt.dt_in_seconds
    ns = hvsrpy.TimeSeries(np.concatenate([record.ns.amplitude for record in records]), dt)
    ew = hvsrpy.TimeSeries(np.concatenate([record.ew.amplitude for record in records]), dt)
    vt = hvsrpy.TimeSeries(np.concatenate([record.vt.amplitude for record in records]), dt)
    degrees_from_north = records[0].degrees_from_north
    meta = records[0].meta
    srecord3c = hvsrpy.SeismicRecording3C(ns, ew, vt,
                                          degrees_from_north=degrees_from_north,
                                          meta=meta)
    return plot_srecord3c(srecord3c)


def plot_raw_srecord3c(file_contents):
    """If file loads correctly, create a plot of the associated time series."""
    srecord3c = hvsrpy.SeismicRecording3C._from_dict(file_contents)
    return plot_srecord3c(srecord3c)


def preprocess_srecord3c(srecord3c_data, new_start_time_value, new_stop_time_value, preprocess_settings_data):
    srecord3c = hvsrpy.SeismicRecording3C._from_dict(srecord3c_data)
    srecord3c.trim(new_start_time_value, new_stop_time_value)
    records = [srecord3c]
    settings = hvsrpy.HvsrPreProcessingSettings(**preprocess_settings_data)
    records = hvsrpy.preprocess(records, settings)
    return records


@ app.callback(
    Output("plot-seismic-record", "children"),
    [Input("srecord3c", "data"),
     Input("preprocess-settings", "data")],
    [State("new-start-time", "value"),
     State("new-end-time", "value")]
)
def srecord3c_plotting(srecord3c_data, preprocess_settings_data, new_start_time_value, new_stop_time_value):
    triggered_id = dash.ctx.triggered_id

    if triggered_id == "srecord3c" or preprocess_settings_data is None:
        return plot_raw_srecord3c(srecord3c_data)

    if triggered_id == "preprocess-settings" and preprocess_settings_data is not None:
        records = preprocess_srecord3c(srecord3c_data,
                                       new_start_time_value,
                                       new_stop_time_value,
                                       preprocess_settings_data)
        return plot_preprocessed_srecord3c(records)

    raise PreventUpdate


@ app.callback(
    [Output("preprocess-default-container", "style"),
     Output("traditional-container", "style"),
     Output("preprocess-default-container-continued", "style"),
     Output("process-method", "options"),
     Output("process-method", "value")],
    Input('processing-workflow', 'value'),
    State('process-method', "options"))
def dynamic_hvsr_preprocess_settings(processing_workflow_value, process_method_options):
    """Show/hide hvsr process tab inputs according to previous selections."""

    if processing_workflow_value == "manual":
        options = [
            dict(label="Traditional", value="traditional"),
            dict(label="Azimuthal", value="azimuthal"),
            dict(label="Diffuse Field", value="diffuse"),
        ]

        return (
            DISPLAY_CONTAINER,
            DISPLAY_CONTAINER,
            DISPLAY_CONTAINER,
            options,
            None,
        )

    if processing_workflow_value == "autohvsr":
        options = [
            dict(label="Traditional", value="traditional"),
            # dict(label="Azimuthal", value="azimuthal"), #TODO(jpv): Skip this for now.
        ]

        return (
            DISPLAY_CONTAINER,
            HIDE_CONTAINER,
            DISPLAY_CONTAINER,
            options,
            "traditional",
        )

    raise PreventUpdate


@ app.callback([Output("butterworth-filter-lower-frequency-container", "style"),
               Output("butterworth-filter-upper-frequency-container", "style"),],
               [Input('butterworth-filter', 'value')])
def dynamic_filtering_settings(value):
    """Show/hide filter inputs according to type of filter specified."""

    if value == "bandpass":
        return (DISPLAY_CONTAINER,
                DISPLAY_CONTAINER)
    elif value == "lowpass":
        return (HIDE_CONTAINER,
                DISPLAY_CONTAINER)
    elif value == "highpass":
        return (DISPLAY_CONTAINER,
                HIDE_CONTAINER)
    elif value == "none":
        return (HIDE_CONTAINER,
                HIDE_CONTAINER)
    else:
        raise PreventUpdate


@ app.callback(
    [Output("preprocess-settings", "data"),
     Output("preprocess-continue-instructions", "children"),
     Output("preprocess-continue-instructions", "style"),
     Output("process-tab", "disabled")],
    [Input("preprocess-button", "n_clicks"),
     Input("reset-to-preprocess-step", "data")],
    [State("srecord3c", "data"),
     State("processing-workflow", "value"),
     State("orient-to-degrees-from-north", "value"),
     State("butterworth-filter", "value"),
     State("butterworth-filter-lower-frequency", "value"),
     State("butterworth-filter-upper-frequency", "value"),
     State("window-length", "value"),
     State("detrend", "value"),
     State("preprocess-continue-instructions", "children"),
     State("preprocess-continue-instructions", "style"),
     State("preprocess-settings", "data")
     ]
)
def create_preprocess_settings(execute_button_n_clicks,
                               reset_to_preprocess_step_data,
                               srecord3c_data,
                               processing_workflow_value,
                               orient_to_degrees_from_north_value,
                               butterworth_filter_value,
                               butterworth_filter_value_lower_frequency_value,
                               butterworth_filter_value_upper_frequency_value,
                               window_length_value,
                               detrend_value,
                               preprocess_continue_instructions_children,
                               preprocess_continue_instructions_style,
                               preprocess_settings_data,
                               ):
    triggered_id = dash.ctx.triggered_id

    if triggered_id == "reset-to-preprocess-step":
        disable_tab, hide_text = reset_to_preprocess_step_data
        return (preprocess_settings_data,
                "" if hide_text else preprocess_continue_instructions_children,
                preprocess_continue_instructions_style,
                disable_tab
                )

    if execute_button_n_clicks is not None:
        if processing_workflow_value is None:
            return (None,
                    "Please select your Processing Workflow before attempting to preprocess.",
                    {**preprocess_continue_instructions_style, "color": COLORS["error"]},
                    True,
                    )

        if butterworth_filter_value == "none":
            filter_description = (None, None)
        elif butterworth_filter_value == "bandpass":
            filter_description = (butterworth_filter_value_lower_frequency_value,
                                  butterworth_filter_value_upper_frequency_value)
        elif butterworth_filter_value == "lowpass":
            filter_description = (None,
                                  butterworth_filter_value_upper_frequency_value)
        elif butterworth_filter_value == "highpass":
            filter_description = (butterworth_filter_value_lower_frequency_value,
                                  None)
        else:
            raise ValueError(f"butterworth_filter_value = {butterworth_filter_value} is unknown.")

        # if using autohvsr, require 35 time windows.
        if processing_workflow_value == "autohvsr":
            time_windows = 35
            srecord3c = hvsrpy.SeismicRecording3C._from_dict(srecord3c_data)
            duration_in_seconds = srecord3c.vt.time()[-1]
            window_length_value = duration_in_seconds / time_windows

        settings = hvsrpy.HvsrPreProcessingSettings(orient_to_degrees_from_north=float(orient_to_degrees_from_north_value),
                                                    filter_corner_frequencies_in_hz=filter_description,
                                                    window_length_in_seconds=window_length_value,
                                                    detrend=None if detrend_value == "none" else detrend_value,
                                                    )
        return (settings.attr_dict,
                "Preprocess settings applied, continue to the Process tab.",
                {**preprocess_continue_instructions_style, "color": COLORS["primary"]},
                False,
                )

    raise PreventUpdate


@ app.callback([Output("combine-horizontals-container", "style"),
                Output("process-base-container", "style"),
                Output("frequency-sampling-container", "style"),
                Output("traditional-traditional", "style"),
                Output("traditional-single-azimuth", "style"),
                Output("traditional-rotdpp", "style"),
                Output("azimuthal", "style"),
                Output("statistics-container", "style"),
                Output("resonance-search-range-container", "style"),
                Output("rejection", "style"),
                Output("diffuse", "style")],
               [Input('process-method', 'value'),
                Input('combine-horizontals-select', 'value'),
                Input('processing-workflow', 'value')],
               )
def dynamic_hvsr_process_settings(process_method_value, combine_horizontals_value, processing_workflow_value):
    """Show/hide hvsr process tab inputs according to previous selections."""

    if processing_workflow_value == "manual":

        if process_method_value == "traditional":
            if combine_horizontals_value is None:
                return (DISPLAY_CONTAINER,
                        HIDE_CONTAINER,
                        HIDE_CONTAINER,
                        HIDE_CONTAINER,
                        HIDE_CONTAINER,
                        HIDE_CONTAINER,
                        HIDE_CONTAINER,
                        HIDE_CONTAINER,
                        HIDE_CONTAINER,
                        HIDE_CONTAINER,
                        HIDE_CONTAINER)
            if combine_horizontals_value == "single_azimuth":
                return (DISPLAY_CONTAINER,
                        DISPLAY_CONTAINER,
                        DISPLAY_CONTAINER,
                        HIDE_CONTAINER,
                        DISPLAY_CONTAINER,
                        HIDE_CONTAINER,
                        HIDE_CONTAINER,
                        DISPLAY_CONTAINER,
                        DISPLAY_CONTAINER,
                        DISPLAY_CONTAINER,
                        HIDE_CONTAINER)
            if combine_horizontals_value == "rotdpp":
                return (DISPLAY_CONTAINER,
                        DISPLAY_CONTAINER,
                        DISPLAY_CONTAINER,
                        HIDE_CONTAINER,
                        HIDE_CONTAINER,
                        DISPLAY_CONTAINER,
                        HIDE_CONTAINER,
                        DISPLAY_CONTAINER,
                        DISPLAY_CONTAINER,
                        DISPLAY_CONTAINER,
                        HIDE_CONTAINER)
            return (DISPLAY_CONTAINER,
                    DISPLAY_CONTAINER,
                    DISPLAY_CONTAINER,
                    DISPLAY_CONTAINER,
                    HIDE_CONTAINER,
                    HIDE_CONTAINER,
                    HIDE_CONTAINER,
                    DISPLAY_CONTAINER,
                    DISPLAY_CONTAINER,
                    DISPLAY_CONTAINER,
                    HIDE_CONTAINER)

        if process_method_value == "azimuthal":
            return (HIDE_CONTAINER,
                    DISPLAY_CONTAINER,
                    DISPLAY_CONTAINER,
                    HIDE_CONTAINER,
                    HIDE_CONTAINER,
                    HIDE_CONTAINER,
                    DISPLAY_CONTAINER,
                    DISPLAY_CONTAINER,
                    DISPLAY_CONTAINER,
                    DISPLAY_CONTAINER,
                    HIDE_CONTAINER)

        if process_method_value == "diffuse":
            return (HIDE_CONTAINER,
                    DISPLAY_CONTAINER,
                    DISPLAY_CONTAINER,
                    HIDE_CONTAINER,
                    HIDE_CONTAINER,
                    HIDE_CONTAINER,
                    HIDE_CONTAINER,
                    HIDE_CONTAINER,
                    DISPLAY_CONTAINER,
                    HIDE_CONTAINER,
                    DISPLAY_CONTAINER)

    if processing_workflow_value == "autohvsr":

        if process_method_value == "traditional":
            if combine_horizontals_value is None:
                return (DISPLAY_CONTAINER,
                        HIDE_CONTAINER,
                        HIDE_CONTAINER,
                        HIDE_CONTAINER,
                        HIDE_CONTAINER,
                        HIDE_CONTAINER,
                        HIDE_CONTAINER,
                        HIDE_CONTAINER,
                        HIDE_CONTAINER,
                        HIDE_CONTAINER,
                        HIDE_CONTAINER)
            if combine_horizontals_value == "single_azimuth":
                return (DISPLAY_CONTAINER,
                        DISPLAY_CONTAINER,
                        HIDE_CONTAINER,
                        HIDE_CONTAINER,
                        DISPLAY_CONTAINER,
                        HIDE_CONTAINER,
                        HIDE_CONTAINER,
                        DISPLAY_CONTAINER,
                        HIDE_CONTAINER,
                        HIDE_CONTAINER,
                        HIDE_CONTAINER)
            if combine_horizontals_value == "rotdpp":
                return (DISPLAY_CONTAINER,
                        DISPLAY_CONTAINER,
                        HIDE_CONTAINER,
                        HIDE_CONTAINER,
                        HIDE_CONTAINER,
                        DISPLAY_CONTAINER,
                        HIDE_CONTAINER,
                        DISPLAY_CONTAINER,
                        HIDE_CONTAINER,
                        HIDE_CONTAINER,
                        HIDE_CONTAINER)
            return (DISPLAY_CONTAINER,
                    DISPLAY_CONTAINER,
                    HIDE_CONTAINER,
                    DISPLAY_CONTAINER,
                    HIDE_CONTAINER,
                    HIDE_CONTAINER,
                    HIDE_CONTAINER,
                    DISPLAY_CONTAINER,
                    HIDE_CONTAINER,
                    HIDE_CONTAINER,
                    HIDE_CONTAINER)

        if process_method_value == "azimuthal":
            return (HIDE_CONTAINER,
                    DISPLAY_CONTAINER,
                    HIDE_CONTAINER,
                    HIDE_CONTAINER,
                    HIDE_CONTAINER,
                    HIDE_CONTAINER,
                    DISPLAY_CONTAINER,
                    DISPLAY_CONTAINER,
                    HIDE_CONTAINER,
                    HIDE_CONTAINER,
                    HIDE_CONTAINER)

        if process_method_value == "diffuse":
            raise ValueError("autohvsr not allowed with diffuse processing")

    raise PreventUpdate


@ app.callback(
    Output('fdwra', 'style'),
    Input('rejection-select', 'value'),
)
def dynamic_hvsr_rejection_settings(rejection_selection_value):

    if rejection_selection_value == "fdwra":
        return DISPLAY_CONTAINER

    if rejection_selection_value == "False":
        return HIDE_CONTAINER

    raise PreventUpdate


def prepare_traditional_settings(combine_horizontals_select_value, window_type_value, window_width_value, smoothing_operator_value, smoothing_bandwidth_value, frequency_resampling_in_hz, single_azimuth_value, rotdpp_azimuthal_interval_value, rotdpp_azimuthal_ppth_percential_value):
    if combine_horizontals_select_value == "single_azimuth":
        return hvsrpy.HvsrTraditionalSingleAzimuthProcessingSettings(
            window_type_and_width=(window_type_value, window_width_value),
            smoothing_operator_and_bandwidth=(smoothing_operator_value, smoothing_bandwidth_value),
            frequency_resampling_in_hz=frequency_resampling_in_hz,
            azimuth_in_degrees=single_azimuth_value
        ).attr_dict

    if combine_horizontals_select_value == "rotdpp":
        return hvsrpy.HvsrTraditionalRotDppProcessingSettings(
            window_type_and_width=(window_type_value, window_width_value),
            smoothing_operator_and_bandwidth=(smoothing_operator_value, smoothing_bandwidth_value),
            frequency_resampling_in_hz=frequency_resampling_in_hz,
            ppth_percentile_for_rotdpp_computation=rotdpp_azimuthal_ppth_percential_value,
            azimuths_in_degrees=np.arange(0, 180, rotdpp_azimuthal_interval_value)
        ).attr_dict

    return hvsrpy.HvsrTraditionalProcessingSettings(
        method_to_combine_horizontals=combine_horizontals_select_value,
        window_type_and_width=(window_type_value, window_width_value),
        smoothing_operator_and_bandwidth=(smoothing_operator_value, smoothing_bandwidth_value),
        frequency_resampling_in_hz=frequency_resampling_in_hz
    ).attr_dict


def prepare_azimuthal_settings(window_type_value, window_width_value, smoothing_operator_value, smoothing_bandwidth_value, frequency_resampling_in_hz, azimuthal_interval_value):
    return hvsrpy.HvsrAzimuthalProcessingSettings(
        window_type_and_width=(window_type_value, window_width_value),
        smoothing_operator_and_bandwidth=(smoothing_operator_value, smoothing_bandwidth_value),
        frequency_resampling_in_hz=frequency_resampling_in_hz,
        azimuths_in_degrees=np.arange(0, 180, azimuthal_interval_value)
    ).attr_dict


def prepare_diffuse_settings(window_type_value, window_width_value, smoothing_operator_value, smoothing_bandwidth_value, frequency_resampling_in_hz):
    return hvsrpy.HvsrDiffuseFieldProcessingSettings(
        window_type_and_width=(window_type_value, window_width_value),
        smoothing_operator_and_bandwidth=(smoothing_operator_value, smoothing_bandwidth_value),
        frequency_resampling_in_hz=frequency_resampling_in_hz
    ).attr_dict


def create_processing_settings_manual(process_method_value, combine_horizontals_select_value,
                                      window_type_value, window_width_value, smoothing_operator_value, smoothing_bandwidth_value,
                                      minimum_frequency_value, maximum_frequency_value, n_frequency_value, sampling_type_frequency_value,
                                      single_azimuth_value, rotdpp_azimuthal_interval_value, rotdpp_azimuthal_ppth_percential_value,
                                      azimuthal_interval_value):
    if sampling_type_frequency_value == "linear":
        frequency_resampling_in_hz = np.linspace(
            minimum_frequency_value, maximum_frequency_value, n_frequency_value)
    else:
        frequency_resampling_in_hz = np.geomspace(
            minimum_frequency_value, maximum_frequency_value, n_frequency_value)

    if process_method_value == "traditional":
        return prepare_traditional_settings(combine_horizontals_select_value, window_type_value, window_width_value,
                                            smoothing_operator_value, smoothing_bandwidth_value, frequency_resampling_in_hz, single_azimuth_value,
                                            rotdpp_azimuthal_interval_value, rotdpp_azimuthal_ppth_percential_value)

    if process_method_value == "azimuthal":
        print(frequency_resampling_in_hz)
        return prepare_azimuthal_settings(window_type_value, window_width_value,
                                          smoothing_operator_value, smoothing_bandwidth_value, frequency_resampling_in_hz, azimuthal_interval_value)

    if process_method_value == "diffuse":
        return prepare_diffuse_settings(window_type_value, window_width_value,
                                        smoothing_operator_value, smoothing_bandwidth_value, frequency_resampling_in_hz)


def create_processing_settings_autohvsr(srecord3c, process_method_value, combine_horizontals_select_value,
                                        window_type_value, window_width_value, smoothing_operator_value, smoothing_bandwidth_value,
                                        single_azimuth_value, rotdpp_azimuthal_interval_value, rotdpp_azimuthal_ppth_percential_value,
                                        azimuthal_interval_value):
    # define consistent frequency vector.
    desired_frequency_vector_in_hz = np.geomspace(0.05, 50, 256)

    # require 15 significant cycles.
    significant_cycles = 15

    # require 35 time windows.
    time_windows = 35

    # window length (s)
    duration_in_seconds = srecord3c.vt.time()[-1]
    windowlength_in_seconds = duration_in_seconds / time_windows

    # frequency vector (Hz)
    minimum_frequency = significant_cycles / windowlength_in_seconds
    fids = desired_frequency_vector_in_hz > minimum_frequency
    frequency_resampling_in_hz = desired_frequency_vector_in_hz[fids]

    if process_method_value == "traditional":
        return prepare_traditional_settings(combine_horizontals_select_value, window_type_value, window_width_value,
                                            smoothing_operator_value, smoothing_bandwidth_value, frequency_resampling_in_hz, single_azimuth_value,
                                            rotdpp_azimuthal_interval_value, rotdpp_azimuthal_ppth_percential_value)

    if process_method_value == "azimuthal":
        return prepare_azimuthal_settings(window_type_value, window_width_value,
                                          smoothing_operator_value, smoothing_bandwidth_value, frequency_resampling_in_hz, azimuthal_interval_value)

    if process_method_value == "diffuse":
        return prepare_diffuse_settings(window_type_value, window_width_value,
                                        smoothing_operator_value, smoothing_bandwidth_value, frequency_resampling_in_hz)


@ app.callback(
    Output("process-settings", "data"),
    Input('process-button', 'n_clicks'),
    [State("processing-workflow", "value"),
     State("srecord3c", "data"),
     State("new-start-time", "value"),
     State("new-end-time", "value"),
     State("process-method", "value"),
     State("combine-horizontals-select", "value"),
     State("window-type", "value"),
     State("window-width", "value"),
     State("smoothing-operator", "value"),
     State("smoothing-bandwidth", "value"),
     State("minimum-frequency", "value"),
     State("maximum-frequency", "value"),
     State("n-frequency", "value"),
     State("sampling-type-frequency", "value"),
     State("single-azimuth", "value"),
     State("rotdpp-azimuthal-interval", "value"),
     State("rotdpp-azimuthal-ppth-percentile", "value"),
     State("azimuthal-interval", "value")]
)
def create_process_settings(process_button_n_clicks, processing_workflow_value, srecord_data, new_start_time, new_end_time, process_method_value, combine_horizontals_select_value,
                            window_type_value, window_width_value, smoothing_operator_value, smoothing_bandwidth_value,
                            minimum_frequency_value, maximum_frequency_value, n_frequency_value, sampling_type_frequency_value,
                            single_azimuth_value, rotdpp_azimuthal_interval_value, rotdpp_azimuthal_ppth_percential_value,
                            azimuthal_interval_value):

    if process_button_n_clicks is not None:
        if process_method_value is None:
            return "process_method_value"

        if combine_horizontals_select_value is None and process_method_value not in ["azimuthal", "diffuse"]:
            return "combine_horizontals_select_value"

        if processing_workflow_value == "manual":
            return create_processing_settings_manual(process_method_value, combine_horizontals_select_value,
                                                     window_type_value, window_width_value, smoothing_operator_value, smoothing_bandwidth_value,
                                                     minimum_frequency_value, maximum_frequency_value, n_frequency_value, sampling_type_frequency_value,
                                                     single_azimuth_value, rotdpp_azimuthal_interval_value, rotdpp_azimuthal_ppth_percential_value,
                                                     azimuthal_interval_value)

        if processing_workflow_value == "autohvsr":
            srecord3c = hvsrpy.SeismicRecording3C._from_dict(srecord_data)
            srecord3c.trim(new_start_time, new_end_time)
            return create_processing_settings_autohvsr(srecord3c, process_method_value, combine_horizontals_select_value,
                                                       window_type_value, window_width_value, smoothing_operator_value, smoothing_bandwidth_value,
                                                       single_azimuth_value, rotdpp_azimuthal_interval_value, rotdpp_azimuthal_ppth_percential_value,
                                                       azimuthal_interval_value)

    raise PreventUpdate


DEFAULT_PLOT_KWARGS = {
    "width_of_individual_hvsr_curve": 0.3,
    "color_of_individual_valid_hvsr_curve": "#888888",
    "label_of_individual_valid_hvsr_curve": "Accepted HVSR Curve",
    "color_of_individual_invalid_hvsr_curve": "#00ffff",
    "label_of_individual_invalid_hvsr_curve": "Rejected HVSR Curve",
    "color_of_mean_hvsr_curve": "black",
    "width_of_mean_hvsr_curve": 1.3,
    "label_of_mean_hvsr_curve": "Mean Curve",
    "color_of_nth_std_mean_hvsr_curve": "black",
    "width_of_nth_std_mean_hvsr_curve": 1.3,
    "label_of_nth_std_mean_hvsr_curve": r"$Mean Curve \pm 1 STD",
    "linestyle_of_nth_std_mean_hvsr_curve": "--",
    "color_of_nth_std_frequency_range": "#ff8080",
    "label_of_nth_std_frequency_range_normal": r"$\mu_{fn} \pm \sigma_{fn}",
    "label_of_nth_std_frequency_range_lognormal": r"$(\mu_{ln,fn} \pm \sigma_{ln,fn})^*",
    "label_of_valid_peak_individual_curves": r"$f_{n,i}$",
    "edge_color_of_valid_peak_individual_curves": "black",
    "fill_color_of_valid_peak_individual_curves": "white",
    "label_of_valid_peak_mean_curve": r"$f_{n,mc$",
    "fill_color_of_mean_curve_peak": "#66ff33"
}


def pt_to_px(x): return 4/3*x


DEFAULT_PLOT_KWARGS["width_of_individual_hvsr_curve"] = pt_to_px(
    DEFAULT_PLOT_KWARGS["width_of_individual_hvsr_curve"])
DEFAULT_PLOT_KWARGS["width_of_mean_hvsr_curve"] = pt_to_px(
    DEFAULT_PLOT_KWARGS["width_of_mean_hvsr_curve"])
DEFAULT_PLOT_KWARGS["width_of_nth_std_mean_hvsr_curve"] = pt_to_px(
    DEFAULT_PLOT_KWARGS["width_of_nth_std_mean_hvsr_curve"])

# changes to avoid latex in legends
DEFAULT_PLOT_KWARGS["label_of_nth_std_mean_hvsr_curve"] = "Mean Curve +/- 1 Standard Deviation"
DEFAULT_PLOT_KWARGS["label_of_nth_std_frequency_range_normal"] = "Mean Frequency +/- 1 Standard Deviation"
DEFAULT_PLOT_KWARGS["label_of_nth_std_frequency_range_lognormal"] = "Mean Frequency +/- 1 Standard Deviation"
DEFAULT_PLOT_KWARGS["label_of_valid_peak_individual_curves"] = "Peak of Individual Valid HVSR Curve"
DEFAULT_PLOT_KWARGS["label_of_valid_peak_mean_curve"] = "Peak of Mean HVSR Curve"


def _prepare_individual_hvsr_curves(hvsr):
    """Prepare HVSR curves for plotting.

    .. warning::
        Private methods are subject to change without warning.

    """
    if isinstance(hvsr, hvsrpy.HvsrTraditional):
        return [hvsr]
    elif isinstance(hvsr, hvsrpy.HvsrAzimuthal):
        return hvsr.hvsrs
    else:
        return hvsr


def _plot_individual_invalid_hvsr_curves(fig, hvsr):
    hvsrs = _prepare_individual_hvsr_curves(hvsr)
    name = DEFAULT_PLOT_KWARGS["label_of_individual_invalid_hvsr_curve"]
    show_legend = True
    for hvsr in hvsrs:
        for amplitude in hvsr.amplitude[~hvsr.valid_window_boolean_mask]:
            fig.add_trace(go.Scatter(x=hvsr.frequency, y=amplitude, name=name, showlegend=show_legend, legendgroup="invalid", legendrank=2,
                                     line=dict(color=DEFAULT_PLOT_KWARGS["color_of_individual_invalid_hvsr_curve"],
                                               width=DEFAULT_PLOT_KWARGS["width_of_individual_hvsr_curve"])), row=1, col=1),
            show_legend = False


def _plot_individual_valid_hvsr_curves(fig, hvsr):
    hvsrs = _prepare_individual_hvsr_curves(hvsr)
    name = DEFAULT_PLOT_KWARGS["label_of_individual_valid_hvsr_curve"]
    show_legend = True
    for hvsr in hvsrs:
        for amplitude in hvsr.amplitude[hvsr.valid_window_boolean_mask]:

            fig.add_trace(go.Scatter(x=hvsr.frequency, y=amplitude, name=name, showlegend=show_legend, legendgroup="valid", legendrank=1,
                                     line=dict(color=DEFAULT_PLOT_KWARGS["color_of_individual_valid_hvsr_curve"],
                                               width=DEFAULT_PLOT_KWARGS["width_of_individual_hvsr_curve"])), row=1, col=1)
            show_legend = False


def _plot_mean_hvsr_curve(fig, hvsr, distribution_mean_curve_value):
    name = DEFAULT_PLOT_KWARGS["label_of_mean_hvsr_curve"]
    mean_curve = hvsr.mean_curve(distribution=distribution_mean_curve_value)
    fig.add_trace(go.Scatter(x=hvsr.frequency, y=mean_curve, name=name,
                  line=dict(color=DEFAULT_PLOT_KWARGS["color_of_mean_hvsr_curve"],
                            width=DEFAULT_PLOT_KWARGS["width_of_mean_hvsr_curve"])), row=1, col=1)


def _plot_mean_pm_std_hvsr_curve(fig, hvsr, distribution_mean_curve_value, n=1):
    name = DEFAULT_PLOT_KWARGS["label_of_nth_std_mean_hvsr_curve"]
    fig.add_trace(go.Scatter(x=hvsr.frequency, y=hvsr.nth_std_curve(n=n, distribution=distribution_mean_curve_value), name=name, legendgroup="hvsr_std",
                  line=dict(color=DEFAULT_PLOT_KWARGS["color_of_mean_hvsr_curve"],
                            width=DEFAULT_PLOT_KWARGS["width_of_nth_std_mean_hvsr_curve"],
                            dash="dash")), row=1, col=1)
    fig.add_trace(go.Scatter(x=hvsr.frequency, y=hvsr.nth_std_curve(n=-n, distribution=distribution_mean_curve_value), showlegend=False, legendgroup="hvsr_std",
                  line=dict(color=DEFAULT_PLOT_KWARGS["color_of_mean_hvsr_curve"],
                            width=DEFAULT_PLOT_KWARGS["width_of_nth_std_mean_hvsr_curve"],
                            dash="dash")), row=1, col=1)


def _plot_individual_peaks_from_iterable_of_peaks(fig, frequency, amplitude):
    name = DEFAULT_PLOT_KWARGS["label_of_valid_peak_individual_curves"]
    show_legend = True
    for _frequency, _amplitude in zip(frequency, amplitude):
        fig.add_trace(go.Scatter(x=_frequency, y=_amplitude, name=name, showlegend=show_legend, legendgroup="peak", mode="markers",
                                 marker=dict(color=DEFAULT_PLOT_KWARGS["fill_color_of_valid_peak_individual_curves"],
                                             size=4,
                                             line=dict(color=DEFAULT_PLOT_KWARGS["edge_color_of_valid_peak_individual_curves"],
                                                       width=1)),
                                 ), row=1, col=1)
        show_legend = False


def _plot_individual_peaks(fig, hvsr):
    hvsrs = _prepare_individual_hvsr_curves(hvsr)
    frequency = [hvsr.peak_frequencies for hvsr in hvsrs]
    amplitude = [hvsr.peak_amplitudes for hvsr in hvsrs]
    _plot_individual_peaks_from_iterable_of_peaks(fig, frequency, amplitude)


def _plot_hvsr_resonance_from_values(fig, f_lower, f_upper, hvsr, distribution_resonance_value, show_legend=True):
    amplitude = np.round(1.2*np.max(hvsr.amplitude))
    color = DEFAULT_PLOT_KWARGS["color_of_nth_std_frequency_range"]
    name = DEFAULT_PLOT_KWARGS[f"label_of_nth_std_frequency_range_{distribution_resonance_value}"]
    fig.add_trace(go.Scatter(x=[f_lower, f_upper], y=[amplitude]*2, mode="lines", name=name, legendgroup="resonance", showlegend=show_legend,
                  fill="tozeroy", line=dict(color=color, width=0)), row=1, col=1)


def _plot_hvsr_resonance(fig, hvsr, distribution_resonance_value, n=1):
    f_lower = hvsr.nth_std_fn_frequency(n=-n, distribution=distribution_resonance_value)
    f_upper = hvsr.nth_std_fn_frequency(n=+n, distribution=distribution_resonance_value)
    _plot_hvsr_resonance_from_values(fig, f_lower, f_upper, hvsr,
                                     distribution_resonance_value, show_legend=True)


def _plot_peak_mean_curve_multiple(fig, frequency, amplitude):
    name = DEFAULT_PLOT_KWARGS["label_of_valid_peak_mean_curve"]
    fig.add_trace(go.Scatter(x=frequency, y=amplitude, name=name, mode="markers",
                             marker=dict(color=DEFAULT_PLOT_KWARGS["fill_color_of_mean_curve_peak"],
                                         symbol="diamond",
                                         line=dict(color=DEFAULT_PLOT_KWARGS["edge_color_of_valid_peak_individual_curves"],
                                                   width=1)),
                             ), row=1, col=1)


def _plot_peak_mean_curve(fig, hvsr, distribution_mean_curve_value, search_range_in_hz):
    x, y = hvsr.mean_curve_peak(distribution=distribution_mean_curve_value,
                                search_range_in_hz=search_range_in_hz)
    _plot_peak_mean_curve_multiple(fig, [x], [y])


def _plot_azimuthal_hvsr_3d(fig, hvsr, distribution_mean_curve_value):
    x = hvsr.frequency
    y = hvsr.azimuths
    z = np.empty((len(y)+1, len(x)))
    median_curves = hvsr.mean_curve_by_azimuth(distribution=distribution_mean_curve_value)
    z[:-1, :] = median_curves
    z[-1, :] = median_curves[0]
    fig.add_trace(go.Surface(z=z, x=x, y=y))


def plot_hvsr_diffuse(hvsr, distribution_resonance_value, distribution_mean_curve_value, search_range_in_hz):
    fig = plotly.subplots.make_subplots(rows=1, cols=1,
                                        x_title="Frequency (Hz)", y_title="HVSR Amplitude")

    _plot_mean_hvsr_curve(fig, hvsr, distribution_mean_curve_value)
    _plot_peak_mean_curve(fig, hvsr, distribution_mean_curve_value, search_range_in_hz)
    fig.update_yaxes(rangemode="tozero")
    fig.update_xaxes(type="log")
    fig.update_layout(margin=dict(t=50, b=100, l=100, r=50),
                      height=600)

    return (dcc.Graph(figure=fig), None)


def plot_hvsr_azimuthal(hvsr, distribution_resonance_value, distribution_mean_curve_value, search_range_in_hz):
    fig = plotly.subplots.make_subplots(rows=1, cols=1,
                                        x_title="Frequency (Hz)", y_title="HVSR Amplitude")

    _plot_individual_invalid_hvsr_curves(fig, hvsr)
    _plot_individual_valid_hvsr_curves(fig, hvsr)
    _plot_mean_hvsr_curve(fig, hvsr, distribution_mean_curve_value)
    _plot_mean_pm_std_hvsr_curve(fig, hvsr, distribution_mean_curve_value, n=1)
    _plot_individual_peaks(fig, hvsr)
    _plot_hvsr_resonance(fig, hvsr, distribution_resonance_value)
    _plot_peak_mean_curve(fig, hvsr, distribution_mean_curve_value, search_range_in_hz)
    fig.update_yaxes(rangemode="tozero")
    fig.update_xaxes(type="log")
    fig.update_layout(margin=dict(t=50, b=100, l=100, r=50),
                      height=600)

    fig2 = go.Figure()
    _plot_azimuthal_hvsr_3d(fig2, hvsr, distribution_mean_curve_value)
    fig2.update_scenes(xaxis=dict(type="log", title="Frequency (Hz)"))
    fig2.update_scenes(yaxis=dict(title="Azimuth (degrees)"))
    fig2.update_scenes(zaxis=dict(rangemode="tozero", title="HVSR Amplitude"))
    camera = dict(up=dict(x=0, y=0, z=1),
                  center=dict(x=0, y=0, z=0),
                  eye=dict(x=-1.3, y=-1.7, z=1.1))
    fig2.update_layout(scene_camera=camera,
                       margin=dict(t=50, b=0, l=0, r=50),
                       height=600)

    return (dcc.Graph(figure=fig), dcc.Graph(figure=fig2))


# TODO(jpv): Implement aziuthal processing with autohvsr.
# def plot_hvsr_azimuthal_autohvsr(hvsr, distribution_resonance_value, distribution_mean_curve_value, search_range_in_hz):
#     fig = plotly.subplots.make_subplots(rows=1, cols=1,
#                                         x_title="Frequency (Hz)", y_title="HVSR Amplitude")

#     _plot_individual_invalid_hvsr_curves(fig, hvsr)
#     _plot_individual_valid_hvsr_curves(fig, hvsr)
#     _plot_mean_hvsr_curve(fig, hvsr, distribution_mean_curve_value)
#     _plot_mean_pm_std_hvsr_curve(fig, hvsr, distribution_mean_curve_value, n=1)
#     # _plot_individual_peaks(fig, hvsr)
#     # _plot_hvsr_resonance(fig, hvsr, distribution_resonance_value)
#     # _plot_peak_mean_curve(fig, hvsr, distribution_mean_curve_value, search_range_in_hz)
#     fig.update_yaxes(rangemode="tozero")
#     fig.update_xaxes(type="log")
#     fig.update_layout(margin=dict(t=50, b=100, l=100, r=50),
#                       height=600)

#     fig2 = go.Figure()
#     _plot_azimuthal_hvsr_3d(fig2, hvsr, distribution_mean_curve_value)
#     fig2.update_scenes(xaxis=dict(type="log", title="Frequency (Hz)"))
#     fig2.update_scenes(yaxis=dict(title="Azimuth (degrees)"))
#     fig2.update_scenes(zaxis=dict(rangemode="tozero", title="HVSR Amplitude"))
#     camera = dict(up=dict(x=0, y=0, z=1),
#                   center=dict(x=0, y=0, z=0),
#                   eye=dict(x=-1.3, y=-1.7, z=1.1))
#     fig2.update_layout(scene_camera=camera,
#                        margin=dict(t=50, b=0, l=0, r=50),
#                        height=600)

#     return (dcc.Graph(figure=fig), dcc.Graph(figure=fig2))


def plot_hvsr_traditional(hvsr, distribution_resonance_value, distribution_mean_curve_value, search_range_in_hz):
    fig = plotly.subplots.make_subplots(rows=1, cols=1,
                                        x_title="Frequency (Hz)", y_title="HVSR Amplitude")

    _plot_individual_invalid_hvsr_curves(fig, hvsr)
    _plot_individual_valid_hvsr_curves(fig, hvsr)
    _plot_mean_hvsr_curve(fig, hvsr, distribution_mean_curve_value)
    _plot_mean_pm_std_hvsr_curve(fig, hvsr, distribution_mean_curve_value, n=1)
    _plot_individual_peaks(fig, hvsr)
    _plot_hvsr_resonance(fig, hvsr, distribution_resonance_value)
    _plot_peak_mean_curve(fig, hvsr, distribution_mean_curve_value, search_range_in_hz)
    fig.update_yaxes(rangemode="tozero")
    fig.update_xaxes(type="log")
    fig.update_layout(margin=dict(t=50, b=100, l=100, r=50),
                      height=600)

    return (dcc.Graph(figure=fig), None)


def plot_hvsr_traditional_autohvsr(hvsr, distribution_resonance_value, distribution_mean_curve_value, df):
    fig = plotly.subplots.make_subplots(rows=1, cols=1,
                                        x_title="Frequency (Hz)",
                                        y_title="HVSR Amplitude")

    # calculate window boolean mask
    valid_window_boolean_mask = np.zeros((hvsr.n_curves,), dtype=bool)
    for window_idx in range(hvsr.n_curves):
        # if any curve has a peak, keep it as valid; otherwise reject it.
        if len(df[(df["window idx"] == window_idx) & (df["valid"] == True)]) > 0:
            valid_window_boolean_mask[window_idx] = True

    some_windows_valid = True
    if np.sum(valid_window_boolean_mask) == 0:
        some_windows_valid = False
        hvsr.valid_window_boolean_mask = valid_window_boolean_mask

    _plot_individual_invalid_hvsr_curves(fig, hvsr)
    _plot_individual_valid_hvsr_curves(fig, hvsr)
    _plot_mean_hvsr_curve(fig, hvsr, distribution_mean_curve_value)
    _plot_mean_pm_std_hvsr_curve(fig, hvsr, distribution_mean_curve_value, n=1)

    stats = []

    if some_windows_valid:

        # plot resonances
        frequencies, amplitudes = [], []
        for window_idx in range(hvsr.n_curves):
            rows = df[(df["window idx"] == window_idx) & (df["valid"] == True)]
            frequency = rows["peak frequency"]
            amplitude = rows["peak amplitude"]
            frequencies.append(frequency)
            amplitudes.append(amplitude)
        _plot_individual_peaks_from_iterable_of_peaks(fig, frequencies, amplitudes)

        # plot mean peak
        frequencies, amplitudes = [], []
        mc = hvsr.mean_curve(distribution_mean_curve_value)
        resonances = df["resonance"].unique()
        for resonance in resonances:
            if resonance == -1:
                continue
            _frequencies = df[(df["resonance"] == resonance)]["peak frequency"]
            f_min, f_max = np.min(_frequencies), np.max(_frequencies)
            _frequency, _amplitude = hvsrpy.HvsrCurve._find_peak_bounded(
                hvsr.frequency, mc, search_range_in_hz=(f_min, f_max))
            frequencies.append(_frequency)
            amplitudes.append(_amplitude)
            stats.append([_frequency, _amplitude])
        _plot_peak_mean_curve_multiple(fig, frequencies, amplitudes)

        # plot autohvsr mean frequency +/- 1 std
        show_legend = True
        idx = 0
        for resonance in resonances:
            if resonance == -1:
                continue
            _frequencies = df[(df["resonance"] == resonance)]["peak frequency"]
            mean = hvsrpy.statistics._nanmean_weighted(distribution_resonance_value, _frequencies)
            std = hvsrpy.statistics._nanstd_weighted(distribution_resonance_value, _frequencies)

            _amplitudes = df[(df["resonance"] == resonance)]["peak amplitude"]
            mean_a = hvsrpy.statistics._nanmean_weighted(distribution_resonance_value, _amplitudes)
            std_a = hvsrpy.statistics._nanstd_weighted(distribution_resonance_value, _amplitudes)

            stats[idx].extend([mean, std, distribution_resonance_value, mean_a, std_a])

            f_lower = hvsrpy.statistics._nth_std_factory(-1,
                                                         distribution_resonance_value, mean, std)
            f_upper = hvsrpy.statistics._nth_std_factory(+1,
                                                         distribution_resonance_value, mean, std)
            _plot_hvsr_resonance_from_values(
                fig, f_lower, f_upper, hvsr, distribution_resonance_value, show_legend=show_legend)
            show_legend = False
            idx += 1

    fig.update_yaxes(rangemode="tozero")
    fig.update_xaxes(type="log")
    fig.update_layout(margin=dict(t=50, b=100, l=100, r=50),
                      height=600)

    return (dcc.Graph(figure=fig), None, stats)


def prep(x): return str(np.round(x, decimals=2))


def generate_table_for_resonance_from_values(mean_curve_peak_frequency, mean_curve_peak_amplitude,
                                             mean_frequency=None, std_frequency=None, distribution_resonance_value=None,
                                             mean_amplitude=None, std_amplitude=None):
    rows = [
        html.Tr([
            html.Td("Mean Curve Peak Frequency (Hz)"),
            html.Td(prep(mean_curve_peak_frequency)),
        ]),
        html.Tr([
            html.Td("Mean Curve Peak Amplitude"),
            html.Td(prep(mean_curve_peak_amplitude)),
        ]),
    ]

    if distribution_resonance_value is not None:
        unit_frequency = "Hz" if distribution_resonance_value == "normal" else "log(Hz)"
        rows = [
            html.Tr([
                html.Td("Resonance Mean Frequency (Hz)"),
                html.Td(prep(mean_frequency)),
            ]),
            html.Tr([
                html.Td(f"Resonance Standard Deviation Frequency ({unit_frequency})"),
                html.Td(prep(std_frequency)),
            ]),
            html.Tr([
                html.Td("Resonance Mean Amplitude"),
                html.Td(prep(mean_amplitude)),
            ]),
            html.Tr([
                html.Td("Resonance Standard Deviation Amplitude"),
                html.Td(prep(std_amplitude)),
            ]),
            *rows
        ]

    return dbc.Table(html.Tbody(rows),
                     bordered=True, hover=True, className="mt-2",
                     style={"color": "secondary"})


def generate_table_for_resonance(hvsr, distribution_resonance_value, distribution_mean_curve_value, search_range_in_hz):

    mean_curve_peak_frequency, mean_curve_peak_amplitude = hvsr.mean_curve_peak(distribution=distribution_mean_curve_value,
                                                                                search_range_in_hz=search_range_in_hz)

    if isinstance(hvsr, hvsrpy.HvsrDiffuseField):
        return generate_table_for_resonance_from_values(mean_curve_peak_frequency, mean_curve_peak_amplitude)

    mean_frequency = hvsr.mean_fn_frequency(distribution=distribution_resonance_value)
    mean_amplitude = hvsr.mean_fn_amplitude(distribution=distribution_resonance_value)
    std_frequency = hvsr.std_fn_frequency(distribution=distribution_resonance_value)
    std_amplitude = hvsr.std_fn_amplitude(distribution=distribution_resonance_value)

    return generate_table_for_resonance_from_values(mean_curve_peak_frequency, mean_curve_peak_amplitude, mean_frequency, std_frequency,
                                                    distribution_resonance_value, mean_amplitude, std_amplitude)


def generate_table_summary(hvsr):
    if isinstance(hvsr, hvsrpy.HvsrDiffuseField):
        rows = [
            html.Tr([
                html.Td("HVSR Curves"),
                html.Td(1),
            ]),
        ]

    if isinstance(hvsr, hvsrpy.HvsrTraditional):
        rows = [
            html.Tr([
                html.Td("HVSR Curves (one per time window)"),
                html.Td(hvsr.n_curves),
            ]),
            html.Tr([
                html.Td("Accepted HVSR Curves"),
                html.Td(np.sum(hvsr.valid_window_boolean_mask)),
            ]),
            html.Tr([
                html.Td("Rejected HVSR Curves"),
                html.Td(np.sum(~hvsr.valid_window_boolean_mask)),
            ]),
        ]

    if isinstance(hvsr, hvsrpy.HvsrAzimuthal):
        valid = np.sum([np.sum(_hvsr.valid_window_boolean_mask) for _hvsr in hvsr.hvsrs])
        invalid = np.sum([np.sum(~_hvsr.valid_window_boolean_mask) for _hvsr in hvsr.hvsrs])

        rows = [
            html.Tr([
                html.Td("HVSR Curves (one per time window and azimuth)"),
                html.Td(valid+invalid),
            ]),
            html.Tr([
                html.Td("Accepted HVSR Curves"),
                html.Td(valid),
            ]),
            html.Tr([
                html.Td("Rejected HVSR Curves"),
                html.Td(invalid),
            ]),
        ]

    return dbc.Table(html.Tbody(rows),
                     bordered=True, hover=True, className="mt-2",
                     style={"color": "secondary"})


def safe_mean(amplitude, frequency, f_min, f_max):
    boolean_mask = np.logical_and(frequency > f_min, frequency < f_max)

    if np.sum(boolean_mask) == 0:
        return 0

    return np.mean(amplitude[boolean_mask])


def extract_hvsr_features(hvsr, idx=0):
    from hvsrpy.hvsr_curve import find_peaks

    find_peaks_settings = dict(
        prominence=0.25,
    )

    peak_data = []
    mc = hvsr.mean_curve()
    mc_std = hvsr.std_curve()

    # aggregate peak data
    raw_peak_data_list = []
    f_all, a_all = [], []
    for _amplitude in hvsr.amplitude:
        # find all of the potential peaks in a window
        (peak_ids, metadata) = find_peaks(_amplitude, **find_peaks_settings)

        raw_peak_data_list.append((peak_ids,
                                   hvsr.frequency[peak_ids],
                                   _amplitude[peak_ids],
                                   metadata["prominences"]))
        f_all.extend(hvsr.frequency[peak_ids])
        a_all.extend(_amplitude[peak_ids])
    f_all = np.array(f_all)
    a_all = np.array(a_all)

    n_series = len(hvsr.amplitude)

    # loop across windows and extract features
    for window_idx, (_amplitude, raw_peak_data_tuple) in enumerate(zip(hvsr.amplitude, raw_peak_data_list)):

        # mean of window within the specified bins
        bins = [0.01, 0.03, 0.1, 0.3, 1, 3, 10, 30, 100]
        values = []
        for f_min, f_max in zip(bins[:-1], bins[1:]):
            values.append(safe_mean(_amplitude, hvsr.frequency, f_min, f_max))
        names = [f"time window feature {_idx}" for _idx in range(len(values))]
        time_window_features = {name: value for name, value in zip(names, values)}

        # Loop across peaks
        for peak_ids, frequency, amplitude, prominence in zip(*raw_peak_data_tuple):

            # locate number of nearby points (in frequency)
            distances_in_log_frequency = [0, 0.025, 0.05, 0.1, 0.2, 0.4]
            nearby_frequency = []
            for min_distance_threshold, max_distance_threshold in zip(distances_in_log_frequency[:-1], distances_in_log_frequency[1:]):
                all_distances = np.abs(np.log10(f_all) - np.log10(frequency))
                all_nearby = np.sum(np.logical_and(
                    all_distances > min_distance_threshold, all_distances < max_distance_threshold))
                nearby_frequency.append(all_nearby/n_series)
            names = [f"nearby frequency feature {_idx}" for _idx in range(len(nearby_frequency))]
            nearby_frequency_features = {name: value for name,
                                         value in zip(names, nearby_frequency)}

            # locate number of nearby points (in amplitude)
            distances_in_amplitude = [0, 0.5, 1, 2, 4, 10]
            nearby_amplitude = []
            for min_distance_threshold, max_distance_threshold in zip(distances_in_amplitude[:-1], distances_in_amplitude[1:]):
                all_distances = np.abs(a_all - amplitude)
                all_nearby = np.sum(np.logical_and(
                    all_distances > min_distance_threshold, all_distances < max_distance_threshold))
                nearby_amplitude.append(all_nearby/n_series)
            names = [f"nearby amplitude feature {_idx}" for _idx in range(len(nearby_amplitude))]
            nearby_amplitude_features = {name: value for name,
                                         value in zip(names, nearby_amplitude)}

            # organize features
            peak_data_dict = {"record idx": idx,
                              "window idx": window_idx,
                              "peak frequency": frequency,
                              "peak amplitude": amplitude,
                              "peak prominence": prominence,
                              "mc amplitude at peak": mc[peak_ids],
                              "mc std at peak": mc_std[peak_ids],
                              **time_window_features,
                              **nearby_frequency_features,
                              **nearby_amplitude_features,
                              }
            peak_data.append(peak_data_dict)

    return peak_data


def create_hvsrpy_file_href(hvsr, distribution_mean_curve):
    """Generate hrefs to be put inside hv-download and geopsy-download."""
    bytes_io_object = io.BytesIO()
    hvsrpy.write_hvsr_to_file(hvsr, bytes_io_object, distribution_mean_curve)
    bytes_io_object.seek(0, 0)
    encoded = base64.b64encode(bytes_io_object.read()).decode("utf-8").replace("\n", "")
    bytes_io_object.close()
    hvsrpy_downloadable = f'data:text/plain;base64,{encoded}'
    return hvsrpy_downloadable


@ app.callback(
    [Output("plot-hvsr", "children"),
     Output("plot-hvsr-3d", "children"),
     Output("plot-hvsr-tab", "disabled"),
     Output("plot-hvsr-3d-tab", "disabled"),
     Output("process-continue-instructions", "children"),
     Output("process-continue-instructions", "style"),
     Output("hvsrpy-download", "href"),
     Output("hvsrpy-download", "download"),
     Output("general-summary-table", "children"),
     Output("results-table", "children"),
     Output("results-table-1", "children"),
     Output("results-table-2", "children"),
     Output("results-table-3", "children"),
     Output("results-table-4", "children"),
     Output("results-table-5", "children"),
     Output("results-table-1-container", "style"),
     Output("results-table-2-container", "style"),
     Output("results-table-3-container", "style"),
     Output("results-table-4-container", "style"),
     Output("results-table-5-container", "style"),
     Output("results-tab", "disabled")],
    [Input("process-settings", "data"),
     Input("reset-to-process-step", "data")],
    [State("processing-workflow", "value"),
     State("srecord3c", "data"),
     State("new-start-time", "value"),
     State("new-end-time", "value"),
     State("preprocess-settings", "data"),
     State("distribution-resonance", "value"),
     State("minimum-search-frequency", "value"),
     State("maximum-search-frequency", "value"),
     State("distribution-mean-curve", "value"),
     State("rejection-select", "value"),
     State("fdwra-n", "value"),
     State("fdwra-max-iteration", "value"),
     State("process-continue-instructions", "style"),
     State("process-continue-instructions", "children"),
     State("results-table", "style")]
)
def processing_hvsr(process_settings_data, reset_to_process_step_data, processing_workflow_value, srecord3c_data,
                    new_start_time_value, new_end_time_value, preprocess_settings_data,
                    distribution_resonance_value, minimum_search_frequency_value,
                    maximum_search_frequency_value,
                    distribution_mean_curve_value,
                    rejection_select_value,
                    fdwra_n_value, fdwra_max_iteration_value,
                    process_continue_instructions_style,
                    process_continue_instructions_children,
                    results_table_style
                    ):
    triggered_id = dash.ctx.triggered_id
    if triggered_id == "reset-to-process-step":
        disable_tab, hide_text = reset_to_process_step_data
        return (*([False]*2),
                disable_tab,
                disable_tab,
                "" if hide_text else process_continue_instructions_children,
                process_continue_instructions_style,
                "",
                "",
                *([False]*7),
                *([results_table_style]*5),
                disable_tab,
               )

    if triggered_id == "process-settings":

        if process_settings_data == "process_method_value":
            return (None,
                    None,
                    True,
                    True,
                    "Please select Processing Method before attempting to process your data.",
                    {**process_continue_instructions_style, **dict(color=COLORS["error"])},
                    *([None]*14),
                    True,
                    )

        if process_settings_data == "combine_horizontals_select_value":
            return (None,
                    None,
                    True,
                    True,
                    "Please select Method to Combine Horizontals before attempting to process your data.",
                    {**process_continue_instructions_style, **dict(color=COLORS["error"])},
                    *([None]*14),
                    True,
                    )

        # preprocess time-domain recordings with latest settings
        records = preprocess_srecord3c(srecord3c_data,
                                       new_start_time_value,
                                       new_end_time_value,
                                       preprocess_settings_data)

        # need to decode a dictionary of settings back to the appropriate object.
        if process_settings_data["processing_method"] == "diffuse_field":
            settings = hvsrpy.HvsrDiffuseFieldProcessingSettings(**process_settings_data)
        elif process_settings_data["processing_method"] == "azimuthal":
            settings = hvsrpy.HvsrAzimuthalProcessingSettings(**process_settings_data)
        elif process_settings_data["processing_method"] == "traditional":
            if process_settings_data["method_to_combine_horizontals"] == "rotdpp":
                settings = hvsrpy.HvsrTraditionalRotDppProcessingSettings(**process_settings_data)
            elif process_settings_data["method_to_combine_horizontals"] == "single_azimuth":
                settings = hvsrpy.HvsrTraditionalSingleAzimuthProcessingSettings(**process_settings_data)
            else:  
                settings = hvsrpy.HvsrTraditionalProcessingSettings(**process_settings_data)
        else:
            raise NotImplementedError

        # apply time-domain window rejection
        # TODO(jpv): To add at some later date.

        hvsr = hvsrpy.process(records, settings)

        if processing_workflow_value == "manual":
            # correct search range values as necessary.
            minimum_search_frequency_value = max(minimum_search_frequency_value,
                                                 min(hvsr.frequency))
            maximum_search_frequency_value = min(maximum_search_frequency_value,
                                                 max(hvsr.frequency))
            search_range_in_hz = (minimum_search_frequency_value,
                                  maximum_search_frequency_value)

            # apply hvsr-domain window rejection
            if rejection_select_value == "fdwra" and settings.processing_method != "diffuse_field":
                max_iteration = hvsrpy.frequency_domain_window_rejection(hvsr,
                                                                         n=fdwra_n_value,
                                                                         max_iterations=fdwra_max_iteration_value,
                                                                         distribution_fn=distribution_resonance_value,
                                                                         distribution_mc=distribution_mean_curve_value,
                                                                         search_range_in_hz=search_range_in_hz)

            resonance_tables = [generate_table_for_resonance(hvsr, distribution_resonance_value,
                                                             distribution_mean_curve_value, search_range_in_hz)]
            resonance_tables.extend([None]*5)
            resonance_tables_display = [HIDE_CONTAINER]*5
            summary_table = generate_table_summary(hvsr)

            if isinstance(hvsr, hvsrpy.HvsrDiffuseField):
                return (*plot_hvsr_diffuse(hvsr, distribution_resonance_value, distribution_mean_curve_value, search_range_in_hz),
                        False,
                        True,
                        "Processing complete. Continue to the Results and HVSR tabs.",
                        {**process_continue_instructions_style, "color": COLORS["primary"]},
                        create_hvsrpy_file_href(hvsr, distribution_mean_curve_value),
                        "filename.hvsrpy",
                        summary_table,
                        *resonance_tables,
                        *resonance_tables_display,
                        False,
                        )

            if isinstance(hvsr, hvsrpy.HvsrAzimuthal):
                if rejection_select_value != "fdwra":
                    hvsr._update_peaks_bounded(search_range_in_hz=search_range_in_hz)
                return (*plot_hvsr_azimuthal(hvsr, distribution_resonance_value, distribution_mean_curve_value, search_range_in_hz),
                        False,
                        False,
                        "Processing complete. Continue to the Results, HVSR, and HVSR-3D tabs.",
                        {**process_continue_instructions_style, "color": COLORS["primary"]},
                        create_hvsrpy_file_href(hvsr, distribution_mean_curve_value),
                        "filename.hvsrpy",
                        summary_table,
                        *resonance_tables,
                        *resonance_tables_display,
                        False,
                        )

            if isinstance(hvsr, hvsrpy.HvsrTraditional):
                if rejection_select_value != "fdwra":
                    hvsr._update_peaks_bounded(search_range_in_hz=search_range_in_hz)
                return (*plot_hvsr_traditional(hvsr, distribution_resonance_value, distribution_mean_curve_value, search_range_in_hz),
                        False,
                        True,
                        "Processing complete. Continue to the Results and HVSR tabs.",
                        {**process_continue_instructions_style, "color": COLORS["primary"]},
                        create_hvsrpy_file_href(hvsr, distribution_mean_curve_value),
                        "filename.hvsrpy",
                        summary_table,
                        *resonance_tables,
                        *resonance_tables_display,
                        False,
                        )

        if processing_workflow_value == "autohvsr":
            # extract peak features
            _peak_data = extract_hvsr_features(hvsr)
            if len(_peak_data) > 0:

                df = pd.DataFrame(_peak_data)

                # classify peaks
                trained_model = xgb.XGBClassifier()
                trained_model.load_model("protected/2_xgboost_peak_classifier.json")
                df["peak frequency"] = np.log(df["peak frequency"])
                x = df.to_numpy()[:, 2:]
                valid_boolean_mask = trained_model.predict(x).astype(bool)
                df["valid"] = valid_boolean_mask

                # default assumption is that all peaks are invalid, that is they belong to resonance -1
                resonance_values = np.full_like(x[:, 0], -1, dtype=int)
                if sum(valid_boolean_mask) > 0:
                    # only cluster valid peaks
                    x_valid = x[valid_boolean_mask]

                    dbscan_settings = dict(eps=0.2, min_samples=10, metric="euclidean")
                    db = cluster.DBSCAN(**dbscan_settings).fit(x_valid[:, 0:1])
                    y_pred = db.labels_

                    nresonances = set(y_pred)
                    nresonances.discard(-1)

                    # check if a split will help (mean split)
                    delta_resonance = 0
                    for nresonance in nresonances:
                        nresonance += delta_resonance
                        values = x_valid[y_pred == nresonance, 0]

                        if len(values) < 6 or (np.max(values) - np.min(values)) < 1E-3:
                            continue

                        before_variance = np.var(values)
                        split_value = np.mean(values)

                        if len(values[values <= split_value]) < 3 or len(values[values > split_value]) < 3:
                            continue

                        after_variance = np.var(
                            values[values <= split_value]) + np.var(values[values > split_value])

                        # perform split
                        gamma = 0.02
                        if (before_variance - after_variance) > gamma:
                            y_pred[y_pred > nresonance] += 1
                            y_pred[np.logical_and(y_pred == nresonance,
                                                  x_valid[:, 0] > split_value)] += 1
                            delta_resonance += 1

                    resonance_values[valid_boolean_mask] = y_pred

                    # order resonance labels smallest to largest
                    nresonances = set(resonance_values)
                    nresonances.discard(-1)
                    nresonances = list(nresonances)
                    fmeans = []
                    for resonance in nresonances:
                        fmeans.append(np.mean(x[resonance_values == resonance, 0]))
                    old_resonance_order = np.array(nresonances)[np.argsort(fmeans)]
                    new_resonance_order = np.arange(len(nresonances))

                    old_resonance_values = resonance_values.copy()
                    for old_resonance_value, new_resonance_value in zip(old_resonance_order, new_resonance_order):
                        resonance_values[old_resonance_values ==
                                         old_resonance_value] = new_resonance_value

                df["resonance"] = resonance_values

                # reset peak frequency to hz
                df["peak frequency"] = np.exp(df["peak frequency"])

                if isinstance(hvsr, hvsrpy.HvsrAzimuthal):
                    raise NotImplementedError
                    # TODO(jpv): Prepare azimuthal processing with autohvsr.
                    # return (*plot_hvsr_azimuthal_autohvsr(hvsr, distribution_resonance_value, distribution_mean_curve_value, df),
                    #         False,
                    #         "Processing complete. Continue to the Results, HVSR, and HVSR-3D tabs.",
                    #         {**process_continue_instructions_style, "color": COLORS["primary"]},
                    #         generate_table_summary(hvsr),
                    #         *([None]*10),  # *resonance_tables)

                if isinstance(hvsr, hvsrpy.HvsrTraditional):
                    g1, g2, stats = plot_hvsr_traditional_autohvsr(
                        hvsr, distribution_resonance_value, distribution_mean_curve_value, df)
                    nresults = len(stats)

                    resonance_tables = [
                        generate_table_for_resonance_from_values(*stat) for stat in stats]
                    resonance_tables.extend([None]*(6-nresults))
                    display_tables = [DISPLAY_CONTAINER]*(nresults-1)
                    display_tables.extend([HIDE_CONTAINER]*(5-(nresults-1)))

                    return (g1,
                            g2,
                            False,
                            True,
                            "Processing complete. Continue to the Results and HVSR tabs.",
                            {**process_continue_instructions_style, "color": COLORS["primary"]},
                            create_hvsrpy_file_href(hvsr, distribution_mean_curve_value),
                            "filename.hvsrpy",
                            generate_table_summary(hvsr),
                            *resonance_tables,
                            *display_tables,
                            False,
                            )

    raise PreventUpdate


if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port="8050")
