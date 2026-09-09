from pathlib import Path

import pandas as pd


# ==========================================
# Load Dataset
# ==========================================

def load_dataset(filepath: str) -> pd.DataFrame:
    """
    Load CSV or Excel dataset.
    """

    extension = Path(filepath).suffix.lower()

    if extension == ".csv":

        try:
            return pd.read_csv(filepath)

        except UnicodeDecodeError:

            return pd.read_csv(
                filepath,
                encoding="latin-1"
            )

    elif extension in [".xlsx", ".xls"]:

        return pd.read_excel(filepath)

    else:

        raise ValueError(
            f"Unsupported dataset format: {extension}"
        )


# ==========================================
# Profile Dataset
# ==========================================

def profile_dataset(filepath: str) -> dict:
    """
    Generate a profile for a CSV/Excel dataset.
    """

    df = load_dataset(filepath)

    profile = {

        "rows": int(len(df)),

        "columns": int(len(df.columns)),

        "column_names": [
            str(column)
            for column in df.columns
        ],

        "file_type": Path(
            filepath
        ).suffix.lower(),

    }


    # ==========================================
    # Column Information
    # ==========================================

    column_info = []

    for column in df.columns:

        series = df[column]

        information = {

            "name": str(column),

            "dtype": str(
                series.dtype
            ),

            "missing": int(
                series.isna().sum()
            ),

            "unique": int(
                series.nunique(
                    dropna=True
                )
            ),

        }


        # ==========================================
        # Numeric
        # ==========================================

        if pd.api.types.is_numeric_dtype(
            series
        ):

            information["type"] = "numeric"

            information["min"] = safe_number(
                series.min()
            )

            information["max"] = safe_number(
                series.max()
            )

            information["mean"] = safe_number(
                series.mean()
            )

            information["median"] = safe_number(
                series.median()
            )

            information["std"] = safe_number(
                series.std()
            )


        # ==========================================
        # Datetime
        # ==========================================

        elif pd.api.types.is_datetime64_any_dtype(
            series
        ):

            information["type"] = "datetime"

            information["min"] = (
                str(series.min())
                if not series.empty
                else None
            )

            information["max"] = (
                str(series.max())
                if not series.empty
                else None
            )


        # ==========================================
        # Text
        # ==========================================

        else:

            information["type"] = "text"

            information["sample"] = (
                series
                .dropna()
                .astype(str)
                .head(5)
                .tolist()
            )


        column_info.append(
            information
        )


    profile[
        "columns_info"
    ] = column_info


    # ==========================================
    # Missing Values
    # ==========================================

    profile[
        "missing_values"
    ] = {

        str(column): int(
            df[column].isna().sum()
        )

        for column in df.columns

        if df[column].isna().sum() > 0

    }


    # ==========================================
    # Duplicates
    # ==========================================

    profile[
        "duplicate_rows"
    ] = int(
        df.duplicated().sum()
    )


    # ==========================================
    # Preview
    # ==========================================

    profile[
        "preview"
    ] = df.head(10).to_dict(
        orient="records"
    )


    return profile


# ==========================================
# Safe Number
# ==========================================

def safe_number(value):

    if pd.isna(value):

        return None

    try:

        return float(value)

    except (
        TypeError,
        ValueError
    ):

        return None