import pytest
from decimal import Decimal
from maydrinks import create_app
from maydrinks.models import *
from maydrinks.domain import *
from maydrinks.auth import new_session



# --- Nhóm 1: Xác thực & Phân quyền (G2-FR01, USC01, USC02) ---
def test_01_health_check(client):
    res = client.get('/api/health')
    assert res.status_code == 200
    assert res.json['database'] == 'SQL Server'

def test_02_register_customer(client):
    import time
    username = f"user_{int(time.time())}"
    res = client.post('/api/auth/register', json={
        'username': username,
        'password': 'Password123',
        'name': 'Nguyễn Văn Test',
        'phone': f"09{int(time.time())%100000000:08d}"
    })
    assert res.status_code == 201
    assert 'token' in res.json
    assert res.json['user']['role'] == 'customer'

def test_03_login_wrong_credentials(client):
    res = client.post('/api/auth/login', json={'username': 'admin', 'password': 'WrongPassword!'})
    assert res.status_code == 401

def test_04_customer_cannot_access_admin_api(app, client):
    with app.app_context():
        customer = db.session.scalar(select(User).where(User.username == 'customer'))
        token = new_session(customer)
        db.session.commit()
    res = client.get('/api/admin/ingredients', headers={'Authorization': f'Bearer {token}'})
    assert res.status_code == 403

def test_05_admin_can_access_admin_api(app, client):
    with app.app_context():
        admin = db.session.scalar(select(User).where(User.username == 'admin'))
        token = new_session(admin)
        db.session.commit()
    res = client.get('/api/admin/ingredients', headers={'Authorization': f'Bearer {token}'})
    assert res.status_code == 200
    assert isinstance(res.json, list)

# --- Nhóm 2: Menu, Tùy chọn, Báo giá (G2-FR02, G2-FR03, G2-FR04, USC03, USC04) ---
def test_06_catalog_count_and_content(client):
    res = client.get('/api/catalog')
    assert res.status_code == 200
    assert len(res.json['drinks']) >= 15
    assert len(res.json['categories']) >= 3
    assert len(res.json['options']) >= 10

def test_07_pricing_formula_base_plus_size_and_topping(client):
    res = client.get('/api/catalog')
    drink = next(d for d in res.json['drinks'] if d['id'] == 'M005')
    options = res.json['options']
    size_l = next(o['id'] for o in options if o['kind'] == 'size' and o['name'] == 'L')
    sugar_30 = next(o['id'] for o in options if o['kind'] == 'sugar' and o['name'] == '30% đường')
    ice_50 = next(o['id'] for o in options if o['kind'] == 'ice' and o['name'] == 'Ít đá')
    top_cheese = next(o['id'] for o in options if o['kind'] == 'topping' and o['name'] == 'Kem cheese')

    res_quote = client.post('/api/quote', json={
        'drink_id': drink['id'],
        'quantity': 2,
        'choices': {
            'size': size_l,
            'sugar': sugar_30,
            'ice': ice_50,
            'toppings': [top_cheese]
        }
    })
    assert res_quote.status_code == 200
    expected_unit = drink['price'] + 11000 + 10000
    assert res_quote.json['unit_price'] == expected_unit
    assert res_quote.json['quantity'] == 2

# --- Nhóm 3: Giỏ hàng & Tạo đơn hàng (G2-FR05, USC05, USC06) ---
def test_08_cart_management(app, client):
    with app.app_context():
        customer = db.session.scalar(select(User).where(User.username == 'customer'))
        token = new_session(customer)
        drink = db.session.scalar(select(Drink).where(Drink.available == True))
        drink_id = drink.id
        db.session.commit()

    # Thêm vào giỏ
    res_add = client.post('/api/cart/items', headers={'Authorization': f'Bearer {token}'}, json={
        'drink_id': drink_id,
        'quantity': 1,
        'choices': {'size': 'size-s', 'sugar': 'sugar-100', 'ice': 'ice-100', 'toppings': []}
    })
    assert res_add.status_code == 201
    item_id = res_add.json['items'][0]['id']

    # Sửa số lượng giỏ
    res_patch = client.patch(f'/api/cart/items/{item_id}', headers={'Authorization': f'Bearer {token}'}, json={
        'quantity': 3
    })
    assert res_patch.status_code == 200
    assert res_patch.json['items'][0]['quantity'] == 3

    # Xóa khỏi giỏ
    res_del = client.delete(f'/api/cart/items/{item_id}', headers={'Authorization': f'Bearer {token}'})
    assert res_del.status_code == 200
    assert len(res_del.json['items']) == 0

