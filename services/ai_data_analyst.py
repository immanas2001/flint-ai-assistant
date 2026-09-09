"""
Flint AI - Natural Language Data Analyst

This module analyzes a pandas DataFrame and converts
natural-language questions into useful data insights.

It is intentionally independent from chat.py so the
existing chat/chart system keeps working.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


# ============================================================
# TEXT HELPERS
# ============================================================

def normalize(text: str) -> str:
    if text is None:
        return ""

    return " ".join(
        str(text)
        .lower()
        .strip()
        .replace("_", " ")
        .replace("-", " ")
        .split()
    )


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


def format_percentage(value: float) -> str:

    return f"{value:.2f}%"


# ============================================================
# COLUMN DETECTION
# ============================================================

ALIASES = {

    "date": [
        "date",
        "datetime",
        "timestamp",
        "time",
        "day",
    ],

    "close": [
        "close",
        "closing",
        "closing price",
        "close price",
        "adj close",
        "adjusted close",
    ],

    "open": [
        "open",
        "opening",
        "opening price",
        "open price",
    ],

    "high": [
        "high",
        "highest",
        "highest price",
        "high price",
    ],

    "low": [
        "low",
        "lowest",
        "lowest price",
        "low price",
    ],

    "volume": [
        "volume",
        "trading volume",
        "trade volume",
    ],

}


def find_column(
    df: pd.DataFrame,
    question: str,
    preferred: Optional[str] = None,
) -> Optional[str]:

    q = normalize(question)

    # --------------------------------------------------------
    # Preferred semantic column
    # --------------------------------------------------------

    if preferred:

        aliases = ALIASES.get(
            preferred,
            [preferred]
        )

        for column in df.columns:

            column_text = normalize(column)

            for alias in aliases:

                if normalize(alias) == column_text:

                    return column

    # --------------------------------------------------------
    # Exact column name
    # --------------------------------------------------------

    for column in df.columns:

        column_text = normalize(column)

        if column_text in q:

            return column

    # --------------------------------------------------------
    # Alias matching
    # --------------------------------------------------------

    for canonical, aliases in ALIASES.items():

        for alias in aliases:

            if normalize(alias) in q:

                for column in df.columns:

                    column_text = normalize(column)

                    if (
                        column_text == canonical
                        or canonical in column_text
                    ):

                        return column

    return None


def find_numeric_columns(
    df: pd.DataFrame
) -> List[str]:

    return [

        column

        for column in df.columns

        if pd.api.types.is_numeric_dtype(
            df[column]
        )

    ]


def find_date_column(
    df: pd.DataFrame
) -> Optional[str]:

    # First use column names.

    for column in df.columns:

        name = normalize(column)

        if any(
            keyword in name
            for keyword in [
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

    # Then inspect the actual values.

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


# ============================================================
# DATA PREPARATION
# ============================================================

def prepare_dataframe(
    df: pd.DataFrame
) -> pd.DataFrame:

    result = df.copy()

    # Remove completely empty columns.

    result = result.dropna(
        axis=1,
        how="all"
    )

    return result


# ============================================================
# OVERVIEW
# ============================================================

def dataset_overview(
    df: pd.DataFrame
) -> Dict[str, Any]:

    numeric = find_numeric_columns(df)

    date_column = find_date_column(df)

    return {

        "rows": int(len(df)),

        "columns": int(len(df.columns)),

        "column_names": [
            str(column)
            for column in df.columns
        ],

        "numeric_columns": [
            str(column)
            for column in numeric
        ],

        "date_column": (
            str(date_column)
            if date_column
            else None
        ),

        "missing_values": int(
            df.isna().sum().sum()
        ),

        "duplicate_rows": int(
            df.duplicated().sum()
        ),

    }


# ============================================================
# QUESTION INTENT
# ============================================================

def detect_intent(
    question: str
) -> str:

    q = normalize(question)

    # --------------------------------------------------------
    # Trend
    # --------------------------------------------------------

    if any(
        phrase in q
        for phrase in [
            "trend",
            "trending",
            "going up",
            "going down",
            "increased",
            "decreased",
            "growth",
            "performance",
            "overall performance",
        ]
    ):

        return "trend"

    # --------------------------------------------------------
    # Best / highest
    # --------------------------------------------------------

    if any(
        phrase in q
        for phrase in [
            "best day",
            "highest",
            "maximum",
            "max",
            "peak",
            "largest",
        ]
    ):

        return "highest"

    # --------------------------------------------------------
    # Worst / lowest
    # --------------------------------------------------------

    if any(
        phrase in q
        for phrase in [
            "worst day",
            "lowest",
            "minimum",
            "min",
            "bottom",
            "smallest",
        ]
    ):

        return "lowest"

    # --------------------------------------------------------
    # Average
    # --------------------------------------------------------

    if any(
        phrase in q
        for phrase in [
            "average",
            "mean",
            "avg",
        ]
    ):

        return "average"

    # --------------------------------------------------------
    # Median
    # --------------------------------------------------------

    if "median" in q:

        return "median"

    # --------------------------------------------------------
    # Volatility
    # --------------------------------------------------------

    if any(
        phrase in q
        for phrase in [
            "volatility",
            "volatile",
            "standard deviation",
            "std",
            "risk",
        ]
    ):

        return "volatility"

    # --------------------------------------------------------
    # Correlation
    # --------------------------------------------------------

    if any(
        phrase in q
        for phrase in [
            "correlation",
            "correlated",
            "relationship",
        ]
    ):

        return "correlation"

    # --------------------------------------------------------
    # Compare
    # --------------------------------------------------------

    if any(
        phrase in q
        for phrase in [
            "compare",
            "comparison",
            "difference between",
        ]
    ):

        return "compare"

    # --------------------------------------------------------
    # Missing
    # --------------------------------------------------------

    if any(
        phrase in q
        for phrase in [
            "missing",
            "null",
            "empty",
            "blank",
        ]
    ):

        return "missing"

    # --------------------------------------------------------
    # Duplicate
    # --------------------------------------------------------

    if "duplicate" in q:

        return "duplicates"

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    if any(
        phrase in q
        for phrase in [
            "summary",
            "summarize",
            "summarise",
            "overview",
            "analyze",
            "analyse",
            "insights",
        ]
    ):

        return "overview"

    return "unknown"


# ============================================================
# BEST / HIGHEST VALUE
# ============================================================

def analyze_highest(
    df: pd.DataFrame,
    question: str
) -> str:

    column = find_column(
        df,
        question,
        preferred="close"
    )

    if column is None:

        numeric = find_numeric_columns(df)

        if not numeric:

            return (
                "I couldn't find a numeric "
                "column to analyze."
            )

        column = numeric[0]

    series = pd.to_numeric(
        df[column],
        errors="coerce"
    )

    if series.dropna().empty:

        return (
            f"`{column}` does not contain "
            "usable numeric values."
        )

    index = series.idxmax()

    value = series.loc[index]

    date_column = find_date_column(df)

    date_text = None

    if date_column:

        date_value = df.loc[
            index,
            date_column
        ]

        date_text = str(
            date_value
        )

    answer = (
        f"### 📈 Highest {column}\n\n"
        f"The highest **{column}** was "
        f"**{format_number(value)}**."
    )

    if date_text:

        answer += (
            f"\n\nIt occurred on "
            f"**{date_text}**."
        )

    return answer


# ============================================================
# LOWEST VALUE
# ============================================================

def analyze_lowest(
    df: pd.DataFrame,
    question: str
) -> str:

    column = find_column(
        df,
        question,
        preferred="close"
    )

    if column is None:

        numeric = find_numeric_columns(df)

        if not numeric:

            return (
                "I couldn't find a numeric "
                "column to analyze."
            )

        column = numeric[0]

    series = pd.to_numeric(
        df[column],
        errors="coerce"
    )

    if series.dropna().empty:

        return (
            f"`{column}` does not contain "
            "usable numeric values."
        )

    index = series.idxmin()

    value = series.loc[index]

    date_column = find_date_column(df)

    date_text = None

    if date_column:

        date_text = str(
            df.loc[
                index,
                date_column
            ]
        )

    answer = (
        f"### 📉 Lowest {column}\n\n"
        f"The lowest **{column}** was "
        f"**{format_number(value)}**."
    )

    if date_text:

        answer += (
            f"\n\nIt occurred on "
            f"**{date_text}**."
        )

    return answer


# ============================================================
# AVERAGE
# ============================================================

def analyze_average(
    df: pd.DataFrame,
    question: str
) -> str:

    column = find_column(
        df,
        question,
        preferred="close"
    )

    if column is None:

        numeric = find_numeric_columns(df)

        if not numeric:

            return "No numeric column was found."

        column = numeric[0]

    series = pd.to_numeric(
        df[column],
        errors="coerce"
    )

    value = series.mean()

    return (
        f"### 📊 Average {column}\n\n"
        f"The average **{column}** is "
        f"**{format_number(value)}**."
    )


# ============================================================
# MEDIAN
# ============================================================

def analyze_median(
    df: pd.DataFrame,
    question: str
) -> str:

    column = find_column(
        df,
        question,
        preferred="close"
    )

    if column is None:

        numeric = find_numeric_columns(df)

        if not numeric:

            return "No numeric column was found."

        column = numeric[0]

    series = pd.to_numeric(
        df[column],
        errors="coerce"
    )

    value = series.median()

    return (
        f"### 📊 Median {column}\n\n"
        f"The median **{column}** is "
        f"**{format_number(value)}**."
    )


# ============================================================
# VOLATILITY
# ============================================================

def analyze_volatility(
    df: pd.DataFrame,
    question: str
) -> str:

    column = find_column(
        df,
        question,
        preferred="close"
    )

    if column is None:

        numeric = find_numeric_columns(df)

        if not numeric:

            return "No numeric column was found."

        column = numeric[0]

    series = pd.to_numeric(
        df[column],
        errors="coerce"
    ).dropna()

    if len(series) < 2:

        return (
            "There aren't enough numeric "
            "values to calculate volatility."
        )

    standard_deviation = series.std()

    mean = series.mean()

    if mean != 0:

        coefficient = (
            standard_deviation / mean
        ) * 100

    else:

        coefficient = 0

    return (
        f"### 📊 {column} Volatility\n\n"
        f"- Standard deviation: "
        f"**{format_number(standard_deviation)}**\n"
        f"- Relative volatility: "
        f"**{format_percentage(coefficient)}**"
    )


# ============================================================
# TREND ANALYSIS
# ============================================================

def analyze_trend(
    df: pd.DataFrame,
    question: str
) -> str:

    date_column = find_date_column(df)

    column = find_column(
        df,
        question,
        preferred="close"
    )

    if column is None:

        numeric = find_numeric_columns(df)

        if not numeric:

            return "No numeric column was found."

        column = numeric[0]

    series = pd.to_numeric(
        df[column],
        errors="coerce"
    )

    valid = series.dropna()

    if len(valid) < 2:

        return (
            "There aren't enough values "
            "to determine a trend."
        )

    first_value = float(
        valid.iloc[0]
    )

    last_value = float(
        valid.iloc[-1]
    )

    change = (
        last_value - first_value
    )

    if first_value != 0:

        percentage = (
            change / first_value
        ) * 100

    else:

        percentage = 0

    if percentage > 0.5:

        direction = "upward 📈"

    elif percentage < -0.5:

        direction = "downward 📉"

    else:

        direction = "relatively flat ➡️"

    answer = (
        f"### {column} Trend\n\n"
        f"The overall trend is **{direction}**.\n\n"
        f"- Starting value: "
        f"**{format_number(first_value)}**\n"
        f"- Ending value: "
        f"**{format_number(last_value)}**\n"
        f"- Change: "
        f"**{format_number(change)}**\n"
        f"- Percentage change: "
        f"**{format_percentage(percentage)}**"
    )

    if date_column:

        answer += (
            f"\n\nThe analysis uses "
            f"`{date_column}` as the time axis."
        )

    return answer


# ============================================================
# CORRELATION
# ============================================================

def analyze_correlation(
    df: pd.DataFrame,
    question: str
) -> str:

    numeric = find_numeric_columns(df)

    if len(numeric) < 2:

        return (
            "At least two numeric columns "
            "are required for correlation."
        )

    mentioned = []

    for column in numeric:

        if normalize(column) in normalize(question):

            mentioned.append(
                column
            )

    if len(mentioned) >= 2:

        column_a = mentioned[0]

        column_b = mentioned[1]

    else:

        column_a = numeric[0]

        column_b = numeric[1]

    correlation = df[
        [column_a, column_b]
    ].corr().iloc[0, 1]

    if pd.isna(correlation):

        return (
            "I couldn't calculate a valid "
            "correlation for these columns."
        )

    absolute = abs(
        correlation
    )

    if absolute >= 0.8:

        strength = "very strong"

    elif absolute >= 0.6:

        strength = "strong"

    elif absolute >= 0.4:

        strength = "moderate"

    elif absolute >= 0.2:

        strength = "weak"

    else:

        strength = "very weak"

    direction = (
        "positive"
        if correlation > 0
        else "negative"
    )

    return (
        f"### 🔗 Correlation\n\n"
        f"**{column_a}** and "
        f"**{column_b}** have a "
        f"**{strength} {direction} "
        f"correlation**.\n\n"
        f"Correlation coefficient: "
        f"**{correlation:.4f}**"
    )


# ============================================================
# MISSING VALUES
# ============================================================

def analyze_missing(
    df: pd.DataFrame
) -> str:

    missing = df.isna().sum()

    missing = missing[
        missing > 0
    ].sort_values(
        ascending=False
    )

    if missing.empty:

        return (
            "### ✅ Data Quality\n\n"
            "No missing values were detected."
        )

    lines = []

    total = int(
        missing.sum()
    )

    lines.append(
        f"Total missing values: "
        f"**{total:,}**\n"
    )

    for column, count in missing.items():

        percentage = (
            count / len(df)
        ) * 100

        lines.append(
            f"- **{column}**: "
            f"{count:,} "
            f"({percentage:.2f}%)"
        )

    return (
        "### ⚠️ Missing Values\n\n"
        +
        "\n".join(lines)
    )


# ============================================================
# DUPLICATES
# ============================================================

def analyze_duplicates(
    df: pd.DataFrame
) -> str:

    count = int(
        df.duplicated().sum()
    )

    if count == 0:

        return (
            "### ✅ Duplicate Check\n\n"
            "No duplicate rows were detected."
        )

    percentage = (
        count / len(df)
    ) * 100

    return (
        "### ⚠️ Duplicate Rows\n\n"
        f"The dataset contains "
        f"**{count:,} duplicate rows** "
        f"({percentage:.2f}% of the dataset)."
    )


# ============================================================
# OVERVIEW / INSIGHTS
# ============================================================

def analyze_overview(
    df: pd.DataFrame
) -> str:

    overview = dataset_overview(
        df
    )

    answer = []

    answer.append(
        "## 📊 Dataset Analysis"
    )

    answer.append("")

    answer.append(
        "### Dataset Overview"
    )

    answer.append("")

    answer.append(
        f"- Rows: **{overview['rows']:,}**"
    )

    answer.append(
        f"- Columns: **{overview['columns']:,}**"
    )

    answer.append(
        f"- Missing values: "
        f"**{overview['missing_values']:,}**"
    )

    answer.append(
        f"- Duplicate rows: "
        f"**{overview['duplicate_rows']:,}**"
    )

    answer.append("")

    answer.append(
        "### Columns"
    )

    answer.append("")

    for column in overview[
        "column_names"
    ]:

        answer.append(
            f"- `{column}`"
        )

    # --------------------------------------------------------
    # Numeric summary
    # --------------------------------------------------------

    numeric = overview[
        "numeric_columns"
    ]

    if numeric:

        answer.append("")

        answer.append(
            "### Numeric Columns"
        )

        answer.append("")

        for column in numeric:

            series = pd.to_numeric(
                df[column],
                errors="coerce"
            ).dropna()

            if series.empty:
                continue

            answer.append(
                f"**{column}** — "
                f"mean "
                f"{format_number(series.mean())}, "
                f"min "
                f"{format_number(series.min())}, "
                f"max "
                f"{format_number(series.max())}"
            )

    # --------------------------------------------------------
    # Date range
    # --------------------------------------------------------

    date_column = overview[
        "date_column"
    ]

    if date_column:

        dates = pd.to_datetime(
            df[date_column],
            errors="coerce"
        ).dropna()

        if not dates.empty:

            answer.append("")

            answer.append(
                "### 📅 Date Range"
            )

            answer.append("")

            answer.append(
                f"- Start: "
                f"**{dates.min()}**"
            )

            answer.append(
                f"- End: "
                f"**{dates.max()}**"
            )

    return "\n".join(answer)


# ============================================================
# MAIN ANALYST
# ============================================================

def analyze_question(
    df: pd.DataFrame,
    question: str
) -> Dict[str, Any]:

    df = prepare_dataframe(
        df
    )

    if df.empty:

        return {

            "success": False,

            "answer": (
                "The dataset is empty."
            ),

            "intent": "unknown",

        }

    intent = detect_intent(
        question
    )

    try:

        if intent == "highest":

            answer = analyze_highest(
                df,
                question
            )

        elif intent == "lowest":

            answer = analyze_lowest(
                df,
                question
            )

        elif intent == "average":

            answer = analyze_average(
                df,
                question
            )

        elif intent == "median":

            answer = analyze_median(
                df,
                question
            )

        elif intent == "volatility":

            answer = analyze_volatility(
                df,
                question
            )

        elif intent == "trend":

            answer = analyze_trend(
                df,
                question
            )

        elif intent == "correlation":

            answer = analyze_correlation(
                df,
                question
            )

        elif intent == "missing":

            answer = analyze_missing(
                df
            )

        elif intent == "duplicates":

            answer = analyze_duplicates(
                df
            )

        elif intent == "overview":

            answer = analyze_overview(
                df
            )

        else:

            answer = analyze_overview(
                df
            )

        return {

            "success": True,

            "answer": answer,

            "intent": intent,

        }

    except Exception as exc:

        return {

            "success": False,

            "answer": (
                "I couldn't complete the "
                f"analysis: {exc}"
            ),

            "intent": intent,

        }


# ============================================================
# COMPATIBILITY HELPERS
# ============================================================

def is_analyst_question(
    question: str
) -> bool:

    q = normalize(question)

    keywords = [

        "analyze",
        "analyse",
        "insight",
        "trend",
        "performance",
        "highest",
        "lowest",
        "average",
        "mean",
        "median",
        "volatility",
        "correlation",
        "compare",
        "missing",
        "duplicate",
        "overview",
        "summary",
        "best day",
        "worst day",

    ]

    return any(
        keyword in q
        for keyword in keywords
    )


# ============================================================
# END
# ============================================================