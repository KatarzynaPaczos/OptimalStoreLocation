# Code to visualize the results using folium
import folium
from src.utils import _xy_to_latlon

def show_candidates(candidates_xy, ref_lat=52.2297, city = "Warsaw"):
    # Center the map around the city
    candidated_latlon = _xy_to_latlon(candidates_xy, ref_lat=ref_lat)
    city_center = [52.2297, 21.0122]  # Coordinates for Warsaw
    m = folium.Map(location=city_center, zoom_start=12)
    # Add housing locations
    for row in candidated_latlon:
        folium.CircleMarker(location=row,
                            radius=1, color='blue', fill=True, fill_color='blue',
                            fill_opacity=0.6,
                            #popup=f"Type: {row['building_type']}, Area: {row['area_m2']:.1f} m², Residents: {row['residents']}"
                        ).add_to(m)
    m.save(f"{city}_candidated.html")
    print(f"Map saved to candid.html")


def generate_map(housing, zabka_locations, new_locations, city="Warszawa"):
    # Center the map around the city
    city_center = [52.2297, 21.0122]  # Coordinates for Warsaw
    m = folium.Map(location=city_center, zoom_start=12)

    # Add housing locations
    for _, row in housing.iterrows():
        folium.CircleMarker(location=[row['centroid_lat'], row['centroid_lon']],
                            radius=1, color='blue', fill=True, fill_color='blue',
                            fill_opacity=0.6,
                            popup=f"Type: {row['building_type']}, Area: {row['area_m2']:.1f} m², Residents: {row['residents']}"
                        ).add_to(m)

    # Add existing Żabka locations
    for _, row in zabka_locations.iterrows():
        folium.CircleMarker(location=[row['lat'], row['lon']], radius=1,
                            color="green", fill=True, fill_color="green",
                            fill_opacity=0.9, popup="Żabka Location"
                        ).add_to(m)
    # Add new proposed locations
    for lat, lon, score, rank in new_locations:
        folium.Marker(location=[lat, lon],
            icon=folium.Icon(color='red', icon='star', prefix='fa'),
            popup=f"Proposed Location - Score: {score} - rank {rank}"
        ).add_to(m)

    # Save the map to an HTML file
    m.save(f"{city}_zabka_map.html")
    print(f"Map saved to {city}_zabka_map.html")
