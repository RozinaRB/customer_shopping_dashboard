# 📋 Project Plan: Customer Shopping Analytics Dashboard

**Author:** Antigravity AI  
**Created:** 2026-10-28  
**Tech Stack:** Streamlit · Polars · Plotly · Python 3.11 · Conda (`mini_dash`)

---

## 🎯 Project Goal

Build a two-page interactive Streamlit web application that:
1. **Page 1 — Data Ingestion & Validation:** Accepts a CSV upload, validates the 18-column schema strictly, reports diagnostics and errors clearly.
2. **Page 2 — Analytics Dashboard:** Shows 4 KPI cards and a tabbed interface with 4 table reports + 6 interactive Plotly visualizations.

---

## 🗂️ Directory Structure

```
customer_shopping_dashboard/
├── PLAN.md                      ← This file: project plan & architecture decisions
├── TODO.md                      ← Granular task checklist
├── README.md                    ← Quickstart guide
├── environment.yml              ← Conda environment definition
├── .gitignore
│
├── data/
│   └── shopping_trends.csv      ← Sample CSV (user uploads at runtime)
│
└── src/
    ├── __init__.py              ← Python package marker
    ├── app.py                   ← Main entry point: navigation & page routing
    ├── validation.py            ← Schema validation & file diagnostics
    ├── analysis.py              ← Polars data transformations & KPI calculations
    └── visualization.py         ← Plotly chart factory functions
```

---

## 🏗️ Architecture Decisions

### Navigation Strategy
- Use `st.session_state` to track `page` (values: `"upload"` or `"dashboard"`).
- `app.py` reads `st.session_state.page` and renders the correct page function.
- After a successful validation, the session state is updated and `st.rerun()` triggers the redirect.

### Data Flow
```
CSV Upload (Page 1)
    ↓
validation.py → parse_csv() → validate_schema()
    ↓ (success)
st.session_state["df"] = polars DataFrame
st.session_state["page"] = "dashboard"
st.rerun()
    ↓
Page 2: analysis.py & visualization.py consume st.session_state["df"]
```

### Module Responsibilities

| Module | Key Functions |
|---|---|
| `validation.py` | `parse_uploaded_file()`, `get_diagnostics()`, `validate_schema()` |
| `analysis.py` | `compute_kpis()`, `filter_data()`, `location_report()`, `category_report()`, `demographic_report()` |
| `visualization.py` | `chart_top_locations()`, `chart_customer_distribution()`, `chart_revenue_by_category()`, `chart_seasonal_sales()`, `chart_payment_methods()`, `chart_age_vs_spending()` |
| `app.py` | `render_upload_page()`, `render_dashboard_page()`, `main()` |

### Styling Decisions
- Use a consistent Plotly color palette: `px.colors.qualitative.Bold`
- Charts use transparent backgrounds (`paper_bgcolor="rgba(0,0,0,0)"`, `plot_bgcolor="rgba(0,0,0,0)"`) so they adapt to Streamlit's theme.
- KPI cards are rendered using `st.metric()` for clean, built-in styling.
- Tables rendered with `st.dataframe()` (interactive by default).

---

## 📊 Page 2 Visual Map

```
┌─────────────────────────────────────────────────────────┐
│  💰 Total Revenue  👥 Customers  💳 Avg Order  ⭐ Rating  │  ← KPI Row
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│  [ 📋 Table Reports ]  [ 📊 Visual Insights ]            │  ← Tabs
│                                                         │
│  Tab 1:                                                 │
│   • Filtered Raw Data Table                             │
│   • Location Performance Report                         │
│   • Category & Item Summary                             │
│   • Demographic & Payment Breakdown                     │
│                                                         │
│  Tab 2:  Global Filters: Location | Category | Season   │
│   • Top Revenue Locations (Horizontal Bar)              │
│   • Customer Distribution by Location (Bar)             │
│   • Revenue by Category (Donut)                         │
│   • Seasonal Sales Trend (Grouped Bar)                  │
│   • Payment Method Preference (Pie)                     │
│   • Age Distribution vs Spending (Scatter/Histogram)    │
└─────────────────────────────────────────────────────────┘
```

---

## ✅ Validation Rules (18 Columns)

| Column | Type Check |
|---|---|
| Customer ID | Must exist (non-null) |
| Age | Numeric |
| Gender | String |
| Item Purchased | String |
| Category | String |
| Purchase Amount (USD) | Numeric (positive) |
| Location | String |
| Size | String |
| Color | String |
| Season | String |
| Review Rating | Numeric (1.0–5.0) |
| Subscription Status | String |
| Shipping Type | String |
| Discount Applied | String |
| Promo Code Used | String |
| Previous Purchases | Numeric |
| Payment Method | String |
| Frequency of Purchases | String |
