from flask import Blueprint, render_template

views_bp = Blueprint('views', __name__)

@views_bp.route('/')
def login_page():
    return render_template('login.html')

@views_bp.route('/dashboard')
def dashboard_page():
    return render_template('dashboard.html')

@views_bp.route('/customers')
def customers_page():
    return render_template('customers.html')

@views_bp.route('/products')
def products_page():
    return render_template('products.html')

@views_bp.route('/categories')
def categories_page():
    return render_template('categories.html')

@views_bp.route('/suppliers')
def suppliers_page():
    return render_template('suppliers.html')

@views_bp.route('/quotations')
def quotations_page():
    return render_template('quotations.html')

@views_bp.route('/orders')
def orders_page():
    return render_template('orders.html')

@views_bp.route('/invoices')
def invoices_page():
    return render_template('invoices.html')

@views_bp.route('/payments')
def payments_page():
    return render_template('payments.html')

@views_bp.route('/reports')
def reports_page():
    return render_template('reports.html')
