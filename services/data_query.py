from pathlib import Path

import pandas as pd


# ==========================================
# Load Dataset
# ==========================================

def load_dataset(filepath: str) -> pd.DataFrame:
    """
    Load CSV or Excel dataset.
    """

    path = Path(filepath)

    if not path.exists():

        raise FileNotFoundError(
            f"Dataset not found: {filepath}"
        )


    extension = path.suffix.lower()


    if extension == ".csv":

        try:

            return pd.read_csv(
                filepath
            )

        except UnicodeDecodeError:

            return pd.read_csv(
                filepath,
                encoding="latin-1"
            )


    if extension in [
        ".xlsx",
        ".xls"
    ]:

        return pd.read_excel(
            filepath
        )


    raise ValueError(
        f"Unsupported dataset format: {extension}"
    )


# ==========================================
# Find Column
# ==========================================

def find_column(
    df: pd.DataFrame,
    column_name: str
):
    """
    Find a column using flexible
    case-insensitive matching.
    """

    if column_name is None:

        return None


    column_name = (
        str(column_name)
        .strip()
        .lower()
    )


    # ==========================================
    # Exact Match
    # ==========================================

    for column in df.columns:

        if (
            str(column)
            .strip()
            .lower()
            == column_name
        ):

            return column


    # ==========================================
    # Normalized Match
    # ==========================================

    normalized_target = (
        column_name
        .replace("_", " ")
        .replace("-", " ")
        .strip()
    )


    for column in df.columns:

        normalized_column = (
            str(column)
            .strip()
            .lower()
            .replace("_", " ")
            .replace("-", " ")
        )


        if (
            normalized_column
            == normalized_target
        ):

            return column


    return None


# ==========================================
# Get Numeric Columns
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
# Get Text Columns
# ==========================================

def get_text_columns(
    df: pd.DataFrame
):

    return [

        column

        for column in df.columns

        if not pd.api.types.is_numeric_dtype(
            df[column]
        )

    ]


# ==========================================
# Dataset Overview
# ==========================================

def dataset_overview(
    df: pd.DataFrame
) -> dict:

    return {

        "rows":
            int(len(df)),

        "columns":
            int(len(df.columns)),

        "column_names": [

            str(column)

            for column in df.columns

        ],

        "numeric_columns": [

            str(column)

            for column
            in get_numeric_columns(df)

        ],

        "text_columns": [

            str(column)

            for column
            in get_text_columns(df)

        ],

        "duplicate_rows":
            int(
                df.duplicated().sum()
            ),

        "missing_values": {

            str(column):
                int(
                    df[column]
                    .isna()
                    .sum()
                )

            for column in df.columns

        }

    }


# ==========================================
# Column Statistics
# ==========================================

def column_statistics(
    df: pd.DataFrame,
    column_name: str
) -> dict:

    column = find_column(
        df,
        column_name
    )


    if column is None:

        raise ValueError(
            f"Column '{column_name}' was not found."
        )


    series = df[column]


    # ==========================================
    # Non Numeric
    # ==========================================

    if not pd.api.types.is_numeric_dtype(
        series
    ):

        return {

            "column":
                str(column),

            "type":
                "non-numeric",

            "count":
                int(
                    series.count()
                ),

            "unique":
                int(
                    series.nunique()
                ),

            "missing":
                int(
                    series.isna().sum()
                ),

            "top":
                (
                    series.mode()
                    .iloc[0]
                    if not series.mode().empty
                    else None
                )

        }


    # ==========================================
    # Numeric
    # ==========================================

    return {

        "column":
            str(column),

        "type":
            "numeric",

        "count":
            int(
                series.count()
            ),

        "missing":
            int(
                series.isna().sum()
            ),

        "unique":
            int(
                series.nunique()
            ),

        "min":
            safe_number(
                series.min()
            ),

        "max":
            safe_number(
                series.max()
            ),

        "mean":
            safe_number(
                series.mean()
            ),

        "median":
            safe_number(
                series.median()
            ),

        "sum":
            safe_number(
                series.sum()
            ),

        "std":
            safe_number(
                series.std()
            ),

        "variance":
            safe_number(
                series.var()
            )

    }


# ==========================================
# Average
# ==========================================

def calculate_average(
    df: pd.DataFrame,
    column_name: str
):

    column = require_numeric_column(
        df,
        column_name
    )


    return safe_number(
        df[column].mean()
    )


# ==========================================
# Maximum
# ==========================================

def calculate_maximum(
    df: pd.DataFrame,
    column_name: str
):

    column = require_numeric_column(
        df,
        column_name
    )


    return safe_number(
        df[column].max()
    )


# ==========================================
# Minimum
# ==========================================

def calculate_minimum(
    df: pd.DataFrame,
    column_name: str
):

    column = require_numeric_column(
        df,
        column_name
    )


    return safe_number(
        df[column].min()
    )


# ==========================================
# Sum
# ==========================================

def calculate_sum(
    df: pd.DataFrame,
    column_name: str
):

    column = require_numeric_column(
        df,
        column_name
    )


    return safe_number(
        df[column].sum()
    )


# ==========================================
# Median
# ==========================================

def calculate_median(
    df: pd.DataFrame,
    column_name: str
):

    column = require_numeric_column(
        df,
        column_name
    )


    return safe_number(
        df[column].median()
    )


# ==========================================
# Standard Deviation
# ==========================================

def calculate_standard_deviation(
    df: pd.DataFrame,
    column_name: str
):

    column = require_numeric_column(
        df,
        column_name
    )


    return safe_number(
        df[column].std()
    )


# ==========================================
# Variance
# ==========================================

def calculate_variance(
    df: pd.DataFrame,
    column_name: str
):

    column = require_numeric_column(
        df,
        column_name
    )


    return safe_number(
        df[column].var()
    )


# ==========================================
# Count
# ==========================================

def calculate_count(
    df: pd.DataFrame,
    column_name: str | None = None
):

    if column_name is None:

        return int(
            len(df)
        )


    column = find_column(
        df,
        column_name
    )


    if column is None:

        raise ValueError(
            f"Column '{column_name}' was not found."
        )


    return int(
        df[column].count()
    )


