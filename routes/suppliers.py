from flask import Blueprint, request, jsonify
from models import db
from models.supplier import Supplier
from routes.auth import role_required, jwt_required

suppliers_bp = Blueprint('suppliers', __name__)

@suppliers_bp.route('', methods=['GET'])
@jwt_required()
def get_suppliers():
    search = request.args.get('search', '').strip()
    query = Supplier.query
    
    if search:
        query = query.filter(
            (Supplier.name.ilike(f'%{search}%')) |
            (Supplier.email.ilike(f'%{search}%')) |
            (Supplier.phone.ilike(f'%{search}%')) |
            (Supplier.gst_number.ilike(f'%{search}%'))
        )
        
    suppliers = query.order_by(Supplier.name.asc()).all()
    return jsonify([s.to_dict() for s in suppliers]), 200

@suppliers_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_supplier(id):
    s = Supplier.query.get(id)
    if not s:
        return jsonify({'message': 'Supplier not found'}), 404
    return jsonify(s.to_dict()), 200

@suppliers_bp.route('', methods=['POST'])
@role_required('Admin', 'Sales Manager')
def create_supplier():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    address = data.get('address', '').strip()
    gst_number = data.get('gst_number', '').strip()
    
    if not name or not email or not phone:
        return jsonify({'message': 'Name, email, and phone number are required'}), 400
        
    new_supplier = Supplier(
        name=name, email=email, phone=phone,
        address=address, gst_number=gst_number
    )
    
    try:
        db.session.add(new_supplier)
        db.session.commit()
        return jsonify({'message': 'Supplier created successfully', 'supplier': new_supplier.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to create supplier', 'error': str(e)}), 500

@suppliers_bp.route('/<int:id>', methods=['PUT'])
@role_required('Admin', 'Sales Manager')
def update_supplier(id):
    s = Supplier.query.get(id)
    if not s:
        return jsonify({'message': 'Supplier not found'}), 404
        
    data = request.get_json() or {}
    
    if 'name' in data:
        s.name = data['name'].strip()
    if 'email' in data:
        s.email = data['email'].strip()
    if 'phone' in data:
        s.phone = data['phone'].strip()
    if 'address' in data:
        s.address = data['address'].strip()
    if 'gst_number' in data:
        s.gst_number = data['gst_number'].strip()
        
    try:
        db.session.commit()
        return jsonify({'message': 'Supplier updated successfully', 'supplier': s.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to update supplier', 'error': str(e)}), 500

@suppliers_bp.route('/<int:id>', methods=['DELETE'])
@role_required('Admin', 'Sales Manager')
def delete_supplier(id):
    s = Supplier.query.get(id)
    if not s:
        return jsonify({'message': 'Supplier not found'}), 404
        
    try:
        db.session.delete(s)
        db.session.commit()
        return jsonify({'message': 'Supplier deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to delete supplier', 'error': str(e)}), 500
