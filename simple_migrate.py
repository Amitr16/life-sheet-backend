#!/usr/bin/env python3
"""
Simple database migration script to add new fields to financial_profile table
"""

import pymysql
import os

def migrate_database():
    """Add new columns to financial_profile table"""
    
    try:
        # Database connection parameters (using SQLite for simplicity)
        db_path = '/home/ubuntu/life-sheet-backend/instance/database.db'
        
        # Create instance directory if it doesn't exist
        os.makedirs('/home/ubuntu/life-sheet-backend/instance', exist_ok=True)
        
        # Connect to SQLite database
        import sqlite3
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        
        print("Connected to database successfully!")
        
        # Check if table exists, if not create it
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS financial_profile (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                age INTEGER DEFAULT 0,
                monthly_income DECIMAL(15,2) DEFAULT 0,
                annual_income DECIMAL(15,2) DEFAULT 0,
                asset_value DECIMAL(15,2) DEFAULT 0,
                loan_value DECIMAL(15,2) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # List of new columns to add
        new_columns = [
            ("current_annual_gross_income", "DECIMAL(15,2) DEFAULT 0"),
            ("work_tenure_years", "INTEGER DEFAULT 0"), 
            ("total_asset_gross_market_value", "DECIMAL(15,2) DEFAULT 0"),
            ("total_loan_outstanding_value", "DECIMAL(15,2) DEFAULT 0"),
            ("financial_goal_1", "DECIMAL(15,2) DEFAULT 0"),
            ("financial_goal_2", "DECIMAL(15,2) DEFAULT 0"), 
            ("financial_goal_3", "DECIMAL(15,2) DEFAULT 0"),
            ("financial_goal_1_name", "VARCHAR(255) DEFAULT ''"),
            ("financial_goal_2_name", "VARCHAR(255) DEFAULT ''"),
            ("financial_goal_3_name", "VARCHAR(255) DEFAULT ''"),
            ("annual_expense_1", "DECIMAL(15,2) DEFAULT 0"),
            ("annual_expense_2", "DECIMAL(15,2) DEFAULT 0"),
            ("annual_expense_3", "DECIMAL(15,2) DEFAULT 0"),
            ("annual_expense_1_name", "VARCHAR(255) DEFAULT ''"),
            ("annual_expense_2_name", "VARCHAR(255) DEFAULT ''"),
            ("annual_expense_3_name", "VARCHAR(255) DEFAULT ''")
        ]
        
        print("Starting database migration...")
        
        # Get existing columns
        cursor.execute("PRAGMA table_info(financial_profile)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        print(f"Existing columns: {existing_columns}")
        
        # Add new columns one by one
        for column_name, column_def in new_columns:
            if column_name not in existing_columns:
                try:
                    sql = f"ALTER TABLE financial_profile ADD COLUMN {column_name} {column_def}"
                    print(f"Adding column: {column_name}")
                    cursor.execute(sql)
                    connection.commit()
                    print(f"✓ Added column: {column_name}")
                except Exception as e:
                    print(f"✗ Error adding column {column_name}: {e}")
                    connection.rollback()
            else:
                print(f"✓ Column {column_name} already exists")
        
        # Verify final schema
        cursor.execute("PRAGMA table_info(financial_profile)")
        final_columns = [row[1] for row in cursor.fetchall()]
        print(f"\nFinal table schema:")
        for col in final_columns:
            print(f"  - {col}")
        
        cursor.close()
        connection.close()
        print("\n✅ Database migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    migrate_database()

