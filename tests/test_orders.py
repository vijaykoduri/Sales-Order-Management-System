def test_quotation_creation_and_conversion(client, auth_headers):
    # 1. Create a customer
    cust_res = client.post('/api/customers', json={
        'name': 'Client C',
        'email': 'clientc@test.com',
        'phone': '1234567890'
    }, headers=auth_headers)
    cust_id = cust_res.get_json()['customer']['id']
    
    # 2. Create a product category
    cat_res = client.post('/api/categories', json={
        'name': 'Category Alpha',
        'description': 'Description alpha'
    }, headers=auth_headers)
    cat_id = cat_res.get_json()['category']['id']
    
    # 3. Create a product
    prod_res = client.post('/api/products', json={
        'name': 'Product Red',
        'code': 'P-RED',
        'sku': 'SKU-RED',
        'category_id': cat_id,
        'cost_price': 10.0,
        'selling_price': 15.0,
        'stock_quantity': 50,
        'unit': 'Units'
    }, headers=auth_headers)
    prod_id = prod_res.get_json()['product']['id']
    
    # 4. Create Quotation
    quote_res = client.post('/api/orders/quotations', json={
        'customer_id': cust_id,
        'discount_rate': 10.0,  # 10%
        'gst_rate': 18.0,       # 18% GST
        'items': [
            {
                'product_id': prod_id,
                'quantity': 10
            }
        ]
    }, headers=auth_headers)
    assert quote_res.status_code == 201
    quote_data = quote_res.get_json()['quotation']
    assert quote_data['status'] == 'Draft'
    # subtotal = 10 * 15 = 150
    # discount = 150 * 0.1 = 15
    # tax = (150 - 15) * 0.18 = 24.3
    # grand = 150 - 15 + 24.3 = 159.3
    assert abs(quote_data['grand_total'] - 159.3) < 0.01
    
    # Approve Quotation
    quote_id = quote_data['id']
    app_res = client.post(f'/api/orders/quotations/{quote_id}/approve', headers=auth_headers)
    assert app_res.status_code == 200
    
    # Convert Quotation
    conv_res = client.post(f'/api/orders/quotations/{quote_id}/convert', headers=auth_headers)
    assert conv_res.status_code == 201
    order_data = conv_res.get_json()['order']
    assert order_data['status'] == 'Pending'
    
    # 5. Confirm Order (Triggers stock deduction and invoice generation)
    order_id = order_data['id']
    confirm_res = client.put(f'/api/orders/orders/{order_id}/status', json={
        'status': 'Confirmed'
    }, headers=auth_headers)
    assert confirm_res.status_code == 200
    
    # Verify product stock deducted: original 50, ordered 10, remaining should be 40
    prod_check = client.get(f'/api/products/{prod_id}', headers=auth_headers)
    assert prod_check.get_json()['stock_quantity'] == 40
    
    # Verify Invoice automatically generated
    inv_check = client.get('/api/invoices', headers=auth_headers)
    invoices = inv_check.get_json()
    assert len(invoices) == 1
    assert invoices[0]['order_id'] == order_id
    assert invoices[0]['payment_status'] == 'Pending'
    assert abs(invoices[0]['grand_total'] - 159.3) < 0.01
