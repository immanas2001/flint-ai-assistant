from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

import json


# ============================================================
# DATA QUERY
# ============================================================

from services.data_query import (
    generate_chart_data,
    load_dataset,
)


# ============================================================
# AI DATA ANALYST
# ============================================================

from services.ai_data_analyst import (
    analyze_question,
    is_analyst_question,
)


# ============================================================
# AI SERVICES
# ============================================================

from assistant.ai import (
    ask_ai,
    ask_ai_stream,
    retrieve_context,
)


# ============================================================
# DATABASE
# ============================================================

from database.database import (
    create_chat,
    get_all_chats,
    get_messages,
    save_message,
    delete_chat,
    rename_chat,
    get_chat,
)


# ============================================================
# DATASET MANAGER
# ============================================================

from services.dataset_manager import (
    get_chat_dataset,
)


# ============================================================
# DATA QUESTION
# ============================================================

from services.data_question import (
    answer_data_question,
)


# ============================================================
# CHART ENGINE
# ============================================================

from services.chart_engine import (
    create_chart,
)


# ============================================================
# QUESTION ROUTER
# ============================================================

from services.question_router import (
    route_question,
    QuestionType,
)


# ============================================================
# INSIGHT ENGINE
# ============================================================

from services.insight_engine import (
    create_insight_report,
)


# ============================================================
# SMART VISUALIZATION
# ============================================================

