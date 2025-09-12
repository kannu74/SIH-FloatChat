import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.dialects.postgresql import insert
import chromadb

# Import our custom modules
from backend.data_processing.processor import process_netcdf_file

# --- MOVED load_dotenv() TO THE TOP ---
# This ensures environment variables are loaded before any other code runs.
load_dotenv()
# ------------------------------------

def run(argo_floats_table):
    """Main function to run the data ingestion pipeline."""
    # load_dotenv() was moved from here

    # --- 1. Connect to Databases ---
    try:
        db_url = (
            f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:"
            f"{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:"
            f"{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
        )
        pg_engine = create_engine(db_url)
        print("Successfully connected to PostgreSQL.")
    except Exception as e:
        print(f"Failed to connect to PostgreSQL: {e}")
        return

    try:
        chroma_client = chromadb.PersistentClient(path="db/chroma_db")
        argo_collection = chroma_client.get_or_create_collection(name="argo_float_summaries")
        print("Successfully connected to ChromaDB.")
    except Exception as e:
        print(f"Failed to connect to ChromaDB: {e}")
        return

    # --- 2. Process Data Files ---
    data_dir = os.path.join('data', 'raw')
    processed_files = 0
    
    for filename in os.listdir(data_dir):
        if filename.endswith(".nc"):
            file_path = os.path.join(data_dir, filename)
            print(f"Processing file: {file_path}...")
            
            metadata, measurements_df = process_netcdf_file(file_path)

            if metadata is None or measurements_df is None:
                print(f"Halting ingestion due to critical error in processing {filename}.")
                break

            try:
                with pg_engine.connect() as connection:
                    # Load measurement data
                    measurements_df.to_sql('argo_measurements', connection, if_exists='append', index=False)
                    
                    # Upsert logic for argo_floats table
                    insert_values = pd.DataFrame([metadata]).to_dict(orient='records')[0]
                    stmt = insert(argo_floats_table).values(insert_values)
                    
                    update_dict = {
                        'project_name': stmt.excluded.project_name,
                        'latest_latitude': stmt.excluded.latest_latitude,
                        'latest_longitude': stmt.excluded.latest_longitude
                    }
                    
                    on_conflict_stmt = stmt.on_conflict_do_update(
                        index_elements=['float_id'],
                        set_=update_dict
                    )
                    
                    connection.execute(on_conflict_stmt)
                    connection.commit()

                    # Upsert summary for vector database
                    summary_text = (
                        f"ARGO float with ID {metadata['float_id']} from the {metadata['project_name']} project. "
                        f"Its latest known position is at latitude {metadata['latest_latitude']:.2f} "
                        f"and longitude {metadata['latest_longitude']:.2f}. "
                        f"This float measures ocean temperature, salinity, and pressure profiles."
                    )
                    
                    argo_collection.upsert(
                        documents=[summary_text],
                        metadatas=[{"source": "argo_float_metadata"}],
                        ids=[metadata['float_id']]
                    )

                print(f"Successfully ingested data for float {metadata['float_id']}.")
                processed_files += 1

            except Exception as e:
                print("\n" + "="*50)
                print(f"FATAL ERROR: Failed to load data from '{filename}' into the database.")
                print(f"REASON: {e}")
                print("="*50 + "\n")
                break

    print(f"\nData ingestion complete. Processed {processed_files} files.")

if __name__ == "__main__":
    # This block now runs after load_dotenv() at the top of the file
    try:
        db_url_main = (
            f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:"
            f"{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:"
            f"{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
        )
        main_engine = create_engine(db_url_main)
        meta = MetaData()
        argo_floats = Table('argo_floats', meta, autoload_with=main_engine)
        run(argo_floats)
    except Exception as e:
        print(f"Could not initialize database connection. Please check your .env file. Error: {e}")