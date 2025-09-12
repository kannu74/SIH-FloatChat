import xarray as xr
import pandas as pd

def process_netcdf_file(file_path):
    """
    Reads an ARGO NetCDF file and extracts metadata and measurement data.
    """
    try:
        with xr.open_dataset(file_path, decode_times=True) as ds:
            # --- FINAL FIX: Use .decode() to convert bytes to string ---
            platform_number_str = ds['PLATFORM_NUMBER'].values[0].decode('latin-1').strip()
            project_name_str = ds['PROJECT_NAME'].values[0].decode('latin-1').strip()
            # -----------------------------------------------------------

            # Extract metadata
            metadata = {
                'float_id': platform_number_str,
                'project_name': project_name_str,
                'latest_latitude': ds['LATITUDE'].values[-1],
                'latest_longitude': ds['LONGITUDE'].values[-1],
            }

            # Prepare measurements DataFrame
            df = ds[['JULD', 'PRES', 'TEMP', 'PSAL', 'LATITUDE', 'LONGITUDE']].to_dataframe()
            
            # Handle potential multi-index by resetting it
            df = df.reset_index()

            # Rename columns
            df = df.rename(columns={
                'JULD': 'timestamp',
                'PRES': 'pressure',
                'TEMP': 'temperature',
                'PSAL': 'salinity',
                'LATITUDE': 'latitude',
                'LONGITUDE': 'longitude'
            })
            
            df['float_id'] = platform_number_str

            return metadata, df[['float_id', 'timestamp', 'latitude', 'longitude', 'pressure', 'temperature', 'salinity']]

    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return None, None