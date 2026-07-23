from flask import Blueprint, request, jsonify, send_file
from models import db
from models.invoice import Invoice
from routes.auth import role_required, jwt_required
from services.pdf_service import generate_invoice_pdf
from datetime import datetime

invoices_bp = Blueprint('invoices', __name__)

@invoices_bp.route('', methods=['GET'])
@jwt_required()
def get_invoices():
    search = request.args.get('search', '').strip()
    status = request.args.get('status', '').strip()
    
    query = Invoice.query
    
    if search:
        # Join order and customer to search on fields
        from models.order import Order
        from models.customer import Customer
        query = query.join(Order).join(Customer).filter(
            (Invoice.invoice_number.ilike(f'%{search}%')) |
            (Order.order_number.ilike(f'%{search}%')) |
            (Customer.name.ilike(f'%{search}%')) |
            (Customer.company.ilike(f'%{search}%'))
        )
        
    if status:
        query = query.filter(Invoice.payment_status == status)
        
    invoices = query.order_by(Invoice.created_at.desc()).all()
    return jsonify([inv.to_dict() for inv in invoices]), 200

@invoices_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_invoice(id):
    inv = Invoice.query.get(id)
    if not inv:
        return jsonify({'message': 'Invoice not found'}), 404
    return jsonify(inv.to_dict()), 200

@invoices_bp.route('/<int:id>/pdf', methods=['GET'])
@jwt_required()
def download_invoice_pdf(id):
    inv = Invoice.query.get(id)
    if not inv:
        return jsonify({'message': 'Invoice not found'}), 404
        
    pdf_buffer = generate_invoice_pdf(inv)
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"Invoice_{inv.invoice_number}.pdf",
        mimetype='application/pdf'
    )

@invoices_bp.route('/<int:id>', methods=['PUT'])
@role_required('Admin', 'Sales Manager')
def update_invoice(id):
    inv = Invoice.query.get(id)
    if not inv:
        return jsonify({'message': 'Invoice not found'}), 404
        
    data = request.get_json() or {}
    
    # Allow updating due date or metadata
    due_date_str = data.get('due_date')
    if due_date_str:
        try:
            inv.due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
        except ValueError:
            return jsonify({'message': 'Invalid date format. Use ISO format (YYYY-MM-DD)'}), 400
            
    try:
        db.session.commit()
        return jsonify({'message': 'Invoice updated successfully', 'invoice': inv.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to update invoice', 'error': str(e)}), 500
