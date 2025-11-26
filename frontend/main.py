import requests

from flask import Flask, session as flask_session
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user

from datetime import datetime

import dash
from dash import dcc, html, Input, Output, State, dash_table, ALL, MATCH
import dash_bootstrap_components as dbc

import pandas as pd
import base64, io, json
import plotly.express as px
import plotly.graph_objects as go
import logging
from pathlib import Path

from config import settings
from schemas.report import Report


# --------------------------
# User class
# --------------------------
class DashUser(UserMixin):
    def __init__(self, id, email):
        self.id = id
        self.email = email


# --------------------------
# Flask + LoginManager (for Dash)
# --------------------------
flask_server = Flask(__name__)
flask_server.secret_key = settings.SECRET_KEY

login_manager = LoginManager()
login_manager.init_app(flask_server)
login_manager.login_view = "/dash/"
initial_file_path = Path() / "samples" / "test_file.csv"
initial_configuration_path = Path() / "samples" / "dashboard_1.json"
components = {"todo": "todo"}


@login_manager.user_loader
def load_user(user_id):
    email = flask_session.get("email")
    if email:
        return DashUser(user_id, email)
    return None


# --------------------------
# Dash app
# --------------------------
app = dash.Dash(
    __name__,
    server=flask_server,
    routes_pathname_prefix="/dash/",
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True
)
navbar = dbc.Navbar(
    children=[
        # Left: App Title
        dbc.NavbarBrand("Data Viz", className="ms-2"),

        # Hamburger toggle for mobile
        dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),

        # Collapsible menu items (right side)
        dbc.Collapse(
            dbc.Nav(
                [
                    dbc.NavItem(dbc.NavLink("Download PDF", id="download-pdf-btn", href="#", className="nav-link")),
                    dbc.NavItem(dbc.NavLink("Home", href="#", className="nav-link")),
                    dbc.NavItem(dbc.NavLink("About", href="#", className="nav-link")),
                    dbc.NavItem(dbc.NavLink("GitHub", href="https://github.com/", target="_blank")),
                    dbc.NavItem(dbc.NavLink("Logout", id="logout-btn", href="#", target="_blank")),
                ],
                className="ms-auto",  # Push to right
                navbar=True,
            ),
            id="navbar-collapse",
            is_open=False,
            navbar=True,
        ),
    ],
    color="dark",
    dark=True,
    sticky="top",

)

footer = html.Footer(
    [f"""
    Data Visualisation Dashboard
    """,
     html.Br(),
     html.Hr(),
     f"{datetime.today().strftime("%Y-%m-%d")}"
        , html.Div("Contact:"),
     html.Div([
         html.A(html.I(className="fas fa-envelope"), href="mailto:sgvolpe@gmail.com", target="_blank"),
         html.A(html.I(className="fab fa-linkedin"), href="https://linkedin.com/in/santiago-gonzalez-volpe-22009a35",
                target="_blank"),
         html.A(html.I(className="fab fa-github"), href="https://github.com/sgvolpe", target="_blank")
     ], className="footer-links"),
     html.Div("Developed by SGV", className="footer-signature")

     ],
    className="footer"
)
app.layout = html.Div(
    [
        navbar,
        html.Div(
    id="page-content",
    children=["no content."]
), footer
    ]
                      )


@app.callback(
    Output("navbar-collapse", "is_open"),
    Input("navbar-toggler", "n_clicks"),
    State("navbar-collapse", "is_open"),
)
def toggle_navbar(n, is_open):
    if n:
        return not is_open
    return is_open



store = [dcc.Store(id="stored-data", storage_type="session"),
         dcc.Store(id="dashboard-state", data={"tabs": []}, storage_type="session"),
       ]


def login_layout():
    return dbc.Container([
        dcc.Location(id="url_login", refresh=True),
        dbc.Row(dbc.Col(
            dbc.Card(dbc.CardBody([
                html.H2("Login", className="text-center mb-4"),
                dbc.FormFloating([
                    dbc.Input(type="email", id="login-email", placeholder="Email"),
                    dbc.Label("Email")
                ]),
                dbc.FormFloating([
                    dbc.Input(type="password", id="login-password", placeholder="Password"),
                    dbc.Label("Password")
                ]),
                dbc.Button("Login", id="login-button", color="primary", className="w-100 mt-2"),
                html.Div(id="login-alert", className="mt-3")
            ]), className="shadow p-3 rounded"),
            width=12, style={"maxWidth": "400px", "margin": "auto"}
        ), className="vh-100 d-flex align-items-center justify-content-center")
    ], fluid=True)


