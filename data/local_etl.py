import logging
import pandas as pd
import numpy as np
from pathlib import Path
from data.utils import fetch_stores_data, fetch_housing_data
from data.utils import DEFAULT_LEVELS, DEFAULT_AREA

SQR_METER_PER_PERSON = 25
logger = logging.getLogger(__name__)

def run_etl_stores(city:str, country: str, store: str):
    bronze_stores(city, country, store)
    silver_stores(city)
    golden_stores(city)


def bronze_stores(city:str, country: str, store: str):
    out_path = Path("data/bronze") / f"{city.lower().replace(' ', '_')}_store_locations.parquet"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df = fetch_stores_data(city, country, store)
    df.to_parquet(out_path, index=False)


def silver_stores(city):
    path = f"data/bronze/{city.lower().replace(' ', '_')}_store_locations.parquet"
    df = pd.read_parquet(path)
    if not df.empty:
        df = df.dropna(subset=["lat", "lon"])
    df = clean_iqr(df)
    out_path = Path("data/silver") / f"{city.lower().replace(' ', '_')}_store_locations.parquet"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path, index=False)


def golden_stores(city):
    path = f"data/silver/{city.lower().replace(' ', '_')}_store_locations.parquet"
    df = pd.read_parquet(path)
    out_path = Path("data/golden")/f"{city.lower().replace(' ', '_')}_store_locations.parquet"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path, index=False)


def run_etl_housing(city:str, country: str):
    bronze_housing(city, country)
    silver_housing(city)
    golden_housing(city)


def bronze_housing(city:str, country: str):
    housing = fetch_housing_data(city, country)
    out_path = Path("data/bronze") / f"{city.lower().replace(' ', '_')}_housing.parquet"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    housing.to_parquet(out_path, index=False)
    logger.info(f"Saved housing data to {out_path}")


def silver_housing(city):
    path = f"data/bronze/{city.lower().replace(' ', '_')}_housing.parquet"
    df = pd.read_parquet(path)
    if not df.empty:
        df = df.dropna(subset=["lat", "lon"])
    df = clean_iqr(df)
    df["area_m2"] = df["area_m2"].fillna(DEFAULT_AREA)
    df.loc[df["area_m2"] == 0, "area_m2"] = DEFAULT_AREA
    df["area_m2"] = df["area_m2"].astype(float)
    df["levels"] = pd.to_numeric(df["levels"], errors="coerce")
    df["levels"] = df["levels"].fillna(DEFAULT_LEVELS)
    df.loc[df["levels"] == 0, "levels"] = DEFAULT_LEVELS
    df["levels"] = df["levels"].astype(float)
    out_path = f"data/silver/{city.lower().replace(' ', '_')}_housing.parquet"
    df.to_parquet(out_path, index=False)


def golden_housing(city):
    path = f"data/silver/{city.lower().replace(' ', '_')}_housing.parquet"
    df = pd.read_parquet(path)
    df = number_of_residents(df)
    out_path = f"data/golden/{city.lower().replace(' ', '_')}_housing.parquet"
    df.to_parquet(out_path, index=False)


def number_of_residents(housing: pd.DataFrame) -> pd.DataFrame:
    housing.loc[:, "residents"] = housing.levels * np.ceil(housing.area_m2 / SQR_METER_PER_PERSON)
    housing.loc[:, "residents"] = housing["residents"].fillna(3)
    return housing


def iqr_bounds(series, factor = 3):
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            lower = q1 - factor * iqr
            upper = q3 + factor * iqr
            return lower, upper


def clean_iqr(df, cols=["lat", "lon"], factor=3):
    mask = np.ones(len(df), dtype=bool)
    for col in cols:
        lower, upper = iqr_bounds(df[col], factor=factor)
        mask &= (df[col] >= lower) & (df[col] <= upper)

    cleaned = df.loc[mask].reset_index(drop=True)
    removed = len(df) - len(cleaned)
    logger.info(f"Removed {removed} outliers out of {len(df)} rows "
          f"({removed/len(df)*100:.2f}%).")
    return cleaned
