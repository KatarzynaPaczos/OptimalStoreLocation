
import requests
import pandas as pd
import numpy as np
from shapely.geometry import Polygon
from pathlib import Path
from src.utils import _latlon_to_xy, clean_iqr

DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
RESIDENTIAL_TYPES = ["house",
                    "detached",
                    "semidetached_house",
                    "terrace",
                    "bungalow",
                    "apartments",
                    "residential"]
SQR_METER_PER_PERSON = 25

def city_slug(city: str) -> str:
    return city.lower().replace(" ", "_")


def csv_path(city: str, kind: str) -> Path:
    # kind: "zabka_loationc" or "housing"
    return DATA_DIR / f"{city_slug(city)}_{kind}.csv"


def save_dataframe(df: pd.DataFrame, path_or_name):
    if isinstance(path_or_name, (str, Path)):
        path = Path(path_or_name)
        if path.suffix == "":
            path = DATA_DIR / f"{path}.csv"
    else:
        raise ValueError("save_dataframe: path_or_name must be str or Path")
    df.to_csv(path, index=False)


def load_dataframe(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def load_zabka_data(city: str = "Warszawa") -> pd.DataFrame:
    out_path = csv_path(city, "zabka_locations")
    if out_path.exists():
        print(f"{out_path} already exist")
        return load_dataframe(out_path)
    print("Collecting the data ...")
    query = f"""
    [out:json][timeout:60];
    area["name"="Polska"]["boundary"="administrative"]->.country;
    area["name"="{city}"]["boundary"="administrative"]->.searchArea;
    nwr["shop"="convenience"]["brand"~"Żabka",i](area.searchArea);
    out center;
    """
    resp = requests.get("https://overpass-api.de/api/interpreter", params={'data': query})
    resp.raise_for_status()
    data = resp.json()
    rows = []
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        # some 'way/rel' dont have lat/lon, byt has center.{lat,lon}
        lat = el.get("lat") or (el.get("center") or {}).get("lat")
        lon = el.get("lon") or (el.get("center") or {}).get("lon")
        rows.append({
            "name": tags.get("name"),
            "lat": lat,
            "lon": lon,
            "housenumber": tags.get("addr:housenumber"),
            "street": tags.get("addr:street"),
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        df.dropna(subset=["lat", "lon"], inplace=True)

    save_dataframe(df, out_path)
    return df


def calculate_area(coords: list):
    """
    coords: list of (lon, lat)
    returns: (area_m2, centroid_lonlat)
    """
    if len(coords) < 3:
        return 0.0, None

    # centroid in lon/lat from the original geometry
    lonlat_poly = Polygon(coords)
    centroid = lonlat_poly.centroid  # lon/lat centroid

    # project to planar meters using equirectangular approximation
    ref_lat = float(np.mean([lat for _, lat in coords]))
    xy = _latlon_to_xy(coords, ref_lat=ref_lat)
    proj_poly = Polygon(xy)

    area_m2 = float(proj_poly.area)
    return area_m2, centroid


def load_housing_type(city: str, btype: str) -> pd.DataFrame:
    """
    Fetches buildings of type `btype` (e.g., "house" or "apartments") for a given city.
    Returns the centroid, approximate area in square meters, and related attributes.
    """
    query = f"""
    [out:json][timeout:60];
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
                # brak węzła -> pomiń
                continue
            if len(coords) < 3:
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
                "centroid_lon": centroid_lon,
                "centroid_lat": centroid_lat,
                "building_type": btype,
            })
    return pd.DataFrame(rows)


def load_housing_data(city: str = "Warszawa") -> pd.DataFrame:
    out_path = csv_path(city, "housing")
    if out_path.exists():
        print(f"{out_path} already exist")
        return load_dataframe(out_path)
    
    print("Collecting the data ...")
    dfs = []
    for btype in RESIDENTIAL_TYPES:
        try:
            df_part = load_housing_type(city, btype)
            if not df_part.empty:
                dfs.append(df_part)
        except Exception as e:
            print(f"[warn] failed for building={btype}: {e}")

    if dfs:
        housing = pd.concat(dfs, axis=0, ignore_index=True)
        housing.drop_duplicates(
            subset=["centroid_lon", "centroid_lat", "building_type"],
            inplace=True
        )
    else:
        housing = pd.DataFrame(columns=[
            "housenumber","street","levels","area_m2",
            "centroid_lon","centroid_lat","building_type"
        ])

    save_dataframe(housing, out_path)
    return housing


def load_and_filter_data(city: str = "Warszawa"):
    zabka_locations = load_zabka_data(city)
    housing = load_housing_data(city)
    housing = number_of_habitants(housing)
    housing = clean_iqr(housing, cols=["centroid_lat", "centroid_lon"], factor=1.5)
    print("Number of nans, to correct", housing.residents.isna().sum())
    print("Number of nans, to correct", housing.levels.isna().sum())
    print("Number of nans, to correct", housing.area_m2.isna().sum())
    print("Number of nans, to correct", housing.centroid_lat.isna().sum())
    print("Number of nans, to correct", zabka_locations.lat.isna().sum())
    return housing, zabka_locations


def number_of_habitants(housing: pd.DataFrame) -> pd.DataFrame:
    housing.loc[:, "residents"] = housing.levels * np.ceil(housing.area_m2 / SQR_METER_PER_PERSON)
    housing.residents.fillna(3, inplace=True)
    print("New file needed for the proper data handling - ETL and outliers")
    return housing