# ==========================================
# Missing Values
# ==========================================

def calculate_missing(
    df: pd.DataFrame
) -> dict:

    return {

        str(column):
            int(
                df[column]
                .isna()
                .sum()
            )

        for column in df.columns

        if df[column]
        .isna()
        .sum() > 0

    }


# ==========================================
# Total Missing Values
# ==========================================

def calculate_total_missing(
    df: pd.DataFrame
):

    return int(
        df.isna()
        .sum()
        .sum()
    )


# ==========================================
# Unique Values
# ==========================================

def calculate_unique(
    df: pd.DataFrame,
    column_name: str
):

    column = find_column(
        df,
        column_name
    )


    if column is None:

        raise ValueError(
            f"Column '{column_name}' was not found."
        )


    return int(
        df[column].nunique()
    )


# ==========================================
# Top Values
# ==========================================

def top_values(
    df: pd.DataFrame,
    column_name: str,
    n: int = 10
):

    column = find_column(
        df,
        column_name
    )


    if column is None:

        raise ValueError(
            f"Column '{column_name}' was not found."
        )


    return (
        df[column]
        .value_counts(
            dropna=False
        )
        .head(n)
        .to_dict()
    )


# ==========================================
# Bottom Values
# ==========================================

def bottom_values(
    df: pd.DataFrame,
    column_name: str,
    n: int = 10
):

    column = find_column(
        df,
        column_name
    )


    if column is None:

        raise ValueError(
            f"Column '{column_name}' was not found."
        )


    return (
        df[column]
        .value_counts(
            dropna=False
        )
        .tail(n)
        .to_dict()
    )


# ==========================================
# Top Rows
# ==========================================

def top_rows(
    df: pd.DataFrame,
    column_name: str,
    n: int = 10,
    ascending: bool = False
):

    column = require_numeric_column(
        df,
        column_name
    )


    result = (
        df.sort_values(
            by=column,
            ascending=ascending
        )
        .head(n)
        .copy()
    )


    return dataframe_to_records(
        result
    )


# ==========================================
# Bottom Rows
# ==========================================

def bottom_rows(
    df: pd.DataFrame,
    column_name: str,
    n: int = 10
):

    return top_rows(
        df,
        column_name,
        n=n,
        ascending=True
    )


# ==========================================
# Correlation
# ==========================================

def calculate_correlation(
    df: pd.DataFrame,
    column_a: str,
    column_b: str
):

    first_column = require_numeric_column(
        df,
        column_a
    )

    second_column = require_numeric_column(
        df,
        column_b
    )


    value = df[
        first_column
    ].corr(
        df[
            second_column
        ]
    )


    return safe_number(
        value
    )


# ==========================================
# Full Correlation Matrix
# ==========================================

def correlation_matrix(
    df: pd.DataFrame
):

    numeric_df = df[
        get_numeric_columns(df)
    ]


    if numeric_df.empty:

        return {}


    matrix = (
        numeric_df
        .corr()
        .round(4)
    )


    return matrix.to_dict()


# ==========================================
# Highest Row
# ==========================================

def highest_row(
    df: pd.DataFrame,
    column_name: str
):

    column = require_numeric_column(
        df,
        column_name
    )


    if df.empty:

        return None


    index = (
        df[column]
        .idxmax()
    )


    row = df.loc[
        index
    ]


    return row_to_dict(
        row
    )


# ==========================================
# Lowest Row
# ==========================================

def lowest_row(
    df: pd.DataFrame,
    column_name: str
):

    column = require_numeric_column(
        df,
        column_name
    )


    if df.empty:

        return None


    index = (
        df[column]
        .idxmin()
    )


    row = df.loc[
        index
    ]


    return row_to_dict(
        row
    )


# ==========================================
# Describe Numeric Data
# ==========================================

def describe_dataset(
    df: pd.DataFrame
):

    numeric_columns = (
        get_numeric_columns(df)
    )


    if not numeric_columns:

        return {}


    result = (
        df[numeric_columns]
        .describe()
        .round(4)
    )


    return result.to_dict()


# ==========================================
# Dataset Preview
# ==========================================

def dataset_preview(
    df: pd.DataFrame,
    n: int = 5
):

    return dataframe_to_records(
        df.head(n)
    )


# ==========================================
# Dataset Tail
# ==========================================

def dataset_tail(
    df: pd.DataFrame,
    n: int = 5
):

    return dataframe_to_records(
        df.tail(n)
    )


# ==========================================
# Duplicate Rows
# ==========================================

def calculate_duplicates(
    df: pd.DataFrame
):

    return int(
        df.duplicated()
        .sum()
    )


# ==========================================
# Percentage Missing
# ==========================================

def missing_percentage(
    df: pd.DataFrame
):

    if len(df) == 0:

        return {

            str(column): 0.0

            for column in df.columns

        }


    return {

        str(column):
            round(
                (
                    df[column]
                    .isna()
                    .sum()
                    /
                    len(df)
                )
                * 100,
                2
            )

        for column in df.columns

    }


# ==========================================
# Numeric Summary
# ==========================================

def numeric_summary(
    df: pd.DataFrame
):

    result = {}


    for column in get_numeric_columns(
        df
    ):

        result[
            str(column)
        ] = column_statistics(
            df,
            str(column)
        )


    return result


# ==========================================
# Require Numeric Column
# ==========================================

def require_numeric_column(
    df: pd.DataFrame,
    column_name: str
):

    column = find_column(
        df,
        column_name
    )


    if column is None:

        raise ValueError(
            f"Column '{column_name}' was not found."
        )


    if not pd.api.types.is_numeric_dtype(
        df[column]
    ):

        raise ValueError(
            f"Column '{column}' is not numeric."
        )


    return column


# ==========================================
# DataFrame → JSON-Safe Records
# ==========================================

