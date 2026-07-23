from datetime import datetime, timedelta
from models import db

class Invoice(db.Model):
    __tablename__ = 'invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    
    invoice_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    due_date = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(days=15), nullable=False)
    
    grand_total = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    paid_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    outstanding_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    
    payment_status = db.Column(db.String(20), default='Pending', nullable=False) # 'Paid', 'Pending', 'Partial'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    payments = db.relationship('Payment', backref='invoice', cascade='all, delete-orphan', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'order_id': self.order_id,
            'order_number': self.order.order_number if self.order else None,
            'customer_name': self.order.customer.name if self.order and self.order.customer else None,
            'invoice_date': self.invoice_date.isoformat() if self.invoice_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'grand_total': float(self.grand_total),
            'paid_amount': float(self.paid_amount),
            'outstanding_amount': float(self.outstanding_amount),
            'payment_status': self.payment_status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
