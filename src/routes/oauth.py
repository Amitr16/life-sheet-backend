from flask import Blueprint, request, jsonify, redirect, url_for, session
import requests
import secrets
import os
from src.models.user import db, User
from datetime import datetime

oauth_bp = Blueprint('oauth', __name__)

# OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', 'demo-google-client-id')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', 'demo-google-secret')
FACEBOOK_APP_ID = os.getenv('FACEBOOK_APP_ID', 'demo-facebook-app-id')
FACEBOOK_APP_SECRET = os.getenv('FACEBOOK_APP_SECRET', 'demo-facebook-secret')

# OAuth URLs
GOOGLE_AUTH_URL = 'https://accounts.google.com/o/oauth2/auth'
GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_USER_INFO_URL = 'https://www.googleapis.com/oauth2/v2/userinfo'

FACEBOOK_AUTH_URL = 'https://www.facebook.com/v18.0/dialog/oauth'
FACEBOOK_TOKEN_URL = 'https://graph.facebook.com/v18.0/oauth/access_token'
FACEBOOK_USER_INFO_URL = 'https://graph.facebook.com/me'

@oauth_bp.route('/google/login', methods=['GET'])
def google_login():
    """Initiate Google OAuth login"""
    try:
        # Generate state parameter for security
        state = secrets.token_urlsafe(32)
        session['oauth_state'] = state
        
        # Build Google OAuth URL
        params = {
            'client_id': GOOGLE_CLIENT_ID,
            'redirect_uri': request.url_root.rstrip('/') + '/api/oauth/google/callback',
            'scope': 'openid email profile',
            'response_type': 'code',
            'state': state
        }
        
        auth_url = GOOGLE_AUTH_URL + '?' + '&'.join([f'{k}={v}' for k, v in params.items()])
        
        return jsonify({
            'auth_url': auth_url,
            'message': 'Redirect to this URL for Google authentication'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@oauth_bp.route('/google/callback', methods=['GET'])
def google_callback():
    """Handle Google OAuth callback"""
    try:
        # Verify state parameter
        if request.args.get('state') != session.get('oauth_state'):
            return jsonify({'error': 'Invalid state parameter'}), 400
            
        # Get authorization code
        code = request.args.get('code')
        if not code:
            return jsonify({'error': 'No authorization code received'}), 400
            
        # Exchange code for access token
        token_data = {
            'client_id': GOOGLE_CLIENT_ID,
            'client_secret': GOOGLE_CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': request.url_root.rstrip('/') + '/api/oauth/google/callback'
        }
        
        token_response = requests.post(GOOGLE_TOKEN_URL, data=token_data)
        token_json = token_response.json()
        
        if 'access_token' not in token_json:
            return jsonify({'error': 'Failed to get access token'}), 400
            
        # Get user info from Google
        headers = {'Authorization': f'Bearer {token_json["access_token"]}'}
        user_response = requests.get(GOOGLE_USER_INFO_URL, headers=headers)
        user_data = user_response.json()
        
        # Create or get user
        user = create_or_get_oauth_user(user_data, 'google')
        
        # Set session
        session['user_id'] = user.id
        session['user_name'] = user.first_name or user.username
        
        # Redirect to frontend with success
        frontend_url = os.getenv('FRONTEND_URL', 'https://doizqmuw.manus.space')
        return redirect(f'{frontend_url}?oauth_success=true&provider=google')
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@oauth_bp.route('/facebook/login', methods=['GET'])
def facebook_login():
    """Initiate Facebook OAuth login"""
    try:
        # Generate state parameter for security
        state = secrets.token_urlsafe(32)
        session['oauth_state'] = state
        
        # Build Facebook OAuth URL
        params = {
            'client_id': FACEBOOK_APP_ID,
            'redirect_uri': request.url_root.rstrip('/') + '/api/oauth/facebook/callback',
            'scope': 'email,public_profile',
            'response_type': 'code',
            'state': state
        }
        
        auth_url = FACEBOOK_AUTH_URL + '?' + '&'.join([f'{k}={v}' for k, v in params.items()])
        
        return jsonify({
            'auth_url': auth_url,
            'message': 'Redirect to this URL for Facebook authentication'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@oauth_bp.route('/facebook/callback', methods=['GET'])
def facebook_callback():
    """Handle Facebook OAuth callback"""
    try:
        # Verify state parameter
        if request.args.get('state') != session.get('oauth_state'):
            return jsonify({'error': 'Invalid state parameter'}), 400
            
        # Get authorization code
        code = request.args.get('code')
        if not code:
            return jsonify({'error': 'No authorization code received'}), 400
            
        # Exchange code for access token
        token_params = {
            'client_id': FACEBOOK_APP_ID,
            'client_secret': FACEBOOK_APP_SECRET,
            'code': code,
            'redirect_uri': request.url_root.rstrip('/') + '/api/oauth/facebook/callback'
        }
        
        token_response = requests.get(FACEBOOK_TOKEN_URL, params=token_params)
        token_json = token_response.json()
        
        if 'access_token' not in token_json:
            return jsonify({'error': 'Failed to get access token'}), 400
            
        # Get user info from Facebook
        user_params = {
            'access_token': token_json['access_token'],
            'fields': 'id,name,email,first_name,last_name'
        }
        user_response = requests.get(FACEBOOK_USER_INFO_URL, params=user_params)
        user_data = user_response.json()
        
        # Create or get user
        user = create_or_get_oauth_user(user_data, 'facebook')
        
        # Set session
        session['user_id'] = user.id
        session['user_name'] = user.first_name or user.username
        
        # Redirect to frontend with success
        frontend_url = os.getenv('FRONTEND_URL', 'https://doizqmuw.manus.space')
        return redirect(f'{frontend_url}?oauth_success=true&provider=facebook')
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def create_or_get_oauth_user(user_data, provider):
    """Create or get user from OAuth data"""
    try:
        # Extract user information based on provider
        if provider == 'google':
            oauth_id = user_data.get('id')
            email = user_data.get('email')
            first_name = user_data.get('given_name', '')
            last_name = user_data.get('family_name', '')
            username = email.split('@')[0] if email else f'google_user_{oauth_id}'
        elif provider == 'facebook':
            oauth_id = user_data.get('id')
            email = user_data.get('email')
            first_name = user_data.get('first_name', '')
            last_name = user_data.get('last_name', '')
            username = email.split('@')[0] if email else f'facebook_user_{oauth_id}'
        else:
            raise ValueError(f'Unsupported OAuth provider: {provider}')
            
        # Check if user already exists by email
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            # Update last login
            existing_user.last_login = datetime.utcnow()
            db.session.commit()
            return existing_user
            
        # Create new user
        # Make username unique if it already exists
        base_username = username
        counter = 1
        while User.query.filter_by(username=username).first():
            username = f'{base_username}_{counter}'
            counter += 1
            
        new_user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password_hash='oauth_user',  # OAuth users don't have passwords
            is_active=True,
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow()
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        return new_user
        
    except Exception as e:
        db.session.rollback()
        raise e

# Demo endpoints for testing
@oauth_bp.route('/demo/google', methods=['GET'])
def demo_google():
    """Demo Google OAuth for testing"""
    try:
        # Create a demo user
        demo_user_data = {
            'id': '123456789',
            'email': 'demo.google@example.com',
            'given_name': 'Google',
            'family_name': 'User'
        }
        
        user = create_or_get_oauth_user(demo_user_data, 'google')
        
        return jsonify({
            'message': 'Demo Google OAuth successful',
            'user': user.to_dict(),
            'provider': 'google'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@oauth_bp.route('/demo/facebook', methods=['GET'])
def demo_facebook():
    """Demo Facebook OAuth for testing"""
    try:
        # Create a demo user
        demo_user_data = {
            'id': '987654321',
            'email': 'demo.facebook@example.com',
            'first_name': 'Facebook',
            'last_name': 'User'
        }
        
        user = create_or_get_oauth_user(demo_user_data, 'facebook')
        
        return jsonify({
            'message': 'Demo Facebook OAuth successful',
            'user': user.to_dict(),
            'provider': 'facebook'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

