# Google Sheets Information
GOOGLE_SHEETS_LINK = "https://docs.google.com/spreadsheets/d/1DZfC2GULOud8kl8gsGD7D1wmdG9YNhqNPL6L0PMabh8/edit?resourcekey=&gid=1441308570#gid=1441308570"
GOOGLE_SHEETS_TAB = "Form Responses 3"

# Column Titles
NAME_COLUMN = "Name (first + last name)"
PICKUP_COLUMN = "Where would you like to be picked up? Please include your address (drivers too!)."
SERVICE_TYPE_COLUMN = "Which Sunday service are you attending?"
AFTER_SERVICE_PLANS_COLUMN = "Preferred After Church Plans?"
IS_DRIVER_COLUMN = "Are you a driver?"
SUMMER_HC_OR_SERVICE = "Please select which of the following you will need a ride to!"
OC_ADDRESS = PICKUP_COLUMN

# NAME_COLUMN = "Name"
# PICKUP_COLUMN = "Where would you like to be picked up?"
# SERVICE_TYPE_COLUMN = "Are you coming to summer house church on Saturday (May 31st)?"
# AFTER_SERVICE_PLANS_COLUMN = "Preferred after church plans?"
# IS_DRIVER_COLUMN = "Are you a driver?"
# OC_ADDRESS = "Off Campus address"
# SUMMER_HC_OR_SERVICE = "Please select which of the following you will need a ride to!"

# Stop Names
NORTH_STOP_NAME = "North (Brown, Duncan, Jones, Martel, McMurtry)"
SOUTH_STOP_NAME = "South (Baker, Hanszen, Lovett, Sid Richardson, Wiess, Will Rice)"
LIFETOWER_STOP_NAME = "Life Tower"

location_to_address = {
    NORTH_STOP_NAME: "1601 Rice Boulevard, Houston, TX 77005",
    SOUTH_STOP_NAME: "6320 Main St, Houston, TX 77005",
    LIFETOWER_STOP_NAME: "6919 Main St, Houston, TX 77030",
}

# Plans
BACK_HOME_PLAN = "Back home 💙"
LUNCH_PLAN = "Lunch 💛"
FLEXIBLE_PLAN = "flexible"

# Car capacity
PASSENGER_LIMIT = 4
AMOUNT_SEATS_CHANGE = {
    # "Matthew Ahn": 2,
}

# Whitelisting
driver_required_riders_to = {
    # "Jonathan Mak": {"shayla Nguyen", "Pedro Flores-Teran"},
}
rider_groups_to = [
    # {"Khang Le", "seojin Kwon"}
]

driver_required_riders_back = {
    # "Jonathan Mak": {"Grace Kwon", "Seojin Kwon"},
}
rider_groups_back = [
    # {"Khang Le", "Aaron duong"}
]

# Color map for Excel/Maps
location_colors = {
    "North": "FFd9ead3",
    "South": "FF93CCEA",
    "Off": "FFFFFFED",
    "Life": "fff4cccc",
    BACK_HOME_PLAN: "FFD9D2E9",
    "RJM": "FFEAD1DC",
    LUNCH_PLAN: "FFFCE5CD",
    "Either! My plans are flexible 💚": "FFCFE2F3",
    "Refreshments": "FFB6D7A8",
    "NLK 🧡": "FFFFCCA4",
}

CHURCH_LOCATION = (29.892500, -95.525675)

EVENT_TYPES = {
    "church": {
        "form_matches": {"sunday service (sunday)", "both!"},
        "matches": {"1st", "2nd", "9:00", "11:00"},  # used to validate the service time field
        "location": CHURCH_LOCATION,
        "label": "Sunday Service"
    },
    "hc": {
        "form_matches": {"summer hc (saturday)", "both!"},
        "matches": {"summer", "hc", "saturday"},  # might not be needed depending on logic
        "location": CHURCH_LOCATION,
        "label": "Summer HC"
    }
}

# SUMMER HC FORM QUESTION INCLUSION
RIDE_TO_COLUMN = "Please select which of the following you will need a ride to!"
USE_RIDE_SELECTION_FORM_QUESTION = True  # You can toggle this to False later