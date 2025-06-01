import time
from utils.data_loader import DataLoader
from utils.excel_exporter import ExcelExporter
from utils.html_exporter import HTMLExporter
from utils.map_plotter import MapPlotter
from dotenv import load_dotenv
from utils.constants import location_colors, EVENT_TYPES

def main():
    total_start = time.time()
    load_dotenv(override=True)

    print("Loading data...")
    t0 = time.time()
    data = DataLoader().load_data()
    t1 = time.time()
    print(f"✓ Data loaded in {t1 - t0:.2f} seconds")

     # for event_key in EVENT_TYPES:
    #     to = data[f"assignments_to_{event_key}"]
    #     back = data[f"assignments_back_{event_key}"]
    #     print(f"To {event_key}: {sum(len(v) for v in to.values())} riders assigned to {len(to)} drivers")
    #     print(f"Back {event_key}: {sum(len(v) for v in back.values())} riders assigned to {len(back)} drivers")
    #     print(f"Unassigned to {event_key}: {len(data[f'unassigned_riders_to_{event_key}'])}")
    #     print(f"Unassigned back {event_key}: {len(data[f'unassigned_riders_back_{event_key}'])}")

    print("Exporting to Excel...")
    t2 = time.time()
    ExcelExporter().export(data)
    t3 = time.time()
    print(f"✓ Excel exported in {t3 - t2:.2f} seconds")

    print("Exporting to HTML...")
    t4 = time.time()
    html_exporter = HTMLExporter()
    html_exporter.export(data)
    HTMLExporter.generate_index_html(data.get("formatted_time"))
    t5 = time.time()
    print(f"✓ HTML exported in {t5 - t4:.2f} seconds")

    print("Generating maps...")
    t6 = time.time()
    MapPlotter().generate(data)
    t7 = time.time()
    print(f"✓ Maps generated in {t7 - t6:.2f} seconds")

    total_end = time.time()
    print(f"\n=== Total runtime: {total_end - total_start:.2f} seconds ===")

if __name__ == "__main__":
    main()