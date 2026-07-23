from datetime import datetime
from models import db

class Quotation(db.Model):
    __tablename__ = 'quotations'
    
    id = db.Column(db.Integer, primary_key=True)
    quotation_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    
    discount_rate = db.Column(db.Numeric(5, 2), default=0.0) # discount percentage
    discount_amount = db.Column(db.Numeric(10, 2), default=0.0)
    gst_rate = db.Column(db.Numeric(5, 2), default=0.0)      # tax percentage (e.g. 18.00)
    gst_amount = db.Column(db.Numeric(10, 2), default=0.0)
    
    subtotal = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    grand_total = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    
    status = db.Column(db.String(20), default='Draft', nullable=False) # 'Draft', 'Approved', 'Rejected', 'Converted'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = db.relationship('QuotationItem', backref='quotation', cascade='all, delete-orphan', lazy=True)
    orders = db.relationship('Order', backref='quotation', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'quotation_number': self.quotation_number,
            'customer_id': self.customer_id,
            'customer_name': self.customer.name if self.customer else None,
            'customer_company': self.customer.company if self.customer else None,
            'discount_rate': float(self.discount_rate),
            'discount_amount': float(self.discount_amount),
            'gst_rate': float(self.gst_rate),
            'gst_amount': float(self.gst_amount),
            'subtotal': float(self.subtotal),
            'grand_total': float(self.grand_total),
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'items': [item.to_dict() for item in self.items] if self.items else []
        }

class QuotationItem(db.Model):
    __tablename__ = 'quotation_items'
    
    id = db.Column(db.Integer, primary_key=True)
    quotation_id = db.Column(db.Integer, db.ForeignKey('quotations.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price = db.Column(db.Numeric(10, 2), nullable=False) # Unit price
    discount = db.Column(db.Numeric(10, 2), default=0.0) # Line discount amount
    gst = db.Column(db.Numeric(10, 2), default=0.0)      # Line GST amount
    total = db.Column(db.Numeric(10, 2), nullable=False) # (price * qty) - discount + gst
    
    product = db.relationship('Product', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'quotation_id': self.quotation_id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'product_code': self.product.code if self.product else None,
            'quantity': self.quantity,
            'price': float(self.price),
            'discount': float(self.discount),
            'gst': float(self.gst),
            'total': float(self.total)
        }

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    quotation_id = db.Column(db.Integer, db.ForeignKey('quotations.id'), nullable=True)
    
    discount_rate = db.Column(db.Numeric(5, 2), default=0.0)
    discount_amount = db.Column(db.Numeric(10, 2), default=0.0)
    gst_rate = db.Column(db.Numeric(5, 2), default=0.0)
    gst_amount = db.Column(db.Numeric(10, 2), default=0.0)
    shipping_charges = db.Column(db.Numeric(10, 2), default=0.0)
    
    subtotal = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    order_total = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    
    status = db.Column(db.String(20), default='Pending', nullable=False) # 'Pending', 'Confirmed', 'Packed', 'Shipped', 'Delivered', 'Cancelled'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = db.relationship('OrderItem', backref='order', cascade='all, delete-orphan', lazy=True)
    invoices = db.relationship('Invoice', backref='order', cascade='all, delete-orphan', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_number': self.order_number,
            'customer_id': self.customer_id,
            'customer_name': self.customer.name if self.customer else None,
            'customer_company': self.customer.company if self.customer else None,
            'quotation_id': self.quotation_id,
            'quotation_number': self.quotation.quotation_number if self.quotation else None,
            'discount_rate': float(self.discount_rate),
            'discount_amount': float(self.discount_amount),
            'gst_rate': float(self.gst_rate),
            'gst_amount': float(self.gst_amount),
            'shipping_charges': float(self.shipping_charges),
            'subtotal': float(self.subtotal),
            'order_total': float(self.order_total),
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'items': [item.to_dict() for item in self.items] if self.items else []
        }

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    discount = db.Column(db.Numeric(10, 2), default=0.0)
    gst = db.Column(db.Numeric(10, 2), default=0.0)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    
    product = db.relationship('Product', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'product_code': self.product.code if self.product else None,
            'quantity': self.quantity,
            'price': float(self.price),
            'discount': float(self.discount),
            'gst': float(self.gst),
            'total': float(self.total)
        }
