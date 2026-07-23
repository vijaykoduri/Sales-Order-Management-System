from flask import Blueprint, request, jsonify, send_file
from models import db
from models.order import Quotation, QuotationItem, Order, OrderItem
from models.product import Product
from models.customer import Customer
from models.invoice import Invoice
from models.notification import Notification
from routes.auth import role_required, jwt_required
from services.pdf_service import generate_quotation_pdf, generate_invoice_pdf
from services.stock_service import check_low_stock
from datetime import datetime, timedelta

orders_bp = Blueprint('orders', __name__)

# Helper to generate numbers
def get_next_number(prefix, model, field):
    count = db.session.query(model).count()
    return f"{prefix}-{count+1:05d}"

# ==================================================
# QUOTATIONS ENDPOINTS
# ==================================================

@orders_bp.route('/quotations', methods=['GET'])
@jwt_required()
def get_quotations():
    search = request.args.get('search', '').strip()
    status = request.args.get('status', '').strip()
    
    query = Quotation.query
    if search:
        query = query.join(Customer).filter(
            (Quotation.quotation_number.ilike(f'%{search}%')) |
            (Customer.name.ilike(f'%{search}%')) |
            (Customer.company.ilike(f'%{search}%'))
        )
    if status:
        query = query.filter(Quotation.status == status)
        
    quotations = query.order_by(Quotation.created_at.desc()).all()
    return jsonify([q.to_dict() for q in quotations]), 200

@orders_bp.route('/quotations/<int:id>', methods=['GET'])
@jwt_required()
def get_quotation(id):
    q = Quotation.query.get(id)
    if not q:
        return jsonify({'message': 'Quotation not found'}), 404
    return jsonify(q.to_dict()), 200

