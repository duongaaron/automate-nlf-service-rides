import os
import gspread
import pandas as pd
from copy import deepcopy
from dotenv import load_dotenv
from collections import defaultdict
from oauth2client.service_account import ServiceAccountCredentials

from utils.constants import (
    NAME_COLUMN, PICKUP_COLUMN, SERVICE_TYPE_COLUMN, AFTER_SERVICE_PLANS_COLUMN,
    IS_DRIVER_COLUMN, OC_ADDRESS, location_to_address, RIDE_TO_COLUMN,
    PASSENGER_LIMIT, rider_groups_to, rider_groups_back,
    driver_required_riders_to, driver_required_riders_back,
    CHURCH_LOCATION, EVENT_TYPES, USE_RIDE_SELECTION_FORM_QUESTION,
    GOOGLE_SHEETS_LINK, GOOGLE_SHEETS_TAB
)
from utils.geo_utils import geocode_address, address_coords, oc_people_w_invalid_address, merge_nearby_coords
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
        self.ride_types = set()

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
        self.ride_types = set()

    def __hash__(self): return hash(self.name)
    def __eq__(self, other): return isinstance(other, Rider) and self.name == other.name

class DataLoader:
    def __init__(self):
        load_dotenv(override=True)
        self.JSON_KEY_PATH = os.getenv("JSON_KEY_PATH")
        self.link_to_sheet = GOOGLE_SHEETS_LINK
        self.sheet_name = GOOGLE_SHEETS_TAB
        if not self.link_to_sheet:
            raise ValueError("GOOGLE_SHEET_LINK not set. Make sure .env is loaded and contains the correct key.")

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
        oc_people_w_invalid_address.clear()
        address_coords.clear()
        drivers, riders = set(), set()

        for i in range(len(df)):
            name = df.at[i, NAME_COLUMN].strip()
            pickup_location = df.at[i, PICKUP_COLUMN].strip()
            service_type = df.at[i, SERVICE_TYPE_COLUMN].strip()
            plans = df.at[i, AFTER_SERVICE_PLANS_COLUMN].strip()
            is_driver_val = df.at[i, IS_DRIVER_COLUMN].strip().lower() in {"yes", "yes!"}
            oc_address = df.at[i, OC_ADDRESS].strip()

            normalized_ride_types = set()

            if USE_RIDE_SELECTION_FORM_QUESTION:
                ride_selection_raw = df.at[i, RIDE_TO_COLUMN].strip().lower()
                ride_selection = {s.strip() for s in ride_selection_raw.split(",")}

                normalized_ride_types = set()
                for key, meta in EVENT_TYPES.items():
                    if any(sel in meta["form_matches"] for sel in ride_selection):
                        normalized_ride_types.add(key)

                # fallback
                if not normalized_ride_types:
                    normalized_ride_types = {"church"}

                print(f"{name=}, {ride_selection_raw=}, {ride_selection=}, {service_type=}")
                

            if not name or not service_type:
                continue

            if pickup_location not in location_to_address and not oc_address:
                rider = Rider(name, pickup_location, service_type, plans, None)
                rider.ride_types = normalized_ride_types
                oc_people_w_invalid_address.add(rider)
                continue

            address = location_to_address.get(pickup_location, oc_address)
            coord = address_coords.get(address) or geocode_address(address)
            print(f"Assigned ride types to {name}: {normalized_ride_types}")
            if isinstance(coord, Exception):
                entity = Rider if not is_driver_val else Driver
                person = entity(name, PASSENGER_LIMIT, pickup_location, service_type, plans, address)
                person.ride_types = normalized_ride_types
                oc_people_w_invalid_address.add(person)
                continue

            print(f">>> is_driver_val={is_driver_val}, {name=}, ride_types={normalized_ride_types}")

            if is_driver_val:
                driver = Driver(name, PASSENGER_LIMIT, pickup_location, service_type, plans, address)
                driver.long_lat_pair = coord
                driver.ride_types = normalized_ride_types
                drivers.add(driver)
            else:
                rider = Rider(name, pickup_location, service_type, plans, address)
                rider.long_lat_pair = coord
                rider.ride_types = normalized_ride_types
                riders.add(rider)

        print(f"People with invalid addresses: {[p.name for p in oc_people_w_invalid_address]}")
        print(f"Geocoded addresses: {address_coords}")
        event_data = {}
        for event_key, config in EVENT_TYPES.items():
            if event_key == "hc":
                riders_event = {r for r in riders if event_key in r.ride_types}
                drivers_event = {d for d in drivers if event_key in d.ride_types}
            else:
                riders_event = {
                    r for r in riders
                    if event_key in r.ride_types and any(m.lower() in r.service_type.lower() for m in config["matches"])
                }
                drivers_event = {
                    d for d in drivers
                    if event_key in d.ride_types and any(m.lower() in d.service_type.lower() for m in config["matches"])
                }


            assignments_to, rem_d_to, rem_r_to = assign_whitelisted_groups(drivers_event, riders_event, driver_required_riders_to, rider_groups_to)
            assignments_to, unassigned_riders_to = assign_riders_by_furthest_first(rem_d_to, rem_r_to, destination=config["location"], assignments=assignments_to)

            # Reassign flexible plans before assigning return trip
            if event_key != "hc":
                unassigned_back, _, drivers_event, riders_event = assign_flexible_plans_first(
                    list(drivers_event),
                    list(riders_event)
                )

            assignments_back, rem_d_back, rem_r_back = assign_whitelisted_groups(
                drivers_event, riders_event, driver_required_riders_back, rider_groups_back
            )
            
            assignments_back, unassigned_riders_back = assign_from_church(
            rem_d_back,
            rem_r_back,
            church_location=config["location"],
            assignments=assignments_back,
            ignore_plans=(event_key == "hc")
        )
            event_data[f"assignments_to_{event_key}"] = assignments_to
            event_data[f"assignments_back_{event_key}"] = assignments_back
            event_data[f"unassigned_riders_to_{event_key}"] = list(unassigned_riders_to)
            event_data[f"unassigned_riders_back_{event_key}"] = list(unassigned_riders_back)
            print(f"[{event_key}] Assigned TO: {len(assignments_to)}, BACK: {len(assignments_back)}")

        for event_key in EVENT_TYPES:
            print(f"\n=== {event_key.upper()} ASSIGNMENTS ===")
            
            to_key = f"assignments_to_{event_key}"
            back_key = f"assignments_back_{event_key}"

            print(f"[TO {event_key}]")
            for driver, riders in event_data[to_key].items():
                rider_names = ', '.join(r.name for r in riders)
                print(f"  {driver.name} → {rider_names}")

            print(f"[BACK from {event_key}]")
            for driver, riders in event_data[back_key].items():
                rider_names = ', '.join(r.name for r in riders)
                print(f"  {driver.name} → {rider_names}")

        merged_coords = merge_nearby_coords(address_coords)
        
        return {
            **event_data,
            "address_coords": dict(merged_coords),
            "oc_people_w_invalid_address": list(oc_people_w_invalid_address),
            "formatted_time": pd.Timestamp.now().strftime("%Y-%m-%d_%H-%M")
        }