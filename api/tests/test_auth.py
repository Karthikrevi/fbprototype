
import pytest
import json
from api.furrbutler import create_app
from api.extensions import db
from api.models.user import User, UserRole
from api.models.token_blocklist import TokenBlocklist

@pytest.fixture
def app():
    """Create test app."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False  # Don't expire in tests
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()

@pytest.fixture
def test_user(app):
    """Create a test user."""
    with app.app_context():
        user = User(
            email='test@example.com',
            password='TestPass123',
            role=UserRole.PET_PARENT
        )
        db.session.add(user)
        db.session.commit()
        return user

class TestAuth:
    """Test authentication endpoints."""
    
    def test_register_success(self, client):
        """Test successful user registration."""
        data = {
            'email': 'newuser@example.com',
            'password': 'NewPass123',
            'role': 'pet_parent',
            'full_name': 'New User'
        }
        
        response = client.post('/api/auth/register',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 201
        response_data = json.loads(response.data)
        assert 'user' in response_data
        assert response_data['user']['email'] == 'newuser@example.com'
        assert response_data['user']['role'] == 'pet_parent'
    
    def test_register_duplicate_email(self, client, test_user):
        """Test registration with duplicate email."""
        data = {
            'email': 'test@example.com',
            'password': 'AnotherPass123'
        }
        
        response = client.post('/api/auth/register',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 409
        response_data = json.loads(response.data)
        assert response_data['error']['code'] == 'EMAIL_EXISTS'
    
    def test_register_invalid_email(self, client):
        """Test registration with invalid email."""
        data = {
            'email': 'invalid-email',
            'password': 'ValidPass123'
        }
        
        response = client.post('/api/auth/register',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 400
    
    def test_register_weak_password(self, client):
        """Test registration with weak password."""
        data = {
            'email': 'weak@example.com',
            'password': '123'
        }
        
        response = client.post('/api/auth/register',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 400
    
    def test_login_success(self, client, test_user):
        """Test successful login."""
        data = {
            'email': 'test@example.com',
            'password': 'TestPass123'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert 'access_token' in response_data
        assert 'refresh_token' in response_data
        assert 'user' in response_data
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        data = {
            'email': 'nonexistent@example.com',
            'password': 'WrongPass123'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 401
        response_data = json.loads(response.data)
        assert response_data['error']['code'] == 'INVALID_CREDENTIALS'
    
    def test_get_me_success(self, client, test_user):
        """Test getting current user profile."""
        # Login first
        login_data = {
            'email': 'test@example.com',
            'password': 'TestPass123'
        }
        login_response = client.post('/api/auth/login',
                                   data=json.dumps(login_data),
                                   content_type='application/json')
        
        access_token = json.loads(login_response.data)['access_token']
        
        # Get user profile
        headers = {'Authorization': f'Bearer {access_token}'}
        response = client.get('/api/auth/me', headers=headers)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['user']['email'] == 'test@example.com'
    
    def test_get_me_no_token(self, client):
        """Test getting user profile without token."""
        response = client.get('/api/auth/me')
        
        assert response.status_code == 401
        response_data = json.loads(response.data)
        assert response_data['error']['code'] == 'MISSING_TOKEN'
    
    def test_refresh_token_success(self, client, test_user):
        """Test refreshing access token."""
        # Login first
        login_data = {
            'email': 'test@example.com',
            'password': 'TestPass123'
        }
        login_response = client.post('/api/auth/login',
                                   data=json.dumps(login_data),
                                   content_type='application/json')
        
        refresh_token = json.loads(login_response.data)['refresh_token']
        
        # Refresh token
        headers = {'Authorization': f'Bearer {refresh_token}'}
        response = client.post('/api/auth/refresh', headers=headers)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert 'access_token' in response_data
    
    def test_logout_success(self, client, test_user):
        """Test successful logout."""
        # Login first
        login_data = {
            'email': 'test@example.com',
            'password': 'TestPass123'
        }
        login_response = client.post('/api/auth/login',
                                   data=json.dumps(login_data),
                                   content_type='application/json')
        
        access_token = json.loads(login_response.data)['access_token']
        
        # Logout
        headers = {'Authorization': f'Bearer {access_token}'}
        response = client.post('/api/auth/logout', headers=headers)
        
        assert response.status_code == 200
        
        # Try to access protected endpoint with revoked token
        response = client.get('/api/auth/me', headers=headers)
        assert response.status_code == 401
