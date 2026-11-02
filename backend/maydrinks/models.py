"""Relational entities mapped to the supplied ERD; historical data is immutable."""
from datetime import datetime, timezone
from uuid import uuid4
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, Index

db = SQLAlchemy()
def uid(): return str(uuid4())
def utcnow(): return datetime.now(timezone.utc).replace(tzinfo=None)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String(36), primary_key=True, default=uid)
    username = db.Column(db.Unicode(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)
    role = db.Column(db.String(16), nullable=False, default='customer')
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    __table_args__ = (CheckConstraint("role IN ('customer','staff','admin')", name='ck_user_role'),)

class Profile(db.Model):
    __tablename__ = 'customer_profiles'
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), primary_key=True)
    name = db.Column(db.Unicode(120), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.Unicode(254))
    address = db.Column(db.Unicode(500), nullable=False, default='')
    __table_args__ = (Index('uq_profile_email', 'email', unique=True, mssql_where=db.text('email IS NOT NULL')),)

class AuthSession(db.Model):
    __tablename__ = 'auth_sessions'
    token_hash = db.Column(db.String(64), primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)

class PasswordReset(db.Model):
    __tablename__ = 'password_resets'
    token_hash = db.Column(db.String(64), primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, nullable=False, default=False)

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.String(36), primary_key=True, default=uid)
    name = db.Column(db.Unicode(120), unique=True, nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)

class Drink(db.Model):
    __tablename__ = 'drinks'
    id = db.Column(db.String(36), primary_key=True, default=uid)
    category_id = db.Column(db.String(36), db.ForeignKey('categories.id'), nullable=False)
    name = db.Column(db.Unicode(120), nullable=False)
    description = db.Column(db.UnicodeText, nullable=False, default='')
    price = db.Column(db.Integer, nullable=False)
    image = db.Column(db.Unicode(1000), nullable=False, default='/assets/product-0.jpg')
    active = db.Column(db.Boolean, nullable=False, default=True)
    available = db.Column(db.Boolean, nullable=False, default=True)
    __table_args__ = (CheckConstraint('price >= 0', name='ck_drink_price'),)

class Option(db.Model):
    __tablename__ = 'options'
    id = db.Column(db.String(36), primary_key=True, default=uid)
    kind = db.Column(db.String(16), nullable=False)
    name = db.Column(db.Unicode(80), nullable=False)
    surcharge = db.Column(db.Integer, nullable=False, default=0)
    factor = db.Column(db.Numeric(10, 4), nullable=False, default=1)
    active = db.Column(db.Boolean, nullable=False, default=True)
    __table_args__ = (CheckConstraint("kind IN ('size','topping','sugar','ice')", name='ck_option_kind'), CheckConstraint('surcharge >= 0 AND factor >= 0', name='ck_option_values'))

class DrinkOption(db.Model):
    __tablename__ = 'drink_options'
    drink_id = db.Column(db.String(36), db.ForeignKey('drinks.id'), primary_key=True)
    option_id = db.Column(db.String(36), db.ForeignKey('options.id'), primary_key=True)

class Ingredient(db.Model):
    __tablename__ = 'ingredients'
    id = db.Column(db.String(36), primary_key=True, default=uid)
    name = db.Column(db.Unicode(120), unique=True, nullable=False)
    unit = db.Column(db.String(12), nullable=False)
    quantity = db.Column(db.Numeric(18, 4), nullable=False, default=0)
    minimum = db.Column(db.Numeric(18, 4), nullable=False, default=0)
    last_price = db.Column(db.Numeric(18, 4), nullable=False, default=0)
    active = db.Column(db.Boolean, nullable=False, default=True)
    __table_args__ = (CheckConstraint('quantity >= 0 AND minimum >= 0 AND last_price >= 0', name='ck_ingredient_nonnegative'), CheckConstraint("unit IN ('g','kg','ml','l','unit')", name='ck_ingredient_unit'))