def dataframe_to_records(
    df: pd.DataFrame
):

    records = []


    for _, row in df.iterrows():

        record = {}


        for column, value in row.items():

            if pd.isna(value):

                record[
                    str(column)
                ] = None

            elif isinstance(
                value,
                (
                    pd.Timestamp,
                    pd.Timedelta
                )
            ):

                record[
                    str(column)
                ] = str(value)

            else:

                # Convert numpy/pandas
                # numeric types into
                # normal Python values.

                try:

                    record[
                        str(column)
                    ] = value.item()

                except AttributeError:

                    record[
                        str(column)
                    ] = value


        records.append(
            record
        )


    return records


# ==========================================
# Row → Dictionary
# ==========================================

def row_to_dict(
    row
):

    result = {}


    for column, value in row.items():

        if pd.isna(value):

            result[
                str(column)
            ] = None

        else:

            try:

                result[
                    str(column)
                ] = value.item()

            except AttributeError:

                result[
                    str(column)
                ] = value


    return result


# ==========================================
# Safe Number
# ==========================================

def safe_number(
    value
):

    if value is None:

        return None


    try:

        if pd.isna(value):

            return None

    except (
        TypeError,
        ValueError
    ):

        pass


    try:

        result = float(
            value
        )


        if pd.isna(result):

            return None


        return result


    except (
        TypeError,
        ValueError,
        OverflowError
    ):

        return None

    # ==========================================
# Find Date Column
# ==========================================

def find_date_column(
    df: pd.DataFrame,
    column_name: str | None = None
):
    """
    Find or automatically detect a date column.
    """

    # Explicit column requested
    if column_name:

        column = find_column(
            df,
            column_name
        )

        if column is not None:
            return column

    # Common date column names
    date_keywords = [
        "date",
        "datetime",
        "timestamp",
        "time",
        "day",
        "trading_date"
    ]

    for column in df.columns:

        name = (
            str(column)
            .strip()
            .lower()
            .replace("_", " ")
            .replace("-", " ")
        )

        if any(
            keyword in name
            for keyword in date_keywords
        ):

            converted = pd.to_datetime(
                df[column],
                errors="coerce"
            )

            if converted.notna().sum() > 0:

                return column

    # Automatic detection
    for column in df.columns:

        if (
            pd.api.types.is_datetime64_any_dtype(
                df[column]
            )
        ):

            return column

        converted = pd.to_datetime(
            df[column],
            errors="coerce"
        )

        if (
            converted.notna().sum()
            >= max(3, len(df) * 0.7)
        ):

            return column

    return None


# ==========================================
# Convert Date Column
# ==========================================

def prepare_date_column(
    df: pd.DataFrame,
    date_column: str
):

    column = find_column(
        df,
        date_column
    )

    if column is None:

        raise ValueError(
            f"Date column '{date_column}' "
            "was not found."
        )

    result = df.copy()

    result[column] = pd.to_datetime(
        result[column],
        errors="coerce"
    )

    result = result.dropna(
        subset=[column]
    )

    return result, column


# ==========================================
# Average By Month
# ==========================================

def average_by_month(
    df: pd.DataFrame,
    value_column: str,
    date_column: str | None = None
):

    value_column = require_numeric_column(
        df,
        value_column
    )

    date_column = find_date_column(
        df,
        date_column
    )

    if date_column is None:

        raise ValueError(
            "No date column could be detected."
        )

    result, date_column = prepare_date_column(
        df,
        str(date_column)
    )

    result["__month"] = (
        result[date_column]
        .dt.to_period("M")
        .astype(str)
    )

    grouped = (
        result
        .groupby("__month")[value_column]
        .mean()
        .reset_index()
    )

    grouped.columns = [
        "month",
        "average"
    ]

    return dataframe_to_records(
        grouped
    )


# ==========================================
# Sum By Month
# ==========================================

def sum_by_month(
    df: pd.DataFrame,
    value_column: str,
    date_column: str | None = None
):

    value_column = require_numeric_column(
        df,
        value_column
    )

    date_column = find_date_column(
        df,
        date_column
    )

    if date_column is None:

        raise ValueError(
            "No date column could be detected."
        )

    result, date_column = prepare_date_column(
        df,
        str(date_column)
    )

    result["__month"] = (
        result[date_column]
        .dt.to_period("M")
        .astype(str)
    )

    grouped = (
        result
        .groupby("__month")[value_column]
        .sum()
        .reset_index()
    )

    grouped.columns = [
        "month",
        "total"
    ]

    return dataframe_to_records(
        grouped
    )


# ==========================================
# Highest Value Date
# ==========================================

def highest_value_date(
    df: pd.DataFrame,
    value_column: str,
    date_column: str | None = None
):

    value_column = require_numeric_column(
        df,
        value_column
    )

    date_column = find_date_column(
        df,
        date_column
    )

    if date_column is None:

        raise ValueError(
            "No date column could be detected."
        )

    result, date_column = prepare_date_column(
        df,
        str(date_column)
    )

    if result.empty:

        return None

    index = (
        result[value_column]
        .idxmax()
    )

    row = result.loc[index]

    return row_to_dict(
        row
    )


# ==========================================
# Lowest Value Date
# ==========================================

def lowest_value_date(
    df: pd.DataFrame,
    value_column: str,
    date_column: str | None = None
):

    value_column = require_numeric_column(
        df,
        value_column
    )

    date_column = find_date_column(
        df,
        date_column
    )

    if date_column is None:

        raise ValueError(
            "No date column could be detected."
        )

    result, date_column = prepare_date_column(
        df,
        str(date_column)
    )

    if result.empty:

        return None

    index = (
        result[value_column]
        .idxmin()
    )

    row = result.loc[index]

    return row_to_dict(
        row
    )


# ==========================================
# Monthly Statistics
# ==========================================

