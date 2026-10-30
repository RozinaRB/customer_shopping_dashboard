"""
validation.py
=============
Handles CSV file parsing, data diagnostics, and strict 18-column schema
validation for the Customer Shopping Analytics Dashboard.

Responsibilities:
    - Parse an uploaded Streamlit file object into a Polars DataFrame.
    - Compute basic dataset diagnostics (row count, column count, null rows, numeric columns).
    - Validate that all 18 required columns are present and that critical numeric
      columns contain compatible data types.
    - Return structured error messages for display in the Streamlit UI.
"""

import io
from typing import Any

import polars as pl

# ---------------------------------------------------------------------------
# 1.  Schema Definition
# ---------------------------------------------------------------------------

# The exact 18 column names required by the dataset.
REQUIRED_COLUMNS: list[str] = [
    "Customer ID",
    "Age",
    "Gender",
    "Item Purchased",
    "Category",
    "Purchase Amount (USD)",
    "Location",
    "Size",
    "Color",
    "Season",
    "Review Rating",
    "Subscription Status",
    "Shipping Type",
    "Discount Applied",
    "Promo Code Used",
    "Previous Purchases",
    "Payment Method",
    "Frequency of Purchases",
]

# Columns that MUST be numeric for KPI calculations and chart logic.
NUMERIC_COLUMNS: list[str] = [
    "Age",
    "Purchase Amount (USD)",
    "Review Rating",
    "Previous Purchases",
]

# Column that MUST be non-null (used for customer count KPI).
NON_NULL_COLUMNS: list[str] = ["Customer ID"]


# ---------------------------------------------------------------------------
# 2.  File Parsing
# ---------------------------------------------------------------------------

def parse_uploaded_file(uploaded_file: Any) -> tuple[pl.DataFrame | None, str | None]:
    """
    Parse a Streamlit UploadedFile object into a Polars DataFrame.

    Args:
        uploaded_file: The file object returned by ``st.file_uploader``.

    Returns:
        A tuple of ``(dataframe, error_message)``.
        - On success: ``(DataFrame, None)``
        - On failure: ``(None, error_string)``
    """
    if uploaded_file is None:
        return None, "No file provided."

    # Only accept CSV files — guard against wrong extension uploads.
    if not uploaded_file.name.lower().endswith(".csv"):
        return None, (
            f"❌ Invalid file type: '{uploaded_file.name}'. "
            "Please upload a `.csv` file."
        )

    try:
        # Read raw bytes and hand them to Polars via an in-memory buffer.
        raw_bytes = uploaded_file.read()
        df = pl.read_csv(io.BytesIO(raw_bytes), infer_schema_length=500)
        return df, None

    except pl.exceptions.ComputeError as exc:
        return None, f"❌ CSV parse error: {exc}"
    except Exception as exc:  # noqa: BLE001
        return None, f"❌ Unexpected error while reading file: {exc}"


# ---------------------------------------------------------------------------
# 3.  Data Diagnostics
# ---------------------------------------------------------------------------

def get_diagnostics(df: pl.DataFrame) -> dict[str, int]:
    """
    Compute basic summary statistics for an uploaded dataset.

    Args:
        df: A successfully parsed Polars DataFrame.

    Returns:
        A dictionary with keys:
            - ``total_rows``        : Number of data rows.
            - ``total_columns``     : Number of columns.
            - ``missing_rows``      : Rows containing at least one null value.
            - ``numeric_columns``   : Count of columns Polars inferred as numeric.
    """
    total_rows = df.height
    total_columns = df.width

    # Count rows where ANY column contains a null value.
    missing_rows = df.filter(
        pl.fold(
            acc=pl.lit(False),
            function=lambda acc, s: acc | s.is_null(),
            exprs=pl.all(),
        )
    ).height

    # Count columns whose Polars dtype is numeric (Int* or Float*).
    numeric_columns = sum(
        1
        for dtype in df.dtypes
        if dtype in (
            pl.Int8, pl.Int16, pl.Int32, pl.Int64,
            pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64,
            pl.Float32, pl.Float64,
        )
    )

    return {
        "total_rows": total_rows,
        "total_columns": total_columns,
        "missing_rows": missing_rows,
        "numeric_columns": numeric_columns,
    }


# ---------------------------------------------------------------------------
# 4.  Schema Validation
# ---------------------------------------------------------------------------

def validate_schema(df: pl.DataFrame) -> list[str]:
    """
    Validate the uploaded DataFrame against the strict 18-column schema.

    Checks performed (in order):
        1. All 18 required columns are present.
        2. Critical numeric columns contain numeric data (attempts cast if string).
        3. ``Customer ID`` column has no fully-null values.

    Args:
        df: Polars DataFrame to validate.

    Returns:
        A list of human-readable error strings.
        An empty list means validation passed successfully.
    """
    errors: list[str] = []
    actual_columns = set(df.columns)

    # ── Check 1: Missing required columns ───────────────────────────────────
    missing = [col for col in REQUIRED_COLUMNS if col not in actual_columns]
    if missing:
        for col in missing:
            errors.append(f"❌ Missing required column: **'{col}'**")

    # Stop early — further checks are meaningless without the right columns.
    if errors:
        return errors

    # ── Check 2: Numeric compatibility for critical columns ─────────────────
    for col in NUMERIC_COLUMNS:
        dtype = df[col].dtype

        is_numeric = dtype in (
            pl.Int8, pl.Int16, pl.Int32, pl.Int64,
            pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64,
            pl.Float32, pl.Float64,
        )

        if not is_numeric:
            # Attempt a safe cast to Float64 to see if values are numeric strings.
            try:
                df[col].cast(pl.Float64)
                # Cast succeeded — data is fine, just stored as string.
            except Exception:  # noqa: BLE001
                errors.append(
                    f"❌ Column **'{col}'** must be numeric "
                    f"(found type `{dtype}` with non-numeric values)."
                )

    # ── Check 3: Customer ID must not be entirely null ───────────────────────
    for col in NON_NULL_COLUMNS:
        if df[col].null_count() == df.height:
            errors.append(
                f"❌ Column **'{col}'** contains only null values. "
                "A valid customer identifier is required."
            )

    # ── Check 4: Purchase Amount must be positive (spot-check) ──────────────
    purchase_col = "Purchase Amount (USD)"
    if purchase_col in actual_columns:
        try:
            purchase_series = df[purchase_col].cast(pl.Float64)
            negative_count = purchase_series.filter(purchase_series < 0).len()
            if negative_count > 0:
                errors.append(
                    f"⚠️  Column **'{purchase_col}'** contains {negative_count} "
                    "negative value(s). Expected positive monetary amounts."
                )
        except Exception:  # noqa: BLE001
            pass  # Already caught by numeric check above

    return errors


# ---------------------------------------------------------------------------
# 5.  Convenience: cast numeric-string columns after validation
# ---------------------------------------------------------------------------

def coerce_numeric_columns(df: pl.DataFrame) -> pl.DataFrame:
    """
    Cast any critical numeric columns that Polars read as strings into Float64.
    Call this AFTER ``validate_schema`` confirms the data is castable.

    Args:
        df: Validated Polars DataFrame.

    Returns:
        DataFrame with numeric columns properly typed.
    """
    casts = {}
    for col in NUMERIC_COLUMNS:
        if df[col].dtype not in (
            pl.Int8, pl.Int16, pl.Int32, pl.Int64,
            pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64,
            pl.Float32, pl.Float64,
        ):
            casts[col] = pl.col(col).cast(pl.Float64)

    if casts:
        df = df.with_columns(list(casts.values()))

    return df
