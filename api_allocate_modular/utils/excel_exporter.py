import os
import glob
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Alignment, Font
from openpyxl.utils import get_column_letter
from datetime import datetime

from utils.constants import location_colors

class ExcelExporter:
    def __init__(self, output_dir="."):
        self.output_dir = output_dir

    def export(self, data):
        wb = Workbook()
        ws = wb.active
        ws.title = "Assignments"
        formatted_time = data.get("formatted_time", datetime.now().strftime("%Y-%m-%d_%H-%M"))

        used_to = self._place_assignments(
            ws,
            data["assignments_to"],
            data["unassigned_riders_to"],
            data.get("oc_people_w_invalid_address", []),
            start_col=3,
            key_col=2,
            sort_key_driver=lambda d: (d.service_type, d.pickup_location.split()[0]),
            sort_key_rider=lambda r: r.pickup_location.split()[0],
            driver_color_key=lambda d: d.pickup_location.split()[0],
            rider_color_key=lambda r: r.pickup_location.split()[0],
            label_plan=False,
            include_rider_keys_in_legend=True,
        )

        used_from = self._place_assignments(
            ws,
            data["assignments_back"],
            data["unassigned_riders_back"],
            data.get("oc_people_w_invalid_address", []),
            start_col=11,
            key_col=10,
            sort_key_driver=lambda d: d.plans,
            sort_key_rider=lambda r: r.pickup_location.split()[0],
            driver_color_key=lambda d: d.plans,
            rider_color_key=lambda r: r.pickup_location.split()[0],
            label_plan=True,
            include_rider_keys_in_legend=False,
        )

        # Auto-size columns
        for col_index in used_to.union(used_from).union({2, 10}):
            letter = get_column_letter(col_index)
            max_length = max((len(str(cell.value)) for cell in ws[letter] if cell.value), default=0)
            ws.column_dimensions[letter].width = max_length + 2

        filename = f"assignments_{formatted_time}.xlsx"
        full_path = os.path.join(self.output_dir, filename)

        for f in glob.glob(os.path.join(self.output_dir, "**", "assignments*.xlsx"), recursive=True):
            try: os.remove(f)
            except: pass

        wb.save(full_path)
        wb.save(f"./maps/rides_to/{filename}")
        wb.save(f"./maps/rides_back/{filename}")
        print(f"[ExcelExporter] Saved to {full_path}")
        data["excel_path"] = full_path
        return full_path
    

    def _place_assignments(
        self, ws, assignments, unassigned_riders, oc_people_w_invalid_address,
        start_col, key_col, sort_key_driver, sort_key_rider,
        driver_color_key, rider_color_key,
        label_plan, include_rider_keys_in_legend
    ):
        from openpyxl.styles import PatternFill, Alignment, Font

        col = start_col
        row = 2
        curr_car_count = 1
        max_passengers = 0
        local_used_cols = set()
        used_keys = set()

        sorted_assignments = sorted(assignments.items(), key=lambda item: sort_key_driver(item[0]))

        for driver, riders in sorted_assignments:
            driver_text = f"Driver: {driver.name}"
            driver_cell = ws.cell(row=row, column=col, value=driver_text)
            driver_key = driver_color_key(driver)
            used_keys.add(driver_key)
            fill_color = location_colors.get(driver_key, "FFFFFF")
            driver_cell.fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")
            driver_cell.alignment = Alignment(horizontal="center")
            driver_cell.font = Font(bold=True, underline="single")
            local_used_cols.add(col)

            max_passengers = max(max_passengers, len(riders))
            sorted_riders = sorted(riders, key=sort_key_rider)
            for i, rider in enumerate(sorted_riders):
                rider_text = f"{rider.name}"
                rider_cell = ws.cell(row=row + 1 + i, column=col, value=rider_text)
                rider_key = rider_color_key(rider)
                if include_rider_keys_in_legend:
                    used_keys.add(rider_key)
                fill_color = location_colors.get(rider_key, "FFFFFF")
                rider_cell.fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")
                local_used_cols.add(col)

            if curr_car_count % 5 == 0:
                col = start_col
                row += min(8, max_passengers + 3)
            else:
                col += 1
            curr_car_count += 1

        if unassigned_riders or oc_people_w_invalid_address:
            col += 1
            header_cell = ws.cell(row=row, column=col, value="UNASSIGNED RIDERS")
            header_cell.fill = PatternFill(start_color="FFCCCCCC", end_color="FFCCCCCC", fill_type="solid")
            header_cell.alignment = Alignment(horizontal="center")
            header_cell.font = Font(bold=True, underline="single")
            local_used_cols.add(col)

            all_unassigned = sorted(set(unassigned_riders).union(oc_people_w_invalid_address), key=sort_key_rider)
            for i, rider in enumerate(all_unassigned):
                base = f"{rider.name}"
                if rider in unassigned_riders:
                    base += " — No valid driver"
                else:
                    base += " — Invalid off-campus address"
                cell = ws.cell(row=row + 1 + i, column=col, value=base)
                rider_key = rider_color_key(rider).strip()
                if include_rider_keys_in_legend:
                    used_keys.add(rider_key)
                fill_color = location_colors.get(rider_key, "FFFFFF")
                cell.fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")
                local_used_cols.add(col)

        # Add legend
        key_row = 2
        for key in sorted(used_keys):
            key_cell = ws.cell(row=key_row, column=key_col, value=key)
            fill_color = location_colors.get(key, "FFFFFF")
            key_cell.fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")
            key_row += 1

        return local_used_cols