from services.smart_visualization import (
    smart_visualization,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter()


# ============================================================
# REQUEST MODEL
# ============================================================

class ChatRequest(BaseModel):
    message: str
    chat_id: int | None = None


# ============================================================
# RESPONSE HELPERS
# ============================================================

def response_to_text(response) -> str:
    """
    Convert different AI/service response formats into text.
    """

    if response is None:
        return ""

    if isinstance(response, str):
        return response

    if isinstance(response, dict):

        for key in (
            "answer",
            "response",
            "reply",
            "text",
            "message",
            "markdown",
        ):
            value = response.get(key)

            if isinstance(value, str):
                return value

        try:
            return json.dumps(
                response,
                indent=2,
                ensure_ascii=False,
                default=str,
            )

        except Exception:
            return str(response)

    return str(response)


def make_json_safe(value):
    """
    Convert pandas/numpy/Plotly objects into JSON-safe values.
    """

    if value is None:
        return None

    if isinstance(
        value,
        (str, int, float, bool),
    ):
        return value

    if isinstance(value, dict):
        return {
            str(key): make_json_safe(val)
            for key, val in value.items()
        }

    if isinstance(
        value,
        (list, tuple, set),
    ):
        return [
            make_json_safe(item)
            for item in value
        ]

    if hasattr(value, "tolist"):

        try:
            return make_json_safe(
                value.tolist()
            )
        except Exception:
            pass

    if hasattr(value, "to_plotly_json"):

        try:
            return make_json_safe(
                value.to_plotly_json()
            )
        except Exception:
            pass

    if hasattr(value, "item"):

        try:
            return value.item()
        except Exception:
            pass

    return str(value)


def sse_event(
    event_type: str,
    data_value,
) -> str:
    """
    Create a Server-Sent Event payload.
    """

    safe_value = make_json_safe(
        data_value
    )

    payload = json.dumps(
        safe_value,
        ensure_ascii=False,
        allow_nan=False,
    )

    return (
        f"event: {event_type}\n"
        f"data: {payload}\n\n"
    )


# ============================================================
# CHAT HELPERS
# ============================================================

def prepare_chat(
    chat_id: int | None,
):
    """
    Return a valid chat ID and whether a new chat was created.

    If the frontend sends a stale/non-existent chat ID,
    automatically create a fresh chat instead of causing
    a SQLite foreign-key error.
    """

    if chat_id is not None:
        existing_chat = get_chat(chat_id)

        if existing_chat:
            return chat_id, False

    return create_chat(), True


def build_messages(
    chat_id: int,
) -> list[dict]:
    """
    Build the conversation history expected by the AI layer.
    """

    history = get_messages(chat_id)

    return [
        {
            "role": message["role"],
            "content": message["content"],
        }
        for message in history
    ]


def get_dataset_safe(
    chat_id: int,
):
    """
    Safely retrieve the dataset attached to a chat.
    """

    try:
        return get_chat_dataset(
            chat_id
        )

    except Exception as error:
        print(
            "[Flint AI] Dataset manager error:",
            repr(error),
        )
        return None


def rename_new_chat(
    chat_id: int,
    message: str,
) -> None:
    """
    Give a newly-created chat a useful title.
    """

    title = (
        message[:40]
        .strip()
    )

    if not title:
        title = "New Chat"

    rename_chat(
        chat_id,
        title,
    )


def log_route(
    question_type,
    confidence,
    reason,
) -> None:
    """
    Log question-routing information.
    """

    route_name = getattr(
        question_type,
        "value",
        str(question_type),
    )

    print(
        f"[Flint AI] Route: "
        f"{route_name} "
        f"(confidence={confidence:.2f})"
    )

    print(
        "[Flint AI] Route reason:",
        reason,
    )


# ============================================================
# CHART REQUEST DETECTION
# ============================================================

def is_chart_request(
    message: str,
) -> bool:

    if not message:
        return False

    question = (
        message
        .lower()
        .strip()
    )

    chart_words = (
        "plot",
        "chart",
        "graph",
        "visualize",
        "visualise",
        "visualization",
        "visualisation",
        "draw",
        "line chart",
        "line graph",
        "bar chart",
        "bar graph",
        "pie chart",
        "scatter plot",
        "scatter chart",
        "histogram",
        "heatmap",
        "heat map",
        "trend",
        "price movement",
        "stock trend",
        "performance chart",
        "show me a chart",
        "show a chart",
        "show me the graph",
        "show the graph",
    )

    return any(
        word in question
        for word in chart_words
    )


# ============================================================
# INSIGHT REQUEST DETECTION
# ============================================================

def is_insight_request(
    message: str,
) -> bool:

    if not message:
        return False

    question = (
        message
        .lower()
        .strip()
    )

    phrases = (
        "analyze this dataset",
        "analyse this dataset",
        "analyze the dataset",
        "analyse the dataset",
        "analyze my dataset",
        "analyse my dataset",
        "analyze this data",
        "analyse this data",
        "analyze the data",
        "analyse the data",
        "analyze my data",
        "analyse my data",
        "give me insights",
        "give me some insights",
        "dataset insights",
        "give me dataset insights",
        "summarize this dataset",
        "summarise this dataset",
        "summarize the dataset",
        "summarise the dataset",
        "summarize my data",
        "summarise my data",
        "tell me about this dataset",
        "what can you tell me about this dataset",
        "give me an overview",
        "overall analysis",
    )

    return any(
        phrase in question
        for phrase in phrases
    )


# ============================================================
# QUESTION ROUTER
# ============================================================

def detect_question_type(
    question: str,
):
    """
    Determine the type of user question.
    """

    # Explicit chart requests always win.
    if is_chart_request(question):
        return (
            QuestionType.CHART,
            1.0,
            "Explicit chart request detected.",
        )

    result = route_question(question)

    if isinstance(
        result,
        QuestionType,
    ):
        return (
            result,
            1.0,
            "Detected by question router.",
        )

    if hasattr(result, "intent"):
        return (
            result.intent,
            getattr(
                result,
                "confidence",
                1.0,
            ),
            getattr(
                result,
                "reason",
                "Detected by question router.",
            ),
        )

    print(
        "[Flint AI] WARNING: "
        "Unknown router result:",
        repr(result),
    )

    return (
        QuestionType.GENERAL,
        0.5,
        "Router returned an unknown result.",
    )


# ============================================================
# DATASET ANALYST DETECTION
# ============================================================

def should_use_ai_analyst(
    question: str,
) -> bool:

    if not question:
        return False

    q = (
        question
        .lower()
        .strip()
    )

    # Explicit charts go to the chart engine.
    if is_chart_request(q):
        return False

    # Full dataset analysis goes to the insight engine.
    if is_insight_request(q):
        return False

    analyst_phrases = (
        "did the stock go up",
        "did the stock go down",
        "did it go up",
        "did it go down",
        "overall performance",
        "stock performance",
        "how did the stock perform",
        "what was the best day",
        "what was the worst day",
        "highest price",
        "lowest price",
        "highest close",
        "lowest close",
        "average close",
        "median close",
        "how volatile",
        "volatility",
        "standard deviation",
        "correlation",
        "correlated",
        "relationship between",
        "missing values",
        "missing data",
        "duplicate rows",
        "trend of",
        "trend in",
        "is it trending",
    )

    if any(
        phrase in q
        for phrase in analyst_phrases
    ):
        return True

    try:
        return bool(
            is_analyst_question(
                question
            )
        )

    except Exception:
        return False


# ============================================================
# AUTOMATIC DATA CHART DETECTION
# ============================================================

def should_create_data_chart(
    question: str,
) -> bool:

    if not question:
        return False

    q = (
        question
        .lower()
        .strip()
    )

    if is_chart_request(q):
        return True

    if is_insight_request(q):
        return True

    time_words = (
        "over time",
        "by date",
        "by month",
        "by year",
        "by day",
        "daily",
        "weekly",
        "monthly",
        "yearly",
        "trend",
        "history",
        "historical",
    )

    aggregation_words = (
        "average",
        "avg",
        "mean",
        "sum",
        "total",
        "maximum",
        "minimum",
        "max",
        "min",
    )

    has_time_grouping = any(
        word in q
        for word in time_words
    )

    has_aggregation = any(
        word in q
        for word in aggregation_words
    )

    return (
        has_time_grouping
        and has_aggregation
    )


# ============================================================
# AI DATA ANALYST
# ============================================================

async def run_ai_data_analyst(
    question: str,
    chat_id: int,
):
    """
    Run the dataset-specific AI analyst.
    """

    try:

        dataset = get_chat_dataset(
            int(chat_id)
        )

        if dataset is None:
            return {
                "success": False,
                "answer": (
                    "No dataset is attached "
                    "to this chat."
                ),
            }

        filepath = dataset.get(
            "filepath"
        )

        if not filepath:
            return {
                "success": False,
                "answer": (
                    "The dataset path could "
                    "not be found."
                ),
            }

        dataframe = load_dataset(
            filepath
        )

        return analyze_question(
            dataframe,
            question,
        )

    except Exception as error:

        print(
            "[Flint AI] Analyst error:",
            repr(error),
        )

        return {
            "success": False,
            "answer": (
                "I couldn't analyze the "
                f"dataset: {error}"
            ),
        }


# ============================================================
# INSIGHT ENGINE
# ============================================================

async def run_insight_engine(
    chat_id: int,
):
    """
    Generate a complete dataset insight report.
    """

    try:

        dataset = get_chat_dataset(
            int(chat_id)
        )

        if dataset is None:
            return {
                "success": False,
                "answer": (
                    "No dataset is attached "
                    "to this chat."
                ),
            }

        filepath = dataset.get(
            "filepath"
        )

        if not filepath:
            return {
                "success": False,
                "answer": (
                    "The dataset path could "
                    "not be found."
                ),
            }

        dataframe = load_dataset(
            filepath
        )

        return create_insight_report(
            dataframe
        )

    except Exception as error:

        print(
            "[Flint AI] Insight engine error:",
            repr(error),
        )

        return {
            "success": False,
            "answer": (
                "Insight analysis failed: "
                f"{error}"
            ),
        }


# ============================================================
# SMART CHART GENERATOR
# ============================================================

async def generate_smart_chart(
    dataset,
    question: str = "",
):
    """
    Automatically choose an appropriate chart
    when the user asks for visualization.
    """

    try:

        if not dataset:
            return None

        filepath = dataset.get(
            "filepath"
        )

        if not filepath:
            return None

        # Explicit chart request.
        if (
            question
            and is_chart_request(question)
        ):

            print(
                "[Flint AI] "
                "Explicit chart request."
            )

            return create_chart(
                filepath,
                question,
            )

        # Load dataset.
        dataframe = load_dataset(
            filepath
        )

        # Ask smart visualization service
        # to choose the chart configuration.
        selection = smart_visualization(
            dataframe
        )

        if not selection.get(
            "success",
            False,
        ):

            print(
                "[Flint AI] "
                "Smart visualization failed:",
                selection.get(
                    "error",
                    "Unknown error",
                ),
            )

            return None

        chart_type = selection.get(
            "chart_type"
        )

        x_column = selection.get(
            "x_column"
        )

        y_column = selection.get(
            "y_column"
        )

        title = selection.get(
            "title"
        )

        print(
            "[Flint AI] "
            "Smart chart selected:",
            chart_type,
        )

        print(
            "[Flint AI] X:",
            x_column,
            "| Y:",
            y_column,
        )

        # Build instruction for chart engine.
        instruction = (
            f"Create a {chart_type} chart. "
        )

        if x_column:
            instruction += (
                f"Use `{x_column}` "
                "as the X/category axis. "
            )

        if y_column:
            instruction += (
                f"Use `{y_column}` "
                "as the Y/value axis. "
            )

        if title:
            instruction += (
                f"Use `{title}` "
                "as the chart title. "
            )

        instruction += (
            "Create an interactive Plotly "
            "visualization using the dataset."
        )

        return create_chart(
            filepath,
            instruction,
        )

    except Exception as error:

        print(
            "[Flint AI] "
            "Smart visualization error:",
            repr(error),
        )

        return None


# ============================================================
# NORMAL CHAT
# ============================================================

@router.post("/chat")
async def chat(
    data: ChatRequest,
):
    """
    Standard non-streaming chat endpoint.
    """

    chat_id, is_new_chat = prepare_chat(
        data.chat_id
    )

    # Save user message first so the AI
    # receives the latest conversation turn.
    save_message(
        chat_id,
        "user",
        data.message,
    )

    messages = build_messages(
        chat_id
    )

    question_type, confidence, reason = (
        detect_question_type(
            data.message
        )
    )

    log_route(
        question_type,
        confidence,
        reason,
    )

    dataset = get_dataset_safe(
        chat_id
    )

    reply = ""


    # ========================================================
    # INSIGHT ENGINE
    # ========================================================

    if (
        dataset
        and is_insight_request(
            data.message
        )
    ):

        print(
            "[Flint AI] "
            "Running Insight Engine."
        )

        try:

            result = await run_insight_engine(
                chat_id
            )

            if result.get(
                "success",
                False,
            ):
                reply = response_to_text(
                    result
                )
            else:
                reply = result.get(
                    "answer",
                    "Unable to analyze dataset.",
                )

        except Exception as error:

            print(
                "[Flint AI] Insight error:",
                repr(error),
            )

            reply = (
                "I couldn't complete "
                "the dataset analysis."
            )


    # ========================================================
    # AI DATA ANALYST
    # ========================================================

    elif (
        dataset
        and should_use_ai_analyst(
            data.message
        )
    ):

        print(
            "[Flint AI] "
            "Running AI Data Analyst."
        )

        try:

            result = await run_ai_data_analyst(
                data.message,
                chat_id,
            )

            reply = response_to_text(
                result
            )

        except Exception as error:

            print(
                "[Flint AI] Analyst error:",
                repr(error),
            )

            reply = response_to_text(
                ask_ai(
                    messages,
                    chat_id,
                )
            )


    # ========================================================
    # DATA QUESTION
    # ========================================================

    elif (
        question_type
        == QuestionType.DATA
    ):

        try:

            if dataset:

                reply = answer_data_question(
                    data.message,
                    chat_id,
                )

                reply = response_to_text(
                    reply
                )

            else:

                reply = response_to_text(
                    ask_ai(
                        messages,
                        chat_id,
                    )
                )

        except Exception as error:

            print(
                "[Flint AI] "
                "Data question error:",
                repr(error),
            )

            reply = response_to_text(
                ask_ai(
                    messages,
                    chat_id,
                )
            )


    # ========================================================
    # CHART
    # ========================================================

    elif (
        question_type
        == QuestionType.CHART
    ):

        try:

            if not dataset:

                reply = (
                    "I couldn't find a dataset "
                    "for this chat. Please upload "
                    "a CSV or Excel file first."
                )

            else:

                chart_result = create_chart(
                    dataset["filepath"],
                    data.message,
                )

                if chart_result:

                    reply = (
                        "I've generated "
                        "the chart for you."
                    )

                else:

                    reply = (
                        "I couldn't generate "
                        "a chart from this dataset."
                    )

        except Exception as error:

            print(
                "[Flint AI] Chart error:",
                repr(error),
            )

            reply = (
                "I couldn't generate "
                "the chart."
            )


    # ========================================================
    # GENERAL / DOCUMENT
    # ========================================================

    else:

        reply = ask_ai(
            messages,
            chat_id,
        )

        reply = response_to_text(
            reply
        )


    # ========================================================
    # SAVE RESPONSE
    # ========================================================

    save_message(
        chat_id,
        "assistant",
        reply,
    )


    # ========================================================
    # RENAME NEW CHAT
    # ========================================================

    if is_new_chat:

        rename_new_chat(
            chat_id,
            data.message,
        )


    return {
        "chat_id": chat_id,
        "reply": reply,
    }


# ============================================================
# STREAMING CHAT
# ============================================================

@router.post("/chat/stream")
async def chat_stream(
    data: ChatRequest,
    request: Request,
):
    """
    Streaming chat endpoint using Server-Sent Events.
    """

    chat_id, is_new_chat = prepare_chat(
        data.chat_id
    )

    # --------------------------------------------------------
    # Save user message
    # --------------------------------------------------------

    save_message(
        chat_id,
        "user",
        data.message,
    )

    messages = build_messages(
        chat_id
    )

    # --------------------------------------------------------
    # Route
    # --------------------------------------------------------

    question_type, confidence, reason = (
        detect_question_type(
            data.message
        )
    )

    log_route(
        question_type,
        confidence,
        reason,
    )

    # --------------------------------------------------------
    # RAG sources
    # --------------------------------------------------------

    sources = []

    try:

        rag_result = retrieve_context(
            query=data.message,
            chat_id=chat_id,
            n_results=5,
        )

        if isinstance(
            rag_result,
            dict,
        ):
            sources = rag_result.get(
                "sources",
                [],
            )

    except Exception as error:

        print(
            "[Flint AI] RAG error:",
            repr(error),
        )

    # --------------------------------------------------------
    # Dataset
    # --------------------------------------------------------

    dataset = get_dataset_safe(
        chat_id
    )


    # ========================================================
    # RESPONSE GENERATOR
    # ========================================================

    async def response_generator():

        full_response = ""

        try:

            # ------------------------------------------------
            # Chat ID
            # ------------------------------------------------

            yield sse_event(
                "chat_id",
                {
                    "chat_id": chat_id
                },
            )


            # ------------------------------------------------
            # Sources
            # ------------------------------------------------

            if sources:

                yield sse_event(
                    "sources",
                    sources,
                )


            # =================================================
            # EXPLICIT CHART
            # =================================================

            if (
                question_type
                == QuestionType.CHART
            ):

                if not dataset:

                    reply = (
                        "I couldn't find a dataset "
                        "for this chat. Please upload "
                        "a CSV or Excel file first."
                    )

                    full_response = reply

                    yield sse_event(
                        "token",
                        {
                            "text": reply
                        },
                    )

                else:

                    try:

                        print(
                            "[Flint AI] "
                            "Generating chart:",
                            data.message,
                        )

                        chart_result = create_chart(
                            dataset["filepath"],
                            data.message,
                        )

                        if chart_result:

                            reply = (
                                "I've generated "
                                "the chart for you."
                            )

                            full_response = reply

                            yield sse_event(
                                "token",
                                {
                                    "text": reply
                                },
                            )

                            yield sse_event(
                                "chart",
                                chart_result,
                            )

                            print(
                                "[Flint AI] "
                                "Chart generated successfully."
                            )

                        else:

                            reply = (
                                "I couldn't generate "
                                "a chart from this dataset."
                            )

                            full_response = reply

                            yield sse_event(
                                "token",
                                {
                                    "text": reply
                                },
                            )

                    except Exception as error:

                        print(
                            "[Flint AI] Chart error:",
                            repr(error),
                        )

                        reply = (
                            "I couldn't generate "
                            "the chart."
                        )

                        full_response = reply

                        yield sse_event(
                            "token",
                            {
                                "text": reply
                            },
                        )


            # =================================================
            # INSIGHT ENGINE
            # =================================================

            elif (
                dataset
                and is_insight_request(
                    data.message
                )
            ):

                print(
                    "[Flint AI] "
                    "Running Insight Engine."
                )

                try:

                    result = await run_insight_engine(
                        chat_id
                    )

                    if result.get(
                        "success",
                        False,
                    ):

                        reply = response_to_text(
                            result
                        )

                        full_response = reply

                        yield sse_event(
                            "token",
                            {
                                "text": reply
                            },
                        )


                        # --------------------------------------
                        # Smart chart
                        # --------------------------------------

                        print(
                            "[Flint AI] "
                            "Selecting smart visualization."
                        )

                        chart_result = (
                            await generate_smart_chart(
                                dataset
                            )
                        )

                        if chart_result:

                            yield sse_event(
                                "chart",
                                chart_result,
                            )

                            print(
                                "[Flint AI] "
                                "Smart insight chart generated."
                            )

                    else:

                        reply = result.get(
                            "answer",
                            "Unable to analyze dataset.",
                        )

                        full_response = reply

                        yield sse_event(
                            "token",
                            {
                                "text": reply
                            },
                        )

                except Exception as error:

                    print(
                        "[Flint AI] "
                        "Insight engine error:",
                        repr(error),
                    )

                    reply = (
                        "I couldn't complete "
                        "the dataset analysis."
                    )

                    full_response = reply

                    yield sse_event(
                        "token",
                        {
                            "text": reply
                        },
                    )


            # =================================================
            # AI DATA ANALYST
            # =================================================

            elif (
                dataset
                and should_use_ai_analyst(
                    data.message
                )
            ):

                print(
                    "[Flint AI] "
                    "Running AI Data Analyst."
                )

                try:

                    analyst_result = (
                        await run_ai_data_analyst(
                            data.message,
                            chat_id,
                        )
                    )

                    reply = response_to_text(
                        analyst_result
                    )

                    full_response = reply

                    yield sse_event(
                        "token",
                        {
                            "text": reply
                        },
                    )


                    # ------------------------------------------
                    # Smart automatic visualization
                    # ------------------------------------------

                    if (
                        analyst_result.get(
                            "success",
                            False,
                        )
                        and should_create_data_chart(
                            data.message
                        )
                    ):

                        try:

                            print(
                                "[Flint AI] "
                                "Generating smart analyst chart."
                            )

                            chart_result = (
                                await generate_smart_chart(
                                    dataset,
                                    data.message,
                                )
                            )

                            if chart_result:

                                yield sse_event(
                                    "chart",
                                    chart_result,
                                )

                                print(
                                    "[Flint AI] "
                                    "Smart analyst chart generated."
                                )

                        except Exception as error:

                            print(
                                "[Flint AI] "
                                "Smart analyst chart error:",
                                repr(error),
                            )

                except Exception as error:

                    print(
                        "[Flint AI] "
                        "Analyst error:",
                        repr(error),
                    )

                    reply = (
                        "I couldn't analyze "
                        "the dataset."
                    )

                    full_response = reply

                    yield sse_event(
                        "token",
                        {
                            "text": reply
                        },
                    )


            # =================================================
            # DATA QUESTION
            # =================================================

            elif (
                question_type
                == QuestionType.DATA
            ):

                print(
                    "[Flint AI] "
                    "Processing dataset question."
                )

                if dataset:

                    try:

                        reply = answer_data_question(
                            data.message,
                            chat_id,
                        )

                        reply = response_to_text(
                            reply
                        )

                        full_response = reply

                        yield sse_event(
                            "token",
                            {
                                "text": reply
                            },
                        )


                        # --------------------------------------
                        # Automatic smart chart
                        # --------------------------------------

                        if should_create_data_chart(
                            data.message
                        ):

                            try:

                                print(
                                    "[Flint AI] "
                                    "Generating smart data chart."
                                )

                                chart_result = (
                                    await generate_smart_chart(
                                        dataset,
                                        data.message,
                                    )
                                )

                                if chart_result:

                                    yield sse_event(
                                        "chart",
                                        chart_result,
                                    )

                                    print(
                                        "[Flint AI] "
                                        "Smart data chart generated."
                                    )

                            except Exception as error:

                                print(
                                    "[Flint AI] "
                                    "Smart data chart error:",
                                    repr(error),
                                )

                    except Exception as error:

                        print(
                            "[Flint AI] "
                            "Data question error:",
                            repr(error),
                        )

                        reply = (
                            "I couldn't analyze "
                            "the dataset."
                        )

                        full_response = reply

                        yield sse_event(
                            "token",
                            {
                                "text": reply
                            },
                        )

                else:

                    reply = (
                        "I couldn't find a dataset "
                        "for this chat. Please upload "
                        "a CSV or Excel file first."
                    )

                    full_response = reply

                    yield sse_event(
                        "token",
                        {
                            "text": reply
                        },
                    )


            # =================================================
            # GENERAL / DOCUMENT
            # =================================================

            else:

                print(
                    "[Flint AI] "
                    "Using normal AI stream."
                )

                stream = ask_ai_stream(
                    messages,
                    chat_id,
                )

                for chunk in stream:

                    if await request.is_disconnected():
                        break

                    if not chunk:
                        continue

                    chunk_text = response_to_text(
                        chunk
                    )

                    if not chunk_text:
                        continue

                    full_response += chunk_text

                    yield sse_event(
                        "token",
                        {
                            "text": chunk_text
                        },
                    )


        except Exception as error:

            print(
                "[Flint AI] "
                "Streaming Error:",
                repr(error),
            )

            error_message = (
                "Something went wrong: "
                f"{str(error)}"
            )

            yield sse_event(
                "error",
                {
                    "message": error_message
                },
            )


        finally:

            # ------------------------------------------------
            # Save assistant response
            # ------------------------------------------------

            full_response = response_to_text(
                full_response
            )

            if full_response.strip():

                save_message(
                    chat_id,
                    "assistant",
                    full_response,
                )


            # ------------------------------------------------
            # Rename new chat
            # ------------------------------------------------

            if is_new_chat:

                rename_new_chat(
                    chat_id,
                    data.message,
                )


            # ------------------------------------------------
            # Done
            # ------------------------------------------------

            yield sse_event(
                "done",
                {
                    "success": True
                },
            )


    # ========================================================
    # SSE RESPONSE
    # ========================================================

    return StreamingResponse(
        response_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "X-Chat-Id": str(chat_id),
        },
    )


