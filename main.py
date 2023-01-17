import pandas as pd
from pathlib import Path
import pyomo.environ as pyo
from collections import defaultdict


def county_list_to_names(id_list: list, counties: pd.DataFrame) -> list:
    return counties[counties["county_id"].isin(id_list)]["county"].tolist()


def gen_adj_matrix(adj_list: list) -> dict:
    adj_matrix = defaultdict(list)
    for i in range(1, 89):
        adj_matrix[i] = adj_list[i - 1]
    return adj_matrix


def data_ingest(data_path: Path, year: int):
    counties = pd.read_csv(data_path / "oh_county_list.csv")
    counties["county_id"] = pd.Series(range(1, 89))

    df_pop = pd.read_csv(data_path / f"oh_county_pop_{str(year)}.csv")
    df = pd.merge(counties, df_pop, on="county")

    return df, counties


def create_adj_list(data_path: Path) -> list:
    with open(data_path / "oh_adj_loc.dat", "r") as f:
        read_adj = f.readlines()

    adj_sublist = list(map(lambda x: x.strip("\n").split(","), read_adj))
    adj_list = [[int(x) for x in sublst] for sublst in adj_sublist]

    return adj_list


def create_df(df: pd.DataFrame, counties: pd.DataFrame, adj_list: list) -> pd.DataFrame:
    df = pd.concat([df, pd.Series(adj_list, name="adj_id")], axis=1)
    df["adj_names"] = df["adj_id"].apply(lambda x: county_list_to_names(x, counties))

    return df


if __name__ == "__main__":
    data_path = Path("data")
    year = 2021

    adj_list = create_adj_list(data_path)
    adj_matrix = gen_adj_matrix(adj_list)
    df_init, counties = data_ingest(data_path, year)
    df = create_df(df_init, counties, adj_list)

    print(adj_matrix)
    print(df.head())
