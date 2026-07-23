from flask import Blueprint, request, jsonify
from models import db
from models.customer import Customer
from routes.auth import role_required, jwt_required

customers_bp = Blueprint('customers', __name__)

@customers_bp.route('', methods=['GET'])
@jwt_required()
def get_customers():
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    query = Customer.query
    
    if search:
        query = query.filter(
            (Customer.name.ilike(f'%{search}%')) |
            (Customer.company.ilike(f'%{search}%')) |
            (Customer.email.ilike(f'%{search}%')) |
            (Customer.phone.ilike(f'%{search}%')) |
            (Customer.city.ilike(f'%{search}%')) |
            (Customer.state.ilike(f'%{search}%'))
        )
        
    pagination = query.order_by(Customer.name.asc()).paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'customers': [c.to_dict() for c in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
        'per_page': pagination.per_page,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    }), 200

@customers_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_customer(id):
    c = Customer.query.get(id)
    if not c:
        return jsonify({'message': 'Customer not found'}), 404
    return jsonify(c.to_dict()), 200

@customers_bp.route('', methods=['POST'])
@jwt_required()
def create_customer():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    company = data.get('company', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    gst_number = data.get('gst_number', '').strip()
    address = data.get('address', '').strip()
    city = data.get('city', '').strip()
    state = data.get('state', '').strip()
    country = data.get('country', '').strip()
    postal_code = data.get('postal_code', '').strip()
    
    if not name or not email or not phone:
        return jsonify({'message': 'Name, email, and mobile phone number are required'}), 400
        
    # Prevent duplicate email
    if Customer.query.filter_by(email=email).first():
        return jsonify({'message': 'Customer with this email address already exists'}), 400
        
    new_customer = Customer(
        name=name, company=company, email=email, phone=phone,
        gst_number=gst_number, address=address, city=city,
        state=state, country=country, postal_code=postal_code
    )
    
    try:
        db.session.add(new_customer)
        db.session.commit()
        return jsonify({'message': 'Customer created successfully', 'customer': new_customer.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to create customer', 'error': str(e)}), 500

@customers_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_customer(id):
    c = Customer.query.get(id)
    if not c:
        return jsonify({'message': 'Customer not found'}), 404
        
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    
    if email:
        existing = Customer.query.filter_by(email=email).first()
        if existing and existing.id != id:
            return jsonify({'message': 'Customer with this email address already exists'}), 400
        c.email = email
        
    if 'name' in data:
        c.name = data['name'].strip()
    if 'company' in data:
        c.company = data['company'].strip()
    if 'phone' in data:
        c.phone = data['phone'].strip()
    if 'gst_number' in data:
        c.gst_number = data['gst_number'].strip()
    if 'address' in data:
        c.address = data['address'].strip()
    if 'city' in data:
        c.city = data['city'].strip()
    if 'state' in data:
        c.state = data['state'].strip()
    if 'country' in data:
        c.country = data['country'].strip()
    if 'postal_code' in data:
        c.postal_code = data['postal_code'].strip()
        
    try:
        db.session.commit()
        return jsonify({'message': 'Customer updated successfully', 'customer': c.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to update customer', 'error': str(e)}), 500

@customers_bp.route('/<int:id>', methods=['DELETE'])
@role_required('Admin', 'Sales Manager')
def delete_customer(id):
    c = Customer.query.get(id)
    if not c:
        return jsonify({'message': 'Customer not found'}), 404
        
    try:
        db.session.delete(c)
        db.session.commit()
        return jsonify({'message': 'Customer deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to delete customer', 'error': str(e)}), 500
