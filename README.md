# ⚡ Plugging into the Future: Electricity Consumption Analysis in India (2019-2020)

An interactive, dark-themed Full-Stack Data Engineering and Analytics web application that analyzes state-wise electricity usage patterns in India from **January 2019 to December 2020**.

This project investigates seasonal peaks, regional differences, and the severe demand drops caused by the **COVID-19 lockdowns in early 2020**, along with each state's recovery trajectory.

---

## 🏗️ Architecture & Pipeline

```
  ┌─────────────────┐      ┌──────────────┐      ┌───────────────┐
  │  Consumption.csv│ ───▶ │  SQLite DB   │ ◀─── │   Flask App   │
  │  (Raw Dataset)  │      │  (SQLAlchemy)│      │   (app.py)    │
  └─────────────────┘      └──────────────┘      └───────┬───────┘
                                                         │
                                                 ┌───────▼───────┐
                                                 │ Jinja Pages   │
                                                 │ (HTML + CSS)  │
                                                 └───────┬───────┘
                                                         │
                                                 ┌───────▼───────┐
                                                 │ Tableau Embed │
                                                 │ (Embedding v3)│
                                                 └───────────────┘
```

1. **Data Collection & Storage**: A Pandas ETL script loads, cleans, and structures 16,599 daily data records, mapping region codes (`NR`, `WR`, etc.) and state abbreviations (`UP`, `MP`, etc.) to full-form presentation names, storing them in an SQLite database.
2. **Flask Backend**: An asynchronous SQLAlchemy API feeds real-time summary statistics, regional rankings, and recovery trends to the frontend templates.
3. **Glassmorphism Frontend UI**: Built with a responsive dark sidebar, animated progress bars, scroll animations, data tables, and an integrated Tableau dashboard.
4. **Tableau Embedding v3**: Embeds active dashboards programmatically using Tableau’s modern Embedding API v3 with desktop layout constraints.

---

## 📊 Three Core Scenarios Addressed

1. **Overall Consumption Trends**: Tracking monthly national shifts, seasonal demand swings (summer cooling vs. winter heating), and the severe impact of COVID-19 lockdown phases.
2. **Regional Variations in Demand**: Side-by-side analysis of Northern, Southern, Eastern, Western, and Northeastern state metrics (e.g., exposing heavy industrial load in Western states vs. low footprint in Northeastern states).
3. **Recovery After Lockdown**: Tracking recovery percentages and speed from the deepest trough in April 2020 through December 2020.

---

## 🛠️ Technology Stack

* **Data ETL / Pipeline**: Python 3, Pandas, NumPy
* **Database & ORM**: SQLite 3, SQLAlchemy 2.x
* **Backend Framework**: Flask 3.x (Python)
* **Frontend Design**: Modern responsive CSS (Glassmorphism, custom scroll effects, variable-driven dark theme)
* **Visualizations**: Tableau Public / Tableau Embedding API v3

---

## 📁 File Structure

```
electricity-consumption-analysis/
│
├── generate_data.py          # ETL database pipeline
├── sql_queries.py            # Scenario-specific query verification
├── app.py                    # Flask server & backend endpoints
├── requirements.txt          # Python dependencies
├── Consumption.csv           # Raw dataset
├── electricity_db.sqlite     # Generated database (ignored by Git)
│
├── static/
│   └── css/
│       └── style.css         # Dark theme style system
│
└── templates/
    ├── index.html            # Dashboard UI template
    └── insights.html         # Data tables & recovery analytics page
```

---

## 🚀 Installation & Local Execution

### 1.Navigate
```bash
cd electricity-consumption-analysis
```

### 2. Install dependencies
Ensure you have Python installed, then run:
```bash
pip install -r requirements.txt
```

### 3. Run the ETL Pipeline
Process the raw CSV file and build the local SQLite database:
```bash
python generate_data.py
```

### 4. Verify SQL Queries (Optional)
Run the verification script to output database stats directly in the console:
```bash
python sql_queries.py
```

### 5. Launch the Web Application
```bash
python app.py
```
Open **[http://127.0.0.1:5000/](http://127.0.0.1:5000/)** in your browser to view the application.

---

## 📈 Connecting Your Tableau Dashboard

By default, the dashboard includes a sample Tableau visualization. To replace it with your own:

1. Publish your dashboard to **Tableau Public** or your private server.
2. Copy the dashboard share URL.
3. Open `templates/index.html` and replace the `src` attribute of the `<tableau-viz>` element (line ~155) with your URL:

```html
<tableau-viz id="tableauViz"
             src="https://public.tableau.com/views/YOUR_WORKBOOK_NAME/YOUR_DASHBOARD"
             width="100%"
             height="650"
             toolbar="bottom"
             hide-tabs>
</tableau-viz>
```

---

## ✅ Tableau Performance Checklist

Before submitting, make sure to optimize your Tableau dashboard performance:
* **Use Extracts**: Convert your database link into a Tableau extract (`.hyper`) for rapid rendering.
* **Pre-Aggregate**: If daily details aren't needed, aggregate views to the monthly level in your queries.
* **Optimize Calculated Fields**: Avoid nested LOD (Level of Detail) calculations. Perform mathematical additions/conversions database-side before rendering.
* **Filter Contexts**: Turn your main parameters (e.g., date ranges, regions) into *Context Filters* to decrease Tableau's active dataset scan size.
