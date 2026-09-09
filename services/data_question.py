import re
from typing import Optional

import pandas as pd


# ==========================================
# Data Query Functions
# ==========================================

from services.data_query import (
    load_dataset,
    dataset_overview,
    dataset_insights,
    format_dataset_insights,
    calculate_average,
    calculate_maximum,
    calculate_minimum,
    calculate_sum,
    calculate_count,
    calculate_missing,
    calculate_unique,
    top_values,
    calculate_median,
    calculate_standard_deviation,
    calculate_correlation,
    highest_row,
    lowest_row,
    top_rows,
    bottom_rows,
    dataset_preview,
    average_by_month,
    sum_by_month,
    monthly_statistics,
    highest_value_date,
    lowest_value_date,
)


# ==========================================
# Dataset Manager
# ==========================================

from services.dataset_manager import (
    get_chat_dataset,
)


# ==========================================
# Helpers
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
# Format Number
# ==========================================

def format_number(value):

    if value is None:
        return "N/A"

    try:

        value = float(value)

        if pd.isna(value):
            return "N/A"

        if value.is_integer():
            return f"{int(value):,}"

        return f"{value:,.4f}"

    except (
        TypeError,
        ValueError,
    ):

        return str(value)


# ==========================================
# Format Row
# ==========================================

def format_row(row):

    if not row:
        return "No matching row was found."

    lines = []

    for key, value in row.items():

        if (
            pd.isna(value)
            if not isinstance(
                value,
                (dict, list)
            )
            else False
        ):

            value = "N/A"

        elif isinstance(value, float):

            value = format_number(value)

        lines.append(
            f"- **{key}**: {value}"
        )

    return "\n".join(lines)


# ==========================================
# Format Records
# ==========================================

def format_records(records):

    if not records:
        return "No records found."

    lines = []

    for index, record in enumerate(
        records,
        start=1
    ):

        lines.append(
            f"### {index}."
        )

        for key, value in record.items():

            if value is None:

                value = "N/A"

            elif isinstance(value, float):

                value = format_number(value)

            lines.append(
                f"- **{key}**: {value}"
            )

        lines.append("")

    return "\n".join(lines)


# ==========================================
# SMART COLUMN ALIASES
# ==========================================

COLUMN_ALIASES = {

    "close": {
        "close",
        "closing",
        "closing price",
        "close price",
        "closing value",
        "close value",
        "closing rate",
        "closing amount",
        "market close",
        "closing market price",
        "adj close",
        "adjusted close",
    },

    "open": {
        "open",
        "opening",
        "opening price",
        "open price",
        "opening value",
        "opening rate",
    },

    "high": {
        "high",
        "highest",
        "highest price",
        "high price",
        "highest value",
        "daily high",
        "high value",
    },

    "low": {
        "low",
        "lowest",
        "lowest price",
        "low price",
        "lowest value",
        "daily low",
        "low value",
    },

    "volume": {
        "volume",
        "vol",
        "trading volume",
        "trade volume",
        "transaction volume",
    },

    "adjusted close": {
        "adjusted close",
        "adjusted closing",
        "adjusted closing price",
        "adj close",
        "adj closing",
        "adj close price",
    },

    "date": {
        "date",
        "day",
        "datetime",
        "date time",
        "timestamp",
        "time",
    },

    "sales": {
        "sales",
        "sale",
        "total sales",
        "sales amount",
        "sales value",
    },

    "revenue": {
        "revenue",
        "income",
        "total revenue",
        "revenue amount",
        "revenue value",
    },

    "profit": {
        "profit",
        "profits",
        "net profit",
        "profit amount",
        "profit value",
        "earnings",
        "net income",
    },

    "quantity": {
        "quantity",
        "qty",
        "units",
        "number of units",
    },

}


# ==========================================
# SMART COLUMN DETECTION
# ==========================================

