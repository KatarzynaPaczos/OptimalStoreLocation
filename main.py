import logging
from data.data_preprocessing import load_and_filter_data
from src.optimization import find_best_location
from src.visualization import generate_map

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    #handlers=[
    #    logging.FileHandler("etl.log"), #logi zapisuja się na ekranie
    #    logging.StreamHandler()
    #]
)
logger = logging.getLogger(__name__)

def main():
    # how many new locations to create
    n_locations = 10
    city = "Warszawa"
    country = "Poland"
    store = "Żabka"
    logger.info("Searching for %d new %s store locations in %s, %s.", n_locations, store, city, country)
    
    housing, zabka_locations = load_and_filter_data(city, country, store)
    new_locations = find_best_location(
        housing=housing,
        store_locations=zabka_locations,
        n=n_locations, use_grid=True
    )

    for i, (lat, lon, cust_prox, store_prox, ratio, score, _) in enumerate(new_locations, 1):
        logger.info(f"Location {i}: ({lat:.5f}, {lon:.5f}) | Score: {cust_prox:.2f}, {store_prox:.2f}, {ratio:.2f}, {score:.2f}")
    generate_map(housing, zabka_locations, new_locations)


if __name__ == "__main__":
    main()
