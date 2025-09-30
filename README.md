# 🏪 Smart Store Location Optimization for grocery store

**Find the best new locations for Żabka stores in Warsaw using data-driven spatial analysis and Bayesian optimization.**

---

## 🚀 Project Overview

This project uses open data and bayes optimisation to recommend optimal new locations for grocery store - specifically for Żabka, a popular Polish convenience store chain. By analyzing residential density and existing store placements, it ensures new stores are accessible to residents and not clustered too closely.

**Key Features:**
- End-to-end ETL pipeline (Bronze/Silver/Gold layers) for clean, reproducible data processing
- Spatial analysis using OpenStreetMap data
- Outlier filtering and housing density estimation
- Bayesian optimization to maximize customer reach and minimize store overlap
- Interactive map visualization with folium

---

## 🌟 Example Result

![Map Visualization](results/screenshot.png)

---

## 💡 Why Is This Cool?

- **Real-world impact:** Helps optimize retail expansion using open data and AI
- **Scalable pipeline:** Ready for any city or store chain
- **Modern stack:** ETL layers, spatial analytics, Bayesian optimization, interactive maps

---

## 📊 Data Sources

- **OpenStreetMap (OSM):** Store locations, residential buildings
- **Overpass API:** Automated spatial queries

---

## 🛠️ How It Works

- **ETL Pipeline:**  
  Raw data is ingested from OpenStreetMap (Bronze), cleaned and filtered with outlier removal and feature engineering (Silver), then aggregated and enriched for analysis (Gold).

- **Spatial Analysis:**  
  Latitude and longitude coordinates are converted to metric space, and residents per building are estimated to understand population distribution.

- **Optimization:**  
  Bayesian optimization is applied to identify new store locations that maximize customer proximity while minimizing competition with existing stores.

- **Visualization:**  
  Results are presented on interactive maps, displaying residential buildings, current Żabka stores, and recommended new locations.

---

## 🧑‍💻 Usage

```bash
source ./venv/Scripts/activate
python3 main.py
```
- Outputs recommended new store locations and saves an interactive map in `results/`.

### Run dev
To check code style and function names before committing, run:
```bash
bash run_checks.sh
```

---

## 📬 Contact

*Feel free to connect on [LinkedIn](https://www.linkedin.com/in/katarzyna-paczos/) or check out my [GitHub](https://github.com/KatarzynaPaczos)!*
