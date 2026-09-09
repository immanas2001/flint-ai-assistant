"""
Flint AI - Smart Visualization Engine

Automatically selects an appropriate chart type
based on the structure of a pandas DataFrame.

Explicit user requests should still be handled by
the existing chart engine.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd


# ============================================================
# HELPERS
# ============================================================

def normalize_column(
    column: Any
) -> str:

    return (
        str(column)
        .lower()
        .strip()
        .replace("_", " ")
        .replace("-", " ")
    )


def is_numeric_column(
    df: pd.DataFrame,
    column: str
) -> bool:

    return pd.api.types.is_numeric_dtype(
        df[column]
    )


def is_datetime_column(
    df: pd.DataFrame,
    column: str
) -> bool:

    if pd.api.types.is_datetime64_any_dtype(
        df[column]
    ):
        return True

    try:

        converted = pd.to_datetime(
            df[column],
            errors="coerce"
        )

        return (
            converted.notna().mean()
            >= 0.7
        )

    except Exception:

        return False


def get_numeric_columns(
    df: pd.DataFrame
) -> List[str]:

    return [

        column

        for column in df.columns

        if is_numeric_column(
            df,
            column
        )

    ]


def get_datetime_columns(
    df: pd.DataFrame
) -> List[str]:

    return [

        column

        for column in df.columns

        if is_datetime_column(
            df,
            column
        )

    ]


def get_categorical_columns(
    df: pd.DataFrame
) -> List[str]:

    result = []

    for column in df.columns:

        if is_numeric_column(
            df,
            column
        ):

            continue

        if is_datetime_column(
            df,
            column
        ):

            continue

        unique_count = (
            df[column]
            .dropna()
            .nunique()
        )

        # Suitable categorical columns.

        if (
            unique_count >= 2
            and unique_count <= 30
        ):

            result.append(
                column
            )

    return result


# ============================================================
# STOCK COLUMN DETECTION
# ============================================================

def find_column(
    df: pd.DataFrame,
    aliases: List[str]
) -> Optional[str]:

    aliases = [
        normalize_column(
            alias
        )
        for alias in aliases
    ]

    # Exact match.

    for column in df.columns:

        normalized = normalize_column(
            column
        )

        if normalized in aliases:

            return column

    # Partial match.

    for column in df.columns:

        normalized = normalize_column(
            column
        )

        for alias in aliases:

            if alias in normalized:

                return column

    return None


def find_stock_columns(
    df: pd.DataFrame
) -> Dict[str, Optional[str]]:

    return {

        "date":
            find_column(
                df,
                [
                    "date",
                    "datetime",
                    "timestamp",
                    "time",
                ],
            ),

        "open":
            find_column(
                df,
                [
                    "open",
                    "opening price",
                ],
            ),

        "high":
            find_column(
                df,
                [
                    "high",
                    "highest",
                    "high price",
                ],
            ),

        "low":
            find_column(
                df,
                [
                    "low",
                    "lowest",
                    "low price",
                ],
            ),

        "close":
            find_column(
                df,
                [
                    "close",
                    "closing price",
                    "adj close",
                    "adjusted close",
                ],
            ),

        "volume":
            find_column(
                df,
                [
                    "volume",
                    "trading volume",
                ],
            ),
    }


# ============================================================
# CHART TYPES
# ============================================================

CHART_LINE = "line"

CHART_BAR = "bar"

CHART_SCATTER = "scatter"

CHART_HISTOGRAM = "histogram"

CHART_HEATMAP = "heatmap"

CHART_PIE = "pie"


# ============================================================
# DATASET PROFILE
# ============================================================

def profile_dataset(
    df: pd.DataFrame
) -> Dict[str, Any]:

    numeric_columns = (
        get_numeric_columns(df)
    )

    datetime_columns = (
        get_datetime_columns(df)
    )

    categorical_columns = (
        get_categorical_columns(df)
    )

    stock_columns = (
        find_stock_columns(df)
    )

    return {

        "rows":
            int(len(df)),

        "columns":
            int(len(df.columns)),

        "numeric_columns":
            numeric_columns,

        "datetime_columns":
            datetime_columns,

        "categorical_columns":
            categorical_columns,

        "stock_columns":
            stock_columns,

    }


# ============================================================
# SMART CHART SELECTION
# ============================================================

def choose_chart(
    df: pd.DataFrame
) -> Dict[str, Any]:

    if df is None:

        return {

            "success": False,

            "error":
                "No dataset provided.",

        }

    if df.empty:

        return {

            "success": False,

            "error":
                "The dataset is empty.",

        }

    profile = profile_dataset(
        df
    )

    numeric = profile[
        "numeric_columns"
    ]

    dates = profile[
        "datetime_columns"
    ]

    categories = profile[
        "categorical_columns"
    ]

    stock = profile[
        "stock_columns"
    ]

    # ========================================================
    # 1. STOCK DATA
    # ========================================================

    if (
        stock.get("date")
        and stock.get("close")
    ):

        return {

            "success": True,

            "chart_type":
                CHART_LINE,

            "x_column":
                stock["date"],

            "y_column":
                stock["close"],

            "title":
                f"{stock['close']} Over Time",

            "reason":
                "A date/time column and stock "
                "price column were detected.",

        }

    # ========================================================
    # 2. DATE + NUMERIC
    # ========================================================

    if (
        dates
        and numeric
    ):

        return {

            "success": True,

            "chart_type":
                CHART_LINE,

            "x_column":
                dates[0],

            "y_column":
                numeric[0],

            "title":
                f"{numeric[0]} Over Time",

            "reason":
                "A time column and numeric "
                "column were detected.",

        }

    # ========================================================
    # 3. CATEGORY + NUMERIC
    # ========================================================

    if (
        categories
        and numeric
    ):

        category = categories[0]

        # Limit category chart size.

        unique_count = (
            df[category]
            .dropna()
            .nunique()
        )

        if unique_count <= 15:

            return {

                "success": True,

                "chart_type":
                    CHART_BAR,

                "x_column":
                    category,

                "y_column":
                    numeric[0],

                "title":
                    f"{numeric[0]} by {category}",

                "reason":
                    "A categorical column and "
                    "numeric column were detected.",

            }

    # ========================================================
    # 4. TWO NUMERIC COLUMNS
    # ========================================================

    if len(numeric) >= 2:

        return {

            "success": True,

            "chart_type":
                CHART_SCATTER,

            "x_column":
                numeric[0],

            "y_column":
                numeric[1],

            "title":
                f"{numeric[1]} vs {numeric[0]}",

            "reason":
                "Multiple numeric columns were "
                "detected, making a scatter plot "
                "useful for relationship analysis.",

        }

    # ========================================================
    # 5. ONE NUMERIC COLUMN
    # ========================================================

    if len(numeric) == 1:

        return {

            "success": True,

            "chart_type":
                CHART_HISTOGRAM,

            "x_column":
                numeric[0],

            "y_column":
                None,

            "title":
                f"Distribution of {numeric[0]}",

            "reason":
                "A single numeric column was "
                "detected.",

        }

    # ========================================================
    # 6. CATEGORICAL ONLY
    # ========================================================

    if categories:

        category = categories[0]

        unique_count = (
            df[category]
            .dropna()
            .nunique()
        )

        if unique_count <= 10:

            return {

                "success": True,

                "chart_type":
                    CHART_PIE,

                "x_column":
                    category,

                "y_column":
                    None,

                "title":
                    f"Distribution of {category}",

                "reason":
                    "A small categorical column "
                    "was detected.",

            }

    # ========================================================
    # 7. FALLBACK
    # ========================================================

    return {

        "success": False,

        "error":
            "No suitable visualization "
            "could be determined.",

    }


# ============================================================
# BUILD CHART INSTRUCTION
# ============================================================

def build_chart_instruction(
    selection: Dict[str, Any]
) -> str:

    if not selection.get(
        "success",
        False
    ):

        return ""

    chart_type = selection[
        "chart_type"
    ]

    x_column = selection.get(
        "x_column"
    )

    y_column = selection.get(
        "y_column"
    )

    title = selection.get(
        "title"
    )

    if chart_type == CHART_LINE:

        return (
            "Create an interactive Plotly "
            "line chart. "
            f"Use `{x_column}` as the X axis "
            f"and `{y_column}` as the Y axis. "
            f"Title: `{title}`."
        )

    if chart_type == CHART_BAR:

        return (
            "Create an interactive Plotly "
            "bar chart. "
            f"Use `{x_column}` as the category "
            f"axis and `{y_column}` as the value. "
            f"Title: `{title}`."
        )

    if chart_type == CHART_SCATTER:

        return (
            "Create an interactive Plotly "
            "scatter plot. "
            f"Use `{x_column}` as the X axis "
            f"and `{y_column}` as the Y axis. "
            f"Title: `{title}`."
        )

    if chart_type == CHART_HISTOGRAM:

        return (
            "Create an interactive Plotly "
            "histogram. "
            f"Use `{x_column}` as the numeric "
            f"column. "
            f"Title: `{title}`."
        )

    if chart_type == CHART_PIE:

        return (
            "Create an interactive Plotly "
            "pie chart. "
            f"Use `{x_column}` as the category "
            f"column and show the frequency "
            f"of each category. "
            f"Title: `{title}`."
        )

    if chart_type == CHART_HEATMAP:

        return (
            "Create an interactive Plotly "
            "correlation heatmap using all "
            "numeric columns."
        )

    return ""


# ============================================================
# MAIN FUNCTION
# ============================================================

def smart_visualization(
    df: pd.DataFrame
) -> Dict[str, Any]:

    selection = choose_chart(
        df
    )

    if not selection.get(
        "success",
        False
    ):

        return selection

    selection[
        "instruction"
    ] = build_chart_instruction(
        selection
    )

    return selection


# ============================================================
# END
# ============================================================