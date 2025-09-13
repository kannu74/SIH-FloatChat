import os
import chromadb
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure the Gemini API key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Database schema for the prompt context
DB_SCHEMA = """
Table Name: argo_measurements
Columns:
- id (INTEGER, Primary Key)
- float_id (VARCHAR)
- timestamp (TIMESTAMP WITH TIME ZONE)
- latitude (REAL)
- longitude (REAL)
- pressure (REAL)
- temperature (REAL)
- salinity (REAL)

Table Name: argo_floats
Columns:
- id (SERIAL, Primary Key)
- float_id (VARCHAR, Unique)
- latest_latitude (REAL)
- latest_longitude (REAL)
- project_name (VARCHAR)
"""

def get_sql_from_question(question: str) -> str:
    """
    Uses a RAG pipeline with Gemini to convert a natural language question into a SQL query.
    """
    try:
        # 1. Retrieve context from ChromaDB
        client = chromadb.PersistentClient(path="db/chroma_db")
        collection = client.get_collection(name="argo_float_summaries")

        context_docs = collection.peek(limit=5)
        context_str = "\n".join(doc for doc in context_docs['documents'])

        # 2. Augment: Construct a detailed prompt for the LLM
        prompt = f"""
        You are an expert PostgreSQL assistant. Your task is to convert a user's question about ARGO float data into a valid PostgreSQL query.

        You must only output the SQL query and nothing else. Do not include any explanations or markdown formatting like ```sql.

        Here is the database schema you must use:
        {DB_SCHEMA}

        Here is some general context about the data available:
        {context_str}

        User Question: "{question}"

        SQL Query:
        """

        # 3. Generate: Call the Gemini model
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)

        generated_sql = response.text.strip()

        # Basic cleanup of the generated SQL
        if "```" in generated_sql:
            generated_sql = generated_sql.replace("```sql", "").replace("```", "").strip()

        print(f"DEBUG: Generated SQL -> {generated_sql}")
        return generated_sql

    except Exception as e:
        print(f"An error occurred in the RAG handler: {e}")
        return "SELECT 'An error occurred while generating the SQL query. Please check the logs.';"