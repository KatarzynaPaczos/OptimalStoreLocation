from src.data_preprocessing import load_and_filter_data
#from src.optimization import find_best_location
from src.visualization import generate_map

def main():

    # how many new locations to create
    n_locations = 5
    city = "Warszawa"
    print(f"I will look for {n_locations} new locations in {city} city.")
    housing, zabka_locations = load_and_filter_data(city)
    print("housing", housing.head())
    print("zabka_locations", zabka_locations.head())

    generate_map(housing, zabka_locations, new_locations=[])

    '''
    # optimize for the best locations
    new_locations = find_best_location(
        housing=housing,
        zabka_locations=zabka_locations,
        n_locations=n_locations
    )
    
    for i, (lat, lon, score) in enumerate(new_locations, 1):
        print(f"Location {i}: ({lat:.6f}, {lon:.6f})  |  Score: {score:.2f}")

    # Visualize the result
    generate_map(housing, zabka_locations, new_locations)
    '''
if __name__ == "__main__":
    main()
