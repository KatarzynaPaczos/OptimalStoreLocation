from data.data_preprocessing import load_and_filter_data
from src.optimization import find_best_location
from src.visualization import generate_map

def main():
    # how many new locations to create
    n_locations = 10
    city = "Warszawa"
    print(f"I will look for {n_locations} new locations in {city} city.")
    housing, zabka_locations = load_and_filter_data(city)
    # optimize for the best locations
    '''
    new_locations = find_best_location(
        housing=housing,
        store_locations=zabka_locations,
        n=n_locations, use_grid = True
    )

    for i, (lat, lon, cust_prox, store_prox, ratio, score, idx) in enumerate(new_locations, 1):
        print(f"Location {i}: ({lat}, {lon})  |  Score: {cust_prox:.2f}, {store_prox:.2f}, {ratio:.2f}, {score:.2f}")

    # Visualize the result
    generate_map(housing, zabka_locations, new_locations)
    '''
if __name__ == "__main__":
    main()
