import plotly.express as px
import geopandas as gpd
from pathlib import Path
import preprocess_data as ppd
import pandas as pd
import dash
from dash.dependencies import Input, Output
from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template

data_path = Path("data/")
output_path = Path("output/")
# solution_name = "solution_model_1_static.csv"

df, adjacent_matrix = ppd.get_df_adj(data_path, 2021)

geodata = gpd.read_file(data_path / "us_counties.geojson")
geodata.id = geodata.id.astype(str).astype(int)
geodata_ohio = geodata[geodata.id.isin(df.fips)]

color_blank = px.colors.qualitative.Pastel[1]
color_neighbour = px.colors.qualitative.Pastel[0]
color_selected = px.colors.qualitative.Pastel[2]
color_solution = px.colors.qualitative.Pastel[3]
custom_color_map = {
    "blank": color_blank,
    "neighbour": color_neighbour,
    "selected": color_selected,
    "solution": color_solution,
}

geo_df = (
    pd.merge(
        left=gpd.GeoDataFrame.from_features(geodata_ohio),
        right=df,
        left_on="id",
        right_on="fips",
    )
    .set_index("county_id")
    .assign(lat=lambda d: d.geometry.centroid.y, lon=lambda d: d.geometry.centroid.x)
)

# geo_df["colors"] = "blank"
combined_id_official = geo_df.index.astype(str) + ": " + geo_df["NAME"]
combined_id_camm = geo_df["camm_id"].astype(str) + ": " + geo_df["NAME"]


def get_solutions(df, solution_name):
    solutions = pd.read_csv(output_path / solution_name)
    solutions_county_id = solutions["county_id"].values.tolist()
    solutions_camm_id = ppd.county_ids_to_camm_ids(df, solutions_county_id)
    return solutions, solutions_county_id, solutions_camm_id


def get_neighbours(selection, geo_df=geo_df, adjacent_matrix=adjacent_matrix):
    if selection is None:
        return None
    else:
        selection_df = geo_df.loc[adjacent_matrix[selection]]
        selection_df["colors"] = "neighbour"
        selection_df.loc[selection, "colors"] = "selected"
        return selection_df


def set_solution_colors(solutions):
    geo_df["colors"] = "blank"
    geo_df.loc[geo_df.index.isin(solutions["county_id"]), "colors"] = "solution"
    return geo_df


def get_figure(fig, hover):
    if hover != -1 and hover is not None:
        highlights = get_neighbours(hover)

        print_hi = highlights["NAME"].values.tolist()
        print(f"Highlighting for {hover} : {print_hi}")
        # print(f"latitude: = {highlights['lat']}")
        fig.add_trace(
            px.choropleth(
                highlights,
                geojson=highlights.geometry,
                color=highlights.colors,
                hover_name=highlights.NAME,
                locations=highlights.index,
                color_discrete_map=custom_color_map,
            ).data[0]
        )
    return fig

app = dash.Dash(external_stylesheets=[dbc.themes.FLATLY])

server = app.server

# app.layout = html.Div(
#     [
#         html.H1(children='Visualising the Ohio bank optimization problem'),
#         html.Div("Hover over a county to highlight its neighbours."),
        
#         html.Label('Choose a county labelling system to use:'),
#         dcc.RadioItems(
#             id="county_id_select",
#             options=["Official", "Camm18"],
#             value="Official",
#             inline=True,
#         ),
#         html.Br(),
        
#         html.Label("Highlight one of the 3 optimal solutions for Question 1:"),
#         dcc.RadioItems(
#             id="solution_select",
#             options=["sol1", "sol2", "sol3"],
#             value="sol1",
#             inline=True,
#         ),
#         html.Br(),
        
#         html.Div(children=[
#             html.P(id="solutions_name"),
#             html.P(id="solutions_county_id"),
#             html.P(id="solutions_camm_id"),
#         ]),
        
#         dcc.Graph(
#             id="choropleth",
#             responsive=True,
#             style={"width": "95vw", "height": "95vh"},
#             clear_on_unhover=True,
#         ),
#     ], style={'display': 'flex', 'flex-direction': 'column'}
# )

