# Smart Store Location

This project looks for the best new locations for Żabka stores by checking where people live and where stores already exist. Żabka is a small local grocery chain in Poland, popular because the shops are close to people and open for long hours.

Since there are already many stores and many people, the aim is to find places where a new Żabka would be most useful, giving residents easy access without putting shops too close to each other.

## What data do we use?

OpenStreetMap (OSM) via Overpass API – to fetch:
* existing Żabka store locations,
* residential buildings (e.g., building=house, building=apartments) for simple housing density proxies.