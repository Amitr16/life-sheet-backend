from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class FinancialProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    
    # Core financial inputs based on Excel analysis
    current_annual_gross_income = db.Column(db.Float, nullable=True)
    work_tenure_years = db.Column(db.Integer, nullable=True)
    total_asset_gross_market_value = db.Column(db.Float, default=0)
    total_loan_outstanding_value = db.Column(db.Float, default=0)
    loan_tenure_years = db.Column(db.Integer, nullable=True)
    
    # Legacy fields (keeping for backward compatibility)
    monthly_income = db.Column(db.Float, nullable=True)
    annual_income = db.Column(db.Float, nullable=True)
    asset_value = db.Column(db.Float, default=0)
    loan_value = db.Column(db.Float, default=0)
    
    # Calculation assumptions
    lifespan_years = db.Column(db.Integer, default=85)
    income_growth_rate = db.Column(db.Float, default=0.06)  # 6% inflation
    asset_growth_rate = db.Column(db.Float, default=0.06)   # 6% inflation
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with user
    user = db.relationship('User', backref=db.backref('financial_profiles', lazy=True))
    
    def __repr__(self):
        return f'<FinancialProfile {self.id} for User {self.user_id}>'
    
    def calculate_total_existing_assets(self):
        """Calculate total existing assets"""
        return (self.total_asset_gross_market_value or 0)
    
    def calculate_total_human_capital(self):
        """Calculate total human capital based on income and work tenure (no growth rate)"""
        if self.current_annual_gross_income and self.work_tenure_years:
            return self.current_annual_gross_income * self.work_tenure_years
        return 0
    
    def calculate_total_existing_liabilities(self):
        """Calculate total existing liabilities"""
        return (self.total_loan_outstanding_value or 0)
    
    def calculate_total_future_expenses(self):
        """Calculate total future expenses from dynamic expense entries"""
        total = 0
        for expense in self.expenses:
            if expense.amount:
                # Multiply by remaining years (simplified calculation)
                remaining_years = max(0, (self.lifespan_years or 85) - (self.age or 25))
                total += expense.amount * remaining_years
        return total
    
    def calculate_total_financial_goals(self):
        """Calculate total financial goals from dynamic goal entries"""
        return sum(goal.amount for goal in self.goals if goal.amount)
    
    def calculate_current_networth(self):
        """Calculate current net worth"""
        assets = self.calculate_total_existing_assets()
        liabilities = self.calculate_total_existing_liabilities()
        return assets - liabilities
    
    def calculate_surplus_deficit(self):
        """Calculate surplus/deficit"""
        total_assets = self.calculate_total_existing_assets() + self.calculate_total_human_capital()
        total_liabilities = (self.calculate_total_existing_liabilities() + 
                           self.calculate_total_future_expenses() + 
                           self.calculate_total_financial_goals())
        return total_assets - total_liabilities
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'age': self.age,
            
            # Core fields
            'current_annual_gross_income': self.current_annual_gross_income,
            'work_tenure_years': self.work_tenure_years,
            'total_asset_gross_market_value': self.total_asset_gross_market_value,
            'total_loan_outstanding_value': self.total_loan_outstanding_value,
            'loan_tenure_years': self.loan_tenure_years,
            
            # Legacy fields
            'monthly_income': self.monthly_income,
            'annual_income': self.annual_income,
            'asset_value': self.asset_value,
            'loan_value': self.loan_value,
            
            # Assumptions
            'lifespan_years': self.lifespan_years,
            'income_growth_rate': self.income_growth_rate,
            'asset_growth_rate': self.asset_growth_rate,
            
            # Dynamic collections
            'goals': [goal.to_dict() for goal in self.goals],
            'expenses': [expense.to_dict() for expense in self.expenses],
            
            # Calculated values
            'total_existing_assets': self.calculate_total_existing_assets(),
            'total_human_capital': self.calculate_total_human_capital(),
            'total_existing_liabilities': self.calculate_total_existing_liabilities(),
            'total_future_expenses': self.calculate_total_future_expenses(),
            'total_financial_goals': self.calculate_total_financial_goals(),
            'current_networth': self.calculate_current_networth(),
            'surplus_deficit': self.calculate_surplus_deficit(),
            
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'loans': [loan.to_dict() for loan in self.loans]
        }