class Recipe(db.Model):
    __tablename__ = 'recipes'
    id = db.Column(db.String(36), primary_key=True, default=uid)
    drink_id = db.Column(db.String(36), db.ForeignKey('drinks.id'), nullable=False)
    size_id = db.Column(db.String(36), db.ForeignKey('options.id'), nullable=False)
    name = db.Column(db.Unicode(160), nullable=False)
    instructions = db.Column(db.UnicodeText, nullable=False, default='')
    active = db.Column(db.Boolean, nullable=False, default=True)
    __table_args__ = (db.UniqueConstraint('drink_id', 'size_id', name='uq_recipe_variant'),)

class RecipeLine(db.Model):
    __tablename__ = 'recipe_lines'
    id = db.Column(db.String(36), primary_key=True, default=uid)
    recipe_id = db.Column(db.String(36), db.ForeignKey('recipes.id'), nullable=False, index=True)
    ingredient_id = db.Column(db.String(36), db.ForeignKey('ingredients.id'), nullable=False)
    quantity = db.Column(db.Numeric(18, 4), nullable=False)
    unit = db.Column(db.String(12), nullable=False)
    scales_with = db.Column(db.String(12), nullable=False, default='none')
    __table_args__ = (CheckConstraint('quantity > 0', name='ck_recipe_qty'), CheckConstraint("scales_with IN ('none','sugar','ice')", name='ck_recipe_scale'))

class ToppingLine(db.Model):
    __tablename__ = 'topping_recipe_lines'
    option_id = db.Column(db.String(36), db.ForeignKey('options.id'), primary_key=True)
    ingredient_id = db.Column(db.String(36), db.ForeignKey('ingredients.id'), primary_key=True)
    quantity = db.Column(db.Numeric(18, 4), nullable=False)
    unit = db.Column(db.String(12), nullable=False)
    __table_args__ = (CheckConstraint('quantity > 0', name='ck_topping_qty'),)

class Cart(db.Model):
    __tablename__ = 'carts'
    id = db.Column(db.String(36), primary_key=True, default=uid)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), unique=True, nullable=False)

