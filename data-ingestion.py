import requests
import urllib3
from sqlalchemy import URL, create_engine, text
from urllib3.exceptions import InsecureRequestWarning
import pandas as pd
from urllib.parse import quote_plus


urllib3.disable_warnings(InsecureRequestWarning)

try:
    # Make request without SSL verification
    response = requests.get('https://ebanguka.moh.gov.rw/api/exposed/transfers', 
                           verify=False, timeout=30)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        # Convert JSON response to DataFrame
        data = response.json()
        df = pd.DataFrame(data)
        
        # Convert dict/object columns to JSON strings
        import json
        for col in df.columns:
            if df[col].dtype == 'object':
                # Check if any values are dicts
                sample_value = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
                if isinstance(sample_value, dict):
                    df[col] = df[col].apply(lambda x: json.dumps(x) if isinstance(x, dict) else x)
        
        # Display basic info about the DataFrame
        print(f"\nDataFrame shape: {df.shape}")
        # print(f"Columns: {list(df.columns)}")
        # print("\nFirst few rows:")
        # print(df.head())
        
        # Optional: Display data types
        print("\nData types:")
        print(df.dtypes)
        
        # Export to CSV file
        csv_filename = f"ebanguka_data_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(csv_filename, index=False)
        print(f"\nData exported to CSV file: {csv_filename}")
        
    else:
        print(response.text)
        
except Exception as e:
    print(f"Error: {e}")


df = df.sort_values('createdAt', ascending=False)


def cleanup_and_create_in_emergency_schema(df):
    """Clean up existing table and create in emergency schema using your connection"""
    
    db_host = "localhost"
    db_port = 5432
    db_name = "greenriver"
    db_user = "postgres"
    
    print(f"Connecting to database: {db_user}@{db_host}:{db_port}/{db_name}")
    
    engine = create_engine(URL.create(
        "postgresql+psycopg2",
        username=db_user,
        password="rv!@07842",
        host=db_host,
        port=db_port,
        database=db_name,
    ))
    
    with engine.connect() as conn:
        # Drop table from public schema if it exists
        try:
            conn.execute(text("DROP TABLE IF EXISTS public.ebanguka"))
            print("Cleaned up any existing table in public schema")
        except Exception as e:
            print(f"Public schema cleanup: {e}")
        
        # Drop table from emergency schema if it exists  
        try:
            conn.execute(text("DROP TABLE IF EXISTS emergency.ebanguka"))
            print("Cleaned up any existing table in emergency schema")
        except Exception as e:
            print(f"Emergency schema cleanup: {e}")
        
        conn.commit()
    
    # Now create in emergency schema
    create_table_and_insert_data(df, 'ebanguka', schema='emergency')

def create_table_and_insert_data(df, table_name, schema='public'):
    """Create table and insert DataFrame data into specified schema"""
    
    engine = create_engine(URL.create(
        "postgresql+psycopg2",
        username="postgres",
        password="rv!@07842",
        host="localhost",
        port=5432,
        database="greenriver",
    ))
    
    try:
        # Create schema if it doesn't exist
        with engine.connect() as conn:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
            conn.commit()
        
        # Insert data using pandas to_sql
        df.to_sql(
            name=table_name,
            con=engine,
            schema=schema,
            if_exists='replace',
            index=False,
            method='multi'
        )
        
        print(f"Successfully created table {schema}.{table_name} with {len(df)} rows")
        
    except Exception as e:
        print(f"Error creating table {schema}.{table_name}: {e}")
        raise
    
    finally:
        engine.dispose()

# Run this to clean up and create correctly
if 'df' in locals() and not df.empty:
    cleanup_and_create_in_emergency_schema(df)
else:
    print("No data available to process")
