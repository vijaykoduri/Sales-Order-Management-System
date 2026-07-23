from flask import Blueprint, request, jsonify
from models import db
from models.category import Category
from routes.auth import role_required

categories_bp = Blueprint('categories', __name__)

@categories_bp.route('', methods=['GET'])
def get_categories():
    search = request.args.get('search', '').strip()
    query = Category.query
    
    if search:
        query = query.filter(Category.name.ilike(f'%{search}%'))
        
    categories = query.order_by(Category.name.asc()).all()
    return jsonify([c.to_dict() for c in categories]), 200

@categories_bp.route('', methods=['POST'])
@role_required('Admin', 'Sales Manager')
def create_category():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    
    if not name:
        return jsonify({'message': 'Category name is required'}), 400
        
    # Prevent duplicates
    if Category.query.filter_by(name=name).first():
        return jsonify({'message': 'Category with this name already exists'}), 400
        
    new_cat = Category(name=name, description=description)
    try:
        db.session.add(new_cat)
        db.session.commit()
        return jsonify({'message': 'Category created successfully', 'category': new_cat.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to create category', 'error': str(e)}), 500

@categories_bp.route('/<int:id>', methods=['PUT'])
@role_required('Admin', 'Sales Manager')
def update_category(id):
    cat = Category.query.get_or_456 = Category.query.get(id)
    if not cat:
        return jsonify({'message': 'Category not found'}), 404
        
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    
    if name:
        # Verify another category doesn't have the same name
        existing = Category.query.filter_by(name=name).first()
        if existing and existing.id != id:
            return jsonify({'message': 'Category with this name already exists'}), 400
        cat.name = name
        
    if 'description' in data:
        cat.description = description
        
    try:
        db.session.commit()
        return jsonify({'message': 'Category updated successfully', 'category': cat.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to update category', 'error': str(e)}), 500

@categories_bp.route('/<int:id>', methods=['DELETE'])
@role_required('Admin', 'Sales Manager')
def delete_category(id):
    cat = Category.query.get(id)
    if not cat:
        return jsonify({'message': 'Category not found'}), 404
        
    try:
        db.session.delete(cat)
        db.session.commit()
        return jsonify({'message': 'Category deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to delete category', 'error': str(e)}), 500
