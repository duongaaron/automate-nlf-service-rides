import re
from openpyxl import load_workbook

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

        # Extract just the filename from the path
        excel_filename = excel_path.split("/")[-1] if "/" in excel_path else excel_path

        # Add the download button HTML
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

        with open("assignments_table.html", "w", encoding="utf-8") as f:
            f.write(full_html)

        print("[HTMLExporter] HTML table saved to assignments_table.html")
        data["html_path"] = "assignments_table.html"