from datetime import datetime
from zoneinfo import ZoneInfo
from utils.data_loader import DataLoader
from utils.excel_exporter import ExcelExporter
from utils.html_exporter import HTMLExporter
from utils.map_plotter import MapPlotter

def main():
    print("Loading data...")
    data = DataLoader().load_data()

    print("Exporting to Excel...")
    ExcelExporter().export(data)

    print("Exporting to HTML...")
    HTMLExporter().export(data)

    print("Generating maps...")
    MapPlotter().generate(data)

    from bs4 import BeautifulSoup

    now_cst = datetime.now(ZoneInfo("America/Chicago"))
    formatted_time = now_cst.strftime("%m-%d-%Y %H-%M-%S")

    # Load the HTML file
    with open("index.html", "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    # Find the first <h1> element and update its contents
    if soup.h1:
        soup.h1.string = f"Click on the links to show the map of partitions for this week's driver/rider assignments. Updated {formatted_time} CST"

    # Write the modified HTML back
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(str(soup))

    excel_filename = f"assignments_{formatted_time}.xlsx"

    index_html = f"""
    <h1>Click on the links to show the map of partitions for this week's driver/rider assignments. Updated {formatted_time} CST</h1>
    <ul>
    <li><a href="./maps/rides_to/">Rides to map</a></li>
    <li><a href="./maps/rides_back/">Rides back map</a></li>
    </ul>

    <div style="z-index: 9999; display: flex; gap: 10px;">
    <a href="{excel_filename}" download>
        <button style="margin: 10px; padding: 10px 20px; font-size: 14px; background-color: #4CAF50; color: white; border: none; border-radius: 5px;">
        Download Assignments as Excel
        </button>
    </a>
    </div>

    <div style="overflow-x: auto; -webkit-overflow-scrolling: touch; touch-action: auto;">
    <iframe
        src="assignments_table.html"
        width="100%"
        style="min-width: 1000px; height: 80vh; border: 1px solid #ccc;"
    ></iframe>
    </div>
    """

    with open("index.html", "w") as f:
        f.write(index_html)

    print("All tasks completed.")

if __name__ == "__main__":
    main()
