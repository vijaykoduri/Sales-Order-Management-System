import os
import socket
from urllib.parse import urlparse
from flask import Flask, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from models import db
from config import config_by_name

# Routes imports
from routes.auth import auth_bp
from routes.customers import customers_bp
from routes.products import products_bp
from routes.categories import categories_bp
from routes.suppliers import suppliers_bp
from routes.orders import orders_bp
from routes.invoices import invoices_bp
from routes.payments import payments_bp
from routes.reports import reports_bp
from routes.notifications import notifications_bp
from routes.views import views_bp

def check_db_connection(db_url):
    """Checks if PostgreSQL database socket is reachable"""
    if not db_url or "sqlite" in db_url:
        return True
    try:
        result = urlparse(db_url)
        host = result.hostname or 'localhost'
        port = result.port or 5432
        with socket.create_connection((host, port), timeout=1.5):
            return True
    except Exception:
        return False

def create_app(config_name=None):
    if not config_name:
        config_name = os.getenv('FLASK_ENV', 'development')
        
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])
    
    # Pre-check database availability before binding SQLAlchemy
    db_url = app.config.get('SQLALCHEMY_DATABASE_URI')
    if db_url and db_url.startswith("postgresql") and not check_db_connection(db_url):
        print("WARNING: PostgreSQL database is unreachable. Falling back to local SQLite database...")
        db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'sales_order_system.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
    
    # Enable CORS
    CORS(app)
    
    # Initialize Database
    db.init_app(app)
    
    # Initialize JWT
    jwt = JWTManager(app)
    
    # Token extraction middleware from query parameters
    @app.before_request
    def extract_token_from_query():
        token = request.args.get('token')
        if token and not request.headers.get('Authorization'):
            # Copy token into request headers
            request.environ['HTTP_AUTHORIZATION'] = f"Bearer {token}"
            
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(customers_bp, url_prefix='/api/customers')
    app.register_blueprint(products_bp, url_prefix='/api/products')
    app.register_blueprint(categories_bp, url_prefix='/api/categories')
    app.register_blueprint(suppliers_bp, url_prefix='/api/suppliers')
    app.register_blueprint(orders_bp, url_prefix='/api/orders')
    app.register_blueprint(invoices_bp, url_prefix='/api/invoices')
    app.register_blueprint(payments_bp, url_prefix='/api/payments')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')
    app.register_blueprint(notifications_bp, url_prefix='/api/notifications')
    app.register_blueprint(views_bp, url_prefix='')
    
    # Database table creation & default category seeding
    with app.app_context():
        db.create_all()
        seed_data()
        
    return app

def seed_data():
    """Seed default product categories on startup if empty"""
    from models.category import Category
    if Category.query.count() == 0:
        categories = [
            Category(name="Electronics", description="Mobile phones, computers, monitors, accessories"),
            Category(name="Office Supplies", description="Paper, notebooks, folders, pens, furniture"),
            Category(name="Services", description="Consultancy, installation, configuration fees"),
            Category(name="Raw Materials", description="Metals, wood, plastic parts for assemblies")
        ]
        db.session.bulk_save_objects(categories)
        db.session.commit()

import sys
# Guard module-level initialization when importing inside automated tests
if 'pytest' not in sys.modules and not os.getenv('PYTEST_CURRENT_TEST'):
    app = create_app()
else:
    app = None

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    if not app:
        app = create_app()
        
    flask_env = os.getenv('FLASK_ENV', 'development')
    if flask_env == 'production':
        try:
            from waitress import serve
            print(f"Starting production WSGI server (waitress) on port {port}...")
            serve(app, host='0.0.0.0', port=port)
        except ImportError:
            print("waitress is not installed. Falling back to development server...")
            app.run(host='0.0.0.0', port=port)
    else:
        app.run(host='0.0.0.0', port=port)

