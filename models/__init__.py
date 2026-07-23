from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import models to register them with the metadata
from models.user import User
from models.category import Category
from models.product import Product
from models.customer import Customer
from models.supplier import Supplier
from models.order import Quotation, QuotationItem, Order, OrderItem
from models.invoice import Invoice
from models.payment import Payment
from models.notification import Notification
