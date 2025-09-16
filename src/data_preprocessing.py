
import requests
import pandas as pd
import numpy as np
from shapely.geometry import Polygon
from pathlib import Path

DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
RESIDENTIAL_TYPES = ["house",
                    "detached",
                    "semidetached_house",
                    "terrace",
                    "bungalow",
                    "apartments",
                    "residential"]

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
            centroid_lon, centroid_lat = centroid.x, centroid.y

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


def calculate_area(coords: list): 
    polygon = Polygon(coords)
    # Calculate area in square meters (approximate, assuming coords are lon/lat)
    # Convert degrees to meters using approximate conversion at Warsaw's latitude
    # 1 degree lat ~ 111 km, 1 degree lon ~ 111 km * cos(latitude)
    lat_mean = sum([lat for lon, lat in coords]) / len(coords)
    meter_per_degree_lat = 111000  # meters per degree latitude
    meter_per_degree_lon = 111000 * abs(np.cos(np.radians(lat_mean)))  # meters per degree longitude
    
    projected_coords = [
        ((lon * meter_per_degree_lon), (lat * meter_per_degree_lat))
        for lon, lat in coords
    ]
    projected_polygon = Polygon(projected_coords)
    return projected_polygon.area, polygon.centroid


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
    return housing, zabka_locations