def find_column_from_question(
    df: pd.DataFrame,
    question: str
) -> Optional[str]:

    question_normalized = normalize_text(
        question
    )

    if not question_normalized:
        return None

    # ==========================================
    # 1. Exact Column Match
    # ==========================================

    exact_candidates = []

    for column in df.columns:

        original = str(column)

        normalized = normalize_text(
            original
        )

        if not normalized:
            continue

        if normalized in question_normalized:

            exact_candidates.append(
                (
                    original,
                    len(normalized)
                )
            )

    if exact_candidates:

        exact_candidates.sort(
            key=lambda item: item[1],
            reverse=True
        )

        return exact_candidates[0][0]

    # ==========================================
    # 2. Word-Based Column Match
    # ==========================================

    candidates = []

    question_words = set(
        question_normalized.split()
    )

    for column in df.columns:

        original = str(column)

        normalized = normalize_text(
            original
        )

        column_words = normalized.split()

        if not column_words:
            continue

        if all(
            word in question_words
            for word in column_words
        ):

            candidates.append(
                (
                    original,
                    len(column_words)
                )
            )

    if candidates:

        candidates.sort(
            key=lambda item: item[1],
            reverse=True
        )

        return candidates[0][0]

    # ==========================================
    # 3. Smart Alias Matching
    # ==========================================

    alias_matches = []

    for canonical, aliases in COLUMN_ALIASES.items():

        for alias in aliases:

            alias_normalized = normalize_text(
                alias
            )

            if alias_normalized in question_normalized:

                for column in df.columns:

                    column_normalized = normalize_text(
                        column
                    )

                    if column_normalized == canonical:

                        alias_matches.append(
                            (
                                column,
                                len(alias_normalized)
                            )
                        )

                    elif canonical in column_normalized:

                        alias_matches.append(
                            (
                                column,
                                len(alias_normalized)
                            )
                        )

    if alias_matches:

        alias_matches.sort(
            key=lambda item: item[1],
            reverse=True
        )

        return alias_matches[0][0]

    # ==========================================
    # 4. Partial Alias / Column Matching
    # ==========================================

    for canonical, aliases in COLUMN_ALIASES.items():

        mentioned = False

        for alias in aliases:

            alias_normalized = normalize_text(
                alias
            )

            if alias_normalized in question_normalized:

                mentioned = True
                break

        if not mentioned:
            continue

        for column in df.columns:

            column_normalized = normalize_text(
                column
            )

            if canonical in column_normalized:

                return column

    return None


# ==========================================
# Detect Multiple Columns
# ==========================================

def find_columns_from_question(
    df: pd.DataFrame,
    question: str
) -> list:

    detected = []

    question_normalized = normalize_text(
        question
    )

    # ==========================================
    # Direct column names
    # ==========================================

    for column in df.columns:

        normalized_column = normalize_text(
            column
        )

        if (
            normalized_column
            and normalized_column
            in question_normalized
        ):

            if column not in detected:

                detected.append(column)

    # ==========================================
    # Alias detection
    # ==========================================

    for canonical, aliases in COLUMN_ALIASES.items():

        alias_found = False

        for alias in aliases:

            if normalize_text(alias) in question_normalized:

                alias_found = True
                break

        if not alias_found:
            continue

        for column in df.columns:

            normalized_column = normalize_text(
                column
            )

            if (
                normalized_column == canonical
                or canonical in normalized_column
            ):

                if column not in detected:

                    detected.append(column)

    return detected


# ==========================================
# Numeric Column Detection
# ==========================================

def find_numeric_column(
    df: pd.DataFrame,
    question: str
):

    column = find_column_from_question(
        df,
        question
    )

    if column is not None:

        if pd.api.types.is_numeric_dtype(
            df[column]
        ):

            return column

    numeric_columns = [

        column

        for column in df.columns

        if pd.api.types.is_numeric_dtype(
            df[column]
        )

    ]

    # ==========================================
    # Exactly one numeric column
    # ==========================================

    if len(numeric_columns) == 1:

        return numeric_columns[0]

    # ==========================================
    # Financial Priority
    # ==========================================

    question_lower = (
        question.lower()
    )

    financial_priority = [

        "adjusted close",
        "close",
        "closing",
        "price",
        "volume",
        "sales",
        "revenue",
        "profit",
        "amount",

    ]

    for keyword in financial_priority:

        if keyword in question_lower:

            for column in numeric_columns:

                if (
                    keyword
                    in normalize_text(column)
                ):

                    return column

    # ==========================================
    # Generic Numeric Priority
    # ==========================================

    if numeric_columns:

        return numeric_columns[0]

    return None


