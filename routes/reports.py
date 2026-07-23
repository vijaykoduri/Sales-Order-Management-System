from flask import Blueprint, jsonify, send_file, request
from models import db
from models.customer import Customer
from models.product import Product
from models.order import Order, OrderItem, Quotation
from models.invoice import Invoice
from routes.auth import role_required, jwt_required
from services.excel_service import generate_sales_excel, generate_inventory_excel
from sqlalchemy import func
from datetime import datetime, timedelta

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """
    Compiles complete statistics for the ERP dashboard.
    """
    now = datetime.utcnow()
    first_day_of_month = datetime(now.year, now.month, 1)
    
    # Simple aggregates
    customer_count = Customer.query.count()
    product_count = Product.query.count()
    order_count = Order.query.count()
    quotation_count = Quotation.query.count()
    
    pending_orders = Order.query.filter_by(status='Pending').count()
    completed_orders = Order.query.filter_by(status='Delivered').count()
    
    # Low stock quantity alerts count
    low_stock_count = Product.query.filter(Product.stock_quantity <= 10).count()
    
    # Monthly Revenue (Current Month)
    monthly_rev = db.session.query(func.sum(Order.order_total)).filter(
        Order.created_at >= first_day_of_month,
        Order.status != 'Cancelled'
    ).scalar() or 0.0
    
    # Recent Orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    
    # Low stock items list
    low_stock_products = Product.query.filter(Product.stock_quantity <= 10).limit(5).all()
    
    # Top Selling Products (By volume sold)
    top_products_query = db.session.query(
        Product.name,
        func.sum(OrderItem.quantity).label('total_qty')
    ).join(OrderItem).group_by(Product.id, Product.name).order_by(func.sum(OrderItem.quantity).desc()).limit(5).all()
    
    top_products = [{'name': name, 'qty': int(qty)} for name, qty in top_products_query]
    
    # Admin metrics
    from models.user import User
    user_count = User.query.count()
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    # Manager & Employee metrics
    total_receivables = db.session.query(func.sum(Invoice.outstanding_amount)).scalar() or 0.0
    converted_quotes_count = Quotation.query.filter_by(status='Converted').count()
    draft_quotations_count = Quotation.query.filter_by(status='Draft').count()
    
    # 6-Month Monthly Revenue Chart data
    chart_labels = []
    chart_data = []
    
    for i in range(5, -1, -1):
        # Calculate target month date bounds
        year = now.year
        month = now.month - i
        if month <= 0:
            month += 12
            year -= 1
            
        start_date = datetime(year, month, 1)
        # End date calculation: next month day 1
        next_month = month + 1
        next_year = year
        if next_month > 12:
            next_month = 1
            next_year += 1
        end_date = datetime(next_year, next_month, 1)
        
        month_label = start_date.strftime('%B %Y')
        month_rev = db.session.query(func.sum(Order.order_total)).filter(
            Order.created_at >= start_date,
            Order.created_at < end_date,
            Order.status != 'Cancelled'
        ).scalar() or 0.0
        
        chart_labels.append(month_label)
        chart_data.append(float(month_rev))
        
    return jsonify({
        'customer_count': customer_count,
        'product_count': product_count,
        'order_count': order_count,
        'quotation_count': quotation_count,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
        'low_stock_count': low_stock_count,
        'monthly_revenue': float(monthly_rev),
        'recent_orders': [o.to_dict() for o in recent_orders],
        'low_stock_products': [p.to_dict() for p in low_stock_products],
        'top_products': top_products,
        'user_count': user_count,
        'recent_users': [u.to_dict() for u in recent_users],
        'total_receivables': float(total_receivables),
        'converted_quotes_count': converted_quotes_count,
        'draft_quotations_count': draft_quotations_count,
        'revenue_chart': {
            'labels': chart_labels,
            'data': chart_data
        }
    }), 200

@reports_bp.route('/sales', methods=['GET'])
@jwt_required()
def get_sales_analytics():
    """
    Returns granular sales summaries grouped by customer and product.
    """
    # Total revenue
    total_sales = db.session.query(func.sum(Order.order_total)).filter(Order.status != 'Cancelled').scalar() or 0.0
    
    # Total outstanding bills
    total_outstanding = db.session.query(func.sum(Invoice.outstanding_amount)).scalar() or 0.0
    
    # Top customer sales volume
    customer_sales_query = db.session.query(
        Customer.name,
        func.sum(Order.order_total).label('sales_volume')
    ).join(Order).filter(Order.status != 'Cancelled').group_by(Customer.id, Customer.name).order_by(func.sum(Order.order_total).desc()).limit(5).all()
    
    top_customers = [{'name': name, 'sales': float(sales)} for name, sales in customer_sales_query]
    
    return jsonify({
        'total_sales': float(total_sales),
        'total_outstanding': float(total_outstanding),
        'top_customers': top_customers
    }), 200

@reports_bp.route('/export/sales', methods=['GET'])
@role_required('Admin', 'Sales Manager')
def export_sales_excel():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    buffer = generate_sales_excel(orders)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"Sales_Orders_Report_{datetime.utcnow().strftime('%Y%m%d')}.xlsx",
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@reports_bp.route('/export/inventory', methods=['GET'])
@role_required('Admin', 'Sales Manager')
def export_inventory_excel():
    products = Product.query.order_by(Product.name.asc()).all()
    buffer = generate_inventory_excel(products)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"Inventory_Status_{datetime.utcnow().strftime('%Y%m%d')}.xlsx",
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