def monthly_statistics(
    df: pd.DataFrame,
    value_column: str,
    date_column: str | None = None
):

    value_column = require_numeric_column(
        df,
        value_column
    )

    date_column = find_date_column(
        df,
        date_column
    )

    if date_column is None:

        raise ValueError(
            "No date column could be detected."
        )

    result, date_column = prepare_date_column(
        df,
        str(date_column)
    )

    result["__month"] = (
        result[date_column]
        .dt.to_period("M")
        .astype(str)
    )

    grouped = (
        result
        .groupby("__month")[value_column]
        .agg(
            [
                "count",
                "mean",
                "min",
                "max",
                "sum"
            ]
        )
        .reset_index()
    )

    grouped.columns = [
        "month",
        "count",
        "average",
        "minimum",
        "maximum",
        "total"
    ]

    return dataframe_to_records(
        grouped
    )

# ==========================================
# Automatic Dataset Insights
# ==========================================

def dataset_insights(
    df: pd.DataFrame
) -> dict:
    """
    Generate a high-level analytical summary
    of the dataset.

    This is designed for questions like:

        - Analyze this dataset
        - Give me insights
        - Summarize this data
        - What can you tell me about this dataset?
    """

    if df is None:

        raise ValueError(
            "Dataset is None."
        )


    if df.empty:

        return {
            "success": False,
            "message": "The dataset is empty."
        }


    # ==========================================
    # Basic Overview
    # ==========================================

    rows = int(
        len(df)
    )

    columns = int(
        len(df.columns)
    )


    numeric_cols = get_numeric_columns(
        df
    )

    text_cols = get_text_columns(
        df
    )


    duplicate_count = calculate_duplicates(
        df
    )


    total_missing = calculate_total_missing(
        df
    )


    missing_by_column = calculate_missing(
        df
    )


    missing_percentages = missing_percentage(
        df
    )


    # ==========================================
    # Numeric Statistics
    # ==========================================

    numeric_statistics = {}


    for column in numeric_cols:

        try:

            numeric_statistics[
                str(column)
            ] = column_statistics(
                df,
                str(column)
            )

        except Exception:

            continue


    # ==========================================
    # Best / Worst Numeric Values
    # ==========================================

    highest_values = {}

    lowest_values = {}


    for column in numeric_cols:

        try:

            highest_values[
                str(column)
            ] = safe_number(
                df[column].max()
            )

            lowest_values[
                str(column)
            ] = safe_number(
                df[column].min()
            )

        except Exception:

            continue


    # ==========================================
    # Most Important Numeric Column
    #
    # Prefer financial columns when present.
    # ==========================================

    preferred_keywords = [
        "close",
        "price",
        "sales",
        "revenue",
        "profit",
        "amount",
        "volume",
    ]


    primary_numeric_column = None


    for keyword in preferred_keywords:

        for column in numeric_cols:

            normalized = (
                str(column)
                .strip()
                .lower()
                .replace("_", " ")
                .replace("-", " ")
            )


            if keyword in normalized:

                primary_numeric_column = column

                break


        if primary_numeric_column is not None:

            break


    # Fallback
    if (
        primary_numeric_column is None
        and numeric_cols
    ):

        primary_numeric_column = (
            numeric_cols[0]
        )


    # ==========================================
    # Primary Column Statistics
    # ==========================================

    primary_statistics = None


    if primary_numeric_column is not None:

        try:

            primary_statistics = (
                column_statistics(
                    df,
                    str(primary_numeric_column)
                )
            )

        except Exception:

            primary_statistics = None


    # ==========================================
    # Date Detection
    # ==========================================

    date_column = find_date_column(
        df
    )


    date_range = None


    if date_column is not None:

        try:

            date_series = pd.to_datetime(
                df[date_column],
                errors="coerce"
            ).dropna()


            if not date_series.empty:

                date_range = {

                    "column":
                        str(date_column),

                    "start":
                        str(
                            date_series.min()
                        ),

                    "end":
                        str(
                            date_series.max()
                        ),

                    "days":
                        int(
                            (
                                date_series.max()
                                -
                                date_series.min()
                            ).days
                        ),

                }

        except Exception:

            date_range = None


    # ==========================================
    # Highest / Lowest Primary Value
    # ==========================================

    highest_row_result = None

    lowest_row_result = None


    if primary_numeric_column is not None:

        try:

            highest_row_result = highest_row(
                df,
                str(primary_numeric_column)
            )

        except Exception:

            highest_row_result = None


        try:

            lowest_row_result = lowest_row(
                df,
                str(primary_numeric_column)
            )

        except Exception:

            lowest_row_result = None


    # ==========================================
    # Correlation Matrix
    # ==========================================

    correlations = {}


    if len(numeric_cols) >= 2:

        try:

            correlations = (
                correlation_matrix(df)
            )

        except Exception:

            correlations = {}


    # ==========================================
    # Strong Correlations
    # ==========================================

    strong_correlations = []


    if correlations:

        processed_pairs = set()


        for column_a, values in correlations.items():

            for column_b, value in values.items():

                if column_a == column_b:

                    continue


                pair = tuple(
                    sorted(
                        [
                            str(column_a),
                            str(column_b)
                        ]
                    )
                )


                if pair in processed_pairs:

                    continue


                processed_pairs.add(
                    pair
                )


                if value is None:

                    continue


                try:

                    correlation_value = float(
                        value
                    )

                except (
                    TypeError,
                    ValueError
                ):

                    continue


                if abs(
                    correlation_value
                ) >= 0.7:

                    strong_correlations.append({

                        "column_a":
                            str(column_a),

                        "column_b":
                            str(column_b),

                        "correlation":
                            round(
                                correlation_value,
                                4
                            ),

                    })


    # ==========================================
    # Most Common Values
    # ==========================================

    common_values = {}


    for column in text_cols:

        try:

            values = top_values(
                df,
                str(column),
                n=5
            )


            common_values[
                str(column)
            ] = values

        except Exception:

            continue


    # ==========================================
    # Data Quality Score
    # ==========================================

    total_cells = (
        rows * columns
    )


    if total_cells > 0:

        missing_ratio = (
            total_missing
            /
            total_cells
        )

    else:

        missing_ratio = 0


    duplicate_ratio = (

        duplicate_count
        /
        rows

        if rows > 0

        else 0

    )


    quality_score = 100.0


    quality_score -= (
        missing_ratio * 60
    )


    quality_score -= (
        duplicate_ratio * 40
    )


    quality_score = max(
        0.0,
        min(
            100.0,
            round(
                quality_score,
                2
            )
        )
    )


    # ==========================================
    # Dataset Type
    # ==========================================

    if date_column is not None:

        if len(numeric_cols) >= 1:

            dataset_type = (
                "time-series"
            )

        else:

            dataset_type = (
                "date-based"
            )

    elif len(numeric_cols) >= 1:

        if len(text_cols) >= 1:

            dataset_type = (
                "mixed analytical dataset"
            )

        else:

            dataset_type = (
                "numeric dataset"
            )

    else:

        dataset_type = (
            "categorical dataset"
        )


    # ==========================================
    # Build Result
    # ==========================================

    return {

        "success": True,

        "dataset_type":
            dataset_type,

        "rows":
            rows,

        "columns":
            columns,

        "column_names": [

            str(column)

            for column in df.columns

        ],

        "numeric_columns": [

            str(column)

            for column in numeric_cols

        ],

        "text_columns": [

            str(column)

            for column in text_cols

        ],

        "date_column":
            (
                str(date_column)
                if date_column is not None
                else None
            ),

        "date_range":
            date_range,

        "duplicate_rows":
            duplicate_count,

        "total_missing_values":
            total_missing,

        "missing_values":
            missing_by_column,

        "missing_percentages":
            missing_percentages,

        "data_quality_score":
            quality_score,

        "primary_numeric_column":
            (
                str(primary_numeric_column)
                if primary_numeric_column is not None
                else None
            ),

        "primary_statistics":
            primary_statistics,

        "numeric_statistics":
            numeric_statistics,

        "highest_values":
            highest_values,

        "lowest_values":
            lowest_values,

        "highest_row":
            highest_row_result,

        "lowest_row":
            lowest_row_result,

        "correlations":
            correlations,

        "strong_correlations":
            strong_correlations,

        "common_values":
            common_values,

    }


