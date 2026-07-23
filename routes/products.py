from flask import Blueprint, request, jsonify
from models import db
from models.product import Product
from models.category import Category
from routes.auth import role_required, jwt_required
from services.stock_service import check_low_stock

products_bp = Blueprint('products', __name__)

@products_bp.route('', methods=['GET'])
def get_products():
    search = request.args.get('search', '').strip()
    category_id = request.args.get('category_id', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    query = Product.query
    
    if search:
        query = query.filter(
            (Product.name.ilike(f'%{search}%')) |
            (Product.code.ilike(f'%{search}%')) |
            (Product.sku.ilike(f'%{search}%'))
        )
        
    if category_id:
        query = query.filter(Product.category_id == category_id)
        
    pagination = query.order_by(Product.name.asc()).paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'products': [p.to_dict() for p in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
        'per_page': pagination.per_page,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    }), 200

@products_bp.route('/<int:id>', methods=['GET'])
def get_product(id):
    p = Product.query.get(id)
    if not p:
        return jsonify({'message': 'Product not found'}), 404
    return jsonify(p.to_dict()), 200

@products_bp.route('', methods=['POST'])
@role_required('Admin', 'Sales Manager')
def create_product():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    code = data.get('code', '').strip()
    sku = data.get('sku', '').strip()
    category_id = data.get('category_id')
    description = data.get('description', '').strip()
    cost_price = data.get('cost_price')
    selling_price = data.get('selling_price')
    stock_quantity = data.get('stock_quantity', 0)
    unit = data.get('unit', 'Units').strip()
    image_url = data.get('image_url', '').strip()
    
    if not name or not code or not sku or not category_id or cost_price is None or selling_price is None:
        return jsonify({'message': 'Missing required fields: name, code, sku, category_id, cost_price, selling_price'}), 400
        
    # Check category exists
    if not Category.query.get(category_id):
        return jsonify({'message': 'Invalid category ID specified'}), 400
        
    # Check duplicates
    if Product.query.filter_by(code=code).first():
        return jsonify({'message': 'Product code already exists'}), 400
        
    if Product.query.filter_by(sku=sku).first():
        return jsonify({'message': 'Product SKU already exists'}), 400
        
    new_product = Product(
        name=name, code=code, sku=sku, category_id=category_id,
        description=description, cost_price=cost_price,
        selling_price=selling_price, stock_quantity=stock_quantity,
        unit=unit, image_url=image_url
    )
    
    try:
        db.session.add(new_product)
        db.session.commit()
        
        # Check if the product has low stock and trigger notification
        check_low_stock(new_product.id)
        
        return jsonify({'message': 'Product created successfully', 'product': new_product.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to create product', 'error': str(e)}), 500

@products_bp.route('/<int:id>', methods=['PUT'])
@role_required('Admin', 'Sales Manager')
def update_product(id):
    p = Product.query.get(id)
    if not p:
        return jsonify({'message': 'Product not found'}), 404
        
    data = request.get_json() or {}
    
    # Validation helpers
    code = data.get('code', '').strip()
    sku = data.get('sku', '').strip()
    category_id = data.get('category_id')
    
    if code:
        existing = Product.query.filter_by(code=code).first()
        if existing and existing.id != id:
            return jsonify({'message': 'Product code already exists'}), 400
        p.code = code
        
    if sku:
        existing = Product.query.filter_by(sku=sku).first()
        if existing and existing.id != id:
            return jsonify({'message': 'Product SKU already exists'}), 400
        p.sku = sku
        
    if category_id:
        if not Category.query.get(category_id):
            return jsonify({'message': 'Invalid category ID specified'}), 400
        p.category_id = category_id
        
    if 'name' in data:
        p.name = data['name'].strip()
    if 'description' in data:
        p.description = data['description'].strip()
    if 'cost_price' in data:
        p.cost_price = data['cost_price']
    if 'selling_price' in data:
        p.selling_price = data['selling_price']
    if 'stock_quantity' in data:
        p.stock_quantity = data['stock_quantity']
    if 'unit' in data:
        p.unit = data['unit'].strip()
    if 'image_url' in data:
        p.image_url = data['image_url'].strip()
        
    try:
        db.session.commit()
        
        # Check low stock warnings
        check_low_stock(p.id)
        
        return jsonify({'message': 'Product updated successfully', 'product': p.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to update product', 'error': str(e)}), 500

@products_bp.route('/<int:id>', methods=['DELETE'])
@role_required('Admin', 'Sales Manager')
def delete_product(id):
    p = Product.query.get(id)
    if not p:
        return jsonify({'message': 'Product not found'}), 404
        
    try:
        db.session.delete(p)
        db.session.commit()
        return jsonify({'message': 'Product deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to delete product', 'error': str(e)}), 500
