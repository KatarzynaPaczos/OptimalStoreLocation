import logging
import pandas as pd
from pathlib import Path
from data.etl_housing import run_etl_housing
from data.etl_stores import run_etl_stores
DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
logger = logging.getLogger(__name__)

def city_slug(city: str) -> str:
    return city.lower().replace(" ", "_")


def parquet_path(city: str, kind: str) -> Path:
    return DATA_DIR / f"golden/{city_slug(city)}_{kind}.parquet"


def load_dataframe(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path)


def load_stores_data(city: str, country: str, store: str) -> pd.DataFrame:
    out_path = parquet_path(city, "store_locations")
    logger.info(f"Loading store data from {out_path}")
    if out_path.exists():
        logger.info(f"{out_path} already exists. Loading cached data.")
        return load_dataframe(out_path)
    else:
        logger.info(f"{out_path} not found. Running ETL for {store} in {city}, {country}.")
        run_etl_stores(city, country, store)
        return load_dataframe(out_path)


def load_housing_data(city: str, country: str) -> pd.DataFrame:
    out_path = parquet_path(city, "housing")
    if out_path.exists():
        logger.info(f"{out_path} already exists. Loading cached data.")
        return load_dataframe(out_path)
    else:
        logger.info(f"{out_path} not found. Running ETL for housing in {city}, {country}.")
        run_etl_housing(city, country)
        return load_dataframe(out_path)
    

def load_and_filter_data(city: str = "Warszawa", country: str = "Polska", store = "Żabka"):
    store_locations = load_stores_data(city, country, store)
    housing = load_housing_data(city, country)
    return housing, store_locations