# ==========================================
# Format Dataset Insights
# ==========================================

def format_dataset_insights(
    insights: dict
) -> str:
    """
    Convert dataset_insights() output into
    a human-readable Markdown response.
    """

    if not insights:

        return (
            "I couldn't generate insights "
            "from the dataset."
        )


    if not insights.get(
        "success",
        False
    ):

        return insights.get(
            "message",
            "Unable to analyze dataset."
        )


    # ==========================================
    # Basic Information
    # ==========================================

    lines = []


    lines.append(
        "## 📊 Dataset Analysis"
    )


    lines.append("")


    lines.append(
        f"- **Rows:** "
        f"{insights['rows']:,}"
    )


    lines.append(
        f"- **Columns:** "
        f"{insights['columns']:,}"
    )


    lines.append(
        f"- **Dataset type:** "
        f"{insights['dataset_type']}"
    )


    lines.append(
        f"- **Duplicate rows:** "
        f"{insights['duplicate_rows']:,}"
    )


    lines.append(
        f"- **Missing values:** "
        f"{insights['total_missing_values']:,}"
    )


    lines.append(
        f"- **Data quality score:** "
        f"{insights['data_quality_score']}/100"
    )


    # ==========================================
    # Columns
    # ==========================================

    lines.append("")

    lines.append(
        "### 📋 Columns"
    )

    lines.append("")


    for column in insights[
        "column_names"
    ]:

        lines.append(
            f"- `{column}`"
        )


    # ==========================================
    # Date Range
    # ==========================================

    date_range = insights.get(
        "date_range"
    )


    if date_range:

        lines.append("")

        lines.append(
            "### 📅 Time Period"
        )

        lines.append("")


        lines.append(
            f"- **Start:** "
            f"{date_range['start']}"
        )


        lines.append(
            f"- **End:** "
            f"{date_range['end']}"
        )


        lines.append(
            f"- **Duration:** "
            f"{date_range['days']:,} days"
        )


    # ==========================================
    # Primary Numeric Column
    # ==========================================

    primary_column = insights.get(
        "primary_numeric_column"
    )


    primary_stats = insights.get(
        "primary_statistics"
    )


    if (
        primary_column
        and primary_stats
    ):

        lines.append("")

        lines.append(
            f"### 📈 Key Statistics — "
            f"{primary_column}"
        )

        lines.append("")


        if primary_stats.get(
            "mean"
        ) is not None:

            lines.append(
                f"- **Average:** "
                f"{format_insight_number(primary_stats['mean'])}"
            )


        if primary_stats.get(
            "median"
        ) is not None:

            lines.append(
                f"- **Median:** "
                f"{format_insight_number(primary_stats['median'])}"
            )


        if primary_stats.get(
            "min"
        ) is not None:

            lines.append(
                f"- **Minimum:** "
                f"{format_insight_number(primary_stats['min'])}"
            )


        if primary_stats.get(
            "max"
        ) is not None:

            lines.append(
                f"- **Maximum:** "
                f"{format_insight_number(primary_stats['max'])}"
            )


        if primary_stats.get(
            "std"
        ) is not None:

            lines.append(
                f"- **Standard deviation:** "
                f"{format_insight_number(primary_stats['std'])}"
            )


    # ==========================================
    # Best Row
    # ==========================================

    highest = insights.get(
        "highest_row"
    )


    if highest:

        lines.append("")

        lines.append(
            f"### 🔥 Highest "
            f"{primary_column}"
        )

        lines.append("")


        for key, value in highest.items():

            lines.append(
                f"- **{key}:** "
                f"{format_insight_value(value)}"
            )


    # ==========================================
    # Worst Row
    # ==========================================

    lowest = insights.get(
        "lowest_row"
    )


    if lowest:

        lines.append("")

        lines.append(
            f"### 📉 Lowest "
            f"{primary_column}"
        )

        lines.append("")


        for key, value in lowest.items():

            lines.append(
                f"- **{key}:** "
                f"{format_insight_value(value)}"
            )


    # ==========================================
    # Missing Values
    # ==========================================

    missing = insights.get(
        "missing_values",
        {}
    )


    if missing:

        lines.append("")

        lines.append(
            "### ⚠️ Missing Values"
        )

        lines.append("")


        for column, count in missing.items():

            percentage = (
                insights[
                    "missing_percentages"
                ].get(
                    column,
                    0
                )
            )


            lines.append(
                f"- **{column}:** "
                f"{count:,} "
                f"({percentage}%)"
            )


    else:

        lines.append("")

        lines.append(
            "### ✅ Data Quality"
        )

        lines.append("")

        lines.append(
            "No missing values were detected."
        )


    # ==========================================
    # Strong Correlations
    # ==========================================

    correlations = insights.get(
        "strong_correlations",
        []
    )


    if correlations:

        lines.append("")

        lines.append(
            "### 🔗 Strong Correlations"
        )

        lines.append("")


        for item in correlations:

            lines.append(
                f"- **{item['column_a']}** ↔ "
                f"**{item['column_b']}**: "
                f"{item['correlation']}"
            )


    # ==========================================
    # Finish
    # ==========================================

    return "\n".join(
        lines
    )


