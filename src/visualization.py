"""
visualization.py
================
Plotly chart factory functions for the Customer Shopping Analytics Dashboard.

Each function:
    - Accepts a Polars DataFrame (pre-aggregated by analysis.py).
    - Returns a Plotly Figure object ready to pass to ``st.plotly_chart()``.
    - Uses a consistent color palette and transparent background so charts
      adapt naturally to Streamlit's light/dark themes.

Chart index:
    1. chart_top_locations()           — Horizontal bar: top locations by revenue
    2. chart_customer_distribution()   — Vertical bar: customer count per location
    3. chart_revenue_by_category()     — Donut: revenue share by category
    4. chart_seasonal_sales()          — Grouped bar: revenue by season & category
    5. chart_payment_methods()         — Pie: transaction volume by payment method
    6. chart_age_vs_spending()         — Scatter: age vs purchase amount
"""

import polars as pl
import plotly.express as px
import plotly.graph_objects as go

# ---------------------------------------------------------------------------
# Shared Style Helpers
# ---------------------------------------------------------------------------

# A bold, accessible qualitative color palette used across all charts.
COLOR_PALETTE = px.colors.qualitative.Bold

# Transparent background so charts blend with Streamlit's theme.
_TRANSPARENT_BG = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")

# Shared axis line styling for a clean, minimal look.
_AXIS_STYLE = dict(showgrid=True, gridcolor="rgba(180,180,180,0.2)", zeroline=False)


def _apply_base_layout(fig: go.Figure, title: str, height: int = 420) -> go.Figure:
    """
    Apply consistent base layout (title, font, background, margins) to any Figure.

    Args:
        fig:    The Plotly Figure to style.
        title:  Chart title string.
        height: Chart height in pixels. Default 420.

    Returns:
        The same Figure with updated layout (mutated in-place).
    """
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color="#333")),
        height=height,
        margin=dict(l=40, r=40, t=60, b=40),
        font=dict(family="Inter, Arial, sans-serif", size=12),
        legend=dict(bgcolor="rgba(0,0,0,0)", borderwidth=0),
        **_TRANSPARENT_BG,
    )
    return fig


# ---------------------------------------------------------------------------
# 1.  Top Revenue Locations — Horizontal Bar Chart
# ---------------------------------------------------------------------------

def chart_top_locations(df: pl.DataFrame) -> go.Figure:
    """
    Render a horizontal bar chart of the top locations ranked by total revenue.

    Args:
        df: DataFrame with columns ['Location', 'Total Revenue ($)'].
            Expected to already be sorted descending by revenue.

    Returns:
        A Plotly Figure.
    """
    # Convert to pandas for Plotly Express compatibility.
    pdf = df.to_pandas()

    fig = px.bar(
        pdf,
        x="Total Revenue ($)",
        y="Location",
        orientation="h",
        color="Total Revenue ($)",
        color_continuous_scale="Blues",
        text="Total Revenue ($)",
    )

    fig.update_traces(
        texttemplate="$%{text:,.0f}",
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Revenue: $%{x:,.2f}<extra></extra>",
    )

    fig.update_layout(
        yaxis=dict(categoryorder="total ascending"),  # Highest bar at top
        xaxis=dict(**_AXIS_STYLE, tickprefix="$", tickformat=",.0f"),
        coloraxis_showscale=False,
    )

    _apply_base_layout(fig, "🏆 Top Revenue Generating Locations", height=500)
    return fig


# ---------------------------------------------------------------------------
# 2.  Customer Distribution by Location — Vertical Bar Chart
# ---------------------------------------------------------------------------

def chart_customer_distribution(df: pl.DataFrame) -> go.Figure:
    """
    Render a vertical bar chart showing unique customer count per location.

    Args:
        df: DataFrame with columns ['Location', 'Customer Count'].

    Returns:
        A Plotly Figure.
    """
    pdf = df.to_pandas()

    fig = px.bar(
        pdf,
        x="Location",
        y="Customer Count",
        color="Customer Count",
        color_continuous_scale="Teal",
        text="Customer Count",
    )

    fig.update_traces(
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Customers: %{y:,}<extra></extra>",
    )

    fig.update_layout(
        xaxis=dict(tickangle=-45, **_AXIS_STYLE),
        yaxis=dict(**_AXIS_STYLE),
        coloraxis_showscale=False,
    )

    _apply_base_layout(fig, "👥 Customer Distribution by Location", height=460)
    return fig


# ---------------------------------------------------------------------------
# 3.  Revenue by Category — Donut Chart
# ---------------------------------------------------------------------------

