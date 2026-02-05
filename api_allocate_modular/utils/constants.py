# Google Sheets Information
GOOGLE_SHEETS_LINK = "https://docs.google.com/spreadsheets/d/1HoSoVgSTPdy2VV7zRvZMhtQX77LgRZ13DXvOQSluSNQ/edit?gid=395220366#gid=395220366"
# GOOGLE_SHEETS_TAB = "Form Responses RESET V2"
GOOGLE_SHEETS_TAB = "aaron copy"


# Column Titles
NAME_COLUMN = "Name"
PICKUP_COLUMN = "Where would you like to be picked up?"
SERVICE_TYPE_COLUMN = "Which service are you attending?"
AFTER_SERVICE_PLANS_COLUMN = "Preferred after church plans?"
IS_DRIVER_COLUMN = "Are you a driver?"
OC_ADDRESS = "Off Campus address"
# SUMMER_HC_OR_SERVICE = "Please select which of the following you will need a ride to!"

# Stop Names
NORTH_STOP_NAME = "North (Brown, Duncan, Jones, Martel, McMurtry)"
SOUTH_STOP_NAME = "South (Baker, Hanszen, Lovett, Sid Richardson, Wiess, Will Rice)"
LIFETOWER_STOP_NAME = "Life tower"

location_to_address = {
    NORTH_STOP_NAME: "1601 Rice Boulevard, Houston, TX 77005",
    SOUTH_STOP_NAME: "6320 Main St, Houston, TX 77005",
    LIFETOWER_STOP_NAME: "6919 Main St, Houston, TX 77030",
}

# Plans
BACK_HOME_PLAN = "Back home 💙"
LUNCH_PLAN = "Lunch 💛"
FLEXIBLE_PLAN = "Flexible"

# Car capacity
PASSENGER_LIMIT = 4
AMOUNT_SEATS_CHANGE = {
    "Ellie Jung": 5,
}

# Whitelisting
driver_required_riders_to = {
    # "Bailey Peek": {"Amy Son"},
}
rider_groups_to = [
    # {"Camille wong", "seojin Kwon"}
    
]

driver_required_riders_back = {
    # "Seojin Kwon": {"Jane Yoo", "Josh Yang"},
    # "Camille": {"Claire Doh"},
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