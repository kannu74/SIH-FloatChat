import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
import chromadb

# Import our custom modules
from backend.data_processing.processor import process_netcdf_file

def run():
    """Main function to run the data ingestion pipeline."""
    load_dotenv()

    # --- 1. Connect to Databases ---
    # PostgreSQL
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

    # ChromaDB
    try:
        chroma_client = chromadb.PersistentClient(path="db/chroma_db")
        # Get or create the collection. `get_or_create` is idempotent.
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
                continue

            # --- 3. Load Data into Databases ---
            try:
                # Load measurements into PostgreSQL
                measurements_df.to_sql('argo_measurements', pg_engine, if_exists='append', index=False)
                
                # Load float metadata into PostgreSQL (upsert logic can be added later)
                # For now, we'll just insert it as a DataFrame
                pd.DataFrame([metadata]).to_sql('argo_floats', pg_engine, if_exists='append', index=False)

                # Create a text summary for the vector database
                summary_text = (
                    f"ARGO float with ID {metadata['float_id']} from the {metadata['project_name']} project. "
                    f"Its latest known position is at latitude {metadata['latest_latitude']:.2f} "
                    f"and longitude {metadata['latest_longitude']:.2f}. "
                    f"This float measures ocean temperature, salinity, and pressure profiles."
                )

                # Add to ChromaDB
                argo_collection.add(
                    documents=[summary_text],
                    metadatas=[{"source": "argo_float_metadata"}],
                    ids=[metadata['float_id']]
                )
                print(f"Successfully ingested data for float {metadata['float_id']}.")
                processed_files += 1

            except Exception as e:
                print(f"Error loading data for {metadata.get('float_id', 'unknown float')} into databases: {e}")

    print(f"\nData ingestion complete. Processed {processed_files} files.")

if __name__ == "__main__":
    run()