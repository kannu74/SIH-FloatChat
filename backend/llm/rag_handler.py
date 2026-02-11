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
# ChatOllama with GPU-enabled model
llm = ChatOllama(
    model="qwen2.5-coder:7b",
    temperature=0,
    # GPU parameters for Ollama
    num_gpu=1 if compute_device == 'cuda' else 0,  # Use 1 GPU if available
)

# 2. Define the State
class AgentState(TypedDict):
    question: str
    chat_history: List[dict]
    intent: str # 'chat' or 'database'
    response: dict
    sql_query: str

DB_SCHEMA = """
Table Name: argo_measurements
Columns: float_id, timestamp, latitude, longitude, pressure (depth), temperature, salinity
Table Name: argo_floats
Columns: float_id, project_name
"""

# --- NODES ---

def intent_router(state: AgentState):
    """Classifies the user intent to prevent model confusion."""
    prompt = f"""Analyze the user question and classify it as 'CHAT' (greeting, general talk) or 'DATABASE' (requesting maps, charts, or specific data).
    Question: {state['question']}
    Respond with ONLY the word 'CHAT' or 'DATABASE'."""
    
    print(f"[{compute_device.upper()}] Routing intent for question: {state['question'][:50]}...")
    classification = llm.invoke(prompt).content.strip().upper()
    # Handle cases where model adds extra text
    intent = "database" if "DATABASE" in classification else "chat"
    return {"intent": intent}

def chat_node(state: AgentState):
    """Handles conversational responses with the Orca AI personality."""
    prompt = f"""You are Orca AI, a friendly oceanography expert. 
    History: {state['chat_history'][-2:] if state['chat_history'] else 'None'}
    User: {state['question']}
    Respond naturally and briefly.
    Format: {{"response_type": "text", "answer": "your_response"}}"""
    
    print(f"[{compute_device.upper()}] Generating chat response...")
    response = llm.invoke(prompt)
    try:
        clean_json = json.loads(response.content.strip())
    except:
        clean_json = {"response_type": "text", "answer": response.content}
    return {"response": clean_json}

def database_node(state: AgentState):
    """Specialized SQL Engineer node."""
    prompt = f"""You are a SQL expert for ARGO ocean data.
    Schema: {DB_SCHEMA}
    Task: Generate a PostgreSQL query and select a visualization.
    User Question: {state['question']}
    
    Rules:
    - ALWAYS add 'LIMIT 1500'.
    - visualization_type options: 'map', 'line_chart', 'scatter_plot', 'table'.
    - Output ONLY valid JSON:
    {{"response_type": "database", "sql_query": "SELECT...", "visualization_type": "..."}}"""
    
    print(f"[{compute_device.upper()}] Generating SQL query...")
    response = llm.invoke(prompt)
    content = response.content.strip()
    
    # Cleaning Ollama markdown backticks
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
        
    try:
        clean_json = json.loads(content)
    except:
        clean_json = {"response_type": "text", "answer": "I understood the data request but failed to format the JSON. Try asking again."}
    
    return {"response": clean_json}

# --- GRAPH CONSTRUCTION ---

workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("classify_intent", intent_router)
workflow.add_node("handle_chat", chat_node)
workflow.add_node("handle_db", database_node)

# Set Entry Point
workflow.set_entry_point("classify_intent")

# Add Conditional Edges
workflow.add_conditional_edges(
    "classify_intent",
    lambda x: x["intent"],
    {
        "chat": "handle_chat",
        "database": "handle_db"
    }
)

# Set End Points
workflow.add_edge("handle_chat", END)
workflow.add_edge("handle_db", END)

# Compile
app = workflow.compile()

def handle_question(question: str, chat_history: list) -> dict:
    """The entry point called by your Flask API."""
    inputs = {
        "question": question,
        "chat_history": chat_history,
        "intent": "",
        "response": {},
        "sql_query": ""
    }
    
    result = app.invoke(inputs)
    return result["response"]