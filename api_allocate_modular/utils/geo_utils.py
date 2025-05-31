from geopy.distance import geodesic
from geopy.geocoders import GoogleV3
import os

# Caching
coords_to_dist = dict()
address_coords = {}
oc_people_w_invalid_address = set()

# Load API key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
geolocator = GoogleV3(api_key=GOOGLE_API_KEY)

def dist(coord1, coord2):
    if (coord1, coord2) in coords_to_dist:
        return coords_to_dist[(coord1, coord2)]
    if (coord2, coord1) in coords_to_dist:
        return coords_to_dist[(coord2, coord1)]

    miles = geodesic(coord1, coord2).miles
    coords_to_dist[(coord1, coord2)] = miles
    coords_to_dist[(coord2, coord1)] = miles
    return miles

def route_cost(start, waypoints, destination):
    total = 0
    curr = start
    for wp in waypoints:
        total += dist(curr, wp.long_lat_pair)
        curr = wp.long_lat_pair
    total += dist(curr, destination)
    return total

def geocode_address(address):
    if address in address_coords:
        return address_coords[address]

    try:
        full_address = address if "houston" in address.lower() else f"{address}, Houston, USA"
        location = geolocator.geocode(full_address, region="us", timeout=5)
        if location:
            coord = (location.latitude, location.longitude)
            address_coords[address] = coord
            return coord
    except Exception as e:
        print(f"[Geocoder] Failed to geocode {address}: {e}")
        return e
    return None
