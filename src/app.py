"""
app.py
======
Main Streamlit entry point for the Customer Shopping Analytics Dashboard.

Application Architecture:
    - Uses ``st.session_state`` to track the current page ("upload" | "dashboard")
      and the validated Polars DataFrame.
    - Page 1 (upload): CSV upload, data diagnostics, schema validation, error feedback.
    - Page 2 (dashboard): 4 KPI cards + tabbed interface (Table Reports & Visual Insights).

To run:
    streamlit run src/app.py

Modules consumed:
    - validation.py  → parse_uploaded_file, get_diagnostics, validate_schema, coerce_numeric_columns
    - analysis.py    → compute_kpis, filter_data, location_report, category_report, demographic_report,
                       top_locations_data, customer_distribution_data, revenue_by_category_data,
                       seasonal_sales_data, payment_method_data, age_vs_spending_data
    - visualization.py → chart_top_locations, chart_customer_distribution, chart_revenue_by_category,
                         chart_seasonal_sales, chart_payment_methods, chart_age_vs_spending
"""

import streamlit as st
import polars as pl

# Local module imports — these live in the same src/ package.
from validation import (
    parse_uploaded_file,
    get_diagnostics,
    validate_schema,
    coerce_numeric_columns,
)
from analysis import (
    compute_kpis,
    filter_data,
    location_report,
    category_report,
    demographic_report,
    top_locations_data,
    customer_distribution_data,
    revenue_by_category_data,
    seasonal_sales_data,
    payment_method_data,
    age_vs_spending_data,
)
from visualization import (
    chart_top_locations,
    chart_customer_distribution,
    chart_revenue_by_category,
    chart_seasonal_sales,
    chart_payment_methods,
    chart_age_vs_spending,
)


# ===========================================================================
# App Configuration
# ===========================================================================

