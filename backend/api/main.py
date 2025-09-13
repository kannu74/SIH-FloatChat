import os
import pandas as pd
from flask import Flask, request, jsonify # We remove render_template from here
from sqlalchemy import create_engine, text
from backend.llm.rag_handler import get_sql_from_question
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- CRITICAL FIX ---
# This line tells Flask where to find the frontend files from this file's location.
# It looks two directories up (from backend/api/ to sih/) to find the folders.
app = Flask(__name__, template_folder='../../templates', static_folder='../../static')
# --------------------


# --- Database Connection ---
try:
    db_url = (
        f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:"
        f"{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:"
        f"{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
    )
    engine = create_engine(db_url)
    print("Successfully connected to PostgreSQL for API.")
except Exception as e:
    print(f"Failed to connect to PostgreSQL for API: {e}")
    engine = None

@app.route('/api/chat', methods=['POST'])
def chat_handler():
    if not engine:
        return jsonify({"error": "Database connection not available."}), 500

    data = request.get_json()
    if not data or 'question' not in data:
        return jsonify({"error": "Invalid request. 'question' is required."}), 400

    question = data['question']

    # Step 1: Get SQL from the LLM
    sql_query = get_sql_from_question(question)

    # Step 2: Execute the query against the database
    try:
        with engine.connect() as connection:
            df = pd.read_sql(text(sql_query), connection)
            result = df.to_dict(orient='records')
        
        return jsonify({
            "question": question,
            "sql_query": sql_query,
            "data": result
        })
    except Exception as e:
        print(f"Error executing SQL query: {e}")
        return jsonify({
            "error": "Failed to execute the generated SQL query.",
            "sql_query": sql_query,
            "details": str(e)
        }), 500