def chart_revenue_by_category(df: pl.DataFrame) -> go.Figure:
    """
    Render a donut chart showing revenue share across product categories.

    Args:
        df: DataFrame with columns ['Category', 'Total Revenue ($)'].

    Returns:
        A Plotly Figure.
    """
    pdf = df.to_pandas()

    fig = go.Figure(
        go.Pie(
            labels=pdf["Category"],
            values=pdf["Total Revenue ($)"],
            hole=0.45,           # Creates the donut shape.
            marker_colors=COLOR_PALETTE,
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>Revenue: $%{value:,.2f}<br>Share: %{percent}<extra></extra>",
        )
    )

    # Centre annotation showing the chart type.
    fig.update_layout(
        annotations=[
            dict(text="Revenue", x=0.5, y=0.5, font_size=15, showarrow=False)
        ]
    )

    _apply_base_layout(fig, "🍩 Revenue vs Category Breakdown")
    return fig


# ---------------------------------------------------------------------------
# 4.  Seasonal Sales Trend — Grouped Bar Chart
# ---------------------------------------------------------------------------

def chart_seasonal_sales(df: pl.DataFrame) -> go.Figure:
    """
    Render a grouped bar chart comparing revenue across seasons, broken down
    by product category.

    Args:
        df: DataFrame with columns ['Season', 'Category', 'Total Revenue ($)'].

    Returns:
        A Plotly Figure.
    """
    pdf = df.to_pandas()

    # Define a fixed season order for consistent x-axis display.
    season_order = ["Spring", "Summer", "Fall", "Winter"]

    fig = px.bar(
        pdf,
        x="Season",
        y="Total Revenue ($)",
        color="Category",
        barmode="group",
        color_discrete_sequence=COLOR_PALETTE,
        category_orders={"Season": season_order},
        text_auto=".2s",
    )

    fig.update_traces(
        hovertemplate="<b>%{x}</b><br>Category: %{fullData.name}<br>Revenue: $%{y:,.2f}<extra></extra>"
    )

    fig.update_layout(
        xaxis=dict(**_AXIS_STYLE),
        yaxis=dict(**_AXIS_STYLE, tickprefix="$", tickformat=",.0f"),
    )

    _apply_base_layout(fig, "📅 Seasonal Sales Trend by Category")
    return fig


# ---------------------------------------------------------------------------
# 5.  Payment Method Preference — Pie Chart
# ---------------------------------------------------------------------------

def chart_payment_methods(df: pl.DataFrame) -> go.Figure:
    """
    Render a pie chart showing the distribution of payment method usage
    by total transaction volume.

    Args:
        df: DataFrame with columns ['Payment Method', 'Transaction Count'].

    Returns:
        A Plotly Figure.
    """
    pdf = df.to_pandas()

    fig = go.Figure(
        go.Pie(
            labels=pdf["Payment Method"],
            values=pdf["Transaction Count"],
            marker_colors=COLOR_PALETTE,
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>Transactions: %{value:,}<br>Share: %{percent}<extra></extra>",
        )
    )

    _apply_base_layout(fig, "💳 Payment Method Preference")
    return fig


# ---------------------------------------------------------------------------
# 6.  Customer Age Distribution vs Spending — Scatter Plot
# ---------------------------------------------------------------------------

def chart_age_vs_spending(df: pl.DataFrame) -> go.Figure:
    """
    Render a scatter plot showing the relationship between customer age and
    purchase amount, colour-coded by product category.

    Args:
        df: DataFrame with columns ['Age', 'Purchase Amount (USD)', 'Category', 'Gender'].

    Returns:
        A Plotly Figure.
    """
    pdf = df.to_pandas()

    fig = px.scatter(
        pdf,
        x="Age",
        y="Purchase Amount (USD)",
        color="Category",
        symbol="Gender",
        opacity=0.65,
        color_discrete_sequence=COLOR_PALETTE,
        hover_data={"Age": True, "Purchase Amount (USD)": True, "Category": True, "Gender": True},
    )

    fig.update_traces(
        marker=dict(size=7),
        hovertemplate=(
            "<b>Age:</b> %{x}<br>"
            "<b>Spend:</b> $%{y:.2f}<br>"
            "<b>Category:</b> %{customdata[0]}<br>"
            "<b>Gender:</b> %{customdata[1]}<extra></extra>"
        ),
    )

    fig.update_layout(
        xaxis=dict(**_AXIS_STYLE, title="Customer Age"),
        yaxis=dict(**_AXIS_STYLE, title="Purchase Amount (USD)", tickprefix="$"),
    )

    _apply_base_layout(fig, "📊 Customer Age Distribution vs Spending", height=460)
    return fig
