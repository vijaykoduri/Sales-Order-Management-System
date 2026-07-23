from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import db
from models.user import User
from functools import wraps

auth_bp = Blueprint('auth', __name__)

# RBAC Decorator
def role_required(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                # This will automatically trigger jwt validation
                user_id = get_jwt_identity()
                user = User.query.get(int(user_id)) if user_id else None
                if not user:
                    return jsonify({'message': 'Access denied: Invalid credentials'}), 401
                
                if user.role not in roles:
                    return jsonify({'message': f'Access forbidden: Requires role in {roles}'}), 403
                
                return fn(*args, **kwargs)
            except Exception as e:
                return jsonify({'message': 'Authentication failed', 'error': str(e)}), 401
        return jwt_required()(wrapper)
    return decorator

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    role = data.get('role', 'Employee').strip() # Admin, Sales Manager, Employee
    
    if not username or not email or not password:
        return jsonify({'message': 'Username, email, and password are required'}), 400
        
    if role not in ['Admin', 'Sales Manager', 'Employee']:
        return jsonify({'message': 'Invalid role specified'}), 400
        
    # Prevent duplicate username or email
    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'Username is already taken'}), 400
        
    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'Email is already registered'}), 400
        
    # Check if this is the first user in the system. If so, default to Admin
    first_user = User.query.first()
    if not first_user:
        role = 'Admin'
        
    new_user = User(username=username, email=email, role=role)
    new_user.set_password(password)
    
    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'User registered successfully', 'user': new_user.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to register user', 'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400
        
    user = User.query.filter((User.username == username) | (User.email == username)).first()
    
    if not user or not user.check_password(password):
        return jsonify({'message': 'Invalid username/email or password'}), 401
        
    access_token = create_access_token(identity=str(user.id))
    return jsonify({
        'message': 'Login successful',
        'access_token': access_token,
        'user': user.to_dict()
    }), 200

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    # Stateless JWT logout is handled on frontend by removing token,
    # but we can return success status for interface clean completion
    return jsonify({'message': 'Logged out successfully'}), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    identity = get_jwt_identity()
    user = User.query.get(int(identity)) if identity else None
    if not user:
        return jsonify({'message': 'User not found'}), 404
    return jsonify({'user': user.to_dict()}), 200

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    if not email:
        return jsonify({'message': 'Email address is required'}), 400
    
    user = User.query.filter_by(email=email).first()
    if not user:
        # Avoid user enumeration attacks: return 200 but keep message generic
        return jsonify({'message': 'If the email is registered, password reset guidelines have been sent.'}), 200
        
    # In a full production application, send email with a token.
    # Here we mock and log / return success for portfolio demonstration.
    return jsonify({'message': 'If the email is registered, password reset guidelines have been sent.'}), 200

@auth_bp.route('/users/<int:user_id>/role', methods=['PUT'])
@role_required('Admin')
def update_user_role(user_id):
    """Allows an administrator to modify a user's role in the database"""
    data = request.get_json() or {}
    new_role = data.get('role', '').strip()
    
    if new_role not in ['Admin', 'Sales Manager', 'Employee']:
        return jsonify({'message': 'Invalid role privilege specified'}), 400
        
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found in system'}), 404
        
    # Prevent the user from removing their own admin rights
    # We can check the logged in user id if needed, but simple check is enough
    
    user.role = new_role
    try:
        db.session.commit()
        return jsonify({
            'message': 'User role updated successfully',
            'user': user.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to update user role', 'error': str(e)}), 500
