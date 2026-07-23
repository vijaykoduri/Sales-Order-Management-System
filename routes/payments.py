from flask import Blueprint, request, jsonify
from models import db
from models.payment import Payment
from models.invoice import Invoice
from models.notification import Notification
from routes.auth import role_required, jwt_required

payments_bp = Blueprint('payments', __name__)

@payments_bp.route('', methods=['GET'])
@jwt_required()
def get_payments():
    query = Payment.query
    
    invoice_id = request.args.get('invoice_id', type=int)
    if invoice_id:
        query = query.filter(Payment.invoice_id == invoice_id)
        
    payments = query.order_by(Payment.payment_date.desc()).all()
    return jsonify([p.to_dict() for p in payments]), 200

@payments_bp.route('', methods=['POST'])
@jwt_required()
def record_payment():
    data = request.get_json() or {}
    invoice_id = data.get('invoice_id')
    amount = float(data.get('amount', 0.0))
    payment_method = data.get('payment_method', '').strip()
    
    if not invoice_id or amount <= 0 or not payment_method:
        return jsonify({'message': 'Invoice ID, payment method, and a positive amount are required'}), 400
        
    invoice = Invoice.query.get(invoice_id)
    if not invoice:
        return jsonify({'message': 'Invoice not found'}), 404
        
    outstanding = float(invoice.outstanding_amount)
    if amount > outstanding:
        return jsonify({'message': f'Payment amount ({amount}) exceeds outstanding amount ({outstanding})'}), 400
        
    # Generate payment number
    count = Payment.query.count()
    pay_num = f"PAY-{count+1:05d}"
    
    payment = Payment(
        invoice_id=invoice_id,
        payment_number=pay_num,
        amount=amount,
        payment_method=payment_method
    )
    db.session.add(payment)
    
    # Update invoice totals
    invoice.paid_amount = float(invoice.paid_amount) + amount
    invoice.outstanding_amount = outstanding - amount
    
    if invoice.outstanding_amount <= 0:
        invoice.payment_status = 'Paid'
    else:
        invoice.payment_status = 'Partial'
        
    try:
        db.session.commit()
        
        # Notify
        msg = f"Payment of ${amount:.2f} received for Invoice {invoice.invoice_number} via {payment_method}. Status: {invoice.payment_status}."
        notif = Notification(
            message=msg,
            type='Payment'
        )
        db.session.add(notif)
        db.session.commit()
        
        return jsonify({'message': 'Payment recorded successfully', 'payment': payment.to_dict(), 'invoice': invoice.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to record payment', 'error': str(e)}), 500