def protected_layout():
    return html.Div(
        children=[

            html.Div(
                children=[
                    *store,
                    dbc.Container(
                        [
                            dbc.Row(
                                html.H2(
                                    "Drag & Drop Dashboard Builder",
                                    style={"textAlign": "center", "marginTop": "20px"}
                                ),
                            ),
                            dbc.Row(
                                children=[
                                    dbc.Col(
                                        [  # CSV Upload
                                            dcc.Upload(
                                                id="upload-data",
                                                children=html.Div(["Drag and Drop or ", html.A("Select CSV File")]),
                                                style={
                                                    "width": "100%", "height": "100px", "lineHeight": "100px",
                                                    "borderWidth": "2px", "borderStyle": "dashed",
                                                    "borderRadius": "10px", "textAlign": "center", "margin": "10px"},
                                                multiple=False
                                            ),

                                            html.Div(id="file-info-div",
                                                     style={"fontWeight": "bold", "marginTop": "10px"}), ]
                                    ),
                                    dbc.Col(
                                        [  # Upload dashboard JSON
                                            dcc.Upload(
                                                id="upload-dashboard-json",
                                                children=html.Div(["Drag and Drop or ", html.A("Select JSON File")]),
                                                style={
                                                    "width": "100%", "height": "100px", "lineHeight": "100px",
                                                    "borderWidth": "2px", "borderStyle": "dashed",
                                                    "borderRadius": "10px", "textAlign": "center", "margin": "10px"},
                                                multiple=False
                                            )
                                        ]
                                    )
                                ]
                            ),
                            dbc.Row(
                                html.Hr()
                            ),

                            dbc.Row(
                                dbc.Col(
                                    children=[
                                        dbc.Button(
                                            "Save Dashboard JSON",
                                            id="save-dashboard-btn",
                                            color="success",
                                            outline=True,
                                            style={"margin": "10px"}
                                        ),

                                    ]
                                )
                            ),
                            dbc.Row(
                                html.Hr(),

                            ),
                            # Dashboard controls
                            dbc.Row(
                                dbc.Col(
                                    children=[
                                        dbc.Button(
                                            "Add Tab",
                                            id="add-tab-btn",
                                            color="primary",
                                            outline=True,
                                            style={"margin": "10px"}
                                        ),
                                    ]
                                )
                            ),

                            dcc.Download(id="download-dashboard-json"),
                            html.Br(),
                            html.Br(),

                            # Modal for adding components
                            dbc.Modal([
                                dbc.ModalHeader("Add Component"),
                                dbc.ModalBody([
                                    dbc.Label("Component Type"),
                                    dcc.Dropdown(id="component-type-dropdown",
                                                 options=[{"label": "Graph", "value": "graph"},
                                                          {"label": "Table", "value": "table"},
                                                          {"label": "Statistic", "value": "stat"}],
                                                 placeholder="Select component type"),
                                    html.Div(id="component-settings-div")
                                ]),
                                dbc.ModalFooter(
                                    dbc.Button("Add Component", id="confirm-add-component", color="success"))
                            ], id="add-component-modal", is_open=False, size="lg"),

                        ],
                        fluid=True,
                        className="panel"
                    ),
                    dbc.Container(
                        children=[
                            dbc.Row(
                                children=[
                                    dbc.Col(
                                        children=[
                                            html.Div(id="tabs-container"),
                                            html.Div(id="tab-content-container"),
                                        ]
                                    )
                                ]
                            ),
                            dbc.Row(
                                children=[
                                    dbc.Col(
                                        children=[

                                        ]
                                    )
                                ]
                            )
                        ],
                        className="panel"
                    )
                ],
                className="app-content"
            ),
            dcc.Download(id="download-pdf"),
            footer

        ]
    )
    # return dbc.Container([
    #     html.H1("Protected Dashboard"),
    #     html.Div(f"Hello {current_user.email}, you are logged in!"),
    #     dbc.Button("Logout", id="logout-button", color="danger", className="mt-3")
    # ], className="p-4")


# --------------------------
# Dash callbacks
# --------------------------

# Page display callback
@app.callback(
    Output("page-content", "children"),
    Output("logout-btn", "n_clicks"),

    Input("page-content", "id"),
    Input("logout-btn", "n_clicks"),
)
def display_page(_, logout_clicks):
    try:
        print(f"{logout_clicks=}")
        if logout_clicks :
            logout_user()
            flask_session.pop("email", None)
            return login_layout(), None
        if current_user.is_authenticated:
            return protected_layout(), logout_clicks
        return login_layout(), logout_clicks
    except Exception as exc:
        print("ERROR IN DISPLAY PAGE")
        print(exc)


@app.callback(
    Output("login-alert", "children"),
    Input("login-button", "n_clicks"),
    State("login-email", "value"),
    State("login-password", "value"),
    prevent_initial_call=True
)
def process_login(n, email, password):
    if not email or not password:
        return dbc.Alert("Email and password required.", color="danger")
    try:

        # Call FastAPI login endpoint
        response = requests.post(
            f"{settings.AUTH_HOST}:{settings.AUTH_PORT}/dash-login",
            json={"email": email, "password": password}
        )
        if response.status_code != 200:
            print(f"{response.text=}")
            return dbc.Alert(f"{response.text=}Invalid credentials.", color="danger")

        # Log into Flask/Dash
        user = DashUser(id=email, email=email)
        login_user(user)
        flask_session["email"] = email
        return dcc.Location(href="/dash/", id="redirect")
    except Exception as exc:
        print(f"{exc=}")
        return dbc.Alert("Server error", color="danger")


def empty_tab(idx=0, title: str = None) -> dict:
    return {
        'title': title or f'Tab {idx + 1}',
        'children': [
            empty_row(idx=0, tab_idx=idx),
        ]
    }


