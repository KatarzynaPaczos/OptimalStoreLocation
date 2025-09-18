import requests
import pandas as pd
from pathlib import Path
from data.utils import clean_iqr

def run_etl_stores(city:str):
    bronze_stores(city)
    silver_stores(city)
    golden_stores(city)


def bronze_stores(city:str):
    print("Collecting the stores localisation data ...")
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
    out_path = Path("data/bronze") / f"{city.lower().replace(' ', '_')}_store_locations.parquet"
    df = pd.DataFrame(rows)
    df.to_parquet(out_path, index=False)


def silver_stores(city):
    path = f"data/bronze/{city.lower().replace(' ', '_')}_store_locations.parquet"
    df = pd.read_parquet(path)
    if not df.empty:
        df = df.dropna(subset=["lat", "lon"])
    df = clean_iqr(df)
    out_path = f"data/silver/{city.lower().replace(' ', '_')}_store_locations.parquet"
    df.to_parquet(out_path, index=False)


def golden_stores(city):
    path = f"data/silver/{city.lower().replace(' ', '_')}_store_locations.parquet"
    df = pd.read_parquet(path)
    out_path = f"data/golden/{city.lower().replace(' ', '_')}_store_locations.parquet"
    df.to_parquet(out_path, index=False)
    