# ==========================================
# Find Two Numeric Columns
# ==========================================

def find_two_numeric_columns(
    df: pd.DataFrame,
    question: str
):

    mentioned = find_columns_from_question(
        df,
        question
    )

    mentioned_numeric = [

        column

        for column in mentioned

        if pd.api.types.is_numeric_dtype(
            df[column]
        )

    ]

    if len(mentioned_numeric) >= 2:

        return mentioned_numeric[:2]

    numeric = [

        column

        for column in df.columns

        if pd.api.types.is_numeric_dtype(
            df[column]
        )

    ]

    if len(numeric) >= 2:

        return numeric[:2]

    return []


# ==========================================
# Find N
# ==========================================

def find_n(
    question: str
):

    match = re.search(
        r"\b(?:top|bottom|first|last)\s+(\d+)\b",
        question.lower()
    )

    if match:

        return max(
            1,
            min(
                int(match.group(1)),
                100
            )
        )

    return 10


# ==========================================
# Success Response
# ==========================================

def success(
    answer,
    operation,
    column=None
):

    return {

        "success": True,

        "answer": answer,

        "operation": operation,

        "column": column,

    }


# ==========================================
# Failure Response
# ==========================================

def failure(
    answer,
    operation=None,
    column=None
):

    return {

        "success": False,

        "answer": answer,

        "operation": operation,

        "column": column,

    }


# ==========================================
# ADVANCED DATASET INTELLIGENCE
# ==========================================