def empty_row(idx=0, tab_idx=0) -> dict:
    return {
        'type': 'row',
        'children': [
            empty_col(idx=0, row_idx=idx, tab_idx=tab_idx),

        ]
    }


def empty_col(idx=0, tab_idx=0, row_idx=0) -> dict:
    logging.debug("CREATING EMPTY COL")

    return {
        'type': 'col',
        'children': [
            # empty_card(idx, col_idx=idx, tab_idx=tab_idx, row_idx=row_idx),
        ]
    }


def empty_card(idx=0, col_idx=0, tab_idx=0, row_idx=0) -> dict:
    return {
        'type': 'card',
        'title': f'EMPTY Card {idx + 1}',
        'footer': None,
        'children': None,
        "idx": idx,
        "col_idx": col_idx,
        "tab_idx": tab_idx,
        "row_idx": row_idx,
    }


# ---------- Parse CSV ----------
@app.callback(
    Output("stored-data", "data"),
    Output("file-info-div", "children"),
    Input("upload-data", "contents"),
    State("upload-data", "filename")
)
def parse_csv(contents, filename):
    if contents is None:
        df = pd.read_csv(initial_file_path)
        # return None, ""
    else:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        try:
            df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
        except Exception as e:
            return None, f"Error reading CSV: {e}"
    info_text = f"File: {filename} | Rows: {df.shape[0]} | Columns: {df.shape[1]}"
    return df.to_json(date_format="iso", orient="split"), info_text


