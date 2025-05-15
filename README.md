# Automate NLF Service Rides

This project automates the assignment and visualization of church service rides for the NLF community. It assigns riders to drivers for both **to service** and **back from service** directions, generates Excel summaries, and produces interactive maps using Folium for visual inspection.

## 📦 Features

- Assign riders to drivers based on pickup location, service time preferences, and other constraints
- Generates colored Excel spreadsheets showing grouped assignments
- Renders interactive Folium maps with directional arrows for each ride
- Embeds assignment tables in HTML for visual review
- Provides mobile-friendly view and downloadable Excel

## 🗺 Geolocation Methods

This system supports **two methods** for obtaining geographic coordinates for addresses:

### ✅ Method 1: GoogleV3 Geolocation (Recommended for Automation)

- Uses the **Google Maps Geocoding API** via `geopy.geocoders.GoogleV3`
- Requires:
  - A valid **Google Maps API key**
  - Shared access with the **Google Cloud service account email** (nlf-automate-rides-service-acc@nlf-automate-rides.iam.gserviceaccount.com)
- Best for automatic, precise address lookup
- May incur usage costs after the generous quote (1000 requests per day) (I don't think I will ever go over this)

### 🆓 Method 2: Nominatim (Manual CSV Import, Free)

- Uses **OpenStreetMap's Nominatim API**
- More limited and imprecise, but completely **free**
- You must **import a CSV file** (relies on the Google Sheets with all the responses)
- Ideal for quick testing or deployments without API credentials

Choose the method based on your project's size and infrastructure.

## 🗂 Folder Structure

```
.
├── api_allocate.ipynb             # Main code logic 
├── index.html                     # Landing page with links, table, and download (auto-generated)
├── assignments_YYYY-MM-DD.xlsx    # Generated Excel of assignments (auto-generated)
├── assignments_table.html         # HTML-rendered version of the Excel (auto-generated)
├── /maps/
│   ├── /rides_to/
│   │   └── index.html             # Folium map of rides to church (auto-generated)
│   └── /rides_back/
│       └── index.html             # Folium map of rides back from church (auto-generated)
```

## 🛠 How It Works

1. **Run the Python script**: Takes in cleaned rider/driver data and computes assignments.
2. **Export Excel**: A workbook is created with drivers, assigned riders, unassigned riders, and a color-coded key.
3. **Render HTML Table**: The Excel is converted to an HTML table (`assignments_table.html`) and embedded in `index.html`.
4. **Render Folium Maps**: `plot_assignments_map_folium()` generates `index.html` pages in `maps/rides_to/` and `maps/rides_back/`.

## 🌐 Deployment

This site is hosted via **GitHub Pages**.

### To update:

1. Run the assignment generation script locally.
2. Code with automatically generate `index.html`, `assignments_*.xlsx`, and `maps/` folders into the GitHub repo.
3. Commit and push.
4. GitHub Pages will auto-update the site.

## 📲 Mobile Compatibility

- Buttons are styled for touch devices.
- Tables and maps are placed in responsive wrappers (`overflow-x: auto`) for better scrolling on mobile.
- Folium maps support touch zoom/panning but can be finicky; zoom buttons are also available.

## 📥 Download Link

The Excel file with all assignments can be downloaded directly from the homepage using the green **Download Assignments** button.