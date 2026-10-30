"""
analysis.py
===========
All Polars-based data transformation, aggregation, and KPI calculation logic
for the Customer Shopping Analytics Dashboard.

Responsibilities:
    - Compute the four top-level KPI values shown on Page 2.
    - Apply interactive user filters (age, category, gender, purchase amount).
    - Generate aggregated summary DataFrames for the four Table Report sections.

All functions accept a Polars DataFrame and return either a scalar value or
a Polars DataFrame ready for display in Streamlit via ``st.dataframe()``.
"""

import polars as pl


# ---------------------------------------------------------------------------
# 1.  KPI Calculations
# ---------------------------------------------------------------------------

def compute_kpis(df: pl.DataFrame) -> dict[str, float]:
    """
    Compute the four headline KPI metrics displayed at the top of the dashboard.

    Args:
        df: The validated and type-coerced customer shopping DataFrame.

    Returns:
        A dictionary with keys:
            - ``total_revenue``       : Sum of 'Purchase Amount (USD)'.
            - ``total_customers``     : Unique count of 'Customer ID'.
            - ``avg_order_value``     : Mean of 'Purchase Amount (USD)'.
            - ``avg_review_rating``   : Mean of 'Review Rating'.
    """
    total_revenue = df["Purchase Amount (USD)"].cast(pl.Float64).sum()
    total_customers = df["Customer ID"].n_unique()
    avg_order_value = df["Purchase Amount (USD)"].cast(pl.Float64).mean()
    avg_review_rating = df["Review Rating"].cast(pl.Float64).mean()

    return {
        "total_revenue": round(total_revenue, 2),
        "total_customers": total_customers,
        "avg_order_value": round(avg_order_value, 2),
        "avg_review_rating": round(avg_review_rating, 2),
    }


# ---------------------------------------------------------------------------
# 2.  Interactive Filtering
# ---------------------------------------------------------------------------

def filter_data(
    df: pl.DataFrame,
    age_range: tuple[int, int] | None = None,
    categories: list[str] | None = None,
    genders: list[str] | None = None,
    amount_range: tuple[float, float] | None = None,
) -> pl.DataFrame:
    """
    Apply user-selected filters to the DataFrame for the Filtered Raw Data table.

    Args:
        df:            The full validated DataFrame.
        age_range:     Tuple of (min_age, max_age). Filters the 'Age' column.
        categories:    List of category strings. Filters the 'Category' column.
        genders:       List of gender strings. Filters the 'Gender' column.
        amount_range:  Tuple of (min_amount, max_amount). Filters 'Purchase Amount (USD)'.

    Returns:
        A filtered Polars DataFrame.
    """
    filtered = df

    # ── Age filter ──────────────────────────────────────────────────────────
    if age_range is not None:
        min_age, max_age = age_range
        filtered = filtered.filter(
            (pl.col("Age").cast(pl.Int64) >= min_age) &
            (pl.col("Age").cast(pl.Int64) <= max_age)
        )

    # ── Category filter ──────────────────────────────────────────────────────
    if categories:
        filtered = filtered.filter(pl.col("Category").is_in(categories))

    # ── Gender filter ────────────────────────────────────────────────────────
    if genders:
        filtered = filtered.filter(pl.col("Gender").is_in(genders))

    # ── Purchase amount filter ───────────────────────────────────────────────
    if amount_range is not None:
        min_amt, max_amt = amount_range
        filtered = filtered.filter(
            (pl.col("Purchase Amount (USD)").cast(pl.Float64) >= min_amt) &
            (pl.col("Purchase Amount (USD)").cast(pl.Float64) <= max_amt)
        )

    return filtered


# ---------------------------------------------------------------------------
# 3.  Table Report Aggregations
# ---------------------------------------------------------------------------

def location_report(df: pl.DataFrame) -> pl.DataFrame:
    """
    Aggregate sales performance grouped by US state / city Location.

    Columns returned:
        - Location
        - Total Revenue ($)
        - Total Orders
        - Average Rating

    Args:
        df: Validated customer shopping DataFrame.

    Returns:
        A Polars DataFrame sorted by Total Revenue descending.
    """
    report = (
        df
        .with_columns([
            pl.col("Purchase Amount (USD)").cast(pl.Float64),
            pl.col("Review Rating").cast(pl.Float64),
        ])
        .group_by("Location")
        .agg([
            pl.col("Purchase Amount (USD)").sum().alias("Total Revenue ($)"),
            pl.col("Customer ID").count().alias("Total Orders"),
            pl.col("Review Rating").mean().round(2).alias("Average Rating"),
        ])
        .sort("Total Revenue ($)", descending=True)
    )
    return report


