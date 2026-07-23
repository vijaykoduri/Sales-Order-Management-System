def test_create_customer(client, auth_headers):
    response = client.post('/api/customers', json={
        'name': 'Client A',
        'email': 'clienta@test.com',
        'phone': '1234567890',
        'company': 'Corporation Inc'
    }, headers=auth_headers)
    
    data = response.get_json()
    assert response.status_code == 201
    assert data['customer']['name'] == 'Client A'
    assert data['customer']['company'] == 'Corporation Inc'

def test_create_customer_duplicate_email(client, auth_headers):
    # First customer
    client.post('/api/customers', json={
        'name': 'Client A',
        'email': 'clienta@test.com',
        'phone': '1234567890'
    }, headers=auth_headers)
    
    # Second customer with same email
    response = client.post('/api/customers', json={
        'name': 'Client B',
        'email': 'clienta@test.com',
        'phone': '0987654321'
    }, headers=auth_headers)
    
    data = response.get_json()
    assert response.status_code == 400
    assert 'email address already exists' in data['message']

def test_get_customers_list(client, auth_headers):
    # Register multiple
    client.post('/api/customers', json={
        'name': 'Alice', 'email': 'alice@test.com', 'phone': '1111'
    }, headers=auth_headers)
    
    client.post('/api/customers', json={
        'name': 'Bob', 'email': 'bob@test.com', 'phone': '2222'
    }, headers=auth_headers)
    
    # Fetch all
    response = client.get('/api/customers', headers=auth_headers)
    data = response.get_json()
    assert response.status_code == 200
    assert len(data['customers']) >= 2

def test_delete_customer_unauthorized(client):
    # Deleting customer should fail if no JWT headers provided
    response = client.delete('/api/customers/1')
    assert response.status_code == 401
