import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables from .env file
load_dotenv()
password = os.getenv('POSTGRES_PASSWORD')
print(f"DEBUG: Attempting to connect with password: '{password}'")
def setup_database():
    """Connects to PostgreSQL and creates the necessary tables."""
    try:
        # Construct the database URL from environment variables
        db_url = (
            f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:"
            f"{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:"
            f"{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
        )
        engine = create_engine(db_url)

        with engine.connect() as connection:
            print("Successfully connected to PostgreSQL.")
            
            # SQL statements to create tables
            create_floats_table = text("""
            CREATE TABLE IF NOT EXISTS argo_floats (
                id SERIAL PRIMARY KEY,
                float_id VARCHAR(255) UNIQUE NOT NULL,
                latest_latitude REAL,
                latest_longitude REAL,
                project_name VARCHAR(255),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            """)

            create_measurements_table = text("""
            CREATE TABLE IF NOT EXISTS argo_measurements (
                id SERIAL PRIMARY KEY,
                float_id VARCHAR(255) NOT NULL,
                timestamp TIMESTAMP WITH TIME ZONE,
                latitude REAL,
                longitude REAL,
                pressure REAL,
                temperature REAL,
                salinity REAL
            );
            """)
            
            # Execute the creation statements
            connection.execute(create_floats_table)
            connection.execute(create_measurements_table)
            connection.commit()

            print("Tables 'argo_floats' and 'argo_measurements' are ready.")

    except Exception as e:
        print(f"An error occurred during database setup: {e}")

if __name__ == "__main__":
    setup_database()