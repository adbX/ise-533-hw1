import pandas as pd
from pathlib import Path
import pyomo.environ as pyo
from collections import defaultdict


def county_list_to_names(id_list: list, counties: pd.DataFrame) -> list:
    return counties[counties["county_id"].isin(id_list)]["county"].tolist()


def data_ingest(data_path: Path, year: int):
    fips_df = pd.read_csv(data_path / "oh-fips.csv")
    fips_df.astype({"fips": "int"})
    
    counties = pd.read_csv(data_path / "oh_county_list.csv")
    camm_id = pd.read_csv(data_path / "camm_county_mapping.csv")
    
    counties["county_id"] = pd.Series(range(1, 89))

    df_pop = pd.read_csv(data_path / f"oh_county_pop_{str(year)}.csv")
    df_pop.astype({"population": "int"})
    df = pd.merge(counties, df_pop, on="county")
    df = pd.merge(df, fips_df, on="county")
    df = pd.merge(df, camm_id, on="county_id")
    return df, counties

def county_ids_to_camm_ids(df: pd.DataFrame, counties: list) -> list:
    camm_list = df[df["county_id"].isin(counties)]["camm_id"].tolist()
    return sorted(camm_list)

def camm_ids_to_county_ids(df: pd.DataFrame, camm_ids: list) -> list:
    county_list = df[df["camm_id"].isin(camm_ids)]["county_id"].tolist()
    return sorted(county_list)

def create_adjacent_list(data_path: Path) -> list:
    with open(data_path / "oh_adjacent_loc_v2.dat", "r") as f:
        read_adjacent = f.readlines()

    adjacent_sublist = list(map(lambda x: x.strip("\n").split(","), read_adjacent))
    adjacent_list = [[int(x) for x in sublst] for sublst in adjacent_sublist]

    return adjacent_list

def gen_adjacent_matrix(df: pd.DataFrame, adjacent_list: list, camm: bool) -> dict:    
    adjacent_matrix = defaultdict(list)
    for i in range(1, 89):
        adjacent_list[i - 1].append(i)
        adjacent_matrix[i] = adjacent_list[i - 1]
        
    if camm==True:
        camm_matrix = defaultdict(list)
        camm_county_mapping = dict(zip(df.county_id, df.camm_id))
        for key, value in adjacent_matrix.items():
            # print(f"official: {key} -> camm: {camm_county_mapping[key]}")
            # print(f"official: {value} -> camm: {county_ids_to_camm_ids(df, value)}")
            camm_matrix[camm_county_mapping[key]] = county_ids_to_camm_ids(df, value)
        adjacent_matrix=camm_matrix

    return adjacent_matrix

def create_df(
    df: pd.DataFrame, counties: pd.DataFrame, adjacent_list: list
) -> pd.DataFrame:
    df = pd.concat([df, pd.Series(adjacent_list, name="adjacent_id")], axis=1)
    df["adjacent_names"] = df["adjacent_id"].apply(
        lambda x: county_list_to_names(x, counties)
    )

    return df

def get_df_adj(data_path: Path, year: int, camm=False):
    df_init, counties = data_ingest(data_path, year)
    adjacent_list = create_adjacent_list(data_path)
    adjacent_matrix = gen_adjacent_matrix(df_init, adjacent_list, camm=camm)
    df = create_df(df_init, counties, adjacent_list)
    return df, adjacent_matrix


if __name__ == "__main__":
    data_path = Path("data")
    year = 2021

    df_init, counties = data_ingest(data_path, year)
    adjacent_list = create_adjacent_list(data_path)
    adjacent_matrix = gen_adjacent_matrix(df_init, adjacent_list, camm=False)
    camm_matrix = gen_adjacent_matrix(df_init, adjacent_list, camm=True)

    # print()
    # print(camm_matrix)
    # print(adjacent_matrix)
