import xarray as xr
import pandas as pd

def process_netcdf_file(file_path):
    """
    Reads an ARGO NetCDF file and extracts metadata and measurement data.

    Args:
        file_path (str): The path to the NetCDF file.

    Returns:
        tuple: A tuple containing (metadata_dict, measurements_df) or (None, None) on failure.
    """
    try:
        with xr.open_dataset(file_path, decode_times=True) as ds:
            # Extract float ID from attributes
            platform_number_str = str(ds.PLATFORM_NUMBER.values.astype(str).item()).strip()

            # Extract metadata
            metadata = {
                'float_id': platform_number_str,
                'project_name': str(ds.PROJECT_NAME.values.astype(str).item()).strip(),
                'latest_latitude': ds['LATITUDE'].values[-1],
                'latest_longitude': ds['LONGITUDE'].values[-1],
            }

            # Prepare measurements DataFrame
            df = ds[['PRES', 'TEMP', 'PSAL', 'LATITUDE', 'LONGITUDE']].to_dataframe()
            
            # Handle potential multi-index by resetting it
            df = df.reset_index()

            # Rename columns to be more database-friendly
            df = df.rename(columns={
                'JULD': 'timestamp',
                'PRES': 'pressure',
                'TEMP': 'temperature',
                'PSAL': 'salinity',
                'LATITUDE': 'latitude',
                'LONGITUDE': 'longitude'
            })
            
            # Add float_id to each measurement row
            df['float_id'] = platform_number_str

            return metadata, df[['float_id', 'timestamp', 'latitude', 'longitude', 'pressure', 'temperature', 'salinity']]

    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return None, None