# ==========================================
# Format Insight Number
# ==========================================

def format_insight_number(
    value
):

    if value is None:

        return "N/A"


    try:

        value = float(
            value
        )


        if value.is_integer():

            return f"{int(value):,}"


        return f"{value:,.4f}"


    except (
        TypeError,
        ValueError
    ):

        return str(value)


# ==========================================
# Format Insight Value
# ==========================================

def format_insight_value(
    value
):

    if value is None:

        return "N/A"


    if isinstance(
        value,
        (int, float)
    ):

        return format_insight_number(
            value
        )


    return str(value)

# ==========================================
# Smart Column Understanding
# ==========================================

def normalize_column_name(column_name: str) -> str:
    """
    Normalize a column name for easier matching.
    """

    if column_name is None:
        return ""

    value = str(column_name).strip().lower()

    replacements = {
        "_": " ",
        "-": " ",
        ".": " ",
    }

    for old, new in replacements.items():
        value = value.replace(old, new)

    return " ".join(value.split())


# ==========================================
# Column Aliases
# ==========================================

COLUMN_ALIASES = {

    # Date / Time
    "date": {
        "date",
        "datetime",
        "timestamp",
        "time",
        "day",
    },

    # Open
    "open": {
        "open",
        "opening",
        "opening price",
        "open price",
    },

    # High
    "high": {
        "high",
        "highest",
        "high price",
        "highest price",
    },

    # Low
    "low": {
        "low",
        "lowest",
        "low price",
        "lowest price",
    },

    # Close
    "close": {
        "close",
        "closing",
        "closing price",
        "close price",
        "closing value",
        "close value",
    },

    # Adjusted Close
    "adjusted close": {
        "adjusted close",
        "adjusted closing",
        "adj close",
        "adj closing",
        "adjusted close price",
    },

    # Volume
    "volume": {
        "volume",
        "trading volume",
        "trade volume",
    },

    # Revenue
    "revenue": {
        "revenue",
        "sales",
        "total sales",
        "income",
    },

    # Profit
    "profit": {
        "profit",
        "net profit",
        "earnings",
        "net income",
    },

}


# ==========================================
# Find Smart Column
# ==========================================

def find_smart_column(
    df: pd.DataFrame,
    requested_column: str
):
    """
    Find a dataframe column using:

    1. Exact match
    2. Case-insensitive match
    3. Normalized match
    4. Common aliases
    5. Partial matching
    """

    if not requested_column:
        return None


    requested = normalize_column_name(
        requested_column
    )


    # ==========================================
    # Exact / Normalized Match
    # ==========================================

    for column in df.columns:

        normalized_column = (
            normalize_column_name(
                column
            )
        )

        if normalized_column == requested:

            return column


    # ==========================================
    # Alias Match
    # ==========================================

    for canonical_name, aliases in COLUMN_ALIASES.items():

        normalized_aliases = {
            normalize_column_name(alias)
            for alias in aliases
        }


        if requested in normalized_aliases:

            for column in df.columns:

                normalized_column = (
                    normalize_column_name(
                        column
                    )
                )


                if (
                    normalized_column
                    == canonical_name
                ):

                    return column


    # ==========================================
    # Requested Text Inside Column Name
    # ==========================================

    for column in df.columns:

        normalized_column = (
            normalize_column_name(
                column
            )
        )


        if (
            requested in normalized_column
            or normalized_column in requested
        ):

            return column


    # ==========================================
    # Alias Partial Match
    # ==========================================

    for canonical_name, aliases in COLUMN_ALIASES.items():

        for alias in aliases:

            normalized_alias = (
                normalize_column_name(
                    alias
                )
            )


            if (
                normalized_alias in requested
                or requested in normalized_alias
            ):

                for column in df.columns:

                    normalized_column = (
                        normalize_column_name(
                            column
                        )
                    )


                    if (
                        normalized_column
                        == canonical_name
                    ):

                        return column


    return None


# ==========================================
# Detect Columns From Question
# ==========================================

def detect_columns_from_question(
    df: pd.DataFrame,
    question: str
) -> list:
    """
    Detect dataframe columns mentioned
    directly or indirectly in a question.
    """

    if not question:

        return []


    normalized_question = (
        normalize_column_name(
            question
        )
    )


    detected = []


    # ==========================================
    # Direct Column Matching
    # ==========================================

    for column in df.columns:

        normalized_column = (
            normalize_column_name(
                column
            )
        )


        if normalized_column in normalized_question:

            detected.append(
                column
            )


    # ==========================================
    # Alias Matching
    # ==========================================

    for canonical_name, aliases in COLUMN_ALIASES.items():

        for alias in aliases:

            normalized_alias = (
                normalize_column_name(
                    alias
                )
            )


            if normalized_alias in normalized_question:

                column = find_smart_column(
                    df,
                    canonical_name
                )


                if (
                    column is not None
                    and column not in detected
                ):

                    detected.append(
                        column
                    )


                break


    return detected


# ==========================================
# Get Numeric Columns
# ==========================================

