from models import db
from models.product import Product
from models.notification import Notification

def check_low_stock(product_id=None, threshold=10):
    """
    Checks stock levels and creates system notifications for low stock.
    If product_id is provided, checks only that product. Otherwise checks all.
    """
    if product_id:
        products = Product.query.filter_by(id=product_id).all()
    else:
        products = Product.query.all()
        
    alerts_created = []
    for product in products:
        if product.stock_quantity <= threshold:
            # Check if an unread notification already exists for this product warning
            msg = f"Low Stock: '{product.name}' (SKU: {product.sku}) is running low ({product.stock_quantity} {product.unit} left)."
            existing = Notification.query.filter_by(
                type='Stock',
                message=msg,
                is_read=False
            ).first()
            
            if not existing:
                notif = Notification(
                    message=msg,
                    type='Stock'
                )
                db.session.add(notif)
                alerts_created.append(product.name)
                
    if alerts_created:
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            
    return alerts_created
