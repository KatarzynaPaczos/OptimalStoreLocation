from src.data_preprocessing import load_and_filter_data
from src.optimization import find_best_location
from src.visualization import generate_map

def main():
    # how many new locations to create
    n_locations = 10
    city = "Warszawa"
    print(f"I will look for {n_locations} new locations in {city} city.")
    housing, zabka_locations = load_and_filter_data(city)
    print("housing", housing.shape)

    # optimize for the best locations
    new_locations = find_best_location(
        housing=housing,
        store_locations=zabka_locations,
        n=n_locations, use_grid = True
    )

    for i, (lat, lon, score, _) in enumerate(new_locations, 1):
        print(f"Location {i}: ({lat}, {lon})  |  Score: {score}")

    # Visualize the result
    generate_map(housing, zabka_locations, new_locations)

if __name__ == "__main__":
    main()