def get_numeric_columns(
    df: pd.DataFrame
) -> list:

    return [

        column

        for column in df.columns

        if pd.api.types.is_numeric_dtype(
            df[column]
        )

    ]


# ==========================================
# Get Date Columns
# ==========================================

def get_date_columns(
    df: pd.DataFrame
) -> list:

    date_columns = []


    for column in df.columns:

        series = df[column]


        # Already datetime
        if pd.api.types.is_datetime64_any_dtype(
            series
        ):

            date_columns.append(
                column
            )

            continue


        # Date-like column name
        normalized = (
            normalize_column_name(
                column
            )
        )


        if any(
            word in normalized
            for word in [
                "date",
                "time",
                "timestamp",
            ]
        ):

            try:

                converted = pd.to_datetime(
                    series,
                    errors="coerce"
                )


                valid_ratio = (
                    converted.notna().mean()
                )


                if valid_ratio >= 0.6:

                    date_columns.append(
                        column
                    )

            except Exception:

                pass


    return date_columns


# ==========================================
# Dataset Column Intelligence
# ==========================================

def get_column_intelligence(
    df: pd.DataFrame
) -> dict:

    numeric_columns = (
        get_numeric_columns(df)
    )

    date_columns = (
        get_date_columns(df)
    )


    categorical_columns = [

        column

        for column in df.columns

        if column not in numeric_columns
        and column not in date_columns

    ]


    return {

        "all_columns": [
            str(column)
            for column in df.columns
        ],

        "numeric_columns": [
            str(column)
            for column in numeric_columns
        ],

        "date_columns": [
            str(column)
            for column in date_columns
        ],

        "categorical_columns": [
            str(column)
            for column in categorical_columns
        ],

    }

# ==========================================
# ADVANCED DATASET INTELLIGENCE
# ==========================================

def generate_dataset_intelligence(df):

    result = {
        "overview": {},
        "data_quality": {},
        "numeric_statistics": {},
        "categorical_statistics": {},
        "insights": [],
    }

    # ==========================================
    # OVERVIEW
    # ==========================================

    result["overview"] = {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "column_names": [
            str(column)
            for column in df.columns
        ],
        "duplicate_rows": int(
            df.duplicated().sum()
        ),
    }

    # ==========================================
    # DATA QUALITY
    # ==========================================

    missing = {}

    for column in df.columns:

        count = int(
            df[column].isna().sum()
        )

        if count > 0:

            missing[str(column)] = count

    result["data_quality"] = {

        "missing_values": missing,

        "total_missing": int(
            df.isna().sum().sum()
        ),

        "duplicate_rows": int(
            df.duplicated().sum()
        ),

        "data_types": {

            str(column):
            str(df[column].dtype)

            for column in df.columns

        },

    }

    # ==========================================
    # NUMERIC STATISTICS
    # ==========================================

    numeric_columns = df.select_dtypes(
        include="number"
    ).columns

    for column in numeric_columns:

        series = df[column].dropna()

        if series.empty:
            continue

        result["numeric_statistics"][
            str(column)
        ] = {

            "count": int(
                series.count()
            ),

            "mean": float(
                series.mean()
            ),

            "median": float(
                series.median()
            ),

            "minimum": float(
                series.min()
            ),

            "maximum": float(
                series.max()
            ),

            "standard_deviation": float(
                series.std()
            ),

        }

    # ==========================================
    # CATEGORICAL STATISTICS
    # ==========================================

    categorical_columns = df.select_dtypes(
        exclude="number"
    ).columns

    for column in categorical_columns:

        series = df[column].dropna()

        if series.empty:
            continue

        result["categorical_statistics"][
            str(column)
        ] = {

            "unique_values": int(
                series.nunique()
            ),

            "most_common": str(
                series.mode().iloc[0]
                if not series.mode().empty
                else "N/A"
            ),

        }

    # ==========================================
    # AUTOMATIC INSIGHTS
    # ==========================================

    insights = []

    # Missing values
    if result["data_quality"][
        "total_missing"
    ] > 0:

        insights.append(
            "The dataset contains "
            f"{result['data_quality']['total_missing']:,} "
            "missing values."
        )

    else:

        insights.append(
            "The dataset contains no missing values."
        )

    # Duplicates
    duplicates = result["overview"][
        "duplicate_rows"
    ]

    if duplicates > 0:

        insights.append(
            f"The dataset contains "
            f"{duplicates:,} duplicate rows."
        )

    else:

        insights.append(
            "No duplicate rows were detected."
        )

    # Numeric insights
    for column, stats in result[
        "numeric_statistics"
    ].items():

        mean = stats["mean"]
        minimum = stats["minimum"]
        maximum = stats["maximum"]

        if maximum != minimum:

            range_value = (
                maximum - minimum
            )

            insights.append(
                f"{column} ranges from "
                f"{minimum:,.2f} to "
                f"{maximum:,.2f}, with an "
                f"average of {mean:,.2f}."
            )

    # Categorical insights
    for column, stats in result[
        "categorical_statistics"
    ].items():

        insights.append(
            f"{column} contains "
            f"{stats['unique_values']:,} "
            "unique values."
        )

    result["insights"] = insights

    return result

# ==========================================
# FORMAT DATASET INTELLIGENCE
# ==========================================