def build_chart(
        df: pd.DataFrame,
        chart_type: str,
        x: str = None,
        y1: list = None,
        y2: list = None,
        title: str = "",
        layout: dict = None
):
    """
    Build a Plotly chart for Dash based on a dataframe.

    Parameters:
        df (pd.DataFrame): Data source.
        chart_type (str): 'line', 'bar', 'scatter'.
        x (str): Column name for X-axis.
        y1 (list): List of columns for primary Y-axis.
        y2 (list): List of columns for secondary Y-axis (right axis).
        title (str): Chart title.
        width (int): Figure width.
        height (int): Figure height.

    Returns:
        dbc.Card: Dash card containing the chart.
    """

    logging.debug(f"""
    BUILDING CHART:
    {df.shape}
    {chart_type=}
    {x=}
    {y1=}
    {y2=}
    {title=}
""")
    fig = go.Figure()

    logging.debug(f"{layout=}")

    # __________ SETUP DEFAULTS ____________ #
    if layout is None: layout = {}
    logging.debug(f"{layout=}")

    y1 = y1 or []
    y2 = y2 or []

    y1 = [y1] if not isinstance(y1, list) else y1
    y2 = [y2] if not isinstance(y2, list) else y2

    # Add traces for primary Y-axis
    df_columns = df.columns
    for col in y1:
        if col not in df_columns:
            raise Exception(f"{col} not in {df_columns}")
        if chart_type == "line":
            fig.add_trace(go.Scatter(x=df[x], y=df[col], mode="lines+markers", name=col, yaxis="y1"))
        elif chart_type == "bar":
            fig.add_trace(go.Bar(x=df[x], y=df[col], name=col, yaxis="y1"))
        elif chart_type == "scatter":
            fig.add_trace(go.Scatter(x=df[x], y=df[col], mode="markers", name=col, yaxis="y1"))

    # Add traces for secondary Y-axis
    for col in y2:
        if chart_type == "line":
            fig.add_trace(go.Scatter(x=df[x], y=df[col], mode="lines+markers", name=col, yaxis="y2"))
        elif chart_type == "bar":
            fig.add_trace(go.Bar(x=df[x], y=df[col], name=col, yaxis="y2"))
        elif chart_type == "scatter":
            fig.add_trace(go.Scatter(x=df[x], y=df[col], mode="markers", name=col, yaxis="y2"))

    # Layout configuration
    default_layout = {
        "title": title,
        "width": 600,
        "height": 400,
        "yaxis": {"title": "Y1"},
        "yaxis2": {"title": "Y2", "overlaying": "y", "side": "right"} if y2 else None,
        "xaxis": {"title": x},
        "template": "plotly_white",
        "legend": {"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
        "margin": {"l": 40, "r": 40, "t": 40, "b": 40},
    }

    default_layout.update(**layout)
    layout = default_layout

    fig.update_layout(
        **layout
    )
    return dcc.Graph(figure=fig)


def build_component(card, df):
    component_type = card.get("component_type", "N/A")
    try:
        if component_type == "chart":
            x_axis = card.get("x_axis", "N/A")
            y_axis_1 = card.get("y_axis_1", "N/A")
            y_axis_2 = card.get("y_axis_2", "N/A")
            chart_type = card.get("chart_type", None)
            component = build_chart(
                df=df,
                chart_type=chart_type,
                x=x_axis,
                y1=y_axis_1,
                y2=y_axis_2
            )

        else:
            component = "NOT YET SUPPORTED"
    except Exception as exc:
        component = f"ERROR {exc} {card=}"
    return component


# ---------- Render Tabs ----------
def render_card(card, idx, tab_idx, row_idx, col_idx, search_dict, df) -> list:
    logging.debug(f"         RENDERING CARD {idx} ")
    logging.debug(f'        {card=}')
    logging.debug(f'{card=}')
    cards_index = {}

    component = build_component(card, df)

    return [
        dbc.Card(
            [
                dbc.CardHeader([
                    card.get("title", "No Title")
                ]),
                dbc.CardBody([
                    component
                ]),
                dbc.CardFooter([
                    card.get('footer', "No Footer")
                ])
            ])
    ]


def render_create_comp_form(col_idx, tab_idx, row_idx, df):
    columns = [col for col in df.columns]
    chart_types = ["bar", "line", "scatter"]
    aggregations = ["Sum", "Count", "Mean"]
    chart_form = dbc.Row(
        dbc.Col(
            dbc.Card(
                dbc.Form(
                    [
                        dbc.Row(

                            [
                                html.H3("Create a Chart Component"),
                                dbc.Label("Chart Type", width=2),
                                dbc.Col(
                                    dbc.Select(
                                        id={
                                            "type": "chart-type-dropdown",
                                            "tab": tab_idx,
                                            "row": row_idx,
                                            "col": col_idx},
                                        options=[{"label": c, "value": c} for c in chart_types],
                                        value=chart_types[0],
                                    ),
                                    width=4
                                ),
                            ],
                            className="mb-3"
                        ),
                        dbc.Row(
                            [
                                dbc.Label("X Axis", width=2),
                                dbc.Col(
                                    dbc.Select(
                                        id={"type": "x-axis-dropdown", "tab": tab_idx, "row": row_idx, "col": col_idx},
                                        options=[{"label": c, "value": c} for c in columns],
                                        value=columns[0],
                                    ),
                                    width=4
                                ),
                            ],
                            className="mb-3"
                        ),
                        dbc.Row(
                            [
                                dbc.Label("Chart Type", width=2),
                                dbc.Col(
                                    dbc.Select(
                                        id={"type": "chart-type-dropdown", "tab": tab_idx, "row": row_idx,
                                            "col": col_idx},
                                        options=[{"label": c, "value": c} for c in columns],
                                        value=columns[1],
                                    ),
                                    width=4
                                ),
                            ],
                            className="mb-3"
                        ),
                        dbc.Row(
                            [
                                dbc.Label("Y Axis 1", width=2),
                                dbc.Col(
                                    dbc.Select(
                                        id={"type": "y-axis-1-dropdown", "tab": tab_idx, "row": row_idx,
                                            "col": col_idx},
                                        options=[{"label": c, "value": c} for c in columns],
                                        value=columns[1],
                                    ),
                                    width=4
                                ),
                            ],
                            className="mb-3"
                        ),
                        dbc.Row(
                            [
                                dbc.Label("Y Axis 2", width=2),
                                dbc.Col(
                                    dbc.Select(
                                        id={"type": "y-axis-2-dropdown", "tab": tab_idx, "row": row_idx,
                                            "col": col_idx},
                                        options=[{"label": c, "value": c} for c in columns],
                                        value=columns[2],
                                    ),
                                    width=4
                                ),
                            ],
                            className="mb-3"
                        ),
                        dbc.Button(
                            "Generate Chart",
                            id={"type": "add-chart-btn",
                                "tab": tab_idx, "row": row_idx, "col": col_idx},
                            color="primary")
                    ],

                )
            )
        ),
        id={"type": "chart-form", "tab": tab_idx, "row": row_idx, "col": col_idx},
        style={"display": "none"},
        className="component-form"
    )

    table_form = dbc.Row(
        dbc.Col(
            dbc.Card(
                [
                    dbc.CardHeader(html.H4("Create a Table Component")),
                    dbc.CardBody(
                        dbc.Form(
                            children=[
                                dbc.Row(
                                    [
                                        dbc.Label("Select Columns", width=2),
                                        dbc.Col(
                                            dbc.Select(
                                                id={"type": "table-columns-dropdown", "tab": tab_idx, "row": row_idx,
                                                    "col": col_idx},
                                                options=[{"label": c, "value": c} for c in columns],
                                                value="",
                                                # multi=True
                                            ),
                                        ),
                                    ],
                                    className="mb-3"
                                ),
                            ],
                        )
                    )]
            )
        ),
        id={"type": "table-form", "tab": tab_idx, "row": row_idx, "col": col_idx},
        style={"display": "none"},
        className="component-form"
    )
    stat_form = dbc.Row(
        dbc.Col(
            dbc.Card(
                dbc.Form(
                    children=[
                        html.H3("Create a Stat Component"),
                        dbc.Row(
                            [
                                dbc.Label("Select Column", width=2),
                                dbc.Col(
                                    dbc.Select(
                                        id={"type": "table-columns-dropdown", "tab": tab_idx, "row": row_idx,
                                            "col": col_idx},
                                        options=[{"label": c, "value": c} for c in columns],
                                        value="",
                                        # multi=False
                                    ),
                                    width=4
                                ),
                            ],
                            className="mb-3"
                        ),
                        dbc.Row(
                            [
                                dbc.Label("Select Aggregation", width=2),
                                dbc.Col(
                                    dbc.Select(
                                        id={"type": "table-columns-dropdown", "tab": tab_idx, "row": row_idx,
                                            "col": col_idx},
                                        options=[{"label": c, "value": c} for c in aggregations],
                                        value="",
                                        # multi=False
                                    ),
                                    width=4
                                ),
                            ],
                            className="mb-3"
                        ),
                    ]

                )
            )
        ),
        id={"type": "stat-form", "tab": tab_idx, "row": row_idx, "col": col_idx},
        style={"display": "none"},
        className="component-form"
    )
    return [
        html.H2("Add Component..."),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Button(
                        "📋",
                        id={"type": "add-table-btn", "tab": tab_idx, "row": row_idx, "col": col_idx},
                        color="primary",
                        className="m-1",
                        outline=True,

                    ),
                    width="auto"
                ),
                dbc.Tooltip(
                    "Add a new table",
                    target={"type": "add-table-btn", "tab": tab_idx, "row": row_idx, "col": col_idx},
                    placement="top",
                    trigger="hover"
                ),
                dbc.Col(
                    dbc.Button(
                        "📊",
                        id={"type": "show-chart-form",
                            "tab": tab_idx, "row": row_idx, "col": col_idx
                            },
                        color="primary",
                        outline=True,
                        className="m-1"
                    ),
                    width="auto"
                ),
                dbc.Tooltip(
                    "Add a new Chart",
                    target={"type": "show-chart-form", "tab": tab_idx, "row": row_idx, "col": col_idx},
                    placement="top",
                    trigger="hover"
                ),
                dbc.Col(
                    dbc.Button(
                        "🔢",
                        id={"type": "add-stat-btn", "tab": tab_idx, "row": row_idx, "col": col_idx},
                        color="primary",
                        outline=True,
                        className="m-1"
                    ),
                    width="auto"
                ),
                dbc.Tooltip(
                    "Add a new Metric",
                    target={"type": "add-stat-btn", "tab": tab_idx, "row": row_idx, "col": col_idx},
                    placement="top",
                    trigger="hover"
                ),
            ],
            className="justify-content-center"
        ),
        dbc.Row(
            children=[
                chart_form,
                table_form,
                stat_form
            ],
            className="justify-content-center"

        ),

    ]


