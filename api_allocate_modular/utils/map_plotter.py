import folium
import matplotlib.pyplot as plt
from collections import defaultdict
import matplotlib.colors as mcolors
import math
from folium import PolyLine
from folium.plugins import PolyLineTextPath

CHURCH_LOCATION = (29.7107, -95.3994)  # fallback if none provided

class MapPlotter:
    def __init__(self):
        pass

    def get_driver_colors(self, drivers):
        num_drivers = len(drivers)
        cmap = plt.colormaps['tab20'].resampled(max(num_drivers, 1))
        driver_colors = {}
        for idx, driver in enumerate(drivers):
            rgb = cmap(idx % 20)  # avoid overflow
            hex_color = mcolors.to_hex(rgb)
            driver_colors[driver.name] = hex_color
        return driver_colors

    def add_coord_with_offset(self, base_coord, offset_index, total_points, base_radius=0.0009):
        if total_points == 1:
            return base_coord
        angle = 2 * math.pi * offset_index / total_points
        lat, lon = base_coord
        delta_lat = base_radius * math.sin(angle)
        delta_lon = base_radius * math.cos(angle)
        return (lat + delta_lat, lon + delta_lon)

    def plot_assignments_map_folium(self, assignments, address_coords, filename, reverse_arrows=False):
        m = folium.Map(location=(29.71, -95.41), zoom_start=13)
        driver_colors = self.get_driver_colors([driver for driver in assignments])
        coord_entities = defaultdict(list)
        coord_counts = defaultdict(int)
        arrow_symbol = '  ➤  ' if reverse_arrows else '  ◀  '

        for driver, riders in assignments.items():
            coord_entities[driver.address].append(driver)
            for rider in riders:
                coord_entities[rider.address].append(rider)

        for driver, riders in assignments.items():
            color = driver_colors[driver.name]
            base_driver_coord = address_coords.get(driver.address)
            if not base_driver_coord:
                continue
            coord_counts[driver.address] += 1
            driver_idx = coord_counts[driver.address] - 1
            total_driver_group = len(coord_entities[driver.address])
            driver_coord = self.add_coord_with_offset(base_driver_coord, driver_idx, total_driver_group)

            folium.Marker(driver_coord,
                icon=folium.DivIcon(html=f'''
                    <div style="
                        background-color: {color};
                        color: white;
                        font-size: 12px;
                        font-weight: bold;
                        border-radius: 50%;
                        width: 24px;
                        height: 24px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        box-shadow: 0 0 4px rgba(0,0,0,0.5);
                        border: 1px solid black;">D</div>'''),
                popup=f"[D] {driver.name}"
            ).add_to(m)

            path_coords = [driver_coord]

            for rider in riders:
                base_rider_coord = address_coords.get(rider.address)
                if not base_rider_coord:
                    continue
                coord_counts[rider.address] += 1
                rider_idx = coord_counts[rider.address] - 1
                total_rider_group = len(coord_entities[rider.address])
                rider_coord = self.add_coord_with_offset(base_rider_coord, rider_idx, total_rider_group)

                folium.Marker(rider_coord,
                    icon=folium.DivIcon(html=f'''
                        <div style="
                            background-color: white;
                            color: {color};
                            font-size: 12px;
                            font-weight: bold;
                            border-radius: 50%;
                            width: 24px;
                            height: 24px;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            box-shadow: 0 0 4px rgba(0,0,0,0.5);
                            border: 1px solid {color};">R</div>'''),
                    popup=rider.name
                ).add_to(m)

                path_coords.append(rider_coord)

            if reverse_arrows:
                path_coords.append(CHURCH_LOCATION)
                folium.Marker(CHURCH_LOCATION, icon=folium.Icon(color='red', icon='plus', prefix='fa'),
                              popup="Destination: Church").add_to(m)

            for i in range(len(path_coords) - 1):
                line = PolyLine([path_coords[i], path_coords[i + 1]], color=color, weight=3, opacity=0.7).add_to(m)
                PolyLineTextPath(line, arrow_symbol, repeat=True, repeat_distance='5px', offset=0,
                                 attributes={'fill': color, 'font-weight': 'bold'}).add_to(m)

        m.save(filename)
        print(f"[MapPlotter] Saved map to {filename}")

    def generate(self, data):
        self.plot_assignments_map_folium(data["assignments_to"], data["address_coords"], "maps/rides_to/index.html", reverse_arrows=True)
        self.plot_assignments_map_folium(data["assignments_back"], data["address_coords"], "maps/rides_back/index.html", reverse_arrows=False)
