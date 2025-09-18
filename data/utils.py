import numpy as np
from shapely.geometry import Polygon
EARTH_RADIUS = 6371000 #in (m)

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
    print(f"Removed {removed} outliers out of {len(df)} rows "
          f"({removed/len(df)*100:.2f}%).")
    return cleaned


def calculate_area(coords: list):
    """
    coords: list of (lon, lat)
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


def _latlon_to_xy(coords, ref_lat=None):
    """
    coords: list[(lon, lat)]
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