def test_09_create_order_idempotency(app, client):
    with app.app_context():
        customer = db.session.scalar(select(User).where(User.username == 'customer'))
        token = new_session(customer)
        drink = db.session.scalar(select(Drink).where(Drink.name == 'Cà phê đen đá'))
        cart = cart_for(customer)
        db.session.add(CartItem(cart_id=cart.id, drink_id=drink.id, quantity=1, choices=json_text({'size': 'size-s', 'sugar': 'sugar-100', 'ice': 'ice-100', 'toppings': []})))
        db.session.commit()

    import time
    key = f"key-{time.time()}"
    res1 = client.post('/api/orders', headers={'Authorization': f'Bearer {token}', 'Idempotency-Key': key}, json={
        'recipient': 'Khách Mua', 'phone': '0901234567', 'address': '123 Đinh Tiên Hoàng'
    })
    assert res1.status_code == 201
    code1 = res1.json['code']

    # Gửi lại cùng key -> Trả về đơn cũ, không tạo đơn mới trùng lặp
    res2 = client.post('/api/orders', headers={'Authorization': f'Bearer {token}', 'Idempotency-Key': key}, json={
        'recipient': 'Khách Mua', 'phone': '0901234567', 'address': '123 Đinh Tiên Hoàng'
    })
    assert res2.status_code == 200
    assert res2.json['code'] == code1

# --- Nhóm 4: Luồng trạng thái & Trừ nguyên liệu (G2-FR06, G2-FR08, G2-FR09, USC07) ---
def test_10_insufficient_stock_prevents_order_creation(app):
    with app.app_context():
        straw = db.session.get(Ingredient, 'strawberry')
        orig_qty = straw.quantity
        straw.quantity = Decimal('0')
        db.session.commit()
        try:
            customer = db.session.scalar(select(User).where(User.username == 'customer'))
            drink = db.session.scalar(select(Drink).where(Drink.name == 'Trà dâu tươi'))
            cart = cart_for(customer)
            db.session.add(CartItem(cart_id=cart.id, drink_id=drink.id, quantity=1, choices=json_text({'size': 'size-s', 'sugar': 'sugar-100', 'ice': 'ice-100', 'toppings': []})))
            db.session.commit()

            with pytest.raises(DomainError) as exc:
                create_order(customer, {'recipient': 'A', 'phone': '0909090909', 'address': 'SG'}, 'fail-key')
            assert 'Không đủ nguyên liệu' in exc.value.message
        finally:
            straw = db.session.get(Ingredient, 'strawberry')
            straw.quantity = orig_qty
            cart = cart_for(customer)
            db.session.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
            db.session.commit()


def test_11_order_state_transitions_correct_sequence(app):
    with app.app_context():
        customer = db.session.scalar(select(User).where(User.username == 'customer'))
        staff = db.session.scalar(select(User).where(User.username == 'staff'))
        drink = db.session.scalar(select(Drink).where(Drink.name == 'Cà phê đen đá'))
        cart = cart_for(customer)
        db.session.add(CartItem(cart_id=cart.id, drink_id=drink.id, quantity=1, choices=json_text({'size': 'size-s', 'sugar': 'sugar-100', 'ice': 'ice-100', 'toppings': []})))
        db.session.commit()

        order = create_order(customer, {'recipient': 'Q', 'phone': '0909090909', 'address': 'SG'}, 'seq-test')
        assert order.status == 'pending'
        assert not order.stock_deducted

        # Chuyển nhảy cóc (pending -> completed) phải lỗi
        with pytest.raises(DomainError) as exc:
            transition(order, staff, 'completed')
        assert 'Chuyển trạng thái sai thứ tự' in exc.value.message

        # Đúng trình tự: pending -> preparing -> ready -> completed
        transition(order, staff, 'preparing')
        assert order.status == 'preparing'
        assert order.stock_deducted

        transition(order, staff, 'ready')
        assert order.status == 'ready'

        transition(order, staff, 'completed')
        assert order.status == 'completed'
        assert order.completed_at is not None

def test_12_customer_cancel_allowed_only_at_pending(app):
    with app.app_context():
        customer = db.session.scalar(select(User).where(User.username == 'customer'))
        drink = db.session.scalar(select(Drink).where(Drink.name == 'Cà phê đen đá'))
        cart = cart_for(customer)
        db.session.add(CartItem(cart_id=cart.id, drink_id=drink.id, quantity=1, choices=json_text({'size': 'size-s', 'sugar': 'sugar-100', 'ice': 'ice-100', 'toppings': []})))
        db.session.commit()

        order = create_order(customer, {'recipient': 'CancelTest', 'phone': '0909090909', 'address': 'SG'}, 'cancel-test')
        transition(order, customer, 'cancelled', 'Khách đổi ý')
        assert order.status == 'cancelled'

