from enum import Enum


# ==========================================
# Question Types
# ==========================================

class QuestionType(str, Enum):

    DATA = "data"

    DOCUMENT = "document"

    CHART = "chart"

    GENERAL = "general"


# ==========================================
# Chart Keywords
# ==========================================

CHART_KEYWORDS = {

    "plot",
    "chart",
    "graph",

    "visualize",
    "visualise",

    "visualization",
    "visualisation",

    "show graph",
    "show me a graph",
    "show me the graph",

    "show chart",
    "show me a chart",
    "show me the chart",

    "draw",

    "trend",
    "trends",

    "histogram",

    "scatter",
    "scatter plot",

    "bar",
    "bar chart",
    "bar graph",

    "line",
    "line chart",
    "line graph",

    "pie",
    "pie chart",

    "heatmap",
    "heat map",

    "price movement",
    "stock trend",

    "performance chart",

}


# ==========================================
# Data Keywords
# ==========================================

DATA_KEYWORDS = {

    "average",
    "avg",

    "mean",
    "median",

    "maximum",
    "minimum",

    "max",
    "min",

    "sum",
    "total",

    "count",

    "percentage",
    "percent",

    "variance",

    "standard deviation",
    "std",

    "correlation",

    "highest",
    "lowest",

    "largest",
    "smallest",

    "top",
    "bottom",

    "rows",
    "columns",

    "missing",
    "null",

    "duplicate",
    "duplicates",

    "unique",

    "statistics",
    "statistical",

    "describe",

    "dataset",
    "data",

    "value",

    "values",

    "records",

    "insights",

    "analysis",
    "analyze",
    "analyse",

    "summarize",
    "summarise",

    "overview",

}


# ==========================================
# Document Keywords
# ==========================================

DOCUMENT_KEYWORDS = {

    "document",

    "pdf",

    "report",

    "file",

    "uploaded",

    "upload",

    "uploaded document",
    "uploaded file",

    "document says",

    "according to",

    "according to the report",

    "according to the document",

    "according to this document",

    "according to this pdf",

    "summarize",

    "summarise",

    "summary",

    "explain the report",

    "explain the document",

    "explain this pdf",

    "page",

    "chapter",

    "section",

    "from the document",

    "from this document",

    "from the pdf",

}


# ==========================================
# Normalize Question
# ==========================================

def normalize_question(
    question: str
) -> str:

    if not question:

        return ""

    return " ".join(

        question
        .lower()
        .strip()
        .split()

    )


# ==========================================
# Keyword Matching
# ==========================================

def contains_keyword(
    question: str,
    keywords: set[str]
) -> bool:

    for keyword in keywords:

        if keyword in question:

            return True

    return False


# ==========================================
# Route Question
# ==========================================

def route_question(
    question: str
) -> QuestionType:

    question = normalize_question(
        question
    )


    # ==========================================
    # Empty Question
    # ==========================================

    if not question:

        return QuestionType.GENERAL


    # ==========================================
    # CHART
    # ==========================================
    #
    # Chart gets highest priority because a
    # chart request can also contain words such
    # as "data", "dataset", "value", etc.
    #
    # Example:
    #
    # "Plot the Close price from my dataset"
    #
    # Should be CHART.
    # ==========================================

    if contains_keyword(

        question,

        CHART_KEYWORDS

    ):

        return QuestionType.CHART


    # ==========================================
    # DOCUMENT
    # ==========================================
    #
    # Document gets priority over general data
    # keywords.
    #
    # Example:
    #
    # "Summarize this PDF"
    #
    # contains "summarize", but should be
    # DOCUMENT rather than DATA.
    # ==========================================

    if contains_keyword(

        question,

        DOCUMENT_KEYWORDS

    ):

        return QuestionType.DOCUMENT


    # ==========================================
    # DATA
    # ==========================================

    if contains_keyword(

        question,

        DATA_KEYWORDS

    ):

        return QuestionType.DATA


    # ==========================================
    # GENERAL
    # ==========================================

    return QuestionType.GENERAL


# ==========================================
# Simple String Helper
# ==========================================

def get_route(
    question: str
) -> str:

    return route_question(
        question
    ).value


# ==========================================
# Convenience Helpers
# ==========================================

def is_chart_question(
    question: str
) -> bool:

    return (
        route_question(question)
        == QuestionType.CHART
    )


def is_data_question(
    question: str
) -> bool:

    return (
        route_question(question)
        == QuestionType.DATA
    )


def is_document_question(
    question: str
) -> bool:

    return (
        route_question(question)
        == QuestionType.DOCUMENT
    )


def is_general_question(
    question: str
) -> bool:

    return (
        route_question(question)
        == QuestionType.GENERAL
    )


# ==========================================
# Debug / Testing
# ==========================================

if __name__ == "__main__":

    tests = [

        "Analyze this dataset",

        "What is the average Close price?",

        "Show me the Close price as a line chart",

        "Plot the closing prices",

        "Graph Close over time",

        "Compare Open and Close",

        "Show me the stock trend",

        "What does this PDF say?",

        "Summarize this document",

        "According to the report, what is the revenue?",

        "Explain Python functions",

        "Tell me a joke",

    ]


    print()
    print(
        "🔥 Flint AI Question Router"
    )
    print()


    for question in tests:

        route = route_question(
            question
        )


        print(
            f"Question: {question}"
        )

        print(
            f"Route: {route.value}"
        )

        print(
            "-" * 60
        )