def format_dataset_intelligence(
    intelligence
):

    overview = intelligence[
        "overview"
    ]

    quality = intelligence[
        "data_quality"
    ]

    numeric = intelligence[
        "numeric_statistics"
    ]

    categorical = intelligence[
        "categorical_statistics"
    ]

    insights = intelligence[
        "insights"
    ]

    answer = []

    # ==========================================
    # TITLE
    # ==========================================

    answer.append(
        "## 📊 Dataset Intelligence Report"
    )

    answer.append("")

    # ==========================================
    # OVERVIEW
    # ==========================================

    answer.append(
        "### Dataset Overview"
    )

    answer.append("")

    answer.append(
        f"- **Rows:** {overview['rows']:,}"
    )

    answer.append(
        f"- **Columns:** {overview['columns']:,}"
    )

    answer.append(
        f"- **Duplicate Rows:** "
        f"{overview['duplicate_rows']:,}"
    )

    answer.append("")

    answer.append(
        "**Columns:**"
    )

    for column in overview[
        "column_names"
    ]:

        answer.append(
            f"- `{column}`"
        )

    answer.append("")

    # ==========================================
    # DATA QUALITY
    # ==========================================

    answer.append(
        "### 🔍 Data Quality"
    )

    answer.append("")

    answer.append(
        f"- **Total Missing Values:** "
        f"{quality['total_missing']:,}"
    )

    answer.append(
        f"- **Duplicate Rows:** "
        f"{quality['duplicate_rows']:,}"
    )

    if quality["missing_values"]:

        answer.append("")

        answer.append(
            "**Missing Values by Column:**"
        )

        for column, count in quality[
            "missing_values"
        ].items():

            answer.append(
                f"- `{column}`: {count:,}"
            )

    answer.append("")

    # ==========================================
    # NUMERIC STATISTICS
    # ==========================================

    if numeric:

        answer.append(
            "### 📈 Numeric Statistics"
        )

        answer.append("")

        for column, stats in numeric.items():

            answer.append(
                f"**{column}**"
            )

            answer.append(
                f"- Mean: "
                f"{stats['mean']:,.2f}"
            )

            answer.append(
                f"- Median: "
                f"{stats['median']:,.2f}"
            )

            answer.append(
                f"- Minimum: "
                f"{stats['minimum']:,.2f}"
            )

            answer.append(
                f"- Maximum: "
                f"{stats['maximum']:,.2f}"
            )

            answer.append(
                f"- Standard Deviation: "
                f"{stats['standard_deviation']:,.2f}"
            )

            answer.append("")

    # ==========================================
    # CATEGORICAL STATISTICS
    # ==========================================

    if categorical:

        answer.append(
            "### 🏷️ Categorical Statistics"
        )

        answer.append("")

        for column, stats in categorical.items():

            answer.append(
                f"- **{column}** — "
                f"{stats['unique_values']:,} "
                f"unique values; "
                f"most common: "
                f"`{stats['most_common']}`"
            )

        answer.append("")

    # ==========================================
    # INSIGHTS
    # ==========================================

    if insights:

        answer.append(
            "### 💡 Automatic Insights"
        )

        answer.append("")

        for insight in insights:

            answer.append(
                f"- {insight}"
            )

        answer.append("")

    return "\n".join(answer)

# ==========================================
# CHART DATA GENERATOR
# ==========================================

def generate_chart_data(
    df: pd.DataFrame,
    question: str
):
    """
    Automatically prepares chart data based
    on the user's question.
    """

    q = question.lower().strip()

    # ------------------------------------------
    # Find columns
    # ------------------------------------------

    columns = find_columns_from_question(
        df,
        question
    )

    numeric_columns = [
        column
        for column in df.columns
        if pd.api.types.is_numeric_dtype(
            df[column]
        )
    ]

    # ------------------------------------------
    # Detect date column
    # ------------------------------------------

    date_column = None

    for column in df.columns:

        name = normalize_text(column)

        if any(
            word in name
            for word in [
                "date",
                "time",
                "datetime",
                "timestamp"
            ]
        ):

            date_column = column
            break

    # ------------------------------------------
    # Detect requested numeric column
    # ------------------------------------------

    value_column = find_numeric_column(
        df,
        question
    )

    if value_column is None and numeric_columns:

        value_column = numeric_columns[0]

    if value_column is None:

        return {
            "success": False,
            "error": (
                "No numeric column was found "
                "for the chart."
            )
        }

    # ------------------------------------------
    # Determine chart type
    # ------------------------------------------

    chart_type = "line"

    if "bar chart" in q:
        chart_type = "bar"

    elif "bar graph" in q:
        chart_type = "bar"

    elif "histogram" in q:
        chart_type = "histogram"

    elif "scatter" in q:
        chart_type = "scatter"

    elif "pie chart" in q:
        chart_type = "pie"

    elif "pie graph" in q:
        chart_type = "pie"

    elif "line chart" in q:
        chart_type = "line"

    elif "line graph" in q:
        chart_type = "line"

    # ------------------------------------------
    # X axis
    # ------------------------------------------

    if date_column is not None:

        x_column = date_column

    else:

        x_column = df.index.name or "index"

        temp_df = df.copy()

        temp_df[x_column] = range(
            len(temp_df)
        )

        df = temp_df

    # ------------------------------------------
    # Clean data
    # ------------------------------------------

    chart_df = df[
        [x_column, value_column]
    ].copy()

    chart_df = chart_df.dropna()

    # ------------------------------------------
    # Convert datetime
    # ------------------------------------------

    if date_column is not None:

        try:

            chart_df[x_column] = pd.to_datetime(
                chart_df[x_column]
            )

            chart_df = chart_df.sort_values(
                x_column
            )

        except Exception:

            pass

    # ------------------------------------------
    # Limit huge datasets
    # ------------------------------------------

    if len(chart_df) > 5000:

        chart_df = chart_df.tail(5000)

    # ------------------------------------------
    # Convert values to JSON-safe format
    # ------------------------------------------

    records = []

    for _, row in chart_df.iterrows():

        x_value = row[x_column]
        y_value = row[value_column]

        if pd.isna(x_value):
            continue

        if pd.isna(y_value):
            continue

        if hasattr(
            x_value,
            "isoformat"
        ):

            x_value = x_value.isoformat()

        else:

            x_value = str(x_value)

        try:

            y_value = float(y_value)

        except (
            TypeError,
            ValueError
        ):

            continue

        records.append(
            {
                "x": x_value,
                "y": y_value
            }
        )

    # ------------------------------------------
    # Return chart object
    # ------------------------------------------

    return {

        "success": True,

        "chart": {

            "type": chart_type,

            "title": (
                f"{value_column} "
                f"{chart_type.title()}"
            ),

            "x_label": str(
                x_column
            ),

            "y_label": str(
                value_column
            ),

            "data": records,

        }

    }