import json
import operator
from typing import Annotated, TypedDict, Union, List
import torch

from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END

# --- GPU DETECTION AND SETUP ---
def setup_gpu_device():
    """Detect and configure GPU for LLM inference."""
    if torch.cuda.is_available():
        device_name = torch.cuda.get_device_name(0)
        device_count = torch.cuda.device_count()
        print(f"\n{'='*60}")
        print(f"GPU ACCELERATION ENABLED FOR LLM")
        print(f"Device: {device_name}")
        print(f"GPU Count: {device_count}")
        print(f"CUDA Version: {torch.version.cuda}")
        print(f"{'='*60}\n")
        return 'cuda'
    else:
        print(f"\n{'='*60}")
        print(f"GPU NOT AVAILABLE - Using CPU for LLM inference")
        print(f"Note: Ensure Ollama is running with GPU support for optimal performance")
        print(f"{'='*60}\n")
        return 'cpu'

compute_device = setup_gpu_device()

# 1. Configuration - Optimized for GPU with Ollama
llm = ChatOllama(
    model="qwen2.5:7b",
    temperature=0,
    num_gpu=1 if compute_device == 'cuda' else 0,
)

# 2. Define the State
class AgentState(TypedDict):
    question: str
    chat_history: List[dict]
    intent: str  # 'chat', 'database', or 'explain'
    response: dict
    sql_query: str
    detected_language: str  # NEW: stores detected language name

DB_SCHEMA = """
Table Name: argo_measurements
Columns: float_id, timestamp, latitude, longitude, pressure, temperature, salinity
Table Name: argo_floats
Columns: float_id, project_name
"""

# --- LANGUAGE DETECTION ---

def detect_language(state: AgentState):
    """
    Detects the language of the user's question and stores it in state.
    Returns a plain English language name (e.g. 'Spanish', 'French', 'Arabic').
    """
    prompt = f"""Identify the language of the following text. 
    Respond with ONLY the English name of the language (e.g. English, Spanish, French, Arabic, Hindi, Japanese).
    Text: {state['question']}"""

    print(f"[{compute_device.upper()}] Detecting language...")
    lang = llm.invoke(prompt).content.strip()
    # Sanitize: take first word only in case model adds extra text
    detected = lang.split()[0] if lang else "English"
    print(f"[{compute_device.upper()}] Detected language: {detected}")
    return {"detected_language": detected}


# --- NODES ---

def intent_router(state: AgentState):
    """Classifies the user intent to prevent model confusion."""
    prompt = f"""Analyze the user question and classify it as one of:
    - 'CHAT': greeting, general conversation, or oceanography questions not requiring data
    - 'DATABASE': requesting maps, charts, tables, or specific data from the database

    Question: {state['question']}
    Respond with ONLY the word 'CHAT' or 'DATABASE'."""

    print(f"[{compute_device.upper()}] Routing intent for question: {state['question'][:50]}...")
    classification = llm.invoke(prompt).content.strip().upper()
    intent = "database" if "DATABASE" in classification else "chat"
    return {"intent": intent}


def chat_node(state: AgentState):
    """Handles conversational responses with the Orca AI personality."""
    lang = state.get("detected_language", "English")
    prompt = f"""You are Orca AI, a friendly oceanography expert.
    IMPORTANT: You MUST respond entirely in {lang}. Do not use any other language.
    History: {state['chat_history'][-2:] if state['chat_history'] else 'None'}
    User: {state['question']}
    Respond naturally and briefly in {lang}.
    Format: {{"response_type": "text", "answer": "your_response_in_{lang}"}}"""

    print(f"[{compute_device.upper()}] Generating chat response in {lang}...")
    response = llm.invoke(prompt)
    try:
        clean_json = json.loads(response.content.strip())
    except Exception:
        clean_json = {"response_type": "text", "answer": response.content}
    return {"response": clean_json}


def database_node(state: AgentState):
    """Specialized SQL Engineer node."""
    lang = state.get("detected_language", "English")
    prompt = f"""You are a SQL expert for ARGO ocean data.
    Schema: {DB_SCHEMA}
    Task: Generate a PostgreSQL query and select a visualization.
    User Question: {state['question']}

    Rules:
    - ALWAYS add 'LIMIT 50'.
    - If the user asks for a graph or trend → use 'line_chart'.
    - If the user asks for a map → use 'map'.
    - Otherwise use 'table'.
    - visualization_type options: 'map', 'line_chart', 'scatter_plot', 'table', 'bar_chart', 'histogram', 'time_series'.
    - The 'language' field must be set to '{lang}' so the frontend knows the user's language.
    - Output ONLY valid JSON:
    {{"response_type": "database", "sql_query": "SELECT...", "visualization_type": "...", "language": "{lang}"}}"""

    print(f"[{compute_device.upper()}] Generating SQL query...")
    response = llm.invoke(prompt)
    content = response.content.strip()

    # Clean Ollama markdown backticks
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()

    try:
        clean_json = json.loads(content)
    except Exception:
        clean_json = {
            "response_type": "text",
            "answer": "I understood the data request but failed to format the JSON. Try asking again.",
            "language": lang
        }

    return {"response": clean_json}


# --- GRAPH CONSTRUCTION ---

workflow = StateGraph(AgentState)

workflow.add_node("detect_language", detect_language)
workflow.add_node("classify_intent", intent_router)
workflow.add_node("handle_chat", chat_node)
workflow.add_node("handle_db", database_node)

workflow.set_entry_point("detect_language")
workflow.add_edge("detect_language", "classify_intent")

workflow.add_conditional_edges(
    "classify_intent",
    lambda x: x["intent"],
    {
        "chat": "handle_chat",
        "database": "handle_db"
    }
)

workflow.add_edge("handle_chat", END)
workflow.add_edge("handle_db", END)

app = workflow.compile()


def handle_question(question: str, chat_history: list) -> dict:
    """The entry point called by the Flask API for chat."""
    inputs = {
        "question": question,
        "chat_history": chat_history,
        "intent": "",
        "response": {},
        "sql_query": "",
        "detected_language": "English"
    }
    result = app.invoke(inputs)
    return result["response"]


def handle_graph_explanation(
    visualization_type: str,
    data_sample: list,
    sql_query: str,
    language: str = "English"
) -> str:
    """
    Generates a plain-language explanation of a chart/visualization result.
    Called by the /api/explain endpoint in main.py.

    Args:
        visualization_type: e.g. 'line_chart', 'map', 'scatter_plot', 'table'
        data_sample: first few rows of the result data (list of dicts)
        sql_query: the SQL that produced the data
        language: the user's detected language (e.g. 'Spanish')

    Returns:
        A human-readable string explanation in the user's language.
    """
    sample_str = json.dumps(data_sample[:10], indent=2, default=str)

    prompt = f"""You are Orca AI, an expert oceanographer and data analyst.
A user just received a {visualization_type} visualization from an ARGO float database query.

SQL Query used:
{sql_query}

Sample of the data (first rows):
{sample_str}

Your task:
1. Explain what the chart/visualization shows in simple, clear terms.
2. Highlight 2–3 interesting patterns, trends, or observations visible in the data.
3. Give a brief scientific context about what this means for oceanography if relevant.
4. Keep the total explanation under 120 words.
5. IMPORTANT: Write your ENTIRE response in {language}. Do not use any other language.

Respond with ONLY the explanation text — no JSON, no headers, no bullet symbols."""

    print(f"[{compute_device.upper()}] Generating graph explanation in {language}...")
    response = llm.invoke(prompt)
    return response.content.strip()