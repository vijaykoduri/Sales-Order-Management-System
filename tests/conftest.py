import pytest
import sys
import os

# Ensure project root is in the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import db
from models.user import User

@pytest.fixture(scope='session')
def app():
    app = create_app('testing')
    return app

@pytest.fixture(scope='function')
def client(app):
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()

@pytest.fixture
def auth_headers(client):
    """Registers and logs in a test Admin user. Returns headers dict."""
    # Register
    client.post('/api/auth/register', json={
        'username': 'admin_test',
        'email': 'admin@test.com',
        'password': 'password123',
        'role': 'Admin'
    })
    
    # Login
    response = client.post('/api/auth/login', json={
        'username': 'admin_test',
        'password': 'password123'
    })
    
    token = response.get_json()['access_token']
    return {'Authorization': f'Bearer {token}'}