def render_col(col, col_idx, tab_idx, row_idx, search_dict, df: pd.DataFrame) -> dbc.Col:
    logging.debug(f"RENDERING COL {col_idx}")
    logging.debug(f'        {col=}')
    rendered_card = None
    col_children = col.get('children', [])
    if len(col_children) > 0:
        for idx, child in enumerate(col_children):
            add_component_style = {"display": "none", "marginTop": "10px", "marginBottom": "10px"}
            if isinstance(child, dict) and child.get('type') == 'card':
                rendered_card = render_card(
                    child, idx, tab_idx, row_idx, col_idx, search_dict, df
                )
            else:
                rendered_card = str(child)
    else:
        add_component_style = {"display": "block", "marginTop": "10px", "marginBottom": "10px"}

    add_component_row = dbc.Row(
        id={
            "type": "add-component-row",
            "col_idx": col_idx, "tab_idx": tab_idx, "row_idx": row_idx
        },
        children=render_create_comp_form(col_idx, tab_idx, row_idx, df),
        # children=dbc.Col(
        #     dbc.InputGroup(
        #         [
        #             dcc.Dropdown(
        #                 id={
        #                     "type": "component-dropdown",
        #                     "tab": tab_idx,
        #                     "row": row_idx,
        #                     "col": col_idx
        #                 },
        #                 options=[{"label": k, "value": k} for k in components.keys()],
        #                 placeholder="Select component",
        #                 className="report-dropdown"
        #             ),
        #             dbc.Button(
        #                 "Add",
        #                 id={
        #                     "type": "add-component-btn",
        #                     "tab": tab_idx,
        #                     "row": row_idx,
        #                     "col": col_idx
        #                 },
        #                 className="btn btn--sm"
        #             ),
        #         ],
        #     ),
        # ),
        align="center",
        className="add-component-row",
        style=add_component_style
    )

    remove_button = dbc.Button(
        "Remove Column",
        id={"type": "remove-col-btn", "tab": tab_idx, "row": row_idx, "col": col_idx},
        className="btn btn--sm btn--negative hover-buttons",
        color="danger",
        outline=True
    )

    return dbc.Col(
        [
            dbc.Row(
                dbc.Col(
                    children=rendered_card,
                    className="centered"
                )
            ),
            add_component_row,
            dbc.Row(dbc.Col(remove_button, className="centered hover-col-buttons")),

        ],
        className=""
    )


def render_row(row, row_idx, tab_idx, search_dict, df) -> dbc.Row:
    logging.debug(f"""
    RENDERING ROW {row_idx}
    {row}
""")
    children = []
    for idx, child in enumerate(row.get('children', [])):
        if isinstance(child, dict) and child.get('type') == 'col':
            children.append(
                render_col(
                    child, idx, tab_idx, row_idx, search_dict, df
                )
            )
        else:
            children.append(str(child))

    children.append(
        dbc.Row(
            dbc.Col(
                children=dbc.Button(
                    "Add Column",
                    id={"type": "add-col-btn", "tab": tab_idx, "row": row_idx},
                    className="btn btn--sm hover-buttons",
                    color="primary",
                    outline=True
                ),
                className="centered",
            ),
            className="mar-1 centered "
        )

    )

    remove_button = dbc.Button(
        "Remove Row",
        id={"type": "remove-row-btn", "tab": tab_idx, "row": row_idx},
        className="btn btn--sm btn--negative",
        color="danger",
        outline=True
    )
    children.append(
        dbc.Row(
            dbc.Col(remove_button),
            className="centered hover-buttons"
        )

    )

    return dbc.Row(
        children=children,
        className="mar-1",
    )


