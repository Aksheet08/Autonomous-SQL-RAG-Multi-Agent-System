import sqlite3
import pandas as pd
import os

DB_PATH = "real_estate.db"
CSV_URL = "https://raw.githubusercontent.com/STATCowboy/pbidataflowstalk/master/AmesHousing.csv"

def init_db():
    """Downloads Ames Housing Dataset and initializes the real estate database."""
    print("Downloading Ames Housing Dataset...")
    
    # Load data using Pandas
    df = pd.read_csv(CSV_URL)
    
    # Clean column names (replace spaces with underscores, remove special chars if any)
    df.columns = df.columns.str.replace(' ', '_').str.replace('/', '_').str.replace('-', '_')
    
    print(f"Loaded {df.shape[0]} rows and {df.shape[1]} columns.")
    
    # Connect to SQLite
    conn = sqlite3.connect(DB_PATH)
    
    # Write to SQLite
    print("Writing data to SQLite database...")
    df.to_sql('properties', conn, if_exists='replace', index=False)
    
    conn.commit()
    conn.close()
    
    print(f"Database successfully created at {DB_PATH}")

if __name__ == '__main__':
    init_db()
