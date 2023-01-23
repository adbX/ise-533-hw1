import plotly.express as px
import geopandas as gpd
from pathlib import Path
import preprocess_data as ppd
import pandas as pd
import dash
from dash.dependencies import Input, Output
from dash import html
from dash import dcc

data_path = Path("data/")
output_path = Path("output/")
solution_name = "solution_model_1_static.csv"

df, adjacent_matrix = ppd.get_df_adj(data_path, 2021)

geodata = gpd.read_file(data_path / "us_counties.geojson")
geodata.id = geodata.id.astype(str).astype(int)
geodata_ohio = geodata[geodata.id.isin(df.fips)]

color_blank = px.colors.qualitative.Pastel[1]
color_neighbour = px.colors.qualitative.Pastel[0]
color_selected = px.colors.qualitative.Pastel[2]
color_solution = px.colors.qualitative.Pastel[3]
custom_color_map = {
    'blank': color_blank,
    'neighbour': color_neighbour,
    'selected': color_selected,
    'solution': color_solution
}

geo_df = pd.merge(
    left=gpd.GeoDataFrame.from_features(geodata_ohio),
    right=df,
    left_on="id",
    right_on="fips",
).set_index("county_id").assign(lat=lambda d: d.geometry.centroid.y, lon=lambda d: d.geometry.centroid.x)

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
                color_discrete_map=custom_color_map
            ).data[0]
        )
    return fig

app = dash.Dash(__name__)

app.layout = html.Div(
    [
        html.P("Source of county_id label:"),
        dcc.RadioItems(
            id='county_id_select', 
            options=["Official", "Camm18"],
            value="Official",
            inline=True
        ),
        html.P(f"Highlighting solutions for {solution_name}:"),
        html.P(id='solutions_county_id'),
        html.P(id='solutions_camm_id'),
        dcc.Graph(
            id="choropleth",
            responsive=True,
            style={'width': '95vw', 'height': '95vh'},
            clear_on_unhover=True,
        )
    ]
)

@app.callback(Output("choropleth", "figure"),
              Output("solutions_county_id", "children"),
              Output("solutions_camm_id", "children"),
              Input("choropleth", "hoverData"),
              Input("county_id_select", "value"))

def display_figure(hoverData, county_id_select):
    # get_solutions(df, solution_name)
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
        
    fig.add_trace(px.scatter_geo(geo_df,
                    lat=geo_df.lat,
                    lon=geo_df.lon,
                    opacity=0,
                    text=combined_id).data[0])
    
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0}, 
        uirevision="constant",
        showlegend=False,
        height=900,
        title_font_family="Open Sans"
    )

    hover = -1
    if hoverData is not None:
        hover = hoverData["points"][0]["location"]

    div_solutions_county_id = f"County IDs: {solutions_county_id}"
    div_solutions_camm_id = f"Camm IDs: {solutions_camm_id}"

    # print(f"Selected: {hover}")
    return get_figure(fig, hover), div_solutions_county_id, div_solutions_camm_id

# app.run_server(mode='inline', port=8088, debug=True)
app.run_server(debug=True, port=8088)