@orders_bp.route('/quotations', methods=['POST'])
@jwt_required()
def create_quotation():
    data = request.get_json() or {}
    customer_id = data.get('customer_id')
    items_data = data.get('items', [])
    discount_rate = float(data.get('discount_rate', 0.0))
    gst_rate = float(data.get('gst_rate', 0.0))
    
    if not customer_id or not items_data:
        return jsonify({'message': 'Customer ID and at least one item are required'}), 400
        
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({'message': 'Customer not found'}), 404
        
    q_num = get_next_number("QT", Quotation, "quotation_number")
    
    quotation = Quotation(
        quotation_number=q_num,
        customer_id=customer_id,
        discount_rate=discount_rate,
        gst_rate=gst_rate,
        status='Draft'
    )
    
    subtotal = 0.0
    discount_amount = 0.0
    gst_amount = 0.0
    
    db.session.add(quotation)
    
    # Process items
    for item in items_data:
        product_id = item.get('product_id')
        qty = int(item.get('quantity', 1))
        
        prod = Product.query.get(product_id)
        if not prod:
            db.session.rollback()
            return jsonify({'message': f'Product with ID {product_id} not found'}), 404
            
        price = float(prod.selling_price)
        line_subtotal = qty * price
        
        # Line-level calculation
        line_discount = line_subtotal * (discount_rate / 100.0)
        line_gst = (line_subtotal - line_discount) * (gst_rate / 100.0)
        line_total = line_subtotal - line_discount + line_gst
        
        subtotal += line_subtotal
        discount_amount += line_discount
        gst_amount += line_gst
        
        q_item = QuotationItem(
            quotation=quotation,
            product_id=product_id,
            quantity=qty,
            price=price,
            discount=line_discount,
            gst=line_gst,
            total=line_total
        )
        db.session.add(q_item)
        
    quotation.subtotal = subtotal
    quotation.discount_amount = discount_amount
    quotation.gst_amount = gst_amount
    quotation.grand_total = subtotal - discount_amount + gst_amount
    
    try:
        db.session.commit()
        return jsonify({'message': 'Quotation created successfully', 'quotation': quotation.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to create quotation', 'error': str(e)}), 500

@orders_bp.route('/quotations/<int:id>/approve', methods=['POST'])
@role_required('Admin', 'Sales Manager')
def approve_quotation(id):
    q = Quotation.query.get(id)
    if not q:
        return jsonify({'message': 'Quotation not found'}), 404
    if q.status != 'Draft':
        return jsonify({'message': f'Quotation cannot be approved from status: {q.status}'}), 400
        
    q.status = 'Approved'
    try:
        db.session.commit()
        return jsonify({'message': 'Quotation approved', 'quotation': q.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error approving quotation', 'error': str(e)}), 500

@orders_bp.route('/quotations/<int:id>/reject', methods=['POST'])
@role_required('Admin', 'Sales Manager')
def reject_quotation(id):
    q = Quotation.query.get(id)
    if not q:
        return jsonify({'message': 'Quotation not found'}), 404
    if q.status != 'Draft':
        return jsonify({'message': f'Quotation cannot be rejected from status: {q.status}'}), 400
        
    q.status = 'Rejected'
    try:
        db.session.commit()
        return jsonify({'message': 'Quotation rejected', 'quotation': q.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error rejecting quotation', 'error': str(e)}), 500

@orders_bp.route('/quotations/<int:id>/convert', methods=['POST'])
@jwt_required()
def convert_to_order(id):
    q = Quotation.query.get(id)
    if not q:
        return jsonify({'message': 'Quotation not found'}), 404
    if q.status != 'Approved':
        return jsonify({'message': 'Only Approved quotations can be converted to Sales Orders'}), 400
        
    # Generate Order
    so_num = get_next_number("SO", Order, "order_number")
    order = Order(
        order_number=so_num,
        customer_id=q.customer_id,
        quotation_id=q.id,
        discount_rate=q.discount_rate,
        discount_amount=q.discount_amount,
        gst_rate=q.gst_rate,
        gst_amount=q.gst_amount,
        shipping_charges=0.0,
        subtotal=q.subtotal,
        order_total=q.grand_total,
        status='Pending'
    )
    db.session.add(order)
    
    # Copy items
    for q_item in q.items:
        o_item = OrderItem(
            order=order,
            product_id=q_item.product_id,
            quantity=q_item.quantity,
            price=q_item.price,
            discount=q_item.discount,
            gst=q_item.gst,
            total=q_item.total
        )
        db.session.add(o_item)
        
    q.status = 'Converted'
    
    try:
        db.session.commit()
        # Notify employee
        notif = Notification(
            message=f"Quotation {q.quotation_number} converted to Sales Order {order.order_number}",
            type='Order'
        )
        db.session.add(notif)
        db.session.commit()
        return jsonify({'message': 'Sales Order created from quotation successfully', 'order': order.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to convert quotation', 'error': str(e)}), 500

@orders_bp.route('/quotations/<int:id>/pdf', methods=['GET'])
@jwt_required()
def download_quotation_pdf(id):
    q = Quotation.query.get(id)
    if not q:
        return jsonify({'message': 'Quotation not found'}), 404
        
    pdf_buffer = generate_quotation_pdf(q)
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"Quotation_{q.quotation_number}.pdf",
        mimetype='application/pdf'
    )

# ==================================================
# SALES ORDERS ENDPOINTS
# ==================================================

@orders_bp.route('/orders', methods=['GET'])
@jwt_required()
def get_orders():
    search = request.args.get('search', '').strip()
    status = request.args.get('status', '').strip()
    
    query = Order.query
    if search:
        query = query.join(Customer).filter(
            (Order.order_number.ilike(f'%{search}%')) |
            (Customer.name.ilike(f'%{search}%')) |
            (Customer.company.ilike(f'%{search}%'))
        )
    if status:
        query = query.filter(Order.status == status)
        
    orders = query.order_by(Order.created_at.desc()).all()
    return jsonify([o.to_dict() for o in orders]), 200

@orders_bp.route('/orders/<int:id>', methods=['GET'])
@jwt_required()
def get_order(id):
    o = Order.query.get(id)
    if not o:
        return jsonify({'message': 'Order not found'}), 404
    return jsonify(o.to_dict()), 200

@orders_bp.route('/orders', methods=['POST'])
@jwt_required()
def create_order():
    """Create order directly without quotation"""
    data = request.get_json() or {}
    customer_id = data.get('customer_id')
    items_data = data.get('items', [])
    discount_rate = float(data.get('discount_rate', 0.0))
    gst_rate = float(data.get('gst_rate', 0.0))
    shipping_charges = float(data.get('shipping_charges', 0.0))
    
    if not customer_id or not items_data:
        return jsonify({'message': 'Customer ID and at least one item are required'}), 400
        
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({'message': 'Customer not found'}), 404
        
    so_num = get_next_number("SO", Order, "order_number")
    order = Order(
        order_number=so_num,
        customer_id=customer_id,
        discount_rate=discount_rate,
        gst_rate=gst_rate,
        shipping_charges=shipping_charges,
        status='Pending'
    )
    db.session.add(order)
    
    subtotal = 0.0
    discount_amount = 0.0
    gst_amount = 0.0
    
    for item in items_data:
        product_id = item.get('product_id')
        qty = int(item.get('quantity', 1))
        
        prod = Product.query.get(product_id)
        if not prod:
            db.session.rollback()
            return jsonify({'message': f'Product with ID {product_id} not found'}), 404
            
        price = float(prod.selling_price)
        line_subtotal = qty * price
        line_discount = line_subtotal * (discount_rate / 100.0)
        line_gst = (line_subtotal - line_discount) * (gst_rate / 100.0)
        line_total = line_subtotal - line_discount + line_gst
        
        subtotal += line_subtotal
        discount_amount += line_discount
        gst_amount += line_gst
        
        o_item = OrderItem(
            order=order,
            product_id=product_id,
            quantity=qty,
            price=price,
            discount=line_discount,
            gst=line_gst,
            total=line_total
        )
        db.session.add(o_item)
        
    order.subtotal = subtotal
    order.discount_amount = discount_amount
    order.gst_amount = gst_amount
    order.order_total = subtotal - discount_amount + gst_amount + shipping_charges
    
    try:
        db.session.commit()
        return jsonify({'message': 'Sales Order created successfully', 'order': order.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to create sales order', 'error': str(e)}), 500

@orders_bp.route('/orders/<int:id>/status', methods=['PUT'])
@jwt_required()
def update_order_status(id):
    order = Order.query.get(id)
    if not order:
        return jsonify({'message': 'Order not found'}), 404
        
    data = request.get_json() or {}
    new_status = data.get('status')
    
    valid_statuses = ['Pending', 'Confirmed', 'Packed', 'Shipped', 'Delivered', 'Cancelled']
    if new_status not in valid_statuses:
        return jsonify({'message': f'Invalid status. Must be one of {valid_statuses}'}), 400
        
    old_status = order.status
    if old_status == new_status:
        return jsonify({'message': 'Order is already in this status', 'order': order.to_dict()}), 200
        
    # Transactional logic for Confirming/Cancelling
    if new_status == 'Confirmed':
        # Check stock levels first
        for item in order.items:
            if item.product.stock_quantity < item.quantity:
                return jsonify({
                    'message': f"Insufficient stock for '{item.product.name}'. Required: {item.quantity}, Available: {item.product.stock_quantity}"
                }), 400
                
        # Deduct stock
        for item in order.items:
            item.product.stock_quantity -= item.quantity
            
        # Automatically generate invoice
        inv_num = get_next_number("INV", Invoice, "invoice_number")
        invoice = Invoice(
            invoice_number=inv_num,
            order_id=order.id,
            grand_total=order.order_total,
            paid_amount=0.0,
            outstanding_amount=order.order_total,
            payment_status='Pending'
        )
        db.session.add(invoice)
        
        # Notification trigger
        notif = Notification(
            message=f"New Sales Order Confirmed: {order.order_number}. Invoice {inv_num} generated.",
            type='Order'
        )
        db.session.add(notif)
        
    elif new_status == 'Cancelled' and old_status in ['Confirmed', 'Packed', 'Shipped', 'Delivered']:
        # Restore stock levels
        for item in order.items:
            item.product.stock_quantity += item.quantity
            
        # If invoice exists, cancel or zero it out
        invoice = Invoice.query.filter_by(order_id=order.id).first()
        if invoice:
            invoice.payment_status = 'Pending'
            invoice.outstanding_amount = 0
            invoice.paid_amount = 0
            
    order.status = new_status
    
    try:
        db.session.commit()
        
        # Run stock check alerts for low stock levels
        if new_status == 'Confirmed':
            for item in order.items:
                check_low_stock(item.product_id)
                
        return jsonify({'message': f'Order status updated to {new_status}', 'order': order.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to update order status', 'error': str(e)}), 500

@orders_bp.route('/orders/<int:id>/pdf', methods=['GET'])
@jwt_required()
def download_order_pdf(id):
    order = Order.query.get(id)
    if not order:
        return jsonify({'message': 'Order not found'}), 404
        
    # Standard format reuse: An order confirmation is treated similarly to a confirmed invoice,
    # or quotation. We can render using a slight variant. Let's use the Invoice layout but titled as "Sales Order".
    # For speed and consistency, we generate using a dummy invoice layout.
    class DummyInvoice:
        def __init__(self, order):
            self.invoice_number = f"SO-{order.order_number}"
            self.invoice_date = order.created_at
            self.due_date = order.created_at + timedelta(days=15)
            self.payment_status = order.status
            self.order = order
            self.grand_total = order.order_total
            self.paid_amount = 0
            self.outstanding_amount = order.order_total
            
    dummy_invoice = DummyInvoice(order)
    pdf_buffer = generate_invoice_pdf(dummy_invoice)
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"SalesOrder_{order.order_number}.pdf",
        mimetype='application/pdf'
    )
