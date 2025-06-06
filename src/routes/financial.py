from flask import Blueprint, request, jsonify
from src.models.user import db, User
from src.models.financial import FinancialProfile, FinancialGoal, FinancialExpense, FinancialScenario, FinancialLoan
from datetime import datetime, date
import json

financial_bp = Blueprint('financial', __name__)

# Financial Profile Routes
@financial_bp.route('/profile', methods=['POST'])
def create_financial_profile():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['user_id', 'age']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check if user exists
        user = User.query.get(data['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Create new financial profile with core fields
        profile = FinancialProfile(
            user_id=data['user_id'],
            age=data['age'],
            
            # Core financial inputs
            current_annual_gross_income=data.get('current_annual_gross_income'),
            work_tenure_years=data.get('work_tenure_years'),
            total_asset_gross_market_value=data.get('total_asset_gross_market_value', 0),
            total_loan_outstanding_value=data.get('total_loan_outstanding_value', 0),
            loan_tenure_years=data.get('loan_tenure_years'),
            
            # Legacy fields (keeping for backward compatibility)
            monthly_income=data.get('monthly_income'),
            annual_income=data.get('annual_income'),
            asset_value=data.get('asset_value', 0),
            loan_value=data.get('loan_value', 0),
            
            # Calculation assumptions
            lifespan_years=data.get('lifespan_years', 85),
            income_growth_rate=data.get('income_growth_rate', 0.06),
            asset_growth_rate=data.get('asset_growth_rate', 0.06)
        )
        
        db.session.add(profile)
        db.session.commit()
        
        return jsonify({
            'message': 'Financial profile created successfully',
            'profile': profile.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@financial_bp.route('/profile/<int:user_id>', methods=['GET'])
def get_financial_profile(user_id):
    try:
        profile = FinancialProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            return jsonify({'error': 'Financial profile not found'}), 404
        
        return jsonify({'profile': profile.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@financial_bp.route('/profile/<int:profile_id>', methods=['PUT'])
def update_financial_profile(profile_id):
    try:
        profile = FinancialProfile.query.get(profile_id)
        if not profile:
            return jsonify({'error': 'Financial profile not found'}), 404
        
        data = request.get_json()
        
        # Update core fields if provided
        if 'age' in data:
            profile.age = data['age']
        if 'current_annual_gross_income' in data:
            profile.current_annual_gross_income = data['current_annual_gross_income']
        if 'work_tenure_years' in data:
            profile.work_tenure_years = data['work_tenure_years']
        if 'total_asset_gross_market_value' in data:
            profile.total_asset_gross_market_value = data['total_asset_gross_market_value']
        if 'total_loan_outstanding_value' in data:
            profile.total_loan_outstanding_value = data['total_loan_outstanding_value']
        if 'loan_tenure_years' in data:
            profile.loan_tenure_years = data['loan_tenure_years']
        
        # Update legacy fields
        if 'monthly_income' in data:
            profile.monthly_income = data['monthly_income']
        if 'annual_income' in data:
            profile.annual_income = data['annual_income']
        if 'asset_value' in data:
            profile.asset_value = data['asset_value']
        if 'loan_value' in data:
            profile.loan_value = data['loan_value']
        
        # Update assumptions
        if 'lifespan_years' in data:
            profile.lifespan_years = data['lifespan_years']
        if 'income_growth_rate' in data:
            profile.income_growth_rate = data['income_growth_rate']
        if 'asset_growth_rate' in data:
            profile.asset_growth_rate = data['asset_growth_rate']
        
        profile.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Financial profile updated successfully',
            'profile': profile.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Dynamic Financial Goals Routes
@financial_bp.route('/goals', methods=['POST'])
def create_financial_goal():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['user_id', 'profile_id', 'description', 'amount']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Get the next order index for this profile
        max_order = db.session.query(db.func.max(FinancialGoal.order_index)).filter_by(
            profile_id=data['profile_id']
        ).scalar() or 0
        
        # Create new financial goal
        goal = FinancialGoal(
            user_id=data['user_id'],
            profile_id=data['profile_id'],
            description=data['description'],
            amount=data['amount'],
            order_index=max_order + 1,
            target_date=datetime.strptime(data['target_date'], '%Y-%m-%d').date() if data.get('target_date') else None,
            priority=data.get('priority', 'medium'),
            status=data.get('status', 'active')
        )
        
        db.session.add(goal)
        db.session.commit()
        
        return jsonify({
            'message': 'Financial goal created successfully',
            'goal': goal.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@financial_bp.route('/goals/<int:user_id>', methods=['GET'])
def get_financial_goals(user_id):
    try:
        goals = FinancialGoal.query.filter_by(user_id=user_id).order_by(FinancialGoal.order_index).all()
        return jsonify({
            'goals': [goal.to_dict() for goal in goals]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@financial_bp.route('/goals/<int:goal_id>', methods=['PUT'])
def update_financial_goal(goal_id):
    try:
        goal = FinancialGoal.query.get(goal_id)
        if not goal:
            return jsonify({'error': 'Financial goal not found'}), 404
        
        data = request.get_json()
        
        # Update fields if provided
        if 'description' in data:
            goal.description = data['description']
        if 'amount' in data:
            goal.amount = data['amount']
        if 'target_date' in data:
            if data['target_date']:
                goal.target_date = datetime.strptime(data['target_date'], '%Y-%m-%d').date()
            else:
                goal.target_date = None
        if 'priority' in data:
            goal.priority = data['priority']
        if 'status' in data:
            goal.status = data['status']
        
        goal.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Financial goal updated successfully',
            'goal': goal.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@financial_bp.route('/goals/<int:goal_id>', methods=['DELETE'])
def delete_financial_goal(goal_id):
    try:
        goal = FinancialGoal.query.get(goal_id)
        if not goal:
            return jsonify({'error': 'Financial goal not found'}), 404
        
        db.session.delete(goal)
        db.session.commit()
        
        return jsonify({'message': 'Financial goal deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Dynamic Financial Expenses Routes
@financial_bp.route('/expenses', methods=['POST'])
def create_financial_expense():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['user_id', 'profile_id', 'description', 'amount']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Get the next order index for this profile
        max_order = db.session.query(db.func.max(FinancialExpense.order_index)).filter_by(
            profile_id=data['profile_id']
        ).scalar() or 0
        
        # Create new financial expense
        expense = FinancialExpense(
            user_id=data['user_id'],
            profile_id=data['profile_id'],
            description=data['description'],
            amount=data['amount'],
            order_index=max_order + 1,
            expense_type=data.get('expense_type', 'general'),
            frequency=data.get('frequency', 'annual'),
            is_essential=data.get('is_essential', True)
        )
        
        db.session.add(expense)
        db.session.commit()
        
        return jsonify({
            'message': 'Financial expense created successfully',
            'expense': expense.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@financial_bp.route('/expenses/<int:user_id>', methods=['GET'])
def get_financial_expenses(user_id):
    try:
        expenses = FinancialExpense.query.filter_by(user_id=user_id).order_by(FinancialExpense.order_index).all()
        return jsonify({
            'expenses': [expense.to_dict() for expense in expenses]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@financial_bp.route('/expenses/<int:expense_id>', methods=['PUT'])
def update_financial_expense(expense_id):
    try:
        expense = FinancialExpense.query.get(expense_id)
        if not expense:
            return jsonify({'error': 'Financial expense not found'}), 404
        
        data = request.get_json()
        
        # Update fields if provided
        if 'description' in data:
            expense.description = data['description']
        if 'amount' in data:
            expense.amount = data['amount']
        if 'expense_type' in data:
            expense.expense_type = data['expense_type']
        if 'frequency' in data:
            expense.frequency = data['frequency']
        if 'is_essential' in data:
            expense.is_essential = data['is_essential']
        
        expense.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Financial expense updated successfully',
            'expense': expense.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@financial_bp.route('/expenses/<int:expense_id>', methods=['DELETE'])
def delete_financial_expense(expense_id):
    try:
        expense = FinancialExpense.query.get(expense_id)
        if not expense:
            return jsonify({'error': 'Financial expense not found'}), 404
        
        db.session.delete(expense)
        db.session.commit()
        
        return jsonify({'message': 'Financial expense deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Financial Calculations Route
@financial_bp.route('/calculate', methods=['POST'])
def calculate_financial_projections():
    try:
        data = request.get_json()
        
        # Extract input data
        age = data.get('age', 30)
        current_annual_gross_income = data.get('current_annual_gross_income', 0)
        work_tenure_years = data.get('work_tenure_years', 0)
        total_asset_gross_market_value = data.get('total_asset_gross_market_value', 0)
        total_loan_outstanding_value = data.get('total_loan_outstanding_value', 0)
        
        # Growth assumptions based on Excel analysis
        income_growth_rate = data.get('income_growth_rate', 0.06)  # 6% inflation
        asset_growth_rate = data.get('asset_growth_rate', 0.06)    # 6% inflation
        lifespan_years = data.get('lifespan_years', 85)
        
        # Calculate financial metrics based on Excel logic
        retirement_age = 65
        remaining_years = max(0, min(work_tenure_years, retirement_age - age))
        
        # Total Human Capital calculation (simple multiplication, no growth)
        total_human_capital = current_annual_gross_income * work_tenure_years
        
        # Total Existing Assets
        total_existing_assets = total_asset_gross_market_value
        
        # Total Existing Liabilities
        total_existing_liabilities = total_loan_outstanding_value
        
        # Current Net Worth
        current_networth = total_existing_assets - total_existing_liabilities
        
        # Total Future Expenses (from dynamic expenses)
        total_future_expenses = 0
        if 'expenses' in data:
            for expense in data['expenses']:
                expense_amount = expense.get('amount', 0)
                # Multiply by remaining life years
                remaining_life_years = max(0, lifespan_years - age)
                total_future_expenses += expense_amount * remaining_life_years
        
        # Total Financial Goals (from dynamic goals)
        total_financial_goals = 0
        if 'goals' in data:
            for goal in data['goals']:
                total_financial_goals += goal.get('amount', 0)
        
        # Surplus/Deficit calculation
        total_assets = total_existing_assets + total_human_capital
        total_liabilities = total_existing_liabilities + total_future_expenses + total_financial_goals
        surplus_deficit = total_assets - total_liabilities
        
        # Generate projection data for chart
        projections = []
        current_year = 2025  # Base year from Excel
        
        for year in range(0, min(remaining_years + 1, 26), 1):
            # Calculate projected values
            projected_income = current_annual_gross_income * ((1 + income_growth_rate) ** year) if year < remaining_years else 0
            projected_assets = total_asset_gross_market_value * ((1 + asset_growth_rate) ** year)
            
            projections.append({
                'year': current_year + year,
                'age': age + year,
                'income': round(projected_income),
                'assets': round(projected_assets),
                'human_capital': round(projected_income * max(0, remaining_years - year)) if year < remaining_years else 0
            })
        
        return jsonify({
            'calculations': {
                'total_existing_assets': round(total_existing_assets),
                'total_human_capital': round(total_human_capital),
                'total_existing_liabilities': round(total_existing_liabilities),
                'total_future_expenses': round(total_future_expenses),
                'total_financial_goals': round(total_financial_goals),
                'current_networth': round(current_networth),
                'surplus_deficit': round(surplus_deficit)
            },
            'projections': projections
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Financial Scenarios Routes
@financial_bp.route('/scenarios', methods=['POST'])
def create_financial_scenario():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['user_id', 'profile_id', 'scenario_name']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create new financial scenario
        scenario = FinancialScenario(
            user_id=data['user_id'],
            profile_id=data['profile_id'],
            scenario_name=data['scenario_name'],
            description=data.get('description'),
            surplus=data.get('surplus', 0),
            total_assets=data.get('total_assets', 0),
            total_liabilities=data.get('total_liabilities', 0),
            human_capital=data.get('human_capital', 0),
            future_expenses=data.get('future_expenses', 0),
            net_worth=data.get('net_worth', 0),
            asset_growth_rate=data.get('asset_growth_rate', 0.06),
            income_growth_rate=data.get('income_growth_rate', 0.06),
            expense_growth_rate=data.get('expense_growth_rate', 0.06)
        )
        
        db.session.add(scenario)
        db.session.commit()
        
        return jsonify({
            'message': 'Financial scenario created successfully',
            'scenario': scenario.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@financial_bp.route('/scenarios/<int:user_id>', methods=['GET'])
def get_financial_scenarios(user_id):
    try:
        scenarios = FinancialScenario.query.filter_by(user_id=user_id).all()
        return jsonify({
            'scenarios': [scenario.to_dict() for scenario in scenarios]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- Loan CRUD Endpoints ---
@financial_bp.route('/loans', methods=['POST'])
def create_financial_loan():
    try:
        data = request.get_json()
        required_fields = ['user_id', 'profile_id', 'name', 'amount']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        # Get the next order index for this profile
        max_order = db.session.query(db.func.max(FinancialLoan.order_index)).filter_by(
            profile_id=data['profile_id']
        ).scalar() or 0
        loan = FinancialLoan(
            user_id=data['user_id'],
            profile_id=data['profile_id'],
            name=data['name'],
            amount=data['amount'],
            order_index=max_order + 1
        )
        db.session.add(loan)
        db.session.commit()
        return jsonify({'message': 'Financial loan created successfully', 'loan': loan.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@financial_bp.route('/loans/<int:user_id>', methods=['GET'])
def get_financial_loans(user_id):
    try:
        loans = FinancialLoan.query.filter_by(user_id=user_id).order_by(FinancialLoan.order_index).all()
        return jsonify({'loans': [loan.to_dict() for loan in loans]}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@financial_bp.route('/loans/<int:loan_id>', methods=['PUT'])
def update_financial_loan(loan_id):
    try:
        loan = FinancialLoan.query.get(loan_id)
        if not loan:
            return jsonify({'error': 'Financial loan not found'}), 404
        data = request.get_json()
        if 'name' in data:
            loan.name = data['name']
        if 'amount' in data:
            loan.amount = data['amount']
        loan.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'message': 'Financial loan updated successfully', 'loan': loan.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@financial_bp.route('/loans/<int:loan_id>', methods=['DELETE'])
def delete_financial_loan(loan_id):
    try:
        loan = FinancialLoan.query.get(loan_id)
        if not loan:
            return jsonify({'error': 'Financial loan not found'}), 404
        db.session.delete(loan)
        db.session.commit()
        return jsonify({'message': 'Financial loan deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

