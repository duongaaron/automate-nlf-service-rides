from utils.data_loader import DataLoader
from utils.excel_exporter import ExcelExporter
from utils.html_exporter import HTMLExporter
from utils.map_plotter import MapPlotter

def main():
    print("Loading data...")
    data = DataLoader().load_data()
    print(data)

    print("Exporting to Excel...")
    ExcelExporter().export(data)

    print("Exporting to HTML...")
    HTMLExporter().export(data)

    print("Generating maps...")
    MapPlotter().generate(data)

    print("All tasks completed.")

if __name__ == "__main__":
    main()
