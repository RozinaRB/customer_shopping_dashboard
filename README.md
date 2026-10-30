# 📊 Customer Shopping Analytics Dashboard — Detailed Documentation

> A Streamlit-based interactive dashboard that uploads, validates, and analyzes Customer Shopping Preferences data.

### Click the link so you can see full dashboard [https://customershoppingdashboard.streamlit.app/]

---

## 📋 Table of Contents

1. [Project Overview](#1-project-overview)
2. [Features](#2-features)
3. [Technology Stack](#3-technology-stack)
4. [Why Polars?](#4-why-polars)
5. [Project Structure](#5-project-structure)
6. [Dataset Schema](#6-dataset-schema)
7. [How the Dashboard Works](#7-how-the-dashboard-works)
8. [Page 1 — Upload & Validation](#8-page-1--upload--validation)
9. [Page 2 — Executive Dashboard](#9-page-2--executive-dashboard)
10. [Module Reference](#10-module-reference)
11. [How to Run](#11-how-to-run)
12. [CSV File Guidelines](#12-csv-file-guidelines)

---

## 1. Project Overview

The **Customer Shopping Analytics Dashboard** is a fully web-based analytics tool that allows users to upload their own **Customer Shopping Preferences CSV** file and instantly view sales analysis reports.

The dashboard operates in two layers:

1. **Data Ingestion Layer** — Accepts a CSV file upload, parses it, and validates it against an 18-column schema.
2. **Analytics Layer** — Generates KPIs, table reports, and interactive charts from the validated data.

---

## 2. Features

| Feature | Description |
|---------|-------------|
| 📤 CSV Upload | Upload any compatible CSV file |
| 🔍 Automatic Validation | Automatically checks whether all 18 required columns are present |
| 📊 Data Diagnostics | Counts total rows, columns, null rows, and numeric columns |
| 🎯 4 KPI Cards | Total revenue, total customers, average order value, average rating |
| 📋 Filterable Table | Filter using Age slider, Category & Gender multiselect, Amount slider |
| 📈 6 Interactive Charts | Various chart types built with Plotly |
| 🌐 Global Filters | Location, Category, and Season filters in the Visual tab |
| 🔄 Auto-redirect | Automatically navigates to the dashboard once validation passes |

---

## 3. Technology Stack

| Library | Version | Usage |
|---------|---------|-------|
| **Python** | 3.11 | Programming language |
| **Streamlit** | latest | Web UI framework |
| **Polars** | latest | Fast data processing and analysis |
| **Plotly** | latest | Interactive charts and visualizations |
| **PyArrow** | latest | Polars ↔ Pandas conversion support |

---

## 4. Why Polars?

This project uses **Polars** instead of the traditional **Pandas** library. The reasons are explained in detail below.

### ⚡ Speed

Polars uses the Apache Arrow memory model and is written in Rust, making it **5–50× faster** than Pandas for data processing. This difference is clearly noticeable when loading and filtering large CSV files.

### 🔀 Lazy Evaluation

Polars provides a `lazy()` API that performs query optimization — running multiple filters and aggregations together in an optimized pass, avoiding unnecessary intermediate data copies.

### 💾 Memory Efficiency

Polars uses a columnar format which consumes significantly less RAM than Pandas' row-based storage. On the same dataset, Polars typically uses **30–60% less memory**.

### 🛡️ Type Safety

In Polars, every column's dtype is strictly defined. Type conversion cannot happen without an explicit `cast()`, which reduces runtime errors and makes code more predictable. This advantage is leveraged in the `validate_schema()` function of this project.

### 📝 Expressive API

```python
# Polars (used in this project)
df.group_by("Location").agg(
    pl.col("Purchase Amount (USD)").sum().alias("Total Revenue ($)")
).sort("Total Revenue ($)", descending=True)

# Pandas (equivalent)
df.groupby("Location")["Purchase Amount (USD)"].sum().reset_index().sort_values(ascending=False)
```

The Polars API is more expressive and easier to chain.

### Integration with Plotly

Plotly Express does not natively support Polars DataFrames, so `.to_pandas()` is called just before rendering each chart. All heavy computation is done in Polars, and only the small aggregated result is converted to Pandas.

---

## 5. Project Structure

```
customer_shopping_dashboard/
│
├── data/
│   └── shopping_trends.csv      # Sample dataset (for testing)
│
├── src/
│   ├── app.py                   # Main Streamlit app — UI and page routing
│   ├── validation.py            # CSV parsing, diagnostics, schema validation
│   ├── analysis.py              # Polars-based KPIs, filters, aggregations
│   └── visualization.py        # Plotly chart factory functions
│
├── environment.yml              # Conda environment definition
├── README.md                    # Brief project introduction
└── DOCUMENTATION.md             # This file — detailed documentation
```

---

## 6. Dataset Schema

The dashboard expects a CSV file with **exactly 18 columns**. Any file outside this schema will be rejected.

| # | Column Name | Data Type | Description |
|---|-------------|-----------|-------------|
| 1 | `Customer ID` | Integer/String | Unique customer identifier |
| 2 | `Age` | **Numeric** | Customer age (in years) |
| 3 | `Gender` | String | Customer gender (Male / Female) |
| 4 | `Item Purchased` | String | Name of the purchased product |
| 5 | `Category` | String | Product category (Clothing, Footwear, etc.) |
| 6 | `Purchase Amount (USD)` | **Numeric** | Purchase price in US dollars |
| 7 | `Location` | String | Customer location (US State) |
| 8 | `Size` | String | Product size (S, M, L, XL) |
| 9 | `Color` | String | Product color |
| 10 | `Season` | String | Season of purchase (Spring, Summer, Fall, Winter) |
| 11 | `Review Rating` | **Numeric** | Review rating (1.0 – 5.0) |
| 12 | `Subscription Status` | String | Whether customer has a subscription (Yes / No) |
| 13 | `Shipping Type` | String | Type of shipping used |
| 14 | `Discount Applied` | String | Whether a discount was applied (Yes / No) |
| 15 | `Promo Code Used` | String | Whether a promo code was used (Yes / No) |
| 16 | `Previous Purchases` | **Numeric** | Number of previous purchases |
| 17 | `Payment Method` | String | Payment method used |
| 18 | `Frequency of Purchases` | String | Purchase frequency (Weekly, Fortnightly, etc.) |

> **⚠️ Important:** Columns marked **Bold** (`Age`, `Purchase Amount (USD)`, `Review Rating`, `Previous Purchases`) must be numeric — they are used for KPI calculations.

---

## 7. How the Dashboard Works

The complete application flow is shown below:

```
User uploads a CSV file
          │
          ▼
  parse_uploaded_file()
  [Parse CSV → Polars DataFrame]
          │
     Parse failed? ──── Yes ──► Show error, stop
          │ No
          ▼
   get_diagnostics()
  [Count rows, columns, nulls, numeric cols]
          │
          ▼
   validate_schema()
  [Check 18 columns + numeric compatibility]
          │
    Errors found? ──── Yes ──► Show error list, stop
          │ No
          ▼
  coerce_numeric_columns()
  [Cast numeric-string columns to Float64]
          │
          ▼
   Store DataFrame in session_state
          │
          ▼
   st.rerun() → Dashboard Page
```

### Session State Management

Two keys are managed via Streamlit's `st.session_state`:

| Key | Value | Purpose |
|-----|-------|---------|
| `page` | `"upload"` or `"dashboard"` | Determines which page is currently active |
| `df` | `None` or `pl.DataFrame` | Holds the validated DataFrame |

---

## 8. Page 1 — Upload & Validation

This page is shown when the dashboard first starts.

### Step 1: File Upload

An `st.file_uploader` component accepts only `.csv` extension files.

### Step 2: CSV Parsing (`validation.py → parse_uploaded_file`)

The uploaded file's bytes are read and passed to Polars via an `io.BytesIO` buffer:

```python
raw_bytes = uploaded_file.read()
df = pl.read_csv(io.BytesIO(raw_bytes), infer_schema_length=500)
```

`infer_schema_length=500` means Polars examines the first 500 rows to determine the data type of each column.

### Step 3: Data Diagnostics (`validation.py → get_diagnostics`)

Four metrics are computed:

- **Total Rows** — `df.height`
- **Total Columns** — `df.width`
- **Rows with Nulls** — Uses `pl.fold()` to check whether any column contains a null in each row
- **Numeric Columns** — Checks the Polars dtype list for each column

### Step 4: Schema Validation (`validation.py → validate_schema`)

Four checks are performed in order:

1. **Missing Column Check** — Whether any of the 18 required columns are absent
2. **Numeric Type Check** — Whether numeric columns can be cast to `Float64`
3. **Non-null Check** — Whether the `Customer ID` column is entirely null
4. **Positive Amount Check** — Whether `Purchase Amount (USD)` contains any negative values

**If validation fails:** All errors are listed and displayed; navigation to the dashboard is blocked.

**If validation passes:** `coerce_numeric_columns()` is called to cast any string-typed numeric columns to the correct type, then `st.rerun()` auto-redirects to the dashboard.

---

## 9. Page 2 — Executive Dashboard

This page is shown once validation passes successfully.

### KPI Cards (4 Cards)

Four metric cards are displayed at the top of the page:

| KPI | Calculation | Example |
|-----|-------------|---------|
| 💰 Total Revenue | Sum of `Purchase Amount (USD)` | \$125,320.00 |
| 👥 Total Customers | Unique count of `Customer ID` | 3,900 |
| 🧾 Avg Order Value | Mean of `Purchase Amount (USD)` | \$59.76 |
| ⭐ Avg Customer Rating | Mean of `Review Rating` | 3.75 / 5.0 |

---

### Tab 1: 📋 Table Reports

Four structured table reports are displayed sequentially:

#### Report 1 — Filtered Raw Data Table

Displays the full dataset but can be filtered using 4 controls:

| Filter | Type | Column |
|--------|------|--------|
| **Age Range** | Slider (min–max) | `Age` |
| **Category** | Multiselect | `Category` |
| **Gender** | Multiselect | `Gender` |
| **Purchase Amount (\$)** | Slider (min–max) | `Purchase Amount (USD)` |

After applying filters, the count of visible rows is shown, e.g.: *"Showing 1,234 of 3,900 rows after filtering."*

#### Report 2 — Location Performance Report

Aggregates sales data grouped by US State:

| Column | Description |
|--------|-------------|
| Location | State name |
| Total Revenue (\$) | Total revenue for that state (sorted descending) |
| Total Orders | Total number of orders |
| Average Rating | Mean review rating |

#### Report 3 — Category & Item Summary Report

Breaks down performance by product category and item:

| Column | Description |
|--------|-------------|
| Category | Product category |
| Item Purchased | Product name |
| Total Revenue (\$) | Total revenue for that item |
| Avg Purchase Amount (\$) | Average purchase price |
| Total Items Sold | Total number of units sold |

#### Report 4 — Customer Demographic & Payment Breakdown

Analyzes spending grouped by customer characteristics:

| Column | Description |
|--------|-------------|
| Gender | Customer gender |
| Subscription Status | Whether the customer has a subscription |
| Payment Method | Payment method used |
| Total Spending (\$) | Total spending |
| Transaction Count | Number of transactions |

---

### Tab 2: 📊 Visual Insights

#### Global Filters (applied to all charts)

Three global filters at the top of the Visual tab affect all 6 charts simultaneously:

- **📍 Location** — Multiselect (choose states)
- **🏷️ Category** — Multiselect (choose categories)
- **🍂 Season** — Multiselect (choose seasons)

#### 6 Interactive Charts

| # | Chart | Type | Description |
|---|-------|------|-------------|
| 1 | 🏆 Top Revenue Generating Locations | Horizontal Bar | Top 15 states ranked by revenue |
| 2 | 👥 Customer Distribution by Location | Vertical Bar | Unique customer count per state |
| 3 | 🍩 Revenue vs Category Breakdown | Donut Chart | Revenue share percentage by category |
| 4 | 📅 Seasonal Sales Trend by Category | Grouped Bar | Revenue comparison by season and category |
| 5 | 💳 Payment Method Preference | Pie Chart | Transaction volume distribution by payment method |
| 6 | 📊 Customer Age Distribution vs Spending | Scatter Plot | Age vs purchase amount, colored by Category, shaped by Gender |

---

## 10. Module Reference

### `src/app.py` — Main App

Contains all UI logic and page routing. Key functions:

| Function | Purpose |
|----------|---------|
| `_init_session_state()` | Initializes `page` and `df` keys on first load |
| `render_upload_page()` | Renders Page 1 — upload, diagnostics, validation |
| `render_dashboard_page()` | Renders Page 2 — KPIs, tabs, reports, charts |
| `_render_table_reports()` | Renders the 4 table reports |
| `_render_visual_insights()` | Renders global filters + 6 Plotly charts |
| `main()` | Reads session state and routes to the correct page |

---

### `src/validation.py` — Data Validation

| Function | Input | Output |
|----------|-------|--------|
| `parse_uploaded_file(file)` | Streamlit UploadedFile | `(DataFrame, None)` or `(None, error_str)` |
| `get_diagnostics(df)` | Polars DataFrame | `dict` (4 metrics) |
| `validate_schema(df)` | Polars DataFrame | `list[str]` (errors; empty means passed) |
| `coerce_numeric_columns(df)` | Polars DataFrame | Properly typed Polars DataFrame |

**Constants:**
- `REQUIRED_COLUMNS` — List of 18 required column names
- `NUMERIC_COLUMNS` — 4 numeric columns that are type-checked
- `NON_NULL_COLUMNS` — `Customer ID` is rejected if entirely null

---

### `src/analysis.py` — Data Analysis (Polars)

| Function | Purpose | Output |
|----------|---------|--------|
| `compute_kpis(df)` | Computes the 4 KPI values | `dict[str, float]` |
| `filter_data(df, ...)` | Filters by Age, Category, Gender, Amount | Filtered `pl.DataFrame` |
| `location_report(df)` | Revenue aggregation by state | `pl.DataFrame` |
| `category_report(df)` | Aggregation by category and item | `pl.DataFrame` |
| `demographic_report(df)` | Aggregation by gender, subscription, payment | `pl.DataFrame` |
| `top_locations_data(df, top_n)` | Top N states ranked by revenue | `pl.DataFrame` |
| `customer_distribution_data(df)` | Unique customer count per state | `pl.DataFrame` |
| `revenue_by_category_data(df)` | Revenue aggregated by category | `pl.DataFrame` |
| `seasonal_sales_data(df)` | Revenue by season and category | `pl.DataFrame` |
| `payment_method_data(df)` | Transaction count by payment method | `pl.DataFrame` |
| `age_vs_spending_data(df)` | Age, Amount, Category, Gender for scatter | `pl.DataFrame` |

---

### `src/visualization.py` — Plotly Charts

All chart functions accept a pre-aggregated Polars DataFrame, call `.to_pandas()`, and return a `plotly.graph_objects.Figure` ready for `st.plotly_chart()`.

| Function | Chart Type |
|----------|-----------|
| `chart_top_locations(df)` | Horizontal bar (color scale: Blues) |
| `chart_customer_distribution(df)` | Vertical bar (color scale: Teal) |
| `chart_revenue_by_category(df)` | Donut pie chart |
| `chart_seasonal_sales(df)` | Grouped bar (Season × Category) |
| `chart_payment_methods(df)` | Pie chart |
| `chart_age_vs_spending(df)` | Scatter (color = Category, symbol = Gender) |

**Shared styling:**
- `COLOR_PALETTE` — `px.colors.qualitative.Bold` (same color palette across all charts)
- `_TRANSPARENT_BG` — Transparent chart background to blend with Streamlit's theme
- `_apply_base_layout()` — Keeps title, font, and margins consistent across all charts

---

## 11. How to Run

### Method 1: Conda Environment (Recommended)

```bash
# 1. Create the environment
conda env create -f environment.yml

# 2. Activate the environment
conda activate mini_dash

# 3. Launch the dashboard
streamlit run src/app.py
```

### Method 2: pip

```bash
# 1. Install required libraries
pip install streamlit polars plotly pyarrow

# 2. Launch the dashboard
streamlit run src/app.py
```

Once the dashboard starts, open **http://localhost:8501** in your browser.

### Sample Data for Testing

You can use the `data/shopping_trends.csv` file included in the project to test the dashboard right away.

---

## 12. CSV File Guidelines

Keep the following in mind when preparing your own CSV file:

1. **Header row is required** — The first row must contain exactly 18 column names with exact spelling (case-sensitive).
2. **Numeric columns must contain numbers** — `Age`, `Purchase Amount (USD)`, `Review Rating`, and `Previous Purchases` must contain only numeric values.
3. **Purchase Amount must always be positive** — Negative values will trigger a validation warning.
4. **Customer ID column must not be entirely null** — At least some values must be present.
5. **Season column values** — Using `Spring`, `Summer`, `Fall`, `Winter` ensures the seasonal chart displays in the correct order.

### Sample CSV Structure

```csv
Customer ID,Age,Gender,Item Purchased,Category,Purchase Amount (USD),Location,Size,Color,Season,Review Rating,Subscription Status,Payment Method,Shipping Type,Discount Applied,Promo Code Used,Previous Purchases,Frequency of Purchases
1,25,Female,T-Shirt,Clothing,45,New York,M,Blue,Summer,4.2,Yes,Credit Card,Standard,No,No,3,Monthly
2,34,Male,Sneakers,Footwear,120,California,L,White,Spring,3.8,No,PayPal,Express,Yes,Yes,7,Weekly
```

---

*Documentation last updated: October 2026*
