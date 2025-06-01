import re
import os
from openpyxl import load_workbook
from utils.constants import EVENT_TYPES
from datetime import datetime

class HTMLExporter:
    def __init__(self):
        pass

    def clean_cell_value(self, value):
        if not isinstance(value, str):
            return value
        return re.sub(r'[^\x20-\x7E]', '', value)

    def workbook_to_html_colored(self, excel_path):
        wb = load_workbook(filename=excel_path)
        ws = wb.active

        html = '<table border="1" style="border-collapse: collapse; font-family: sans-serif;">\n'
        for row in ws.iter_rows():
            html += '<tr>'
            for cell in row:
                value = self.clean_cell_value(cell.value) if cell.value is not None else ''
                bgcolor = "FFFFFF"
                if cell.fill and cell.fill.fill_type == "solid":
                    raw_color = cell.fill.start_color.rgb
                    if raw_color:
                        bgcolor = raw_color[-6:]  # Strip alpha
                is_bold = "font-weight: bold;" if isinstance(value, str) and value.strip().startswith("Driver:") else ""
                html += f'<td style="background-color: #{bgcolor}; padding: 5px; {is_bold}">{value}</td>'
            html += '</tr>\n'
        html += '</table>'
        return html

    def export(self, data):
        excel_path = data.get("excel_path")
        if not excel_path:
            print("[HTMLExporter] No Excel path provided.")
            return

        html_content = self.workbook_to_html_colored(excel_path)

        excel_filename = excel_path.split("/")[-1] if "/" in excel_path else excel_path

        button_html = f'''
        <div style="z-index: 9999; display: flex; gap: 10px;">
            <a href="{excel_filename}" download>
                <button style="margin: 10px; padding: 10px 20px; font-size: 14px; background-color: #4CAF50; color: white; border: none; border-radius: 5px;">
                    Download Assignments as Excel
                </button>
            </a>
        </div>\n
        '''

        full_html = button_html + html_content

        with open("maps/assignments_table.html", "w", encoding="utf-8") as f:
            f.write(full_html)

        print("[HTMLExporter] HTML table saved to assignments_table.html")
        data["html_path"] = "assignments_table.html"
        
    @staticmethod
    def generate_index_html(timestamp_str=""):
        timestamp = timestamp_str or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Generate each event subpage (same as before)
        for event_key, meta in EVENT_TYPES.items():
            label = meta["label"]
            for direction in ["to", "back"]:
                folder = f"maps/rides_{direction}_{event_key}"
                os.makedirs(folder, exist_ok=True)

                html = f"""<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <title>Driver/Rider Assignments — {label} ({direction})</title>
    </head>
    <body>
        <h1>Assignments for {label} ({direction.upper()})<br>
        Updated {timestamp} CST</h1>
        <ul>
            <li><a href="../assignments_table.html">Return to Full Table View</a></li>
        </ul>
        <iframe
            src="../assignments_table.html"
            width="100%"
            height="2000"
            style="min-width: 1000px; border: 1px solid #ccc;"
            scrolling="yes"
        ></iframe>
    </body>
    </html>
    """
                with open(os.path.join(folder, "index.html"), "w", encoding="utf-8") as f:
                    f.write(html)
                print(f"[HTMLExporter] Generated {folder}/index.html")

        overview_html = f"""<!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8" />
            <title>Ride Assignment Maps Overview</title>
        </head>
        <body>
            <h1>Ride Assignment Maps</h1>
            <p>Updated {timestamp} CST</p>
            <ul>
        """
        for event_key, meta in EVENT_TYPES.items():
            label = meta["label"]
            for direction in ["to", "back"]:
                folder = f"maps/rides_{direction}_{event_key}"
                overview_html += f'        <li><a href="{folder}/index.html">{label} ({direction.upper()})</a></li>\n'

        overview_html += """        <li><a href="maps/assignments_table.html">Full Assignments Table</a></li>
            </ul>

            <iframe
                src="maps/assignments_table.html"
                width="100%"
                height="2000"
                style="min-width: 1000px; border: 1px solid #ccc;"
                scrolling="yes"
            ></iframe>
        </body>
        </html>
        """

        with open("index.html", "w", encoding="utf-8") as f:
            f.write(overview_html)
        print("[HTMLExporter] Generated maps/index.html")