def category_report(df: pl.DataFrame) -> pl.DataFrame:
    """
    Aggregate revenue and item metrics grouped by Category and Item Purchased.

    Columns returned:
        - Category
        - Item Purchased
        - Total Revenue ($)
        - Avg Purchase Amount ($)
        - Total Items Sold

    Args:
        df: Validated customer shopping DataFrame.

    Returns:
        A Polars DataFrame sorted by Category, then Total Revenue descending.
    """
    report = (
        df
        .with_columns(
            pl.col("Purchase Amount (USD)").cast(pl.Float64)
        )
        .group_by(["Category", "Item Purchased"])
        .agg([
            pl.col("Purchase Amount (USD)").sum().round(2).alias("Total Revenue ($)"),
            pl.col("Purchase Amount (USD)").mean().round(2).alias("Avg Purchase Amount ($)"),
            pl.col("Customer ID").count().alias("Total Items Sold"),
        ])
        .sort(["Category", "Total Revenue ($)"], descending=[False, True])
    )
    return report


def demographic_report(df: pl.DataFrame) -> pl.DataFrame:
    """
    Aggregate total spending grouped by Gender, Subscription Status, and Payment Method.

    Columns returned:
        - Gender
        - Subscription Status
        - Payment Method
        - Total Spending ($)
        - Transaction Count

    Args:
        df: Validated customer shopping DataFrame.

    Returns:
        A Polars DataFrame sorted by Total Spending descending.
    """
    report = (
        df
        .with_columns(
            pl.col("Purchase Amount (USD)").cast(pl.Float64)
        )
        .group_by(["Gender", "Subscription Status", "Payment Method"])
        .agg([
            pl.col("Purchase Amount (USD)").sum().round(2).alias("Total Spending ($)"),
            pl.col("Customer ID").count().alias("Transaction Count"),
        ])
        .sort("Total Spending ($)", descending=True)
    )
    return report


# ---------------------------------------------------------------------------
# 4.  Visual Insights Data Prep (used by visualization.py)
# ---------------------------------------------------------------------------

def top_locations_data(df: pl.DataFrame, top_n: int = 15) -> pl.DataFrame:
    """
    Return the top N locations ranked by total revenue.

    Args:
        df:    Validated DataFrame.
        top_n: How many top locations to return. Default is 15.

    Returns:
        A Polars DataFrame with columns ['Location', 'Total Revenue ($)'].
    """
    return (
        df
        .with_columns(pl.col("Purchase Amount (USD)").cast(pl.Float64))
        .group_by("Location")
        .agg(pl.col("Purchase Amount (USD)").sum().round(2).alias("Total Revenue ($)"))
        .sort("Total Revenue ($)", descending=True)
        .head(top_n)
    )


def customer_distribution_data(df: pl.DataFrame) -> pl.DataFrame:
    """
    Return customer count (unique Customer ID) per location.

    Args:
        df: Validated DataFrame.

    Returns:
        A Polars DataFrame with columns ['Location', 'Customer Count'].
    """
    return (
        df
        .group_by("Location")
        .agg(pl.col("Customer ID").n_unique().alias("Customer Count"))
        .sort("Customer Count", descending=True)
    )


def revenue_by_category_data(df: pl.DataFrame) -> pl.DataFrame:
    """
    Return total revenue aggregated by product Category.

    Args:
        df: Validated DataFrame.

    Returns:
        A Polars DataFrame with columns ['Category', 'Total Revenue ($)'].
    """
    return (
        df
        .with_columns(pl.col("Purchase Amount (USD)").cast(pl.Float64))
        .group_by("Category")
        .agg(pl.col("Purchase Amount (USD)").sum().round(2).alias("Total Revenue ($)"))
        .sort("Total Revenue ($)", descending=True)
    )


def seasonal_sales_data(df: pl.DataFrame) -> pl.DataFrame:
    """
    Return revenue broken down by Season and Category for grouped bar chart.

    Args:
        df: Validated DataFrame.

    Returns:
        A Polars DataFrame with columns ['Season', 'Category', 'Total Revenue ($)'].
    """
    return (
        df
        .with_columns(pl.col("Purchase Amount (USD)").cast(pl.Float64))
        .group_by(["Season", "Category"])
        .agg(pl.col("Purchase Amount (USD)").sum().round(2).alias("Total Revenue ($)"))
        .sort("Season")
    )


def payment_method_data(df: pl.DataFrame) -> pl.DataFrame:
    """
    Return transaction volume (count) per Payment Method.

    Args:
        df: Validated DataFrame.

    Returns:
        A Polars DataFrame with columns ['Payment Method', 'Transaction Count'].
    """
    return (
        df
        .group_by("Payment Method")
        .agg(pl.col("Customer ID").count().alias("Transaction Count"))
        .sort("Transaction Count", descending=True)
    )


def age_vs_spending_data(df: pl.DataFrame) -> pl.DataFrame:
    """
    Return per-customer Age and Purchase Amount for a scatter plot.

    Args:
        df: Validated DataFrame.

    Returns:
        A Polars DataFrame with columns ['Age', 'Purchase Amount (USD)', 'Category'].
    """
    return (
        df
        .with_columns([
            pl.col("Age").cast(pl.Int64),
            pl.col("Purchase Amount (USD)").cast(pl.Float64),
        ])
        .select(["Age", "Purchase Amount (USD)", "Category", "Gender"])
    )
