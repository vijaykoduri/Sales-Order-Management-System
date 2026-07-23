def test_user_registration_success(client):
    response = client.post('/api/auth/register', json={
        'username': 'john_doe',
        'email': 'john@example.com',
        'password': 'securepassword',
        'role': 'Employee'
    })
    data = response.get_json()
    assert response.status_code == 201
    assert data['message'] == 'User registered successfully'
    assert data['user']['username'] == 'john_doe'
    assert data['user']['role'] == 'john_doe' or data['user']['role'] == 'Admin' # First registered user becomes Admin automatically

def test_user_registration_duplicate(client):
    # Register first user
    client.post('/api/auth/register', json={
        'username': 'john_doe',
        'email': 'john@example.com',
        'password': 'securepassword',
        'role': 'Employee'
    })
    
    # Attempt duplicate register
    response = client.post('/api/auth/register', json={
        'username': 'john_doe',
        'email': 'john2@example.com',
        'password': 'securepassword',
        'role': 'Employee'
    })
    data = response.get_json()
    assert response.status_code == 400
    assert 'Username is already taken' in data['message']

def test_login_success(client):
    # Register
    client.post('/api/auth/register', json={
        'username': 'jane_doe',
        'email': 'jane@example.com',
        'password': 'securepassword',
        'role': 'Sales Manager'
    })
    
    # Login
    response = client.post('/api/auth/login', json={
        'username': 'jane_doe',
        'password': 'securepassword'
    })
    data = response.get_json()
    assert response.status_code == 200
    assert 'access_token' in data
    assert data['user']['username'] == 'jane_doe'

def test_login_invalid_credentials(client):
    # Login unregistered user
    response = client.post('/api/auth/login', json={
        'username': 'unknown_user',
        'password': 'wrongpassword'
    })
    assert response.status_code == 401
