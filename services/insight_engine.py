"""
Flint AI - Insight Engine

Generates human-readable insights from a pandas DataFrame.

This module is independent from chat.py and ai_data_analyst.py.
It can be used with CSV, Excel, and other tabular datasets.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd
import numpy as np


# ============================================================
# BASIC HELPERS
# ============================================================

def format_number(value: Any) -> str:

    try:

        if pd.isna(value):
            return "N/A"

        value = float(value)

        if value.is_integer():
            return f"{int(value):,}"

        return f"{value:,.2f}"

    except Exception:

        return str(value)


def format_percent(value: Any) -> str:

    try:

        return f"{float(value):.2f}%"

    except Exception:

        return "N/A"


def normalize(text: str) -> str:

    return (
        str(text)
        .lower()
        .strip()
        .replace("_", " ")
        .replace("-", " ")
    )


# ============================================================
# COLUMN DETECTION
# ============================================================

def find_date_column(
    df: pd.DataFrame
) -> Optional[str]:

    # First check column names.

    for column in df.columns:

        name = normalize(column)

        if any(
            word in name
            for word in [
                "date",
                "datetime",
                "timestamp",
                "time",
            ]
        ):

            try:

                converted = pd.to_datetime(
                    df[column],
                    errors="coerce"
                )

                if converted.notna().mean() >= 0.6:

                    return column

            except Exception:

                pass

    # Then inspect values.

    for column in df.columns:

        try:

            converted = pd.to_datetime(
                df[column],
                errors="coerce"
            )

            if converted.notna().mean() >= 0.8:

                return column

        except Exception:

            continue

    return None


def find_column(
    df: pd.DataFrame,
    aliases: List[str]
) -> Optional[str]:

    normalized_aliases = [
        normalize(alias)
        for alias in aliases
    ]

    # Exact match.

    for column in df.columns:

        name = normalize(column)

        if name in normalized_aliases:

            return column

    # Partial match.

    for column in df.columns:

        name = normalize(column)

        for alias in normalized_aliases:

            if alias in name:

                return column

    return None


def get_numeric_columns(
    df: pd.DataFrame
) -> List[str]:

    return [

        column

        for column in df.columns

        if pd.api.types.is_numeric_dtype(
            df[column]
        )

    ]


# ============================================================
# STOCK COLUMN DETECTION
# ============================================================

def get_stock_columns(
    df: pd.DataFrame
) -> Dict[str, Optional[str]]:

    return {

        "open": find_column(
            df,
            [
                "open",
                "opening",
                "open price",
            ]
        ),

        "high": find_column(
            df,
            [
                "high",
                "highest",
                "high price",
            ]
        ),

        "low": find_column(
            df,
            [
                "low",
                "lowest",
                "low price",
            ]
        ),

        "close": find_column(
            df,
            [
                "close",
                "closing",
                "close price",
                "adj close",
                "adjusted close",
            ]
        ),

        "volume": find_column(
            df,
            [
                "volume",
                "trading volume",
            ]
        ),

    }


# ============================================================
# DATA QUALITY
# ============================================================

def get_data_quality(
    df: pd.DataFrame
) -> Dict[str, Any]:

    missing = df.isna().sum()

    missing_columns = {}

    for column, count in missing.items():

        if count > 0:

            missing_columns[
                str(column)
            ] = int(count)

    duplicates = int(
        df.duplicated().sum()
    )

    return {

        "missing_total":
            int(missing.sum()),

        "missing_columns":
            missing_columns,

        "duplicate_rows":
            duplicates,

        "rows":
            int(len(df)),

        "columns":
            int(len(df.columns)),

    }


# ============================================================
# DATE ANALYSIS
# ============================================================

def get_date_analysis(
    df: pd.DataFrame
) -> Dict[str, Any]:

    date_column = find_date_column(
        df
    )

    if date_column is None:

        return {

            "available": False,

            "column": None,

        }

    dates = pd.to_datetime(
        df[date_column],
        errors="coerce"
    ).dropna()

    if dates.empty:

        return {

            "available": False,

            "column":
                date_column,

        }

    return {

        "available": True,

        "column":
            date_column,

        "start":
            str(dates.min()),

        "end":
            str(dates.max()),

        "days":
            int(
                (
                    dates.max()
                    -
                    dates.min()
                ).days
            ),

    }


# ============================================================
# NUMERIC SUMMARY
# ============================================================

def numeric_summary(
    df: pd.DataFrame
) -> Dict[str, Dict[str, float]]:

    result = {}

    for column in get_numeric_columns(
        df
    ):

        series = pd.to_numeric(
            df[column],
            errors="coerce"
        ).dropna()

        if series.empty:
            continue

        result[str(column)] = {

            "count":
                int(series.count()),

            "mean":
                float(series.mean()),

            "median":
                float(series.median()),

            "min":
                float(series.min()),

            "max":
                float(series.max()),

            "std":
                float(series.std()),

        }

    return result


# ============================================================
# TREND ANALYSIS
# ============================================================

def analyze_trend(
    df: pd.DataFrame
) -> Optional[Dict[str, Any]]:

    columns = get_stock_columns(
        df
    )

    close_column = columns.get(
        "close"
    )

    if close_column is None:

        numeric = get_numeric_columns(
            df
        )

        if not numeric:

            return None

        close_column = numeric[0]

    series = pd.to_numeric(
        df[close_column],
        errors="coerce"
    ).dropna()

    if len(series) < 2:

        return None

    first = float(
        series.iloc[0]
    )

    last = float(
        series.iloc[-1]
    )

    change = last - first

    if first != 0:

        percentage = (
            change / first
        ) * 100

    else:

        percentage = 0

    if percentage > 1:

        direction = "upward"

    elif percentage < -1:

        direction = "downward"

    else:

        direction = "relatively flat"

    return {

        "column":
            str(close_column),

        "start":
            first,

        "end":
            last,

        "change":
            change,

        "percentage":
            percentage,

        "direction":
            direction,

    }


# ============================================================
# HIGH / LOW ANALYSIS
# ============================================================

def analyze_extremes(
    df: pd.DataFrame
) -> Dict[str, Any]:

    columns = get_stock_columns(
        df
    )

    result = {}

    for key in [
        "close",
        "high",
        "low",
    ]:

        column = columns.get(
            key
        )

        if column is None:
            continue

        series = pd.to_numeric(
            df[column],
            errors="coerce"
        )

        if series.dropna().empty:
            continue

        max_index = series.idxmax()

        min_index = series.idxmin()

        result[key] = {

            "column":
                str(column),

            "maximum":
                float(
                    series.loc[max_index]
                ),

            "minimum":
                float(
                    series.loc[min_index]
                ),

            "max_index":
                str(max_index),

            "min_index":
                str(min_index),

        }

    return result


# ============================================================
# VOLATILITY
# ============================================================

def analyze_volatility(
    df: pd.DataFrame
) -> Optional[Dict[str, Any]]:

    columns = get_stock_columns(
        df
    )

    close_column = columns.get(
        "close"
    )

    if close_column is None:

        return None

    series = pd.to_numeric(
        df[close_column],
        errors="coerce"
    ).dropna()

    if len(series) < 2:

        return None

    std = float(
        series.std()
    )

    mean = float(
        series.mean()
    )

    if mean != 0:

        coefficient = (
            std / mean
        ) * 100

    else:

        coefficient = 0

    # Daily returns.

    returns = series.pct_change(
    ).dropna()

    if not returns.empty:

        return_std = float(
            returns.std()
        ) * 100

    else:

        return_std = 0

    return {

        "column":
            str(close_column),

        "standard_deviation":
            std,

        "mean":
            mean,

        "coefficient":
            coefficient,

        "return_volatility":
            return_std,

    }


# ============================================================
# VOLUME ANALYSIS
# ============================================================

def analyze_volume(
    df: pd.DataFrame
) -> Optional[Dict[str, Any]]:

    columns = get_stock_columns(
        df
    )

    volume_column = columns.get(
        "volume"
    )

    if volume_column is None:

        return None

    volume = pd.to_numeric(
        df[volume_column],
        errors="coerce"
    ).dropna()

    if volume.empty:

        return None

    mean = float(
        volume.mean()
    )

    maximum = float(
        volume.max()
    )

    if mean != 0:

        max_multiple = (
            maximum / mean
        )

    else:

        max_multiple = 0

    return {

        "column":
            str(volume_column),

        "average":
            mean,

        "maximum":
            maximum,

        "maximum_multiple":
            max_multiple,

    }


# ============================================================
# CORRELATION ANALYSIS
# ============================================================

def analyze_correlations(
    df: pd.DataFrame
) -> List[Dict[str, Any]]:

    numeric = get_numeric_columns(
        df
    )

    if len(numeric) < 2:

        return []

    correlation = df[
        numeric
    ].corr()

    results = []

    for i in range(
        len(numeric)
    ):

        for j in range(
            i + 1,
            len(numeric)
        ):

            column_a = numeric[i]

            column_b = numeric[j]

            value = correlation.loc[
                column_a,
                column_b
            ]

            if pd.isna(value):
                continue

            results.append({

                "column_a":
                    str(column_a),

                "column_b":
                    str(column_b),

                "correlation":
                    float(value),

            })

    results.sort(
        key=lambda x:
            abs(
                x["correlation"]
            ),
        reverse=True,
    )

    return results


# ============================================================
# INSIGHT GENERATOR
# ============================================================

def generate_insights(
    df: pd.DataFrame
) -> Dict[str, Any]:

    df = df.copy()

    # Remove completely empty rows/columns.

    df = df.dropna(
        axis=1,
        how="all"
    )

    df = df.dropna(
        axis=0,
        how="all"
    )

    if df.empty:

        return {

            "success": False,

            "error":
                "The dataset is empty.",

        }

    quality = get_data_quality(
        df
    )

    dates = get_date_analysis(
        df
    )

    numeric = numeric_summary(
        df
    )

    trend = analyze_trend(
        df
    )

    extremes = analyze_extremes(
        df
    )

    volatility = analyze_volatility(
        df
    )

    volume = analyze_volume(
        df
    )

    correlations = (
        analyze_correlations(
            df
        )
    )

    # ========================================================
    # HUMAN READABLE INSIGHTS
    # ========================================================

    insights = []

    # --------------------------------------------------------
    # Trend
    # --------------------------------------------------------

    if trend:

        direction = trend[
            "direction"
        ]

        percentage = trend[
            "percentage"
        ]

        column = trend[
            "column"
        ]

        if direction == "upward":

            insights.append(
                f"📈 **{column}** shows an "
                f"overall upward trend, "
                f"rising by "
                f"**{format_percent(percentage)}**."
            )

        elif direction == "downward":

            insights.append(
                f"📉 **{column}** shows an "
                f"overall downward trend, "
                f"falling by "
                f"**{format_percent(abs(percentage))}**."
            )

        else:

            insights.append(
                f"➡️ **{column}** remained "
                f"relatively stable over "
                f"the available period."
            )

    # --------------------------------------------------------
    # Highest / lowest
    # --------------------------------------------------------

    close_extreme = extremes.get(
        "close"
    )

    if close_extreme:

        insights.append(
            f"🏆 The highest "
            f"**{close_extreme['column']}** "
            f"was **"
            f"{format_number(close_extreme['maximum'])}"
            f"**, while the lowest was "
            f"**"
            f"{format_number(close_extreme['minimum'])}"
            f"**."
        )

    # --------------------------------------------------------
    # Volatility
    # --------------------------------------------------------

    if volatility:

        volatility_value = (
            volatility[
                "return_volatility"
            ]
        )

        if volatility_value >= 5:

            risk_text = "relatively high"

        elif volatility_value >= 2:

            risk_text = "moderate"

        else:

            risk_text = "relatively low"

        insights.append(
            f"📊 The estimated return "
            f"volatility is "
            f"**{format_percent(volatility_value)}**, "
            f"which is {risk_text}."
        )

    # --------------------------------------------------------
    # Volume
    # --------------------------------------------------------

    if volume:

        multiple = volume[
            "maximum_multiple"
        ]

        if multiple >= 2:

            insights.append(
                f"🔊 The maximum trading "
                f"volume was approximately "
                f"**{multiple:.1f}×** the "
                f"average volume, indicating "
                f"a notable volume spike."
            )

    # --------------------------------------------------------
    # Correlation
    # --------------------------------------------------------

    if correlations:

        strongest = correlations[0]

        correlation_value = (
            strongest[
                "correlation"
            ]
        )

        if abs(
            correlation_value
        ) >= 0.7:

            direction = (
                "positive"
                if correlation_value > 0
                else "negative"
            )

            insights.append(
                f"🔗 **"
                f"{strongest['column_a']}"
                f"** and **"
                f"{strongest['column_b']}"
                f"** have a strong "
                f"{direction} correlation "
                f"of **"
                f"{correlation_value:.2f}"
                f"**."
            )

    # --------------------------------------------------------
    # Data quality
    # --------------------------------------------------------

    if quality[
        "missing_total"
    ] > 0:

        insights.append(
            f"⚠️ The dataset contains "
            f"**"
            f"{quality['missing_total']:,}"
            f" missing values**, so "
            f"data cleaning may be "
            f"necessary."
        )

    else:

        insights.append(
            "✅ No missing values were "
            "detected."
        )

    if quality[
        "duplicate_rows"
    ] > 0:

        insights.append(
            f"⚠️ There are **"
            f"{quality['duplicate_rows']:,}"
            f" duplicate rows**."
        )

    else:

        insights.append(
            "✅ No duplicate rows "
            "were detected."
        )

    # ========================================================
    # FINAL RESULT
    # ========================================================

    return {

        "success": True,

        "overview": {

            "rows":
                quality["rows"],

            "columns":
                quality["columns"],

            "missing":
                quality["missing_total"],

            "duplicates":
                quality["duplicate_rows"],

        },

        "date_analysis":
            dates,

        "numeric_summary":
            numeric,

        "trend":
            trend,

        "extremes":
            extremes,

        "volatility":
            volatility,

        "volume":
            volume,

        "correlations":
            correlations,

        "insights":
            insights,

    }


# ============================================================
# MARKDOWN REPORT
# ============================================================

def generate_markdown_report(
    result: Dict[str, Any]
) -> str:

    if not result.get(
        "success",
        False
    ):

        return (
            "❌ Unable to generate "
            "dataset insights."
        )

    overview = result[
        "overview"
    ]

    lines = []

    # ========================================================
    # TITLE
    # ========================================================

    lines.append(
        "## 📊 Flint AI Data Analysis"
    )

    lines.append("")

    # ========================================================
    # OVERVIEW
    # ========================================================

    lines.append(
        "### Dataset Overview"
    )

    lines.append("")

    lines.append(
        f"- Rows: **"
        f"{overview['rows']:,}"
        f"**"
    )

    lines.append(
        f"- Columns: **"
        f"{overview['columns']:,}"
        f"**"
    )

    lines.append(
        f"- Missing values: **"
        f"{overview['missing']:,}"
        f"**"
    )

    lines.append(
        f"- Duplicate rows: **"
        f"{overview['duplicates']:,}"
        f"**"
    )

    # ========================================================
    # DATE
    # ========================================================

    date_info = result[
        "date_analysis"
    ]

    if date_info.get(
        "available"
    ):

        lines.append("")

        lines.append(
            "### 📅 Time Period"
        )

        lines.append("")

        lines.append(
            f"- Date column: "
            f"`{date_info['column']}`"
        )

        lines.append(
            f"- Start: "
            f"**{date_info['start']}**"
        )

        lines.append(
            f"- End: "
            f"**{date_info['end']}**"
        )

    # ========================================================
    # TREND
    # ========================================================

    trend = result.get(
        "trend"
    )

    if trend:

        lines.append("")

        lines.append(
            "### 📈 Trend"
        )

        lines.append("")

        lines.append(
            f"- Column: "
            f"`{trend['column']}`"
        )

        lines.append(
            f"- Starting value: "
            f"**"
            f"{format_number(trend['start'])}"
            f"**"
        )

        lines.append(
            f"- Ending value: "
            f"**"
            f"{format_number(trend['end'])}"
            f"**"
        )

        lines.append(
            f"- Change: "
            f"**"
            f"{format_number(trend['change'])}"
            f"**"
        )

        lines.append(
            f"- Overall change: "
            f"**"
            f"{format_percent(trend['percentage'])}"
            f"**"
        )

        lines.append(
            f"- Direction: "
            f"**{trend['direction']}**"
        )

    # ========================================================
    # VOLATILITY
    # ========================================================

    volatility = result.get(
        "volatility"
    )

    if volatility:

        lines.append("")

        lines.append(
            "### 📉 Volatility"
        )

        lines.append("")

        lines.append(
            f"- Column: "
            f"`{volatility['column']}`"
        )

        lines.append(
            f"- Standard deviation: "
            f"**"
            f"{format_number(volatility['standard_deviation'])}"
            f"**"
        )

        lines.append(
            f"- Return volatility: "
            f"**"
            f"{format_percent(volatility['return_volatility'])}"
            f"**"
        )

    # ========================================================
    # EXTREMES
    # ========================================================

    extremes = result.get(
        "extremes",
        {}
    )

    close_extreme = extremes.get(
        "close"
    )

    if close_extreme:

        lines.append("")

        lines.append(
            "### 🏆 Price Range"
        )

        lines.append("")

        lines.append(
            f"- Highest "
            f"`{close_extreme['column']}`: "
            f"**"
            f"{format_number(close_extreme['maximum'])}"
            f"**"
        )

        lines.append(
            f"- Lowest "
            f"`{close_extreme['column']}`: "
            f"**"
            f"{format_number(close_extreme['minimum'])}"
            f"**"
        )

    # ========================================================
    # VOLUME
    # ========================================================

    volume = result.get(
        "volume"
    )

    if volume:

        lines.append("")

        lines.append(
            "### 🔊 Volume"
        )

        lines.append("")

        lines.append(
            f"- Average volume: "
            f"**"
            f"{format_number(volume['average'])}"
            f"**"
        )

        lines.append(
            f"- Maximum volume: "
            f"**"
            f"{format_number(volume['maximum'])}"
            f"**"
        )

        lines.append(
            f"- Maximum vs average: "
            f"**"
            f"{volume['maximum_multiple']:.2f}×"
            f"**"
        )

    # ========================================================
    # CORRELATIONS
    # ========================================================

    correlations = result.get(
        "correlations",
        []
    )

    if correlations:

        lines.append("")

        lines.append(
            "### 🔗 Strongest Correlations"
        )

        lines.append("")

        for item in correlations[:5]:

            lines.append(
                f"- `{item['column_a']}` ↔ "
                f"`{item['column_b']}`: "
                f"**"
                f"{item['correlation']:.3f}"
                f"**"
            )

    # ========================================================
    # INSIGHTS
    # ========================================================

    insights = result.get(
        "insights",
        []
    )

    if insights:

        lines.append("")

        lines.append(
            "### 💡 Key Insights"
        )

        lines.append("")

        for insight in insights:

            lines.append(
                f"- {insight}"
            )

    return "\n".join(
        lines
    )


# ============================================================
# MAIN FUNCTION
# ============================================================

def create_insight_report(
    df: pd.DataFrame
) -> Dict[str, Any]:

    result = generate_insights(
        df
    )

    if not result.get(
        "success",
        False
    ):

        return result

    result[
        "markdown"
    ] = generate_markdown_report(
        result
    )

    return result


# ============================================================
# END
# ============================================================