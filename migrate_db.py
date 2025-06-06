#!/usr/bin/env python3
"""
Database migration script to add new fields to financial_profile table
"""

import sys
import os
sys.path.append('/home/ubuntu/life-sheet-backend/src')

from main import app, db
from models.financial import FinancialProfile

def migrate_database():
    """Add new columns to financial_profile table"""
    
    with app.app_context():
        try:
            # Get database connection
            connection = db.engine.raw_connection()
            cursor = connection.cursor()
            
            # List of new columns to add
            new_columns = [
                "ADD COLUMN current_annual_gross_income DECIMAL(15,2) DEFAULT 0",
                "ADD COLUMN work_tenure_years INTEGER DEFAULT 0", 
                "ADD COLUMN total_asset_gross_market_value DECIMAL(15,2) DEFAULT 0",
                "ADD COLUMN total_loan_outstanding_value DECIMAL(15,2) DEFAULT 0",
                "ADD COLUMN financial_goal_1 DECIMAL(15,2) DEFAULT 0",
                "ADD COLUMN financial_goal_2 DECIMAL(15,2) DEFAULT 0", 
                "ADD COLUMN financial_goal_3 DECIMAL(15,2) DEFAULT 0",
                "ADD COLUMN financial_goal_1_name VARCHAR(255) DEFAULT ''",
                "ADD COLUMN financial_goal_2_name VARCHAR(255) DEFAULT ''",
                "ADD COLUMN financial_goal_3_name VARCHAR(255) DEFAULT ''",
                "ADD COLUMN annual_expense_1 DECIMAL(15,2) DEFAULT 0",
                "ADD COLUMN annual_expense_2 DECIMAL(15,2) DEFAULT 0",
                "ADD COLUMN annual_expense_3 DECIMAL(15,2) DEFAULT 0",
                "ADD COLUMN annual_expense_1_name VARCHAR(255) DEFAULT ''",
                "ADD COLUMN annual_expense_2_name VARCHAR(255) DEFAULT ''",
                "ADD COLUMN annual_expense_3_name VARCHAR(255) DEFAULT ''"
            ]
            
            print("Starting database migration...")
            
            # Check if table exists
            cursor.execute("SHOW TABLES LIKE 'financial_profile'")
            if not cursor.fetchone():
                print("Creating financial_profile table...")
                db.create_all()
                print("Table created successfully!")
                return
            
            # Check existing columns
            cursor.execute("DESCRIBE financial_profile")
            existing_columns = [row[0] for row in cursor.fetchall()]
            print(f"Existing columns: {existing_columns}")
            
            # Add new columns one by one
            for column_def in new_columns:
                column_name = column_def.split()[2]  # Extract column name
                
                if column_name not in existing_columns:
                    try:
                        sql = f"ALTER TABLE financial_profile {column_def}"
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
            cursor.execute("DESCRIBE financial_profile")
            final_columns = [row[0] for row in cursor.fetchall()]
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

