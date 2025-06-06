#!/usr/bin/env python3
"""
Database migration script to add the loan_tenure_years column to the financial_profile table.
"""
import os
import sys
import pymysql
from urllib.parse import urlparse

# Get the database URL from the environment or use a default
DATABASE_URL = os.environ.get('DATABASE_URL', 'mysql://root:password@localhost/life_sheet')

# Parse the database URL
url = urlparse(DATABASE_URL)
db_user = url.username
db_password = url.password
db_host = url.hostname
db_name = url.path.strip('/')

try:
    # Connect to the database
    conn = pymysql.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name
    )
    
    cursor = conn.cursor()
    
    # Check if the column already exists
    cursor.execute("""
        SELECT COUNT(*)
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = %s
        AND TABLE_NAME = 'financial_profile'
        AND COLUMN_NAME = 'loan_tenure_years'
    """, (db_name,))
    
    column_exists = cursor.fetchone()[0] > 0
    
    if not column_exists:
        # Add the loan_tenure_years column
        cursor.execute("""
            ALTER TABLE financial_profile
            ADD COLUMN loan_tenure_years INT NULL
        """)
        print("Added loan_tenure_years column to financial_profile table")
    else:
        print("loan_tenure_years column already exists")
    
    # Check for other missing columns from the error message
    missing_columns = [
        'lifespan_years',
        'income_growth_rate',
        'asset_growth_rate'
    ]
    
    for column in missing_columns:
        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = %s
            AND TABLE_NAME = 'financial_profile'
            AND COLUMN_NAME = %s
        """, (db_name, column))
        
        column_exists = cursor.fetchone()[0] > 0
        
        if not column_exists:
            # Add the column with appropriate data type
            if column in ['income_growth_rate', 'asset_growth_rate']:
                cursor.execute(f"""
                    ALTER TABLE financial_profile
                    ADD COLUMN {column} FLOAT NULL
                """)
            else:
                cursor.execute(f"""
                    ALTER TABLE financial_profile
                    ADD COLUMN {column} INT NULL
                """)
            print(f"Added {column} column to financial_profile table")
        else:
            print(f"{column} column already exists")
    
    # Commit the changes
    conn.commit()
    print("Database migration completed successfully")
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
finally:
    if 'conn' in locals():
        conn.close()

