import sys
import os
# DON'T CHANGE THIS SECTION
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify, request
from flask_cors import CORS
from src.models.user import db
from src.routes.user import user_bp
from src.routes.financial import financial_bp
from src.routes.oauth import oauth_bp
from src.models.financial import FinancialProfile, FinancialGoal, FinancialExpense
import pymysql

app = Flask(__name__)

# Configure SQLAlchemy
if os.environ.get('DATABASE_URL'):
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
else:
    db_path = os.path.abspath(os.path.join(os.getcwd(), 'instance', 'life_sheet.db'))
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    print('DB Path:', db_path)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_123')

# Enable CORS for all routes
CORS(app, supports_credentials=True, origins=['http://localhost:5173', 'https://life-sheet-app.onrender.com'])

# Session cookie settings for development
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False

# Initialize SQLAlchemy
db.init_app(app)

# Register blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(financial_bp, url_prefix='/api/financial')
app.register_blueprint(oauth_bp, url_prefix='/api/oauth')

# Create database tables if they don't exist
with app.app_context():
    db.create_all()
    
    # Check if columns exist and add them if they don't
    engine = db.engine
    inspector = db.inspect(engine)
    
    try:
        columns = inspector.get_columns('financial_profile')
        column_names = [column['name'] for column in columns]
        
        # List of columns to check and add if missing
        missing_columns = {
            'loan_tenure_years': 'INTEGER',
            'lifespan_years': 'INTEGER',
            'income_growth_rate': 'FLOAT',
            'asset_growth_rate': 'FLOAT'
        }
        
        for column_name, column_type in missing_columns.items():
            if column_name not in column_names:
                print(f"Adding missing column: {column_name}")
                if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite'):
                    db.session.execute(f"ALTER TABLE financial_profile ADD COLUMN {column_name} {column_type}")
                else:
                    db.session.execute(f"ALTER TABLE financial_profile ADD COLUMN {column_name} {column_type} NULL")
        
        db.session.commit()
        print("Database schema updated successfully")
    except Exception as e:
        print(f"Database schema update error: {e}")

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