def generate_dataset_intelligence(
    df: pd.DataFrame
):

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

        "rows": int(
            df.shape[0]
        ),

        "columns": int(
            df.shape[1]
        ),

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

            missing[
                str(column)
            ] = count

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

    numeric_columns = (
        df.select_dtypes(
            include="number"
        ).columns
    )

    for column in numeric_columns:

        series = df[column].dropna()

        if series.empty:
            continue

        result[
            "numeric_statistics"
        ][
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

    categorical_columns = (
        df.select_dtypes(
            exclude="number"
        ).columns
    )

    for column in categorical_columns:

        series = df[column].dropna()

        if series.empty:
            continue

        result[
            "categorical_statistics"
        ][
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

    total_missing = (
        result[
            "data_quality"
        ][
            "total_missing"
        ]
    )

    if total_missing > 0:

        insights.append(
            "The dataset contains "
            f"{total_missing:,} "
            "missing values."
        )

    else:

        insights.append(
            "The dataset contains "
            "no missing values."
        )

    duplicates = (
        result[
            "overview"
        ][
            "duplicate_rows"
        ]
    )

    if duplicates > 0:

        insights.append(
            "The dataset contains "
            f"{duplicates:,} "
            "duplicate rows."
        )

    else:

        insights.append(
            "No duplicate rows were detected."
        )

    for column, stats in result[
        "numeric_statistics"
    ].items():

        mean = stats["mean"]

        minimum = stats["minimum"]

        maximum = stats["maximum"]

        if maximum != minimum:

            insights.append(

                f"{column} ranges from "
                f"{minimum:,.2f} to "
                f"{maximum:,.2f}, "
                f"with an average of "
                f"{mean:,.2f}."

            )

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
        f"- **Rows:** "
        f"{overview['rows']:,}"
    )

    answer.append(
        f"- **Columns:** "
        f"{overview['columns']:,}"
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

    if quality[
        "missing_values"
    ]:

        answer.append("")

        answer.append(
            "**Missing Values by Column:**"
        )

        for column, count in quality[
            "missing_values"
        ].items():

            answer.append(
                f"- `{column}`: "
                f"{count:,}"
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
# Answer Data Question
# ==========================================

def answer_data_question(
    question: str,
    chat_id: int
):

    # ==========================================
    # Find Dataset
    # ==========================================

    dataset = get_chat_dataset(
        chat_id
    )

    if dataset is None:

        return failure(
            "I couldn't find a CSV or Excel "
            "dataset uploaded in this chat."
        )

    filepath = dataset[
        "filepath"
    ]

    # ==========================================
    # Load Dataset
    # ==========================================

    try:

        df = load_dataset(
            filepath
        )

    except Exception as e:

        return failure(
            f"I couldn't read the dataset: {e}"
        )

    if df.empty:

        return failure(
            "The uploaded dataset is empty."
        )

    q = question.lower().strip()

    # ==========================================
    # FULL DATASET ANALYSIS
    # ==========================================

    if (
        "analyze this dataset" in q
        or "analyse this dataset" in q
        or "analyze the dataset" in q
        or "analyse the dataset" in q
        or "analyze my dataset" in q
        or "analyse my dataset" in q
        or "analyze this data" in q
        or "analyse this data" in q
        or "analyze the data" in q
        or "analyse the data" in q
        or "give me insights" in q
        or "give me dataset insights" in q
        or "dataset insights" in q
        or "summarize this dataset" in q
        or "summarise this dataset" in q
        or "summarize the dataset" in q
        or "summarise the dataset" in q
        or "tell me about this dataset" in q
        or "what can you tell me about this dataset" in q
        or "give me an overview" in q
        or "analyze my data" in q
        or "analyse my data" in q
        or "summarize my data" in q
        or "summarise my data" in q
    ):

        try:

            intelligence = (
                generate_dataset_intelligence(
                    df
                )
            )

            answer = (
                format_dataset_intelligence(
                    intelligence
                )
            )

            return success(
                answer,
                "dataset_intelligence"
            )

        except Exception as e:

            return failure(
                (
                    "I couldn't analyze the "
                    f"dataset: {str(e)}"
                ),
                "dataset_intelligence"
            )

    # ==========================================
    # Find Columns
    # ==========================================

    column = find_numeric_column(
        df,
        question
    )

    mentioned_column = (
        find_column_from_question(
            df,
            question
        )
    )

    # ==========================================
    # ROW COUNT
    # ==========================================

    if (
        "how many rows" in q
        or "number of rows" in q
        or "row count" in q
        or "how many records" in q
        or "number of records" in q
        or "record count" in q
    ):

        count = calculate_count(
            df
        )

        return success(
            f"The dataset contains **{count:,} rows**.",
            "row_count"
        )

    # ==========================================
    # COLUMN COUNT
    # ==========================================

    if (
        "how many columns" in q
        or "number of columns" in q
        or "column count" in q
    ):

        return success(
            (
                f"The dataset contains "
                f"**{len(df.columns):,} columns**."
            ),
            "column_count"
        )

    # ==========================================
    # COLUMN NAMES
    # ==========================================

    if (
        "what columns" in q
        or "which columns" in q
        or "list columns" in q
        or "column names" in q
        or "columns are there" in q
    ):

        columns = [
            str(column)
            for column in df.columns
        ]

        formatted = "\n".join(
            f"- `{column}`"
            for column in columns
        )

        return success(
            (
                "The dataset contains these "
                "columns:\n\n"
                f"{formatted}"
            ),
            "column_names"
        )

    # ==========================================
    # DATA PREVIEW
    # ==========================================

    if (
        "show me the data" in q
        or "show the data" in q
        or "preview the data" in q
        or "preview dataset" in q
        or "first 5 rows" in q
        or "first five rows" in q
        or "sample data" in q
    ):

        records = dataset_preview(
            df,
            n=5
        )

        return success(
            (
                "### Dataset Preview\n\n"
                +
                format_records(records)
            ),
            "preview"
        )

    # ==========================================
    # MISSING VALUES
    # ==========================================

    if (
        "missing" in q
        or "null values" in q
        or "nulls" in q
        or "empty values" in q
        or "blank values" in q
    ):

        missing = calculate_missing(
            df
        )

        if not missing:

            answer = (
                "There are **no missing values** "
                "in the dataset."
            )

        else:

            lines = [

                f"- `{column}`: **{count:,}**"

                for column, count
                in missing.items()

            ]

            answer = (
                "### Missing Values\n\n"
                +
                "\n".join(lines)
            )

        return success(
            answer,
            "missing_values"
        )

    # ==========================================
    # DUPLICATES
    # ==========================================

    if (
        "duplicate" in q
        or "duplicates" in q
    ):

        count = int(
            df.duplicated().sum()
        )

        return success(
            (
                f"The dataset contains "
                f"**{count:,} duplicate rows**."
            ),
            "duplicates"
        )

    # ==========================================
    # MONTHLY AVERAGE
    # ==========================================

    if (
        (
            "average" in q
            or "mean" in q
        )
        and
        (
            "by month" in q
            or "each month" in q
            or "per month" in q
            or "monthly" in q
        )
    ):

        if column is None:

            return failure(
                (
                    "Which numeric column should "
                    "I calculate the monthly average for?"
                ),
                "average_by_month"
            )

        try:

            records = average_by_month(
                df,
                str(column)
            )

        except Exception as e:

            return failure(
                str(e),
                "average_by_month",
                str(column)
            )

        return success(
            (
                f"### Average {column} by Month\n\n"
                +
                format_records(records)
            ),
            "average_by_month",
            str(column)
        )

    # ==========================================
    # MONTHLY SUM
    # ==========================================

    if (
        (
            "sum" in q
            or "total" in q
        )
        and
        (
            "by month" in q
            or "each month" in q
            or "per month" in q
            or "monthly" in q
        )
    ):

        if column is None:

            return failure(
                (
                    "Which numeric column should "
                    "I calculate the monthly total for?"
                ),
                "sum_by_month"
            )

        try:

            records = sum_by_month(
                df,
                str(column)
            )

        except Exception as e:

            return failure(
                str(e),
                "sum_by_month",
                str(column)
            )

        return success(
            (
                f"### Total {column} by Month\n\n"
                +
                format_records(records)
            ),
            "sum_by_month",
            str(column)
        )

    # ==========================================
    # MONTHLY STATISTICS
    # ==========================================

    if (
        "monthly statistics" in q
        or "monthly stats" in q
        or "monthly summary" in q
        or "statistics by month" in q
        or "summary by month" in q
    ):

        if column is None:

            return failure(
                (
                    "Which numeric column should "
                    "I summarize by month?"
                ),
                "monthly_statistics"
            )

        try:

            records = monthly_statistics(
                df,
                str(column)
            )

        except Exception as e:

            return failure(
                str(e),
                "monthly_statistics",
                str(column)
            )

        return success(
            (
                f"### Monthly Statistics for {column}\n\n"
                +
                format_records(records)
            ),
            "monthly_statistics",
            str(column)
        )

    # ==========================================
    # HIGHEST VALUE DATE
    # ==========================================

    if (
        (
            "highest" in q
            or "highest value" in q
            or "best trading day" in q
            or "maximum day" in q
        )
        and
        (
            "date" in q
            or "day" in q
            or "when" in q
        )
    ):

        if column is None:

            return failure(
                (
                    "Which numeric column should "
                    "I use to find the highest date?"
                ),
                "highest_value_date"
            )

        try:

            row = highest_value_date(
                df,
                str(column)
            )

        except Exception as e:

            return failure(
                str(e),
                "highest_value_date",
                str(column)
            )

        return success(
            (
                f"### Highest {column} Date\n\n"
                +
                format_row(row)
            ),
            "highest_value_date",
            str(column)
        )

    # ==========================================
    # LOWEST VALUE DATE
    # ==========================================

    if (
        (
            "lowest" in q
            or "lowest value" in q
            or "worst trading day" in q
            or "minimum day" in q
        )
        and
        (
            "date" in q
            or "day" in q
            or "when" in q
        )
    ):

        if column is None:

            return failure(
                (
                    "Which numeric column should "
                    "I use to find the lowest date?"
                ),
                "lowest_value_date"
            )

        try:

            row = lowest_value_date(
                df,
                str(column)
            )

        except Exception as e:

            return failure(
                str(e),
                "lowest_value_date",
                str(column)
            )

        return success(
            (
                f"### Lowest {column} Date\n\n"
                +
                format_row(row)
            ),
            "lowest_value_date",
            str(column)
        )

    # ==========================================
    # CORRELATION
    # ==========================================

    if (
        "correlation" in q
        or "correlated" in q
        or "relationship between" in q
    ):

        columns = find_two_numeric_columns(
            df,
            question
        )

        if len(columns) < 2:

            return failure(
                (
                    "I need at least two numeric "
                    "columns to calculate correlation."
                ),
                "correlation"
            )

        column_a = columns[0]

        column_b = columns[1]

        try:

            result = calculate_correlation(
                df,
                str(column_a),
                str(column_b)
            )

        except Exception as e:

            return failure(
                str(e),
                "correlation",
                f"{column_a}, {column_b}"
            )

        return success(
            (
                f"The correlation between "
                f"**{column_a}** and "
                f"**{column_b}** is "
                f"**{format_number(result)}**."
            ),
            "correlation",
            f"{column_a}, {column_b}"
        )

    # ==========================================
    # MEDIAN
    # ==========================================

    if "median" in q:

        if column is None:

            return failure(
                (
                    "Which numeric column should "
                    "I calculate the median for?"
                ),
                "median"
            )

        try:

            result = calculate_median(
                df,
                str(column)
            )

        except Exception as e:

            return failure(
                str(e),
                "median",
                str(column)
            )

        return success(
            (
                f"The median of **{column}** is "
                f"**{format_number(result)}**."
            ),
            "median",
            str(column)
        )

    # ==========================================
    # STANDARD DEVIATION
    # ==========================================

    if (
        "standard deviation" in q
        or "std deviation" in q
        or "std dev" in q
        or "standard dev" in q
    ):

        if column is None:

            return failure(
                (
                    "Which numeric column should "
                    "I calculate the standard "
                    "deviation for?"
                ),
                "standard_deviation"
            )

        try:

            result = calculate_standard_deviation(
                df,
                str(column)
            )

        except Exception as e:

            return failure(
                str(e),
                "standard_deviation",
                str(column)
            )

        return success(
            (
                f"The standard deviation of "
                f"**{column}** is "
                f"**{format_number(result)}**."
            ),
            "standard_deviation",
            str(column)
        )

    # ==========================================
    # TOP N
    # ==========================================

    if (
        "top " in q
        or "top records" in q
        or "top rows" in q
        or "highest " in q
    ) and not (
        "highest value" in q
        or "highest row" in q
        or "highest date" in q
    ):

        top_column = find_numeric_column(
            df,
            question
        )

        if top_column is None:

            return failure(
                (
                    "Which numeric column should "
                    "I use for the top records?"
                ),
                "top_rows"
            )

        n = find_n(
            question
        )

        try:

            records = top_rows(
                df,
                str(top_column),
                n=n
            )

        except Exception as e:

            return failure(
                str(e),
                "top_rows",
                str(top_column)
            )

        return success(
            (
                f"### Top {n} records by "
                f"{top_column}\n\n"
                +
                format_records(records)
            ),
            "top_rows",
            str(top_column)
        )

    # ==========================================
    # BOTTOM N
    # ==========================================

    if (
        "bottom " in q
        or "bottom records" in q
        or "bottom rows" in q
        or "lowest " in q
    ) and not (
        "lowest value" in q
        or "lowest row" in q
        or "lowest date" in q
    ):

        bottom_column = find_numeric_column(
            df,
            question
        )

        if bottom_column is None:

            return failure(
                (
                    "Which numeric column should "
                    "I use for the bottom records?"
                ),
                "bottom_rows"
            )

        n = find_n(
            question
        )

        try:

            records = bottom_rows(
                df,
                str(bottom_column),
                n=n
            )

        except Exception as e:

            return failure(
                str(e),
                "bottom_rows",
                str(bottom_column)
            )

        return success(
            (
                f"### Bottom {n} records by "
                f"{bottom_column}\n\n"
                +
                format_records(records)
            ),
            "bottom_rows",
            str(bottom_column)
        )

    # ==========================================
    # UNIQUE VALUES
    # ==========================================

    if (
        "unique values" in q
        or "how many unique" in q
        or "unique count" in q
        or "distinct values" in q
    ):

        unique_column = mentioned_column

        if unique_column is None:

            return failure(
                (
                    "Which column should I "
                    "check for unique values?"
                ),
                "unique"
            )

        try:

            result = calculate_unique(
                df,
                str(unique_column)
            )

        except Exception as e:

            return failure(
                str(e),
                "unique",
                str(unique_column)
            )

        return success(
            (
                f"**{unique_column}** contains "
                f"**{result:,} unique values**."
            ),
            "unique",
            str(unique_column)
        )

    # ==========================================
    # MOST COMMON VALUES
    # ==========================================

    if (
        "most common" in q
        or "most frequent" in q
        or "frequent values" in q
        or "most popular" in q
    ):

        top_column = mentioned_column

        if top_column is None:

            return failure(
                (
                    "Which column should I find "
                    "the most common values for?"
                ),
                "top_values"
            )

        try:

            result = top_values(
                df,
                str(top_column),
                n=10
            )

        except Exception as e:

            return failure(
                str(e),
                "top_values",
                str(top_column)
            )

        lines = [

            f"- **{value}**: {count:,}"

            for value, count
            in result.items()

        ]

        return success(
            (
                f"### Most common values in "
                f"{top_column}\n\n"
                +
                "\n".join(lines)
            ),
            "top_values",
            str(top_column)
        )

    # ==========================================
    # AVERAGE / MEAN
    # ==========================================

    if (
        "average" in q
        or "mean" in q
        or "avg" in q
    ):

        if column is None:

            return failure(
                (
                    "Which numeric column should "
                    "I calculate the average for?"
                ),
                "average"
            )

        try:

            result = calculate_average(
                df,
                str(column)
            )

        except Exception as e:

            return failure(
                str(e),
                "average",
                str(column)
            )

        return success(
            (
                f"The average of **{column}** is "
                f"**{format_number(result)}**."
            ),
            "average",
            str(column)
        )

    # ==========================================
    # MAXIMUM
    # ==========================================

    if (
        "maximum" in q
        or "maximum value" in q
        or "highest value" in q
        or "max value" in q
        or "max of" in q
        or "highest" in q
    ):

        if column is None:

            return failure(
                (
                    "Which numeric column should "
                    "I find the maximum for?"
                ),
                "maximum"
            )

        try:

            result = calculate_maximum(
                df,
                str(column)
            )

        except Exception as e:

            return failure(
                str(e),
                "maximum",
                str(column)
            )

        return success(
            (
                f"The highest value in **{column}** "
                f"is **{format_number(result)}**."
            ),
            "maximum",
            str(column)
        )

    # ==========================================
    # MINIMUM
    # ==========================================

    if (
        "minimum" in q
        or "minimum value" in q
        or "lowest value" in q
        or "min value" in q
        or "min of" in q
        or "lowest" in q
    ):

        if column is None:

            return failure(
                (
                    "Which numeric column should "
                    "I find the minimum for?"
                ),
                "minimum"
            )

        try:

            result = calculate_minimum(
                df,
                str(column)
            )

        except Exception as e:

            return failure(
                str(e),
                "minimum",
                str(column)
            )

        return success(
            (
                f"The lowest value in **{column}** "
                f"is **{format_number(result)}**."
            ),
            "minimum",
            str(column)
        )

    # ==========================================
    # SUM / TOTAL
    # ==========================================

    if (
        "sum" in q
        or "total" in q
        or "total of" in q
    ):

        if column is None:

            return failure(
                (
                    "Which numeric column should "
                    "I calculate the total for?"
                ),
                "sum"
            )

        try:

            result = calculate_sum(
                df,
                str(column)
            )

        except Exception as e:

            return failure(
                str(e),
                "sum",
                str(column)
            )

        return success(
            (
                f"The total of **{column}** is "
                f"**{format_number(result)}**."
            ),
            "sum",
            str(column)
        )

    # ==========================================
    # HIGHEST ROW
    # ==========================================

    if (
        "which row had the highest" in q
        or "row with the highest" in q
        or "highest row" in q
    ):

        if column is None:

            return failure(
                (
                    "Which numeric column should "
                    "I use to find the highest row?"
                ),
                "highest_row"
            )

        try:

            row = highest_row(
                df,
                str(column)
            )

        except Exception as e:

            return failure(
                str(e),
                "highest_row",
                str(column)
            )

        return success(
            (
                f"### Row with highest {column}\n\n"
                +
                format_row(row)
            ),
            "highest_row",
            str(column)
        )

    # ==========================================
    # LOWEST ROW
    # ==========================================

    if (
        "which row had the lowest" in q
        or "row with the lowest" in q
        or "lowest row" in q
    ):

        if column is None:

            return failure(
                (
                    "Which numeric column should "
                    "I use to find the lowest row?"
                ),
                "lowest_row"
            )

        try:

            row = lowest_row(
                df,
                str(column)
            )

        except Exception as e:

            return failure(
                str(e),
                "lowest_row",
                str(column)
            )

        return success(
            (
                f"### Row with lowest {column}\n\n"
                +
                format_row(row)
            ),
            "lowest_row",
            str(column)
        )

    # ==========================================
    # GENERAL STATISTICS
    # ==========================================

    if (
        "statistics" in q
        or "describe" in q
        or "stats" in q
        or "summary" in q
        or "dataset overview" in q
        or "overview of dataset" in q
    ):

        overview = dataset_overview(
            df
        )

        numeric_columns = [

            str(column)

            for column in df.columns

            if pd.api.types.is_numeric_dtype(
                df[column]
            )

        ]

        answer = (
            "### Dataset Overview\n\n"
            f"- Rows: **{overview['rows']:,}**\n"
            f"- Columns: **{overview['columns']:,}**\n"
            f"- Duplicate rows: "
            f"**{overview['duplicate_rows']:,}**\n\n"
            "### Numeric Columns\n\n"
        )

        if numeric_columns:

            answer += "\n".join(
                f"- `{column}`"
                for column in numeric_columns
            )

        else:

            answer += (
                "No numeric columns were detected."
            )

        return success(
            answer,
            "statistics"
        )

    # ==========================================
    # Unsupported
    # ==========================================

    return failure(
        "I couldn't understand which data operation "
        "you want me to perform. Try asking for an "
        "average, maximum, minimum, sum, correlation, "
        "top values, dataset insights, or a chart."
    )


# ==========================================
# Compatibility Helpers
# ==========================================

def is_data_question(
    question: str
) -> bool:

    """
    Compatibility helper for chat.py.

    Returns True when the question looks like
    a dataset/data-analysis question.
    """

    q = normalize_text(
        question
    )

    keywords = [

        "dataset",
        "data",
        "csv",
        "excel",
        "average",
        "mean",
        "median",
        "maximum",
        "minimum",
        "highest",
        "lowest",
        "sum",
        "total",
        "count",
        "rows",
        "columns",
        "missing",
        "null",
        "duplicate",
        "unique",
        "statistics",
        "stats",
        "correlation",
        "top",
        "bottom",
        "monthly",
        "by month",
        "analyze",
        "analyse",
        "insights",
        "preview",

    ]

    return any(
        keyword in q
        for keyword in keywords
    )


def data_question(
    question: str,
    chat_id: int
):

    """
    Compatibility wrapper.

    chat.py can call either:

        answer_data_question()

    or:

        data_question()

    """

    return answer_data_question(
        question,
        chat_id
    )


# ==========================================
# END
# ==========================================