def render_tab(tab, tab_idx, search_dict, df) -> dbc.Tab:
    logging.debug(f"""
    RENDERING TAB {tab_idx}
    {tab.get("uid")=}
    {tab.get("method")=}
    {tab=}
    """)
    children = []
    for idx, child in enumerate(tab.get('rows', [])):
        if isinstance(child, dict) and child.get('type') == 'row':
            children.append(
                render_row(
                    child, idx, tab_idx, search_dict, df
                )
            )
            children.append(
                dbc.Row(
                    className="row-separator"
                )
            )
    # Add Row button
    children.append(
        dbc.Row(
            dbc.Col(
                children=[
                    dbc.Button(
                        "Add Row",
                        id={"type": "add-row-btn", "tab": tab_idx},
                        className="btn btn--sm hover-buttons",
                        color="primary",
                        outline=True,
                        style={"positon": "relative", "top": "-20px"}
                    )
                ],
                className="centered mar-1"

            ),
            className="add-row-button-row centered mar-1"
        )

    )
    remove_button = dbc.Button(
        "Remove Tab",
        id={"type": "remove-tab-btn", "tab": tab_idx},
        className="btn btn--sm btn--negative",
        color="danger",
        outline=True,

    )
    children.append(remove_button)
    #
    # return rendered_tab
    return dbc.Tab(
        children=children or ["EMPTY TAB"], label=tab.get('title', f'Tab {tab_idx + 1}'),
        class_name="tab parent-hover parent-col-hover tabs__panel ",  #
        id={"type": "tab", "tab": tab_idx, },
        tab_class_name="tab tabs__tab ",
        tab_style={"max-width": "100%", "padding": "10px"},
        label_style={"max-width": "100%", "padding": "10px"}
    )


@app.callback(
    Output("download-pdf", "data"),
    Input("download-pdf-btn", "n_clicks"),
    State("dashboard-state", "data"),
    State("stored-data", "data"),
    prevent_initial_call=True,
)
def trigger_pdf_download(n, state, data):
    data_js = json.loads(data)
    df = pd.DataFrame(**data_js)
    logging.debug(df)

    report = Report(**state)
    logging.debug(report)
    pdf_bytes = report.pdf(
        df=df
    )

    return dcc.send_bytes(pdf_bytes, "report.pdf")


@app.callback(
    Output({'type': 'chart-form', 'tab': MATCH, 'row': MATCH, 'col': MATCH}, 'style'),
    Output({'type': 'table-form', 'tab': MATCH, 'row': MATCH, 'col': MATCH}, 'style'),
    Output({'type': 'stat-form', 'tab': MATCH, 'row': MATCH, 'col': MATCH}, 'style'),

    Input({'type': 'show-chart-form', 'tab': MATCH, 'row': MATCH, 'col': MATCH}, 'n_clicks'),
    Input({'type': 'add-table-btn', 'tab': MATCH, 'row': MATCH, 'col': MATCH}, 'n_clicks'),
    Input({'type': 'add-stat-btn', 'tab': MATCH, 'row': MATCH, 'col': MATCH}, 'n_clicks'),

    prevent_initial_call=True
)
def toggle_components_form(chart, table, stat):
    ctx = dash.callback_context

    if not ctx.triggered:
        return dash.no_update

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    show = {"display": "block"}
    hide = {"display": "none"}
    if 'show-chart-form' in trigger_id:
        chart_style = show
        table_style = hide
        stat_style = hide
    elif 'add-table-btn' in trigger_id:
        chart_style = hide
        table_style = show
        stat_style = hide
    elif 'add-stat-btn' in trigger_id:
        chart_style = hide
        table_style = hide
        stat_style = show
    else:
        chart_style = hide
        table_style = hide
        stat_style = hide
    return chart_style, table_style, stat_style


@app.callback(
    Output("tabs-container", "children"),
    Input("dashboard-state", "data"),
    State("stored-data", "data")
)
def render_tabs(state, data):
    logging.debug("Rendering Tabs")
    logging.debug(f"{data=}")
    tabs_children = state.get("tabs", []) if isinstance(state, dict) else state
    if data is not None:
        data_js = json.loads(data)
        df = pd.DataFrame(**data_js)
    else:
        df = pd.DataFrame([])

    if not state['tabs']:
        return html.Div("No tabs yet.")
    search_dict = {}
    return dbc.Tabs(
        children=[
            render_tab(
                tab, idx, search_dict, df
            ) for idx, tab in enumerate(tabs_children)
        ],

    )