card_county = dbc.Card([
    dbc.Label("Choose a county labelling system to use:"),
    dbc.RadioItems(
        options=[
            {"label": "Government `county_id` numbering", "value": "Official"},
            {"label": "`county_id` indexing used in Camm18", "value": "Camm18"},
        ],
        value="Camm18",
        id="county_id_select",
        labelCheckedClassName="text-success",
        inputCheckedClassName="border border-success bg-success",
    ),
], body=True)

card_solution = dbc.Card([
    dbc.Label("Choose an optimal solution to highlight for Question 1:"),
    dbc.RadioItems(
        options=[
            {"label": "Solution 1", "value": "sol1"},
            {"label": "Solution 2", "value": "sol2"},
            {"label": "Solution 3", "value": "sol3"},
        ],
        value="sol1",
        id="solution_select",
        labelCheckedClassName="text-success",
        inputCheckedClassName="border border-success bg-success",
    ),
], body=True)

para_solutions = html.Div([
    html.P(id="solutions_name"),
    html.P(id="solutions_county_id"),
    html.P(id="solutions_camm_id"),
])

controls = dbc.Card(
    [
        dbc.Row(
        [
            dbc.Col(card_county, align="center"),
            dbc.Col(card_solution, align="center"),
            para_solutions,
        ],
       
        align="center"),
    ],
    body=True
)

app.layout = dbc.Container(
    [
        html.H1("Visualising the Ohio bank optimization problem"),
        html.Hr(),
        dbc.Row(
            [
                html.P("Hover over a county to highlight its neighbours."),
                dbc.Row(controls, align="center"),
                dbc.Row(
                    dcc.Graph(
                        id="choropleth",
                        responsive=True,
                        style={"width": "100vw", "height": "100vh"},
                        clear_on_unhover=True,
                        )),
            ],
            align="center",
        ),
    ],
    fluid=True, style={'display': 'flex', 'flex-direction': 'column'}
)

@app.callback(
    Output("choropleth", "figure"),
    Output("solutions_county_id", "children"),
    Output("solutions_camm_id", "children"),
    Output("solutions_name", "children"),
    Input("choropleth", "hoverData"),
    Input("county_id_select", "value"),
    Input("solution_select", "value"),
)
def display_figure(hoverData, county_id_select, solution_select):
    # get_solutions(df, solution_name)
    solution_name = "solution_main_model_" + solution_select + ".csv"
    solutions, solutions_county_id, solutions_camm_id = get_solutions(df, solution_name)
    set_solution_colors(solutions)

    fig = px.choropleth(
        geo_df,
        geojson=geo_df.geometry,
        color=geo_df.colors,
        hover_name=geo_df.NAME,
        locations=geo_df.index,
        labels={"neighbours": "adjacent_id"},
        color_discrete_map=custom_color_map,
        template="seaborn",
    )

    if county_id_select == "Camm18":
        combined_id = combined_id_camm
    else:
        combined_id = combined_id_official

    fig.add_trace(
        px.scatter_geo(
            geo_df, lat=geo_df.lat, lon=geo_df.lon, opacity=0, text=combined_id
        ).data[0]
    )

    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        uirevision="constant",
        showlegend=False,
        height=900,
        font_family="Open Sans",
    )

    hover = -1
    if hoverData is not None:
        hover = hoverData["points"][0]["location"]

    div_solutions_county_id = f"County IDs: {solutions_county_id}"
    div_solutions_camm_id = f"Camm IDs: {solutions_camm_id}"
    div_solutions_name = f"Highlighting solutions for {solution_name}:"

    # print(f"Selected: {hover}")
    return (
        get_figure(fig, hover),
        div_solutions_county_id,
        div_solutions_camm_id,
        div_solutions_name,
    )

if __name__ == '__main__':
# app.run_server(mode='inline', port=8088, debug=True)
    app.run_server(debug=True, port=8088)