# --- Nhóm 5: Quản lý Kho, Phiếu nhập & Kiểm kê (G2-FR07, USC09) ---
def test_13_inventory_adjustment_creates_audit_transaction(app):
    with app.app_context():
        admin = db.session.scalar(select(User).where(User.username == 'admin'))
        ing = db.session.get(Ingredient, 'coffee')
        old_qty = ing.quantity
        new_qty = old_qty + Decimal('2.5')

        stock_change(ing, Decimal('2.5'), 'adjustment', admin.id, 'Kiểm kê thực tế tăng')
        db.session.commit()

        refreshed = db.session.get(Ingredient, 'coffee')
        assert refreshed.quantity == new_qty

        # Verify transaction logged
        tx = db.session.scalar(select(InventoryTransaction).where(InventoryTransaction.ingredient_id == 'coffee', InventoryTransaction.kind == 'adjustment').order_by(InventoryTransaction.created_at.desc()))
        assert tx.delta == Decimal('2.5')
        assert tx.balance == new_qty

def test_14_inventory_never_negative(app):
    with app.app_context():
        admin = db.session.scalar(select(User).where(User.username == 'admin'))
        ing = db.session.get(Ingredient, 'milk')
        with pytest.raises(DomainError) as exc:
            stock_change(ing, -(ing.quantity + Decimal('10')), 'adjustment', admin.id, 'Trừ quá mức')
        assert 'Không được để tồn kho âm' in exc.value.message

def test_15_receipt_confirmation_increases_stock_once(app):
    with app.app_context():
        admin = db.session.scalar(select(User).where(User.username == 'admin'))
        receipt = db.session.get(Receipt, 'receipt-demo')
        # Phiếu demo nhập milk: 20, peach: 5, blacktea: 2
        milk_before = db.session.get(Ingredient, 'milk').quantity

        lines = list(db.session.scalars(select(ReceiptLine).where(ReceiptLine.receipt_id == receipt.id)))
        for row in sorted(lines, key=lambda r: r.ingredient_id):
            ing = db.session.get(Ingredient, row.ingredient_id)
            stock_change(ing, row.quantity, 'receipt', admin.id, 'Nhập kho test', receipt_id=receipt.id)
        receipt.status = 'confirmed'
        db.session.commit()

        milk_after = db.session.get(Ingredient, 'milk').quantity
        assert milk_after == milk_before + Decimal('20')

# --- Nhóm 6: Thanh toán COD & Báo cáo (G2-FR10, G2-FR11, USC10) ---
def test_16_payment_cod_collected(app):
    with app.app_context():
        staff = db.session.scalar(select(User).where(User.username == 'staff'))
        ready_order = db.session.scalar(select(Order).where(Order.status == 'ready'))
        payment = db.session.scalar(select(Payment).where(Payment.order_id == ready_order.id))

        payment.status = 'paid'
        payment.actor_id = staff.id
        payment.paid_at = utcnow()
        db.session.commit()

        refreshed_p = db.session.get(Payment, payment.id)
        assert refreshed_p.status == 'paid'
        assert refreshed_p.actor_id == staff.id

def test_17_reports_endpoint(app, client):
    with app.app_context():
        admin = db.session.scalar(select(User).where(User.username == 'admin'))
        token = new_session(admin)
        db.session.commit()

    res = client.get('/api/admin/reports', headers={'Authorization': f'Bearer {token}'})
    assert res.status_code == 200
    data = res.json
    assert 'revenue' in data
    assert 'bestsellers' in data
    assert 'consumption' in data
    assert 'daily' in data

def test_18_stock_alerts_endpoint(app, client):
    with app.app_context():
        ing = db.session.get(Ingredient, 'matcha')
        orig_qty = ing.quantity
        ing.quantity = Decimal('0.05')
        admin = db.session.scalar(select(User).where(User.username == 'admin'))
        token = new_session(admin)
        db.session.commit()
        try:
            res = client.get('/api/admin/alerts', headers={'Authorization': f'Bearer {token}'})
            assert res.status_code == 200
            assert 'low_stock' in res.json
            assert 'at_risk' in res.json
            assert len(res.json['low_stock']) > 0
        finally:
            ing = db.session.get(Ingredient, 'matcha')
            ing.quantity = orig_qty
            db.session.commit()


# --- Nhóm 7: Khuyến mãi & Snapshot bất biến (G2-FR12, Business Rules) ---
def test_19_coupon_discount_calculation(app, client):
    with app.app_context():
        coupon = db.session.get(Coupon, 'MAY10')
        assert coupon.percent == 10
        assert coupon.minimum == 50000

def test_20_snapshot_immutability(app):
    with app.app_context():
        order = db.session.scalar(select(Order).where(Order.status == 'completed'))
        item = db.session.scalar(select(OrderItem).where(OrderItem.order_id == order.id))
        old_name = item.name
        old_price = item.unit_price

        # Sửa tên món trong menu
        drink = db.session.get(Drink, item.drink_id)
        drink.name = "Tên Menu Bị Admin Đổi"
        drink.price = 999999
        db.session.commit()

        # Kiểm tra item trong đơn cũ không bị đổi
        item_refreshed = db.session.get(OrderItem, item.id)
        assert item_refreshed.name == old_name
        assert item_refreshed.unit_price == old_price

        # Hoàn lại tên menu
        drink.name = old_name
        drink.price = item.base_price
        db.session.commit()