# ============================================================
# GET ALL CHATS
# ============================================================

@router.get("/chats")
async def chats():
    return get_all_chats()


# ============================================================
# GET MESSAGES
# ============================================================

@router.get("/messages/{chat_id}")
async def messages(
    chat_id: int,
):
    return get_messages(
        chat_id
    )


# ============================================================
# DELETE CHAT
# ============================================================

@router.delete(
    "/delete-chat/{chat_id}"
)
async def remove_chat(
    chat_id: int,
):

    delete_chat(
        chat_id
    )

    return {
        "success": True
    }


# ============================================================
# CHART DATA ENDPOINT
# ============================================================

@router.post("/chart")
async def generate_chart(
    request: Request,
):
    """
    Generate chart data directly from a chat dataset.
    """

    try:

        body = await request.json()

        question = body.get(
            "question",
            "",
        )

        chat_id = body.get(
            "chat_id"
        )

        if not question:

            return {
                "success": False,
                "error": "Question is required.",
            }

        if chat_id is None:

            return {
                "success": False,
                "error": "chat_id is required.",
            }


        # ----------------------------------------------------
        # Dataset
        # ----------------------------------------------------

        dataset = get_chat_dataset(
            int(chat_id)
        )

        if dataset is None:

            return {
                "success": False,
                "error": (
                    "No dataset found "
                    "for this chat."
                ),
            }


        filepath = dataset.get(
            "filepath"
        )

        if not filepath:

            return {
                "success": False,
                "error": (
                    "Dataset filepath "
                    "could not be found."
                ),
            }


        # ----------------------------------------------------
        # Load dataset
        # ----------------------------------------------------

        dataframe = load_dataset(
            filepath
        )


        # ----------------------------------------------------
        # Generate chart
        # ----------------------------------------------------

        result = generate_chart_data(
            dataframe,
            question,
        )

        return result


    except Exception as error:

        print(
            "[Flint AI] "
            "Chart API error:",
            repr(error),
        )

        return {
            "success": False,
            "error": str(error),
        }