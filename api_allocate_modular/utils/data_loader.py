import os
import gspread
import pandas as pd
from copy import deepcopy
from dotenv import load_dotenv
from collections import defaultdict
from oauth2client.service_account import ServiceAccountCredentials

from utils.constants import (
    NAME_COLUMN, PICKUP_COLUMN, SERVICE_TYPE_COLUMN, AFTER_SERVICE_PLANS_COLUMN,
    IS_DRIVER_COLUMN, OC_ADDRESS, location_to_address,
    PASSENGER_LIMIT, rider_groups_to, rider_groups_back,
    driver_required_riders_to, driver_required_riders_back,
    CHURCH_LOCATION, GOOGLE_SHEETS_TAB, GOOGLE_SHEETS_LINK
)
from utils.geo_utils import geocode_address, address_coords, oc_people_w_invalid_address
from utils.assignment_logic import (
    assign_whitelisted_groups,
    assign_riders_by_furthest_first,
    assign_from_church,
    assign_flexible_plans_first
)

class Driver:
    def __init__(self, name, amount_seats, pickup_location, service_type, plans, address):
        self.name = name
        self.amount_seats = amount_seats
        self.pickup_location = pickup_location
        self.service_type = service_type
        self.plans = plans
        self.long_lat_pair = ()
        self.address = address

    def __hash__(self): return hash(self.name)
    def __eq__(self, other): return isinstance(other, Driver) and self.name == other.name

class Rider:
    def __init__(self, name, pickup_location, service_type, plans, address):
        self.name = name
        self.pickup_location = pickup_location
        self.service_type = service_type
        self.plans = plans
        self.long_lat_pair = ()
        self.address = address

    def __hash__(self): return hash(self.name)
    def __eq__(self, other): return isinstance(other, Rider) and self.name == other.name


class DataLoader:
    def __init__(self):
        load_dotenv(override=True)
        self.JSON_KEY_PATH = os.getenv("JSON_KEY_PATH")
        self.link_to_sheet = GOOGLE_SHEETS_LINK
        self.sheet_name = GOOGLE_SHEETS_TAB

    def load_data(self):
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            self.JSON_KEY_PATH,
            scopes=["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        )
        client = gspread.authorize(creds)
        sheet = client.open_by_url(self.link_to_sheet)
        worksheet = sheet.worksheet(self.sheet_name)

        values = worksheet.get_all_values()
        df = pd.DataFrame(values[1:], columns=values[0])

        formatted = self._format_assignments(df)
        formatted["formatted_time"] = pd.Timestamp.now().strftime("%Y-%m-%d_%H-%M")
        return formatted

    def _format_assignments(self, df):
        drivers, riders = set(), set()

        for i in range(len(df)):
            name = df[NAME_COLUMN][i].strip()
            pickup_location = df[PICKUP_COLUMN][i].strip()
            service_type = df[SERVICE_TYPE_COLUMN][i].strip()
            plans = df[AFTER_SERVICE_PLANS_COLUMN][i].strip()
            is_driver_val = df[IS_DRIVER_COLUMN][i].strip()
            oc_address = df[OC_ADDRESS][i].strip()

            if not name or not service_type:
                continue

            if pickup_location not in location_to_address and (not oc_address):
                rider = Rider(name, pickup_location, service_type, plans, None)
                oc_people_w_invalid_address.add(rider)
                continue

            address = location_to_address.get(pickup_location, oc_address)
            coord = address_coords.get(address) or geocode_address(address)

            if isinstance(coord, Exception):
                (oc_people_w_invalid_address.add(Rider(name, pickup_location, service_type, plans, address))
                 if not is_driver_val else
                 oc_people_w_invalid_address.add(Driver(name, PASSENGER_LIMIT, pickup_location, service_type, plans, address)))
                continue
            
            if is_driver_val.strip() != "":
                driver = Driver(name, PASSENGER_LIMIT, pickup_location, service_type, plans, address)
                driver.long_lat_pair = coord
                drivers.add(driver)
            else:
                rider = Rider(name, pickup_location, service_type, plans, address)
                rider.long_lat_pair = coord
                riders.add(rider)

        print(f"People with invalid addresses: {[p.name for p in oc_people_w_invalid_address]}")
        print(f"Geocoded addresses: {address_coords}")

        drivers_back_raw = deepcopy(list(drivers))
        riders_back_raw = deepcopy(list(riders))

        updated_riders, unassigned_flexible_riders, updated_drivers, _ = assign_flexible_plans_first(
            drivers_back_raw, riders_back_raw
        )

        drivers_back = updated_drivers
        riders_back = updated_riders

        # TO church
        assignments_to, remaining_drivers_to, remaining_riders_to = assign_whitelisted_groups(
            drivers, riders, driver_required_riders_to, rider_groups_to)
        assignments_to, unassigned_riders_to = assign_riders_by_furthest_first(
            remaining_drivers_to, remaining_riders_to, CHURCH_LOCATION, assignments=assignments_to)

        # FROM church
        assignments_back, remaining_drivers_back, remaining_riders_back = assign_whitelisted_groups(
            drivers_back, riders_back, driver_required_riders_back, rider_groups_back
        )
        assignments_back, unassigned_riders_back = assign_from_church(
            remaining_drivers_back, remaining_riders_back,CHURCH_LOCATION, assignments=assignments_back
        )
        return {
            "assignments_to": dict(assignments_to),
            "assignments_back": dict(assignments_back),
            "unassigned_riders_to": list(unassigned_riders_to),
            "unassigned_riders_back": list(unassigned_riders_back),
            "address_coords": dict(address_coords),
            "oc_people_w_invalid_address": list(oc_people_w_invalid_address)
        }