class CartItem(db.Model):
    __tablename__ = 'cart_items'
    id = db.Column(db.String(36), primary_key=True, default=uid)
    cart_id = db.Column(db.String(36), db.ForeignKey('carts.id'), nullable=False, index=True)
    drink_id = db.Column(db.String(36), db.ForeignKey('drinks.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    choices = db.Column(db.UnicodeText, nullable=False)
    __table_args__ = (CheckConstraint('quantity BETWEEN 1 AND 99', name='ck_cart_quantity'),)

class Coupon(db.Model):
    __tablename__ = 'coupons'
    code = db.Column(db.String(40), primary_key=True)
    percent = db.Column(db.Integer, nullable=False)
    minimum = db.Column(db.Integer, nullable=False, default=0)
    expires_at = db.Column(db.DateTime, nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)
    __table_args__ = (CheckConstraint('[percent] BETWEEN 1 AND 50 AND minimum >= 0', name='ck_coupon'),)

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.String(36), primary_key=True, default=uid)
    code = db.Column(db.String(24), unique=True, nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    recipient = db.Column(db.Unicode(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Unicode(500), nullable=False)
    note = db.Column(db.Unicode(1000), nullable=False, default='')
    status = db.Column(db.String(20), nullable=False, default='pending')
    subtotal = db.Column(db.Integer, nullable=False)
    discount = db.Column(db.Integer, nullable=False, default=0)
    total = db.Column(db.Integer, nullable=False)
    coupon_code = db.Column(db.String(40))
    stock_deducted = db.Column(db.Boolean, nullable=False, default=False)
    request_key = db.Column(db.String(80), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)
    completed_at = db.Column(db.DateTime)
    __table_args__ = (db.UniqueConstraint('user_id','request_key',name='uq_order_idempotency'), CheckConstraint("status IN ('pending','preparing','ready','delivering','completed','cancelled')",name='ck_order_status'), CheckConstraint('subtotal >= 0 AND discount >= 0 AND total = subtotal - discount AND total >= 0',name='ck_order_totals'))

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.String(36), primary_key=True, default=uid)
    order_id = db.Column(db.String(36), db.ForeignKey('orders.id'), nullable=False, index=True)
    drink_id = db.Column(db.String(36), db.ForeignKey('drinks.id'), nullable=False)
    name = db.Column(db.Unicode(120), nullable=False)
    image = db.Column(db.Unicode(1000), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    base_price = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Integer, nullable=False)
    choices = db.Column(db.UnicodeText, nullable=False)
    requirements = db.Column(db.UnicodeText, nullable=False)
    __table_args__ = (CheckConstraint('quantity BETWEEN 1 AND 99 AND unit_price >= 0',name='ck_order_item'),)

class StatusHistory(db.Model):
    __tablename__ = 'order_status_history'
    id = db.Column(db.String(36), primary_key=True, default=uid)
    order_id = db.Column(db.String(36), db.ForeignKey('orders.id'), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False)
    actor_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    note = db.Column(db.Unicode(1000), nullable=False, default='')
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.String(36), primary_key=True, default=uid)
    order_id = db.Column(db.String(36), db.ForeignKey('orders.id'), unique=True, nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    method = db.Column(db.String(16), nullable=False, default='COD')
    status = db.Column(db.String(16), nullable=False, default='unpaid')
    actor_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    paid_at = db.Column(db.DateTime)
    __table_args__ = (CheckConstraint('amount >= 0',name='ck_payment_amount'), CheckConstraint("status IN ('unpaid','paid')",name='ck_payment_status'))

class Receipt(db.Model):
    __tablename__ = 'inventory_receipts'
    id = db.Column(db.String(36), primary_key=True, default=uid)
    code = db.Column(db.String(24), unique=True, nullable=False)
    supplier = db.Column(db.Unicode(160), nullable=False)
    received_date = db.Column(db.Date, nullable=False)
    note = db.Column(db.Unicode(1000), nullable=False, default='')
    status = db.Column(db.String(16), nullable=False, default='draft')
    actor_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    confirmed_by = db.Column(db.String(36), db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    confirmed_at = db.Column(db.DateTime)

class ReceiptLine(db.Model):
    __tablename__ = 'inventory_receipt_lines'
    id = db.Column(db.String(36), primary_key=True, default=uid)
    receipt_id = db.Column(db.String(36), db.ForeignKey('inventory_receipts.id'), nullable=False, index=True)
    ingredient_id = db.Column(db.String(36), db.ForeignKey('ingredients.id'), nullable=False)
    quantity = db.Column(db.Numeric(18, 4), nullable=False)
    price = db.Column(db.Numeric(18, 4), nullable=False)
    __table_args__ = (CheckConstraint('quantity > 0 AND price >= 0',name='ck_receipt_values'),)

class InventoryTransaction(db.Model):
    __tablename__ = 'inventory_transactions'
    id = db.Column(db.String(36), primary_key=True, default=uid)
    ingredient_id = db.Column(db.String(36), db.ForeignKey('ingredients.id'), nullable=False, index=True)
    kind = db.Column(db.String(16), nullable=False)
    delta = db.Column(db.Numeric(18, 4), nullable=False)
    balance = db.Column(db.Numeric(18, 4), nullable=False)
    unit_cost = db.Column(db.Numeric(18, 4), nullable=False, default=0)
    order_id = db.Column(db.String(36), db.ForeignKey('orders.id'))
    receipt_id = db.Column(db.String(36), db.ForeignKey('inventory_receipts.id'))
    actor_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    reason = db.Column(db.Unicode(1000), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)
    __table_args__ = (CheckConstraint('balance >= 0',name='ck_inventory_balance'),)

class Audit(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.String(36), primary_key=True, default=uid)
    actor_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    action = db.Column(db.String(80), nullable=False)
    entity_id = db.Column(db.String(80), nullable=False)
    detail = db.Column(db.UnicodeText, nullable=False, default='')
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)