class FinancialGoal(db.Model):
    """Dynamic financial goals - can be added progressively"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    profile_id = db.Column(db.Integer, db.ForeignKey('financial_profile.id'), nullable=False)
    
    # Goal details
    description = db.Column(db.String(255), nullable=False)  # Goal description/name
    amount = db.Column(db.Float, nullable=False)             # Goal amount
    order_index = db.Column(db.Integer, nullable=False)      # Order of creation (1, 2, 3...)
    
    # Optional fields for future enhancement
    target_date = db.Column(db.Date, nullable=True)
    priority = db.Column(db.String(20), default='medium')    # high, medium, low
    status = db.Column(db.String(20), default='active')      # active, completed, paused
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('financial_goals', lazy=True))
    profile = db.relationship('FinancialProfile', backref=db.backref('goals', lazy=True, order_by='FinancialGoal.order_index'))
    
    def __repr__(self):
        return f'<FinancialGoal {self.description} for User {self.user_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'profile_id': self.profile_id,
            'description': self.description,
            'amount': self.amount,
            'order_index': self.order_index,
            'target_date': self.target_date.isoformat() if self.target_date else None,
            'priority': self.priority,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class FinancialExpense(db.Model):
    """Dynamic financial expenses - can be added progressively"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    profile_id = db.Column(db.Integer, db.ForeignKey('financial_profile.id'), nullable=False)
    
    # Expense details
    description = db.Column(db.String(255), nullable=False)  # Expense description/name
    amount = db.Column(db.Float, nullable=False)             # Annual expense amount
    order_index = db.Column(db.Integer, nullable=False)      # Order of creation (1, 2, 3...)
    
    # Expense type for categorization
    expense_type = db.Column(db.String(50), default='general')  # general, emi, insurance, etc.
    
    # Optional fields for future enhancement
    frequency = db.Column(db.String(20), default='annual')   # annual, monthly, quarterly
    is_essential = db.Column(db.Boolean, default=True)       # essential vs discretionary
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('financial_expenses', lazy=True))
    profile = db.relationship('FinancialProfile', backref=db.backref('expenses', lazy=True, order_by='FinancialExpense.order_index'))
    
    def __repr__(self):
        return f'<FinancialExpense {self.description} for User {self.user_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'profile_id': self.profile_id,
            'description': self.description,
            'amount': self.amount,
            'order_index': self.order_index,
            'expense_type': self.expense_type,
            'frequency': self.frequency,
            'is_essential': self.is_essential,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class FinancialScenario(db.Model):
    """Financial scenarios for what-if analysis"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    profile_id = db.Column(db.Integer, db.ForeignKey('financial_profile.id'), nullable=False)
    scenario_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Calculation results
    surplus = db.Column(db.Float, default=0)
    total_assets = db.Column(db.Float, default=0)
    total_liabilities = db.Column(db.Float, default=0)
    human_capital = db.Column(db.Float, default=0)
    future_expenses = db.Column(db.Float, default=0)
    net_worth = db.Column(db.Float, default=0)
    
    # Growth assumptions for scenario
    asset_growth_rate = db.Column(db.Float, default=0.06)    # 6%
    income_growth_rate = db.Column(db.Float, default=0.06)   # 6%
    expense_growth_rate = db.Column(db.Float, default=0.06)  # 6%
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('financial_scenarios', lazy=True))
    profile = db.relationship('FinancialProfile', backref=db.backref('scenarios', lazy=True))
    
    def __repr__(self):
        return f'<FinancialScenario {self.scenario_name} for User {self.user_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'profile_id': self.profile_id,
            'scenario_name': self.scenario_name,
            'description': self.description,
            'surplus': self.surplus,
            'total_assets': self.total_assets,
            'total_liabilities': self.total_liabilities,
            'human_capital': self.human_capital,
            'future_expenses': self.future_expenses,
            'net_worth': self.net_worth,
            'asset_growth_rate': self.asset_growth_rate,
            'income_growth_rate': self.income_growth_rate,
            'expense_growth_rate': self.expense_growth_rate,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class FinancialLoan(db.Model):
    """Dynamic loans - can be added progressively"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    profile_id = db.Column(db.Integer, db.ForeignKey('financial_profile.id'), nullable=False)
    
    # Loan details
    name = db.Column(db.String(255), nullable=False)  # Loan name/description
    amount = db.Column(db.Float, nullable=False)      # Loan amount
    order_index = db.Column(db.Integer, nullable=False)  # Order of creation
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('financial_loans', lazy=True))
    profile = db.relationship('FinancialProfile', backref=db.backref('loans', lazy=True, order_by='FinancialLoan.order_index'))
    
    def __repr__(self):
        return f'<FinancialLoan {self.name} for User {self.user_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'profile_id': self.profile_id,
            'name': self.name,
            'amount': self.amount,
            'order_index': self.order_index,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

