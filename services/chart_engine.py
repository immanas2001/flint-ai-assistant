import re
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# ==========================================
# Load Dataset
# ==========================================

def load_chart_dataset(filepath: str) -> pd.DataFrame:

    extension = Path(filepath).suffix.lower()

    if extension == ".csv":

        try:
            return pd.read_csv(filepath)

        except UnicodeDecodeError:

            return pd.read_csv(
                filepath,
                encoding="latin-1"
            )

    if extension in [".xlsx", ".xls"]:

        return pd.read_excel(filepath)

    raise ValueError(
        f"Unsupported dataset format: {extension}"
    )


# ==========================================
# Normalize Text
# ==========================================

def normalize_text(value) -> str:

    if value is None:
        return ""

    return (
        str(value)
        .strip()
        .lower()
        .replace("_", " ")
        .replace("-", " ")
        .replace(".", " ")
    )


# ==========================================
# Column Aliases
# ==========================================

COLUMN_ALIASES = {

    "date": [
        "date",
        "datetime",
        "timestamp",
        "time",
        "day"
    ],

    "close": [
        "close",
        "closing",
        "closing price",
        "close price",
        "closing value",
        "close value",
        "adj close",
        "adjusted close"
    ],

    "open": [
        "open",
        "opening",
        "opening price",
        "open price"
    ],

    "high": [
        "high",
        "highest",
        "highest price",
        "high price"
    ],

    "low": [
        "low",
        "lowest",
        "lowest price",
        "low price"
    ],

    "volume": [
        "volume",
        "trading volume",
        "trade volume"
    ],

    "revenue": [
        "revenue",
        "sales",
        "total sales"
    ],

    "profit": [
        "profit",
        "net profit",
        "earnings",
        "net income"
    ]
}


# ==========================================
# Find Column
# ==========================================

def find_column(
    df: pd.DataFrame,
    requested: str
):

    requested = normalize_text(
        requested
    )

    # Exact match
    for column in df.columns:

        if normalize_text(column) == requested:

            return column

    # Partial match
    for column in df.columns:

        normalized = normalize_text(
            column
        )

        if (
            requested in normalized
            or normalized in requested
        ):

            return column

    # Alias match
    for canonical, aliases in COLUMN_ALIASES.items():

        normalized_aliases = [
            normalize_text(alias)
            for alias in aliases
        ]

        if requested in normalized_aliases:

            for column in df.columns:

                normalized_column = normalize_text(
                    column
                )

                if (
                    normalized_column == canonical
                    or canonical in normalized_column
                ):

                    return column

    return None


# ==========================================
# Detect Date Column
# ==========================================

