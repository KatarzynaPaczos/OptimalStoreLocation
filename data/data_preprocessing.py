import pandas as pd
import numpy as np
from pathlib import Path
from data.etl_housing import run_etl_housing
from data.etl_stores import run_etl_stores
DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)


def city_slug(city: str) -> str:
    return city.lower().replace(" ", "_")


def parquet_path(city: str, kind: str) -> Path:
    return DATA_DIR / f"golden/{city_slug(city)}_{kind}.parquet"


def load_dataframe(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path)


def load_zabka_data(city: str = "Warszawa") -> pd.DataFrame:
    out_path = parquet_path(city, "store_locations")
    if out_path.exists():
        print(f"{out_path} already exist")
        return load_dataframe(out_path)
    else: 
        run_etl_stores(city)
        return load_dataframe(out_path)


def load_housing_data(city: str = "Warszawa") -> pd.DataFrame:
    out_path = parquet_path(city, "housing")
    if out_path.exists():
        print(f"{out_path} already exist")
        return load_dataframe(out_path)
    else: 
        run_etl_housing(city)
        return load_dataframe(out_path)
    

def load_and_filter_data(city: str = "Warszawa"):
    zabka_locations = load_zabka_data(city)
    print("store_locations", zabka_locations.shape)
    housing = load_housing_data(city)
    print("housing", housing.shape)
    return housing, zabka_locations
