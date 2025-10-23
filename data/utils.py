import numpy as np
import pandas as pd
import time
import logging
import requests
from shapely.geometry import Polygon
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)
EARTH_RADIUS = 6371000 #in (m)

RESIDENTIAL_TYPES = ["house","detached", "semidetached_house",
                    "terrace", "bungalow", "apartments", "residential"]

DEFAULT_AREA = 25
DEFAULT_LEVELS = 2

MAX_RETRIES = 3
RETRY_DELAY = 5

def _latlon_to_xy(coords, ref_lat=None):
    """coords: list[(lon, lat)]
    ref_lat: latitude (deg) used for cos term; if None, uses mean lat of coords
    returns: Nx2 array of (x, y) in meters
    """
    coords = np.asarray(coords, dtype=float)
    lons, lats = coords[:, 0], coords[:, 1]

    if ref_lat is None:
        ref_lat = float(np.mean(lats))

    ref_lat_rad = np.radians(ref_lat)
    x = EARTH_RADIUS * np.radians(lons) * np.cos(ref_lat_rad)
    y = EARTH_RADIUS * np.radians(lats)
    return np.column_stack((x, y)) # how far eat-west (south-north) the point is in meters (from 0,0) point


def _xy_to_latlon(coords_xy, ref_lat = None):
    coords_xy = np.asarray(coords_xy, dtype=float)
    x, y = coords_xy[:, 0], coords_xy[:, 1]

    if ref_lat is None:
        lat_est = np.degrees(y / EARTH_RADIUS)
        ref_lat = float(np.mean(lat_est))

    ref_lat_rad = np.radians(ref_lat)
    lat = np.degrees(y / EARTH_RADIUS)
    lon = np.degrees(x / (EARTH_RADIUS * np.cos(ref_lat_rad)))
    return np.column_stack((lon, lat))


def calculate_area(coords: list):
    """coords: list of (lon, lat)
    returns: (area_m2, centroid_lonlat)
    """
    if len(coords) < 2:
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


def fetch_stores_data(city:str, country: str, store: str):
    query = f"""
    [out:json][timeout:60];
    area["name"="{country}"]["boundary"="administrative"]->.country;
    area["name"="{city}"]["boundary"="administrative"]->.searchArea;
    nwr["shop"="convenience"]["brand"~"{store}",i](area.searchArea);
    out center;
    """
    for attempt in range(1, 3):
        try:
            resp = requests.get("https://overpass-api.de/api/interpreter", params={'data': query}, timeout=120)
            resp.raise_for_status()
            logger.info("Connection to overpass-api - response status code: %d", resp.status_code)


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
            return pd.DataFrame(rows)
        except requests.exceptions.RequestException as e:
                logger.warning(f"Overpass attempt {attempt} failed: {e}")
                if attempt < 3:
                    time.sleep(10)
                else:
                    logger.error("Overpass API failed after 3 attempts.")
                    raise SystemExit


def load_housing_type(city: str, btype: str, country: str) -> pd.DataFrame:
    """Fetches buildings of type `btype` (e.g., "house" or "apartments") for a given city.
    Returns the centroid, approximate area in square meters, and related attributes.
    """
    query = f"""
    [out:json][timeout:300];
    area["name"="{country}"]["boundary"="administrative"]->.country;
    area["name"="{city}"]["boundary"="administrative"]->.searchArea;
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


def fetch_housing_data(city:str, country: str) -> pd.DataFrame:
    dfs = []
    for idx, btype in enumerate(RESIDENTIAL_TYPES, start=1):
        logger.info(f'Collecting housing type {btype} - {idx}/{len(RESIDENTIAL_TYPES)})')
        # Retry logic
        attempt = 1
        success = False
        while attempt <= MAX_RETRIES and not success:
            try:
                df_part = load_housing_type(city, btype, country)
                if df_part is not None and not df_part.empty:
                    dfs.append(df_part)
                    logger.info(f"Successfully fetched data for '{btype}' ({len(df_part)} rows)")
                else:
                    logger.warning(f"No data returned for '{btype}'")
                success = True

            except RequestException as e:
                logger.warning(f"Network error for '{btype}' (attempt {attempt}/{MAX_RETRIES}): {e}")
                attempt += 1
                if attempt <= MAX_RETRIES:
                    time.sleep(RETRY_DELAY)
            except Exception as e:
                logger.error(f"Failed to process '{btype}': {e}", exc_info=True)
                break  # no retry for logical errors
        time.sleep(2)

    if dfs:
        housing = pd.concat(dfs, axis=0, ignore_index=True).drop_duplicates(
            subset=["lon", "lat", "building_type"]
        )
        logger.info(f"Collected {len(housing)} total rows across {len(dfs)} building types.")
    else:
        logger.warning("No data collected for any building type.")
        housing = pd.DataFrame(columns=[
            "housenumber", "street", "levels", "area_m2",
            "lon", "lat", "building_type"
        ])
    return housing