# ---------- Render Tab Content ----------
@app.callback(
    Output("tab-content-container", "children"),
    Input("tabs-container", "value"),
    State("dashboard-state", "data"),
    State("stored-data", "data")
)
def render_tab_content(tab_id, state, json_data):
    if tab_id is None or json_data is None:
        return html.Div("Upload CSV and add a tab to start.")
    df = pd.read_json(json_data, orient="split")
    tab_state = next((t for t in state['tabs'] if t['id'] == tab_id), None)
    if tab_state is None:
        return html.Div("Tab not found.")

    content = []
    for r_idx, row in enumerate(tab_state["rows"]):
        columns = []
        for c_idx, col in enumerate(row["columns"]):
            comp_children = []
            for comp in col.get("components", []):
                if comp["type"] == "graph":
                    fig = px.scatter(df, x=comp["x"], y=comp["y"]) if comp.get("x") and comp.get("y") else px.scatter()
                    comp_children.append(dcc.Graph(figure=fig))
                elif comp["type"] == "table":
                    comp_children.append(dash_table.DataTable(
                        columns=[{"name": c, "id": c} for c in df.columns],
                        data=df.to_dict("records"),
                        page_size=10,
                        style_table={'overflowX': 'auto'},
                        style_cell={'textAlign': 'center'}
                    ))
                elif comp["type"] == "stat":
                    col_name = comp.get("column")
                    agg = comp.get("agg")
                    if col_name and agg:
                        value = getattr(df[col_name], agg)()
                        comp_children.append(
                            html.Div(f"{agg.upper()} of {col_name}: {value}", style={"fontWeight": "bold"}))
            columns.append(dbc.Col(comp_children, width=12 // max(1, len(row["columns"]))))
        content.append(dbc.Row(columns, style={"marginBottom": "20px"}))
    return content


# ---------- Save Dashboard JSON ----------
@app.callback(
    Output("download-dashboard-json", "data"),
    Input("save-dashboard-btn", "n_clicks"),
    State("dashboard-state", "data"),
    prevent_initial_call=True
)
def download_dashboard(n_clicks, state):
    return dict(content=json.dumps(state, indent=2), filename="dashboard.json")


@app.callback(
    Output("dashboard-state", "data"),
    Input("add-tab-btn", "n_clicks"),
    Input("upload-dashboard-json", "contents"),
    Input({'type': 'add-row-btn', 'tab': ALL}, 'n_clicks'),
    Input({'type': 'add-col-btn', 'tab': ALL, 'row': ALL}, 'n_clicks'),
    Input({'type': 'remove-col-btn', 'tab': ALL, "row": ALL, "col": ALL}, 'n_clicks'),
    Input({'type': 'remove-row-btn', 'tab': ALL, "row": ALL, }, 'n_clicks'),
    Input({'type': 'remove-tab-btn', 'tab': ALL}, 'n_clicks'),
    Input({'type': 'add-component-btn', 'tab': ALL, 'row': ALL, 'col': ALL}, 'n_clicks'),

    Input({'type': 'add-chart-btn', 'tab': ALL, 'row': ALL, 'col': ALL}, 'n_clicks'),
    Input({'type': 'x-axis-dropdown', 'tab': ALL, 'row': ALL, 'col': ALL}, 'value'),
    Input({'type': 'y-axis-1-dropdown', 'tab': ALL, 'row': ALL, 'col': ALL}, 'value'),
    Input({'type': 'y-axis-2-dropdown', 'tab': ALL, 'row': ALL, 'col': ALL}, 'value'),
    Input({'type': 'chart-type-dropdown', 'tab': ALL, 'row': ALL, 'col': ALL}, 'value'),

    State("dashboard-state", "data"),
    State("upload-dashboard-json", "filename"),
    State({'type': 'component-dropdown', 'tab': ALL, 'row': ALL, 'col': ALL}, 'value'),

    prevent_initial_call=True
)
def update_dashboard_state(
        add_tab_clicks,
        json_contents,
        add_row_clicks,
        add_col_clicks,
        remove_col_clicks,
        remove_row_clicks,
        remove_tab_clicks,
        add_comp_clicks,
        add_chart_btn, x_axis, y_axis_1, y_axis_2, chart_type,
        state,
        filename,
        dropdown_values
):
    tabs = state.get('tabs', [])

    ctx = dash.callback_context

    if not ctx.triggered:
        return dash.no_update

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    logging.debug(trigger_id)
    # Initialize state if None
    if state is None:
        state = {"tabs": []}

    # Case 1: Add Tab button clicked
    if trigger_id == "add-tab-btn":
        import uuid
        new_tab = {"id": str(uuid.uuid4()), "title": f"Tab {len(state['tabs']) + 1}", "rows": []}
        state['tabs'].append(new_tab)
        return state

    if "remove-tab-btn" in trigger_id:
        logging.debug(f'{remove_tab_clicks=}')
        for tab_idx, tab in enumerate(tabs):
            if tab_idx < len(remove_tab_clicks) and remove_tab_clicks[
                tab_idx] and remove_tab_clicks[
                tab_idx] > 0 and f'remove-tab-btn' in trigger_id and f'"tab":{tab_idx}' in trigger_id:
                tabs.pop(tab_idx)
                state['tabs'] = tabs
                return state


    # Case 2: Dashboard JSON uploaded
    elif trigger_id == "upload-dashboard-json" and json_contents is not None:
        import base64, json
        content_type, content_string = json_contents.split(',')
        decoded = base64.b64decode(content_string)
        loaded_state = json.loads(decoded.decode("utf-8"))
        return loaded_state

    if "add-row-btn" in trigger_id:
        for tab_idx, n in enumerate(add_row_clicks):
            if n and n > 0 and f"add-row-btn" in trigger_id and f'"tab":{tab_idx}' in trigger_id:
                tabs[tab_idx]["rows"].extend([
                    empty_row(
                        idx=len(tabs[tab_idx]["rows"]),
                        tab_idx=tab_idx
                    ),
                ]
                )
                state['tabs'] = tabs
                return state
    if "remove-row-btn" in trigger_id:
        for tab_idx, tab in enumerate(tabs):
            for row_idx, row in enumerate(tab['rows']):
                if row_idx < len(remove_row_clicks) and remove_row_clicks[
                    row_idx] and remove_row_clicks[
                    row_idx] > 0 and f'remove-row-btn' in trigger_id and f'"tab":{tab_idx}' in trigger_id and f'"row":{row_idx}' in trigger_id:
                    tab['rows'].pop(row_idx)
                    state['tabs'] = tabs
                    return state

    if 'add-col-btn' in trigger_id:
        idx = 0
        for tab_idx, tab in enumerate(tabs):
            for row_idx, row in enumerate(tab['rows']):
                logging.debug(row)
                if idx < len(add_col_clicks) and add_col_clicks[idx] and add_col_clicks[
                    idx] > 0 and f'add-col-btn' in trigger_id and f'"tab":{tab_idx}' in trigger_id and f'"row":{row_idx}' in trigger_id:
                    row['children'].append(
                        empty_col(
                            idx=len(row['children']),
                            tab_idx=tab_idx,
                            row_idx=row_idx

                        )
                    )
                    state['tabs'] = tabs
                    return state
                idx += 1

    if 'remove-col-btn' in trigger_id:
        logging.debug(f'{remove_col_clicks=}')
        idx = 0
        for tab_idx, tab in enumerate(tabs):
            for row_idx, row in enumerate(tab["rows"]):
                for col_idx, col in enumerate(row['children']):
                    if idx < len(remove_col_clicks) and remove_col_clicks[idx] and remove_col_clicks[
                        idx] > 0 and f'remove-col-btn' in trigger_id and f'"tab":{tab_idx}' in trigger_id and f'"row":{row_idx}' in trigger_id and f'"col":{col_idx}' in trigger_id:
                        row['children'].pop(col_idx)
                        state['tabs'] = tabs
                        return state
                    idx += 1

    if "add-chart-btn" in trigger_id:
        logging.debug("ADDING CHART")
        idx = 0
        logging.debug(f"{idx=}")

        for tab_idx, tab in enumerate(tabs):

            logging.debug("PROCESSING TAB", tab_idx)
            for row_idx, row in enumerate(tab['rows']):
                logging.debug(" PROCESSING ROW", row_idx)
                for col_idx, col in enumerate(row['children']):
                    logging.debug(" PROCESSING COL", col_idx)
                    if (
                            # idx < len(add_chart_btn)  and
                            add_chart_btn[idx] and
                            add_chart_btn[idx] > 0
                            and f'"tab":{tab_idx}' in trigger_id
                            and f'"row":{row_idx}' in trigger_id
                            and f'"col":{col_idx}' in trigger_id
                    ):
                        logging.debug("WILL ADD CHILDREN CARD TO COL")
                        col['children'].append(
                            {
                                'type': 'card',
                                "component_type": "chart",
                                "chart_type": chart_type[idx],
                                "x_axis": x_axis[idx],
                                "y_axis_1": y_axis_1[idx],
                                "y_axis_2": y_axis_2[idx],
                            }
                        )
                        state['tabs'] = tabs
                        return state
                    idx += 1
    if 'add-component-btn' in trigger_id:
        logging.debug(f'{add_comp_clicks=}')
        idx = 0
        for tab_idx, tab in enumerate(tabs):
            logging.debug("PROCESSING TAB", tab_idx)
            for row_idx, row in enumerate(tab['ROWS']):
                logging.debug(" PROCESSING ROW", row_idx)
                for col_idx, col in enumerate(row['children']):

                    if (
                            idx < len(add_comp_clicks)
                            and add_comp_clicks[idx]
                            and add_comp_clicks[idx] > 0
                            and f'add-component-btn' in trigger_id
                            and f'"tab":{tab_idx}' in trigger_id
                            and f'"row":{row_idx}' in trigger_id
                            and f'"col":{col_idx}' in trigger_id
                    ):
                        logging.debug(f'{dropdown_values=}')
                        comp_type = dropdown_values[idx] if dropdown_values and idx < len(dropdown_values) else None
                        logging.debug(f'{comp_type=}')
                        logging.debug(f'{components.get(comp_type, {})=}')
                        if comp_type:
                            col['children'].append(
                                {
                                    'type': 'card',
                                    **components.get(comp_type, {})
                                }
                            )
                            state['tabs'] = tabs
                            return state
                    idx += 1

    return dash.no_update


# ----------------------------
# Run Dash
# ----------------------------
if __name__ == "__main__":
    flask_server.run(debug=True, port=8050)

