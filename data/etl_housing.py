import pandas as pd
import numpy as np
import requests
from pathlib import Path
import time
from data.utils import clean_iqr, calculate_area

RESIDENTIAL_TYPES = ["house","detached", "semidetached_house",
                    "terrace", "bungalow", "apartments", "residential"]
SQR_METER_PER_PERSON = 25
DEFAULT_AREA = 25
DEFAULT_LEVELS = 2

def run_etl_housing(city:str):
    bronze_housing(city)
    silver_housing(city)
    golden_housing(city)


def bronze_housing(city:str):
    print("Collecting the data ...")
    dfs = []
    for idx, btype in enumerate(RESIDENTIAL_TYPES):
        print(f'Collecting houing type {btype} - {idx+1}/{len(RESIDENTIAL_TYPES)})')
        try:
            df_part = load_housing_type(city, btype)
            if not df_part.empty:
                dfs.append(df_part)
        except Exception as e:
            print(f"[warn] failed for building={btype}: {e}")
        time.sleep(10)

    if dfs:
        housing = pd.concat(dfs, axis=0, ignore_index=True)
        housing.drop_duplicates(
            subset=["lon", "lat", "building_type"],
            inplace=True
        )
    else:
        housing = pd.DataFrame(columns=[
            "housenumber","street","levels","area_m2",
            "lon","lat","building_type"
        ])
    out_path = Path("data/bronze") / f"{city.lower().replace(' ', '_')}_housing.parquet"
    housing.to_parquet(out_path, index=False)


def load_housing_type(city: str, btype: str) -> pd.DataFrame:
    """
    Fetches buildings of type `btype` (e.g., "house" or "apartments") for a given city.
    Returns the centroid, approximate area in square meters, and related attributes.
    """
    query = f"""
    [out:json][timeout:240];
    area["name"="{city}"]->.searchArea;
    (
      way["building"="{btype}"](area.searchArea);
    );
    out body;
    >;
    out skel qt;
    """
    resp = requests.get("https://overpass-api.de/api/interpreter", params={'data': query})
    resp.raise_for_status()
    data = resp.json()

    rows = []
    nodes = {}
    for element in data.get("elements", []):
        if element.get("type") == "node":
            nodes[element["id"]] = (element["lon"], element["lat"])

    for element in data.get("elements", []):
        if element.get("type") == "way":
            tags = element.get("tags", {})
            try:
                coords = [nodes[node_id] for node_id in element.get("nodes", [])]
            except KeyError:
                continue
            if len(coords) < 2:
                continue
            
            area_m2, centroid = calculate_area(coords)
            if centroid is not None:
                centroid_lon, centroid_lat = centroid.x, centroid.y
            else:
                centroid_lon, centroid_lat = None, None

            rows.append({
                "housenumber": tags.get("addr:housenumber"),
                "street": tags.get("addr:street"),
                "levels": tags.get("building:levels"),
                "area_m2": area_m2,
                "lon": centroid_lon,
                "lat": centroid_lat,
                "building_type": btype,
            })
    return pd.DataFrame(rows)


def number_of_residents(housing: pd.DataFrame) -> pd.DataFrame:
    housing.loc[:, "residents"] = housing.levels * np.ceil(housing.area_m2 / SQR_METER_PER_PERSON)
    housing.residents.fillna(3, inplace=True)
    return housing


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
