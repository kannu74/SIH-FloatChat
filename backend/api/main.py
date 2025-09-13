import os
import pandas as pd
from flask import Flask, request, jsonify
from sqlalchemy import create_engine, text
from backend.llm.rag_handler import get_sql_from_question

# This line correctly configures Flask to find the frontend files
app = Flask(__name__, template_folder='../../templates', static_folder='../../static')

# --- Database Connection ---
try:
    # Added ?client_encoding=utf8 to fix connection issues with Supabase pooler
    db_url = (
        f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:"
        f"{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:"
        f"{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}?client_encoding=utf8"
    )
    engine = create_engine(db_url)
    print("Successfully connected to PostgreSQL for API.")
except Exception as e:
    print(f"Failed to connect to PostgreSQL for API: {e}")
    engine = None

@app.route('/api/chat', methods=['POST'])
def chat_handler():
    """Handles incoming chat messages, gets a SQL query from the LLM, executes it, and returns the result."""
    if not engine:
        return jsonify({"error": "Database connection not available."}), 500

    data = request.get_json()
    if not data or 'question' not in data:
        return jsonify({"error": "Invalid request. 'question' is required."}), 400

    question = data['question']

    # Step 1: Get the structured JSON response from the AI
    llm_response = get_sql_from_question(question)
    sql_query = llm_response.get('sql_query')
    viz_type = llm_response.get('visualization_type', 'table') # Default to 'table' if not provided

    # Step 2: Execute the query against the database
    try:
        print(f"DEBUG: Executing SQL query against the database...")
        with engine.connect() as connection:
            df = pd.read_sql(text(sql_query), connection)
            result = df.to_dict(orient='records')
        
        print(f"DEBUG: Query successful. Found {len(result)} records.")
        
        return jsonify({
            "question": question,
            "sql_query": sql_query,
            "visualization": viz_type,
            "data": result
        })
    except Exception as e:
        # This block provides detailed logs if the database query fails
        print("\n" + "="*50)
        print(f"DEBUG: AN ERROR OCCURRED while executing the SQL query.")
        print(f"DEBUG: Query that failed: {sql_query}")
        print(f"DEBUG: Error details: {e}")
        print("="*50 + "\n")
        
        return jsonify({
            "error": "Failed to execute the generated SQL query.",
            "sql_query": sql_query,
            "details": str(e)
        }), 500