def detect_date_column(
    df: pd.DataFrame
):

    # First check names
    for column in df.columns:

        normalized = normalize_text(
            column
        )

        if any(
            word in normalized
            for word in [
                "date",
                "datetime",
                "timestamp",
                "time"
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

    # Then inspect values
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


# ==========================================
# Numeric Columns
# ==========================================

def get_numeric_columns(
    df: pd.DataFrame
):

    return [

        column

        for column in df.columns

        if pd.api.types.is_numeric_dtype(
            df[column]
        )

    ]


# ==========================================
# Detect Price Column
# ==========================================

def detect_price_column(
    df: pd.DataFrame
):

    priority = [

        "close",
        "adjusted close",
        "open",
        "high",
        "low",
        "price"
    ]

    for keyword in priority:

        for column in df.columns:

            normalized = normalize_text(
                column
            )

            if keyword in normalized:

                if pd.api.types.is_numeric_dtype(
                    df[column]
                ):

                    return column

    numeric = get_numeric_columns(
        df
    )

    if numeric:

        return numeric[0]

    return None


# ==========================================
# Detect Columns From Question
# ==========================================

def detect_question_columns(
    df: pd.DataFrame,
    question: str
):

    q = normalize_text(
        question
    )

    detected = []

    # Direct columns
    for column in df.columns:

        normalized = normalize_text(
            column
        )

        if normalized in q:

            detected.append(
                column
            )

    # Aliases
    for canonical, aliases in COLUMN_ALIASES.items():

        found = False

        for alias in aliases:

            if normalize_text(alias) in q:

                found = True
                break

        if not found:
            continue

        for column in df.columns:

            normalized = normalize_text(
                column
            )

            if (
                normalized == canonical
                or canonical in normalized
            ):

                if column not in detected:

                    detected.append(
                        column
                    )

    return detected


# ==========================================
# Detect Chart Type
# ==========================================

def detect_chart_type(
    question: str,
    df: pd.DataFrame,
    detected_columns: list
):

    q = normalize_text(
        question
    )

    # ==========================================
    # Explicit chart requests
    # ==========================================

    if (
        "histogram" in q
        or "distribution" in q
        or "frequency distribution" in q
    ):

        return "histogram"


    if (
        "scatter" in q
        or "relationship" in q
        or "relation between" in q
        or "correlation between" in q
    ):

        return "scatter"


    if (
        "pie" in q
        or "percentage breakdown" in q
        or "proportion" in q
        or "share of" in q
    ):

        return "pie"


    if (
        "bar chart" in q
        or "bar graph" in q
        or "compare" in q
        or "comparison" in q
    ):

        return "bar"


    if (
        "line chart" in q
        or "line graph" in q
        or "trend" in q
        or "over time" in q
        or "historical" in q
        or "history" in q
        or "monthly" in q
        or "daily" in q
        or "weekly" in q
    ):

        return "line"


    # ==========================================
    # Automatic detection
    # ==========================================

    date_column = detect_date_column(
        df
    )

    numeric_columns = get_numeric_columns(
        df
    )

    categorical_columns = [

        column

        for column in df.columns

        if column not in numeric_columns
        and column != date_column

    ]


    # Date + numeric = line
    if (
        date_column is not None
        and numeric_columns
    ):

        return "line"


    # Categorical + numeric = bar
    if (
        categorical_columns
        and numeric_columns
    ):

        return "bar"


    # Two numeric columns = scatter
    if len(numeric_columns) >= 2:

        return "scatter"


    # One numeric column = histogram
    if len(numeric_columns) == 1:

        return "histogram"


    return "bar"


# ==========================================
# Prepare Date
# ==========================================

def prepare_date_column(
    df: pd.DataFrame,
    date_column
):

    result = df.copy()

    result[date_column] = pd.to_datetime(
        result[date_column],
        errors="coerce"
    )

    result = result.dropna(
        subset=[date_column]
    )

    result = result.sort_values(
        date_column
    )

    return result


# ==========================================
# Detect Requested Metric
# ==========================================

def detect_metric_column(
    df: pd.DataFrame,
    question: str
):

    detected = detect_question_columns(
        df,
        question
    )

    for column in detected:

        if pd.api.types.is_numeric_dtype(
            df[column]
        ):

            return column

    return detect_price_column(
        df
    )


# ==========================================
# LINE CHART
# ==========================================

def create_line_chart(
    df: pd.DataFrame,
    question: str
):

    date_column = detect_date_column(
        df
    )

    metric_column = detect_metric_column(
        df,
        question
    )

    if date_column is None:

        raise ValueError(
            "No date/time column was found "
            "for the line chart."
        )

    if metric_column is None:

        raise ValueError(
            "No numeric column was found "
            "for the line chart."
        )

    chart_df = prepare_date_column(
        df,
        date_column
    )

    fig = px.line(

        chart_df,

        x=date_column,

        y=metric_column,

        title=(
            f"{metric_column} Over Time"
        ),

        markers=False

    )

    fig.update_layout(

        template="plotly_dark",

        xaxis_title=str(
            date_column
        ),

        yaxis_title=str(
            metric_column
        ),

        hovermode="x unified",

        margin=dict(
            l=50,
            r=30,
            t=70,
            b=50
        )

    )

    return fig


# ==========================================
# BAR CHART
# ==========================================

def create_bar_chart(
    df: pd.DataFrame,
    question: str
):

    detected = detect_question_columns(
        df,
        question
    )

    numeric_columns = get_numeric_columns(
        df
    )

    categorical_columns = [

        column

        for column in df.columns

        if column not in numeric_columns

    ]


    # Two requested numeric columns
    requested_numeric = [

        column

        for column in detected

        if column in numeric_columns

    ]

    if len(requested_numeric) >= 2:

        plot_df = df[
            requested_numeric
        ].copy()

        fig = px.bar(
            plot_df,
            y=requested_numeric,
            title="Column Comparison"
        )

    else:

        metric_column = (
            requested_numeric[0]
            if requested_numeric
            else detect_price_column(df)
        )

        category_column = None

        for column in detected:

            if column in categorical_columns:

                category_column = column

                break


        if category_column is None:

            if categorical_columns:

                category_column = (
                    categorical_columns[0]
                )


        if category_column is not None:

            grouped = (
                df
                .groupby(
                    category_column,
                    dropna=False
                )[metric_column]
                .mean()
                .reset_index()
            )

            grouped = grouped.sort_values(
                metric_column,
                ascending=False
            ).head(20)


            fig = px.bar(

                grouped,

                x=category_column,

                y=metric_column,

                title=(
                    f"{metric_column} "
                    f"by {category_column}"
                )

            )

        else:

            summary = (
                df[metric_column]
                .describe()
                .reset_index()
            )

            summary.columns = [
                "Statistic",
                "Value"
            ]


            fig = px.bar(

                summary,

                x="Statistic",

                y="Value",

                title=(
                    f"{metric_column} "
                    f"Statistics"
                )

            )


    fig.update_layout(

        template="plotly_dark",

        hovermode="x unified",

        margin=dict(
            l=50,
            r=30,
            t=70,
            b=50
        )

    )

    return fig


# ==========================================
# HISTOGRAM
# ==========================================

def create_histogram(
    df: pd.DataFrame,
    question: str
):

    metric_column = detect_metric_column(
        df,
        question
    )

    if metric_column is None:

        raise ValueError(
            "No numeric column found "
            "for the histogram."
        )


    fig = px.histogram(

        df,

        x=metric_column,

        nbins=40,

        title=(
            f"Distribution of "
            f"{metric_column}"
        )

    )


    fig.update_layout(

        template="plotly_dark",

        xaxis_title=str(
            metric_column
        ),

        yaxis_title="Frequency",

        margin=dict(
            l=50,
            r=30,
            t=70,
            b=50
        )

    )

    return fig


# ==========================================
# SCATTER
# ==========================================

def create_scatter_chart(
    df: pd.DataFrame,
    question: str
):

    detected = detect_question_columns(
        df,
        question
    )


    numeric_detected = [

        column

        for column in detected

        if pd.api.types.is_numeric_dtype(
            df[column]
        )

    ]


    numeric_columns = get_numeric_columns(
        df
    )


    if len(numeric_detected) >= 2:

        x_column = numeric_detected[0]

        y_column = numeric_detected[1]

    elif len(numeric_columns) >= 2:

        x_column = numeric_columns[0]

        y_column = numeric_columns[1]

    else:

        raise ValueError(
            "At least two numeric columns "
            "are required for a scatter plot."
        )


    fig = px.scatter(

        df,

        x=x_column,

        y=y_column,

        title=(
            f"{y_column} vs {x_column}"
        ),

        trendline=None

    )


    fig.update_layout(

        template="plotly_dark",

        xaxis_title=str(
            x_column
        ),

        yaxis_title=str(
            y_column
        ),

        margin=dict(
            l=50,
            r=30,
            t=70,
            b=50
        )

    )

    return fig


# ==========================================
# PIE CHART
# ==========================================

def create_pie_chart(
    df: pd.DataFrame,
    question: str
):

    detected = detect_question_columns(
        df,
        question
    )

    numeric_columns = get_numeric_columns(
        df
    )

    categorical_columns = [

        column

        for column in df.columns

        if column not in numeric_columns

    ]


    category_column = None

    value_column = None


    for column in detected:

        if column in categorical_columns:

            category_column = column

        elif column in numeric_columns:

            value_column = column


    if category_column is None:

        if categorical_columns:

            category_column = (
                categorical_columns[0]
            )

    if value_column is None:

        if numeric_columns:

            value_column = (
                numeric_columns[0]
            )


    if (
        category_column is None
        or value_column is None
    ):

        raise ValueError(
            "A categorical and numeric "
            "column are required for "
            "a pie chart."
        )


    grouped = (

        df
        .groupby(
            category_column,
            dropna=False
        )[value_column]
        .sum()
        .reset_index()

    )


    grouped = grouped.sort_values(
        value_column,
        ascending=False
    ).head(15)


    fig = px.pie(

        grouped,

        names=category_column,

        values=value_column,

        title=(
            f"{value_column} "
            f"Distribution by "
            f"{category_column}"
        )

    )


    fig.update_layout(
        template="plotly_dark"
    )


    return fig


# ==========================================
# Automatic Chart
# ==========================================

def create_automatic_chart(
    df: pd.DataFrame,
    question: str
):

    detected_columns = (
        detect_question_columns(
            df,
            question
        )
    )


    chart_type = detect_chart_type(
        question,
        df,
        detected_columns
    )


    print(
        "[Chart Engine] "
        f"Detected chart type: {chart_type}"
    )


    if chart_type == "line":

        return create_line_chart(
            df,
            question
        )


    if chart_type == "bar":

        return create_bar_chart(
            df,
            question
        )


    if chart_type == "histogram":

        return create_histogram(
            df,
            question
        )


    if chart_type == "scatter":

        return create_scatter_chart(
            df,
            question
        )


    if chart_type == "pie":

        return create_pie_chart(
            df,
            question
        )


    return create_line_chart(
        df,
        question
    )


# ==========================================
# Convert Figure To JSON
# ==========================================

def figure_to_dict(
    figure
):

    return figure.to_plotly_json()


# ==========================================
# Main Chart Function
# ==========================================

def create_chart(
    filepath: str,
    question: str
):

    print(
        "[Chart Engine] "
        f"Question: {question}"
    )


    # ==========================================
    # Load Dataset
    # ==========================================

    df = load_chart_dataset(
        filepath
    )


    if df.empty:

        raise ValueError(
            "The dataset is empty."
        )


    # ==========================================
    # Create Chart
    # ==========================================

    figure = create_automatic_chart(
        df,
        question
    )


    # ==========================================
    # Return Plotly JSON
    # ==========================================

    chart_json = figure_to_dict(
        figure
    )


    return chart_json