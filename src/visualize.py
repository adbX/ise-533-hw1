from urllib.request import urlopen
import json
import plotly.express as px
import geopandas as gpd
from pathlib import Path
import preprocess_data as ppd
import pandas as pd
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
from jupyter_dash import JupyterDash
import dash
from dash import html
from dash import dcc
import streamlit as st

data_path = Path("data/")
df, adjacent_matrix = ppd.get_df_adj(data_path, 2021)
geodata = gpd.read_file(data_path / "us_counties.geojson")
geodata.id = geodata.id.astype(str).astype(int)
geodata_ohio = geodata[geodata.id.isin(df.fips)]

geo_df = pd.merge(
    left=gpd.GeoDataFrame.from_features(geodata_ohio),
    right=df,
    left_on="id",
    right_on="fips",
).set_index("county_id")
geo_df["colors"] = 0

def get_neighbours(selection, geo_df=geo_df, adjacent_matrix=adjacent_matrix):
    if selection is None:
        return None
    else:
        selection_df = geo_df.loc[adjacent_matrix[selection]]
        selection_df["colors"] = 1
        selection_df.loc[selection, "colors"] = 3
        return selection_df


def get_figure(fig, hover):
    if hover != -1:
        highlights = get_neighbours(hover)
        
        print_hi = highlights["NAME"].values.tolist()
        print(f"Highlighting for {hover} : {print_hi}")

        fig.add_trace(
            px.choropleth(
                highlights,
                geojson=highlights.geometry,
                color=highlights.colors,
                hover_name=highlights.NAME,
                locations=highlights.index,
            ).data[0]
        )
    # fig.update_geos(fitbounds="locations", visible=False)
    # fig.update_layout(
    #     margin={"r": 0, "t": 0, "l": 0, "b": 0}, 
    #     uirevision="constant",
    #     showlegend=False
    # )
    return fig


app = dash.Dash(__name__)

app.layout = html.Div(
    [
        dcc.Graph(
            id="choropleth",
            responsive=True,
            style={'width': '95vw', 'height': '95vh'},
        )
    ]
)

@app.callback(Output("choropleth", "figure"),
              [Input("choropleth", "hoverData")])

def display_figure(hoverData):
    # geo_df["colors"] = 0
    # geo_df_json = geo_df.
    # geo_df_json = geo_df.to_json()
    
    fig = px.choropleth(
        geo_df,
        geojson=geo_df.geometry,
        color=geo_df.colors,
        hover_name=geo_df.NAME,
        locations=geo_df.index,
        labels={"neighbours": "adjacent_id"},
        template="seaborn",
    )
    
    # fig.add_scattergeo(
    #     geojson=geo_df_json,
    #     locations=geo_df.index,
    #     locationmode="geojson-id", 
    #     text=geo_df.NAME,
    #     mode='text',
    # )
    
    fig.update_geos(fitbounds="locations")
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

    # print(f"Selected: {hover}")
    return get_figure(fig, hover)

# app.run_server(mode='inline', port=8088, debug=True)
app.run_server(debug=True, port=8088)