st.set_page_config(
    page_title="Shopping Analytics Dashboard",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ---------------------------------------------------------------------------
# Custom CSS — minimal overrides for card-style metric display.
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
        /* KPI card container */
        div[data-testid="metric-container"] {
            background: linear-gradient(135deg, #f8f9fa, #e9ecef);
            border: 1px solid #dee2e6;
            border-radius: 12px;
            padding: 16px 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }
        /* Section divider */
        .section-header {
            border-left: 4px solid #4361ee;
            padding-left: 12px;
            margin-bottom: 8px;
            font-size: 1.1rem;
            font-weight: 600;
            color: #212529;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ===========================================================================
# Session State Initialisation
# ===========================================================================

def _init_session_state() -> None:
    """
    Initialise all required session state keys on first run.
    Prevents KeyError on first load before any user interaction.
    """
    if "page" not in st.session_state:
        st.session_state["page"] = "upload"   # Start on the upload page.
    if "df" not in st.session_state:
        st.session_state["df"] = None          # No data loaded yet.


# ===========================================================================
# PAGE 1 — Data Ingestion & Validation
# ===========================================================================

def render_upload_page() -> None:
    """
    Render the CSV upload, diagnostics, and schema validation page.

    Flow:
        1. Show file uploader.
        2. On file upload → parse → show diagnostics.
        3. Run schema validation → show errors or success banner.
        4. On success → store df in session state and redirect to dashboard.
    """
    # ── Page Header ─────────────────────────────────────────────────────────
    st.title("🛒 Customer Shopping Analytics Dashboard")
    st.markdown("Upload your **Customer Shopping Preferences CSV** to get started.")
    st.divider()

    # ── File Upload Component ────────────────────────────────────────────────
    with st.container():
        st.markdown('<p class="section-header">📂 Upload Dataset</p>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            label="Choose a CSV file",
            type=["csv"],
            help="Upload the 18-column Customer Shopping Preferences dataset.",
        )

    # Only proceed once the user has selected a file.
    if uploaded_file is None:
        st.info("👆 Please upload a `.csv` file to begin validation.")
        return

    # ── Step 1: Parse ────────────────────────────────────────────────────────
    with st.spinner("📊 Parsing CSV file…"):
        df, parse_error = parse_uploaded_file(uploaded_file)

    if parse_error:
        # File could not be read at all — show error and stop.
        st.error(parse_error)
        return

    st.success(f"✅ File **'{uploaded_file.name}'** parsed successfully.")
    st.divider()

    # ── Step 2: Data Diagnostics ─────────────────────────────────────────────
    with st.container():
        st.markdown('<p class="section-header">🔍 Data Diagnostics Summary</p>', unsafe_allow_html=True)
        diagnostics = get_diagnostics(df)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📋 Total Rows",         f"{diagnostics['total_rows']:,}")
        col2.metric("📐 Total Columns",       f"{diagnostics['total_columns']}")
        col3.metric("⚠️ Rows with Nulls",     f"{diagnostics['missing_rows']:,}")
        col4.metric("🔢 Numeric Columns",     f"{diagnostics['numeric_columns']}")

    st.divider()

    # ── Step 3: Schema Validation ────────────────────────────────────────────
    with st.container():
        st.markdown('<p class="section-header">✅ Schema Validation</p>', unsafe_allow_html=True)

        with st.spinner("🔎 Validating schema against 18-column specification…"):
            errors = validate_schema(df)

        if errors:
            # Validation failed — display all errors prominently.
            st.error(
                f"❌ Validation failed with **{len(errors)} error(s)**. "
                "Please fix the issues below and re-upload your file."
            )
            for err in errors:
                st.markdown(f"- {err}")
            return  # Do NOT navigate to the dashboard.

        # Validation passed — coerce any numeric-string columns.
        df = coerce_numeric_columns(df)

        st.success(
            "🎉 All **18 required columns** are present and data types are valid! "
            "Redirecting to dashboard…"
        )

        # Show a raw data preview so users can confirm their data before navigating.
        with st.expander("📄 Raw Data Preview (first 10 rows)", expanded=False):
            st.dataframe(df.head(10).to_pandas(), use_container_width=True)

    # ── Step 4: Navigate to Dashboard ────────────────────────────────────────
    # Store the validated DataFrame and flip the page flag.
    st.session_state["df"] = df
    st.session_state["page"] = "dashboard"
    st.rerun()  # Triggers a full re-run which renders the dashboard page.


# ===========================================================================
# PAGE 2 — Executive Analytics Dashboard
# ===========================================================================

def render_dashboard_page() -> None:
    """
    Render the full analytics dashboard: KPI cards + tabbed reports & charts.

    Sections:
        - Back button to return to the upload page.
        - 4 KPI metric cards (revenue, customers, avg order, avg rating).
        - Tab 1: Table Reports (4 tables with optional filters).
        - Tab 2: Visual Insights (global filters + 6 Plotly charts).
    """
    df: pl.DataFrame = st.session_state["df"]

    # ── Page Header & Navigation ─────────────────────────────────────────────
    col_title, col_back = st.columns([8, 1])
    with col_title:
        st.title("📊 Executive Analytics Dashboard")
    with col_back:
        st.write("")  # Vertical spacer
        if st.button("⬅ Upload New File", use_container_width=True):
            # Reset state and return to upload page.
            st.session_state["df"] = None
            st.session_state["page"] = "upload"
            st.rerun()

    st.divider()

    # ── KPI Cards ────────────────────────────────────────────────────────────
    st.markdown('<p class="section-header">🎯 Key Performance Indicators</p>', unsafe_allow_html=True)
    kpis = compute_kpis(df)

    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    kpi_col1.metric(
        label="💰 Total Revenue",
        value=f"${kpis['total_revenue']:,.2f}",
        help="Sum of all Purchase Amount (USD) values.",
    )
    kpi_col2.metric(
        label="👥 Total Customers",
        value=f"{kpis['total_customers']:,}",
        help="Unique count of Customer IDs.",
    )
    kpi_col3.metric(
        label="🧾 Avg Order Value",
        value=f"${kpis['avg_order_value']:,.2f}",
        help="Mean Purchase Amount (USD) per transaction.",
    )
    kpi_col4.metric(
        label="⭐ Avg Customer Rating",
        value=f"{kpis['avg_review_rating']:.2f} / 5.0",
        help="Mean Review Rating across all transactions.",
    )

    st.divider()

    # ── Tabbed Interface ─────────────────────────────────────────────────────
    tab_tables, tab_visuals = st.tabs(["📋 Table Reports", "📊 Visual Insights"])

    # =====================================================================
    # TAB 1 — Structured Table Reports
    # =====================================================================
    with tab_tables:
        _render_table_reports(df)

    # =====================================================================
    # TAB 2 — Visual Insights & Analytics
    # =====================================================================
    with tab_visuals:
        _render_visual_insights(df)


# ---------------------------------------------------------------------------
# Tab 1 Helper: Table Reports
# ---------------------------------------------------------------------------

def _render_table_reports(df: pl.DataFrame) -> None:
    """
    Render the four structured table reports inside Tab 1.

    Reports:
        1. Filtered Raw Data Table (with interactive controls)
        2. Location Performance Report
        3. Category & Item Summary Report
        4. Customer Demographic & Payment Breakdown
    """

    # ── Report 1: Filtered Raw Data ─────────────────────────────────────────
    st.markdown("### 1️⃣ Filtered Raw Data Table")
    st.caption("Use the controls below to filter the dataset before viewing.")

    with st.expander("🎛️ Filter Controls", expanded=True):
        filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

        # Age slider — derive min/max from actual data.
        age_min = int(df["Age"].cast(pl.Int64).min())
        age_max = int(df["Age"].cast(pl.Int64).max())
        age_range = filter_col1.slider(
            "Age Range",
            min_value=age_min,
            max_value=age_max,
            value=(age_min, age_max),
        )

        # Category multi-select — use unique values from data.
        all_categories = sorted(df["Category"].unique().to_list())
        selected_categories = filter_col2.multiselect(
            "Category",
            options=all_categories,
            default=all_categories,
        )

        # Gender multi-select.
        all_genders = sorted(df["Gender"].unique().to_list())
        selected_genders = filter_col3.multiselect(
            "Gender",
            options=all_genders,
            default=all_genders,
        )

        # Purchase Amount slider.
        amt_min = float(df["Purchase Amount (USD)"].cast(pl.Float64).min())
        amt_max = float(df["Purchase Amount (USD)"].cast(pl.Float64).max())
        amount_range = filter_col4.slider(
            "Purchase Amount ($)",
            min_value=amt_min,
            max_value=amt_max,
            value=(amt_min, amt_max),
        )

    # Apply filters via analysis module.
    filtered_df = filter_data(
        df,
        age_range=age_range,
        categories=selected_categories if selected_categories else None,
        genders=selected_genders if selected_genders else None,
        amount_range=amount_range,
    )

    st.info(f"Showing **{filtered_df.height:,}** of **{df.height:,}** rows after filtering.")
    st.dataframe(filtered_df.to_pandas(), use_container_width=True, height=320)

    st.divider()

    # ── Report 2: Location Performance ──────────────────────────────────────
    st.markdown("### 2️⃣ Location Performance Report")
    st.caption("Total revenue, order volume, and average rating grouped by US state.")

    loc_df = location_report(df)
    st.dataframe(loc_df.to_pandas(), use_container_width=True, height=300)

    st.divider()

    # ── Report 3: Category & Item Summary ───────────────────────────────────
    st.markdown("### 3️⃣ Category & Item Summary Report")
    st.caption("Revenue, average purchase amount, and item count by category and product.")

    cat_df = category_report(df)
    st.dataframe(cat_df.to_pandas(), use_container_width=True, height=320)

    st.divider()

    # ── Report 4: Demographic & Payment Breakdown ────────────────────────────
    st.markdown("### 4️⃣ Customer Demographic & Payment Breakdown")
    st.caption("Total spending matrix grouped by gender, subscription status, and payment method.")

    demo_df = demographic_report(df)
    st.dataframe(demo_df.to_pandas(), use_container_width=True, height=320)


# ---------------------------------------------------------------------------
# Tab 2 Helper: Visual Insights
# ---------------------------------------------------------------------------

def _render_visual_insights(df: pl.DataFrame) -> None:
    """
    Render global filters and all six interactive Plotly charts inside Tab 2.

    Global Filters (apply to all charts in this tab):
        - Location multi-select
        - Category multi-select
        - Season multi-select

    Charts:
        1. Top Revenue Generating Locations (horizontal bar)
        2. Customer Distribution by Location (vertical bar)
        3. Revenue vs Category Breakdown (donut)
        4. Seasonal Sales Trend (grouped bar)
        5. Payment Method Preference (pie)
        6. Customer Age Distribution vs Spending (scatter)
    """

    # ── Global Filters ───────────────────────────────────────────────────────
    st.markdown("#### 🌐 Global Filters")
    gf_col1, gf_col2, gf_col3 = st.columns(3)

    all_locations = sorted(df["Location"].unique().to_list())
    sel_locations = gf_col1.multiselect(
        "📍 Location",
        options=all_locations,
        default=all_locations,
        key="vis_location",
    )

    all_categories = sorted(df["Category"].unique().to_list())
    sel_categories = gf_col2.multiselect(
        "🏷️ Category",
        options=all_categories,
        default=all_categories,
        key="vis_category",
    )

    all_seasons = sorted(df["Season"].unique().to_list())
    sel_seasons = gf_col3.multiselect(
        "🍂 Season",
        options=all_seasons,
        default=all_seasons,
        key="vis_season",
    )

    # Apply global filters to the DataFrame before computing chart data.
    vdf = df
    if sel_locations:
        vdf = vdf.filter(pl.col("Location").is_in(sel_locations))
    if sel_categories:
        vdf = vdf.filter(pl.col("Category").is_in(sel_categories))
    if sel_seasons:
        vdf = vdf.filter(pl.col("Season").is_in(sel_seasons))

    # Guard: show a warning if filters produce an empty result set.
    if vdf.height == 0:
        st.warning("⚠️ No data matches the selected filters. Please broaden your selection.")
        return

    st.divider()

    # ── Row 1: Top Locations + Customer Distribution ──────────────────────────
    chart_row1_left, chart_row1_right = st.columns(2)

    with chart_row1_left:
        top_loc_data = top_locations_data(vdf, top_n=15)
        st.plotly_chart(
            chart_top_locations(top_loc_data),
            use_container_width=True,
        )

    with chart_row1_right:
        cust_dist_data = customer_distribution_data(vdf)
        st.plotly_chart(
            chart_customer_distribution(cust_dist_data),
            use_container_width=True,
        )

    st.divider()

    # ── Row 2: Revenue Donut + Seasonal Sales ────────────────────────────────
    chart_row2_left, chart_row2_right = st.columns(2)

    with chart_row2_left:
        rev_cat_data = revenue_by_category_data(vdf)
        st.plotly_chart(
            chart_revenue_by_category(rev_cat_data),
            use_container_width=True,
        )

    with chart_row2_right:
        seas_data = seasonal_sales_data(vdf)
        st.plotly_chart(
            chart_seasonal_sales(seas_data),
            use_container_width=True,
        )

    st.divider()

    # ── Row 3: Payment Methods + Age vs Spending ─────────────────────────────
    chart_row3_left, chart_row3_right = st.columns(2)

    with chart_row3_left:
        pay_data = payment_method_data(vdf)
        st.plotly_chart(
            chart_payment_methods(pay_data),
            use_container_width=True,
        )

    with chart_row3_right:
        age_data = age_vs_spending_data(vdf)
        st.plotly_chart(
            chart_age_vs_spending(age_data),
            use_container_width=True,
        )


# ===========================================================================
# Main Entry Point
# ===========================================================================

def main() -> None:
    """
    Main function — initialises session state and routes to the correct page
    based on ``st.session_state['page']``.
    """
    _init_session_state()

    if st.session_state["page"] == "upload":
        render_upload_page()
    elif st.session_state["page"] == "dashboard":
        # Safety check: if session expired or df was lost, go back to upload.
        if st.session_state["df"] is None:
            st.session_state["page"] = "upload"
            st.rerun()
        else:
            render_dashboard_page()
    else:
        # Fallback for any unexpected state value.
        st.session_state["page"] = "upload"
        st.rerun()


if __name__ == "__main__":
    main()
