import os
import pandas as pd
import numpy as np
import logging
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, text
from backend.llm.rag_handler import handle_question, handle_graph_explanation
from pydantic import BaseModel
from typing import List, Optional, Any

# Configure logging for structured output
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI()


# --- Request Models ---

class ChatRequest(BaseModel):
    question: str
    chat_history: Optional[List[dict]] = []


class ExplainRequest(BaseModel):
    """Request model for the graph explanation endpoint."""
    visualization_type: str          # e.g. 'line_chart', 'map', 'scatter_plot', 'table'
    data: List[dict]                  # The result rows returned by the SQL query
    sql_query: Optional[str] = ""    # The SQL that produced the data
    language: Optional[str] = "English"  # User's detected language from the chat response


# --- Database Connection ---
try:
    db_url = (
        f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:"
        f"{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:"
        f"{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}?client_encoding=utf8"
    )
    engine = create_engine(db_url)
    logging.info("Successfully connected to PostgreSQL for API.")
except Exception as e:
    logging.error(f"Failed to connect to PostgreSQL for API: {e}", exc_info=True)
    engine = None


# --- Chat Endpoint ---

@app.post('/api/chat')
async def chat_handler(request: ChatRequest):
    question = request.question
    chat_history = request.chat_history

    ai_response = handle_question(question, chat_history)
    response_type = ai_response.get('response_type')
    # Carry the detected language forward to the frontend
    language = ai_response.get('language', 'English')

    if response_type == 'database':
        sql_query = ai_response.get('sql_query')
        viz_type = ai_response.get('visualization_type', 'table')
        try:
            logging.debug(f"Executing SQL query: {sql_query}")
            with engine.connect() as connection:
                df = pd.read_sql(text(sql_query), connection)

            # Fix timestamp serialization
            for col in df.select_dtypes(include=['datetime64[ns]', 'datetimetz']):
                df[col] = df[col].astype(str)

            df = df.replace({np.nan: None})
            result = df.to_dict(orient='records')

            logging.info(f"Query successful. Found {len(result)} records.")

            return JSONResponse({
                "data": result,
                "sql_query": sql_query,
                "visualization": viz_type,
                "language": language          # ← pass language to frontend
            })
        except Exception as e:
            logging.error(f"Error executing SQL query: {sql_query}", exc_info=True)
            return JSONResponse(
                {"error": "Failed to execute SQL query.", "details": str(e)},
                status_code=500
            )

    elif response_type == 'text':
        return JSONResponse({
            "data": ai_response.get('answer'),
            "visualization": "text",
            "language": language
        })

    else:
        logging.warning(f"Received unexpected response type from AI: {response_type}")
        return JSONResponse({
            "data": "Sorry, I received an unexpected response format.",
            "visualization": "text",
            "language": language
        })


# --- Graph Explanation Endpoint ---

@app.post('/api/explain')
async def explain_handler(request: ExplainRequest):
    """
    Accepts a visualization result and returns a plain-language AI explanation
    of what the chart shows, written in the user's language.
    """
    if not request.data:
        return JSONResponse({"explanation": "No data provided to explain."})

    try:
        explanation = handle_graph_explanation(
            visualization_type=request.visualization_type,
            data_sample=request.data,
            sql_query=request.sql_query,
            language=request.language
        )
        return JSONResponse({"explanation": explanation})
    except Exception as e:
        logging.error(f"Error generating graph explanation: {e}", exc_info=True)
        return JSONResponse(
            {"error": "Failed to generate explanation.", "details": str(e)},
            status_code=500
        )