"""JSON API for customer, staff and admin workflows."""
from datetime import date, timedelta
from urllib.parse import urlparse
from flask import Blueprint, request, jsonify, g
from sqlalchemy import select, delete, func, text as sql_text
from .models import *
from .domain import *
from .auth import require, payload

api=Blueprint('api',__name__)
def commit(value,code=200):
    db.session.commit()
    return jsonify(value),code

def boolean(value,name):
    if not isinstance(value,bool): raise DomainError(name+' phải là true/false.')
    return value

def object_rows(value, name, maximum):
    if not isinstance(value,list) or not 1 <= len(value) <= maximum or any(not isinstance(row,dict) for row in value):
        raise DomainError(f'{name} cần 1–{maximum} dòng hợp lệ.')
    return value

def owned_order(key):
    order=db.session.scalar(select(Order).where((Order.id==key)|(Order.code==key)))
    if not order: raise DomainError('Không tìm thấy đơn.',404)
    if g.user.role=='customer' and order.user_id!=g.user.id: raise DomainError('Không tìm thấy đơn.',404)
    return order

def image_url(value):
    value=text(value,'Đường dẫn ảnh',1000)
    if value.startswith('/assets/') and '..' not in value: return value
    parsed=urlparse(value)
    if parsed.scheme=='https' and parsed.netloc and not parsed.username and not parsed.password: return value
    raise DomainError('Ảnh cần đường dẫn /assets/... hoặc URL HTTPS.')

@api.get('/ready')
def ready():
    """Process-only readiness for hosting probes; use /health to verify SQL Server."""
    return jsonify(status='ready')

@api.get('/health')
def health():
    db.session.execute(sql_text('SELECT 1'))
    return jsonify(status='ok',database='SQL Server')

@api.get('/catalog')
def catalog():
    query=select(Drink).join(Category).where(Drink.active==True,Category.active==True)
    if request.args.get('q'): query=query.where(Drink.name.contains(request.args['q'],autoescape=True))
    if request.args.get('category'): query=query.where(Drink.category_id==request.args['category'])
    drinks=[drink_data(x) for x in db.session.scalars(query.order_by(Drink.name))]
    return jsonify(drinks=drinks,categories=[dump(x) for x in db.session.scalars(select(Category).where(Category.active==True))],options=[dump(x) for x in db.session.scalars(select(Option).where(Option.active==True))])

@api.post('/quote')
def quote():
    item=price_item(payload()); item.pop('requirements',None)
    return jsonify(item)

@api.get('/cart')
@require('customer')
def read_cart():
    return commit(cart_data(cart_for(g.user)))

@api.post('/cart/items')
@require('customer')
def add_cart():
    data=payload(); item=price_item(data); cart=cart_for(g.user)
    if db.session.scalar(select(func.count()).select_from(CartItem).where(CartItem.cart_id==cart.id))>=100: raise DomainError('Giỏ có tối đa 100 dòng.')
    db.session.add(CartItem(cart_id=cart.id,drink_id=item['drink_id'],quantity=item['quantity'],choices=json_text(raw_choices(item['choices']))))
    db.session.flush()
    return commit(cart_data(cart),201)

@api.patch('/cart/items/<key>')
@require('customer')
def edit_cart(key):
    data=payload(); cart=cart_for(g.user); row=get(CartItem,key)
    if row.cart_id!=cart.id: raise DomainError('Không tìm thấy món trong giỏ.',404)
    item=price_item({'drink_id':row.drink_id,'quantity':data.get('quantity',row.quantity),'choices':data.get('choices',json.loads(row.choices))})
    row.quantity=item['quantity']; row.choices=json_text(raw_choices(item['choices'])); db.session.flush()
    return commit(cart_data(cart))

@api.delete('/cart/items/<key>')
@require('customer')
def remove_cart(key):
    cart=cart_for(g.user); row=get(CartItem,key)
    if row.cart_id!=cart.id: raise DomainError('Không tìm thấy món trong giỏ.',404)
    db.session.delete(row); db.session.flush()
    return commit(cart_data(cart))

@api.post('/orders')
@require('customer')
def place_order():
    key=text(request.headers.get('Idempotency-Key'),'Idempotency-Key',80)
    existing=db.session.scalar(select(Order).where(Order.user_id==g.user.id,Order.request_key==key))
    if existing:
        return commit(order_data(existing), 200)
    order=create_order(g.user,payload(),key)
    return commit(order_data(order),201)


@api.get('/orders')
@require()
def orders():
    query=select(Order)
    if g.user.role=='customer': query=query.where(Order.user_id==g.user.id)
    if request.args.get('status'): query=query.where(Order.status==request.args['status'])
    if request.args.get('q'): query=query.where((Order.code.contains(request.args['q'],autoescape=True))|(Order.recipient.contains(request.args['q'],autoescape=True)))
    return jsonify([order_data(x) for x in db.session.scalars(query.order_by(Order.created_at.desc()))])

@api.get('/orders/request/<key>')
@require('customer')
def recover_order(key):
    request_key=text(key,'Idempotency-Key',80)
    order=db.session.scalar(select(Order).where(Order.user_id==g.user.id,Order.request_key==request_key))
    if not order: raise DomainError('Chưa tìm thấy đơn cho lần gửi này. Có thể thử gửi lại bằng cùng khóa.',404)
    return jsonify(order_data(order))

@api.get('/orders/<key>')
@require()
def order_detail(key): return jsonify(order_data(owned_order(key)))

@api.post('/orders/<key>/status')
@require('staff','admin')
def update_status(key):
    data=payload(); order=owned_order(key)
    if data.get('expected_status')!=order.status: raise DomainError('Đơn vừa được cập nhật. Hãy tải lại trạng thái.',409)
    transition(order,g.user,data.get('status'),data.get('reason',''))
    return commit(order_data(order))

@api.post('/orders/<key>/cancel')
@require()
def cancel(key):
    data=payload(); order=owned_order(key)
    if order.status=='cancelled': return commit(order_data(order))
    transition(order,g.user,'cancelled',data.get('reason','Khách hàng yêu cầu hủy'))
    return commit(order_data(order))

@api.post('/orders/<key>/payment')
@require('staff','admin')
def pay(key):
    data=payload(); order=owned_order(key)
    if order.status not in ['ready','delivering','completed']: raise DomainError('Chỉ ghi nhận COD khi đơn sẵn sàng giao hoặc đã hoàn tất.',409)
    payment=db.session.scalar(select(Payment).where(Payment.order_id==order.id))
    if integer(data.get('amount'),'Số tiền thu',0,2000000000)!=order.total: raise DomainError('Số tiền thu phải bằng tổng tiền đơn.')
    if payment.status!='paid':
        payment.status='paid'; payment.actor_id=g.user.id; payment.paid_at=utcnow(); audit('payment.collected',order.id,str(order.total))
    return commit(order_data(order))

@api.get('/admin/categories')
@require('admin')
def categories(): return jsonify([dump(x) for x in db.session.scalars(select(Category))])

@api.route('/admin/categories',methods=['POST'])
@api.route('/admin/categories/<key>',methods=['PATCH','DELETE'])
@require('admin')
def save_category(key=None):
    obj=get(Category,key) if key else Category()
    if request.method=='DELETE':
        obj.active=False
    else:
        data=payload(); obj.name=text(data.get('name',obj.name),'Tên danh mục')
        if 'active' in data: obj.active=boolean(data['active'],'Trạng thái')
    db.session.add(obj); db.session.flush(); audit('category.'+request.method.lower(),obj.id)
    return commit(dump(obj))

@api.get('/admin/drinks')
@require('admin')
def drinks(): return jsonify([drink_data(x) for x in db.session.scalars(select(Drink).order_by(Drink.name))])

@api.post('/admin/drinks')
@api.route('/admin/drinks/<key>',methods=['PATCH','DELETE'])
@require('admin')
def save_drink(key=None):
    obj=get(Drink,key) if key else Drink()
    if request.method=='DELETE': obj.active=False; obj.available=False
    else:
        data=payload()
        obj.name=text(data.get('name',obj.name),'Tên đồ uống')
        obj.category_id=get(Category,data.get('category_id',obj.category_id),True).id
        obj.price=integer(data.get('price',obj.price),'Giá cơ bản',0,10000000)
        obj.description=text(data.get('description',obj.description or ''),'Mô tả',2000,False)
        obj.image=image_url(data.get('image',obj.image or '/assets/product-0.jpg'))
        for name in ['available','active']:
            if name in data: setattr(obj,name,boolean(data[name],name))
        db.session.add(obj); db.session.flush()
        if 'option_ids' in data or not key:
            ids=data.get('option_ids',[])
            if not isinstance(ids,list) or any(not isinstance(x,str) for x in ids) or len(ids)!=len(set(ids)) or len(ids)>100: raise DomainError('Danh sách tùy chọn không hợp lệ.')
            selected=[get(Option,x,True) for x in ids]
            if not all(any(x.kind==kind for x in selected) for kind in ['size','sugar','ice']): raise DomainError('Món cần ít nhất một size, mức đường và mức đá.')
            db.session.execute(delete(DrinkOption).where(DrinkOption.drink_id==obj.id))
            for option in selected: db.session.add(DrinkOption(drink_id=obj.id,option_id=option.id))
    db.session.add(obj); db.session.flush(); audit('drink.'+request.method.lower(),obj.id)
    return commit(drink_data(obj))

@api.get('/admin/options')
@require('admin')
def options(): return jsonify([option_data(x) for x in db.session.scalars(select(Option))])

@api.post('/admin/options')
@api.route('/admin/options/<key>',methods=['PATCH','DELETE'])
@require('admin')
def save_option(key=None):
    obj=get(Option,key) if key else Option()
    if request.method=='DELETE': obj.active=False
    else:
        data=payload(); kind=data.get('kind',obj.kind)
        if kind not in ['size','topping','sugar','ice'] or (key and kind!=obj.kind): raise DomainError('Loại tùy chọn không hợp lệ hoặc không thể đổi.')
        obj.kind=kind; obj.name=text(data.get('name',obj.name),'Tên tùy chọn',80)
        obj.surcharge=integer(data.get('surcharge',obj.surcharge or 0),'Phụ thu',0,1000000)
        obj.factor=decimal(data.get('factor',obj.factor if obj.factor is not None else 1),'Hệ số',high=Decimal('3'))
        if 'active' in data: obj.active=boolean(data['active'],'Trạng thái')
        db.session.add(obj); db.session.flush()
        if 'ingredients' in data:
            if kind!='topping': raise DomainError('Chỉ topping có nguyên liệu trực tiếp.')
            rows=object_rows(data['ingredients'],'Topping',50)
            ids=[text(row.get('ingredient_id'),'Mã nguyên liệu',36) for row in rows]
            if len(set(ids))!=len(ids): raise DomainError('Không lặp nguyên liệu trong topping.')
            db.session.execute(delete(ToppingLine).where(ToppingLine.option_id==obj.id))
            for row in rows:
                ing=get(Ingredient,row.get('ingredient_id'),True); qty=decimal(row.get('quantity'),'Định lượng',Decimal('.0001')); unit=row.get('unit')
                convert(qty,unit,ing.unit)
                db.session.add(ToppingLine(option_id=obj.id,ingredient_id=ing.id,quantity=qty,unit=unit))
    db.session.add(obj); db.session.flush(); audit('option.'+request.method.lower(),obj.id)
    return commit(option_data(obj))

@api.get('/admin/ingredients')
@require('admin')
def ingredients(): return jsonify([dump(x) for x in db.session.scalars(select(Ingredient).order_by(Ingredient.name))])

@api.post('/admin/ingredients')
@api.route('/admin/ingredients/<key>',methods=['PATCH','DELETE'])
@require('admin')
def save_ingredient(key=None):
    obj=get(Ingredient,key) if key else Ingredient(quantity=0)
    if request.method=='DELETE':
        obj.active=False
    else:
        data=payload(); obj.name=text(data.get('name',obj.name),'Tên nguyên liệu')
        unit=data.get('unit',obj.unit)
        if not isinstance(unit,str) or unit not in UNIT or (key and unit!=obj.unit): raise DomainError('Đơn vị không hợp lệ hoặc không được đổi sau khi tạo.')
        obj.unit=unit; obj.minimum=decimal(data.get('minimum',obj.minimum or 0),'Ngưỡng cảnh báo'); obj.last_price=decimal(data.get('last_price',obj.last_price or 0),'Giá nhập')
        if 'active' in data: obj.active=boolean(data['active'],'Trạng thái')
    if key and not obj.active:
        if db.session.scalar(select(RecipeLine.id).join(Recipe).where(RecipeLine.ingredient_id==key,Recipe.active==True).limit(1)) or db.session.scalar(select(ToppingLine.option_id).join(Option).where(ToppingLine.ingredient_id==key,Option.active==True).limit(1)):
            raise DomainError('Nguyên liệu đang dùng trong công thức/topping. Ngừng công thức và topping trước khi ẩn.',409)
    db.session.add(obj); db.session.flush(); audit('ingredient.'+request.method.lower(),obj.id)
    return commit(dump(obj))

@api.post('/admin/ingredients/<key>/adjust')
@require('admin')
def adjust(key):
    data=payload(); obj=get(Ingredient,key,True); qty=decimal(data.get('quantity'),'Tồn thực tế'); reason=text(data.get('reason'),'Lý do kiểm kê',1000)
    stock_change(obj,qty-obj.quantity,'adjustment',g.user.id,reason); audit('inventory.adjusted',key,reason)
    return commit(dump(obj))

@api.get('/admin/inventory-transactions')
@require('admin')
def inventory_transactions():
    query=select(InventoryTransaction).order_by(InventoryTransaction.created_at.desc())
    if request.args.get('ingredient_id'): query=query.where(InventoryTransaction.ingredient_id==request.args['ingredient_id'])
    return jsonify([{**dump(x),'ingredient':get(Ingredient,x.ingredient_id).name,'unit':get(Ingredient,x.ingredient_id).unit,'actor':get(Profile,x.actor_id).name} for x in db.session.scalars(query)])

@api.get('/admin/recipes')
@require('admin')
def recipes(): return jsonify([recipe_data(x) for x in db.session.scalars(select(Recipe))])

@api.post('/admin/recipes')
@api.route('/admin/recipes/<key>',methods=['PATCH','DELETE'])
@require('admin')
def save_recipe(key=None):
    obj=get(Recipe,key) if key else Recipe()
    if request.method=='DELETE':
        obj.active=False
    else:
        data=payload()
        obj.active=boolean(data.get('active',obj.active if key else True),'Trạng thái')
        obj.drink_id=get(Drink,data.get('drink_id',obj.drink_id),obj.active).id
        size=get(Option,data.get('size_id',obj.size_id),obj.active)
        if size.kind!='size' or not db.session.get(DrinkOption,(obj.drink_id,size.id)): raise DomainError('Size không thuộc đồ uống.')
        obj.size_id=size.id; obj.name=text(data.get('name',obj.name),'Tên công thức',160)
        obj.instructions=text(data.get('instructions',obj.instructions or ''),'Hướng dẫn',5000,False)
        rows=data.get('lines')
        if rows is None and key:
            rows=[dump(line) for line in db.session.scalars(select(RecipeLine).where(RecipeLine.recipe_id==obj.id))]
        rows=object_rows(rows,'Công thức',50)
        validated=[]
        for row in rows:
            ing=get(Ingredient,row.get('ingredient_id'),obj.active)
            qty=decimal(row.get('quantity'),'Định lượng',Decimal('.0001')); unit=row.get('unit'); scale=row.get('scales_with','none')
            convert(qty,unit,ing.unit)
            if scale not in ['none','sugar','ice']: raise DomainError('Hệ số tùy chọn không hợp lệ.')
            validated.append((ing.id,qty,unit,scale))
        db.session.add(obj); db.session.flush()
        db.session.execute(delete(RecipeLine).where(RecipeLine.recipe_id==obj.id))
        for ingredient_id,qty,unit,scale in validated:
            db.session.add(RecipeLine(recipe_id=obj.id,ingredient_id=ingredient_id,quantity=qty,unit=unit,scales_with=scale))
    db.session.add(obj); db.session.flush(); audit('recipe.'+request.method.lower(),obj.id)
    return commit(recipe_data(obj))

@api.get('/admin/receipts')
@require('admin')
def receipts(): return jsonify([receipt_data(x) for x in db.session.scalars(select(Receipt).order_by(Receipt.created_at.desc()))])

@api.post('/admin/receipts')
@api.patch('/admin/receipts/<key>')
@require('admin')
def save_receipt(key=None):
    data=payload(); obj=get(Receipt,key) if key else Receipt(code='NK'+uid().replace('-','')[:16].upper(),actor_id=g.user.id)
    if key and obj.status!='draft': raise DomainError('Phiếu đã xác nhận không được sửa.',409)
    obj.supplier=text(data.get('supplier'),'Nhà cung cấp',160); obj.note=text(data.get('note',''),'Ghi chú',1000,False)
    try: obj.received_date=date.fromisoformat(data.get('received_date',''))
    except (ValueError,TypeError): raise DomainError('Ngày nhập không hợp lệ.')
    rows=object_rows(data.get('lines'),'Phiếu nhập',100)
    ids=[text(r.get('ingredient_id'),'Mã nguyên liệu',36) for r in rows]
    if len(set(ids))!=len(ids): raise DomainError('Không nhập trùng nguyên liệu trong một phiếu.')
    db.session.add(obj); db.session.flush(); db.session.execute(delete(ReceiptLine).where(ReceiptLine.receipt_id==obj.id))
    for row in rows:
        ing=get(Ingredient,row.get('ingredient_id'),True)
        db.session.add(ReceiptLine(receipt_id=obj.id,ingredient_id=ing.id,quantity=decimal(row.get('quantity'),'Số lượng',Decimal('.0001')),price=decimal(row.get('price'),'Đơn giá')))
    db.session.flush(); audit('receipt.saved',obj.id)
    return commit(receipt_data(obj))

@api.post('/admin/receipts/<key>/confirm')
@require('admin')
def confirm_receipt(key):
    obj=get(Receipt,key)
    if obj.status=='confirmed': return commit(receipt_data(obj))
    lines=list(db.session.scalars(select(ReceiptLine).where(ReceiptLine.receipt_id==key)))
    if not lines: raise DomainError('Phiếu không có nguyên liệu.')
    for row in sorted(lines,key=lambda r:r.ingredient_id):
        ing=get(Ingredient,row.ingredient_id,True); ing.last_price=row.price
        stock_change(ing,row.quantity,'receipt',g.user.id,'Nhập '+obj.code,receipt_id=obj.id)
    obj.status='confirmed'; obj.confirmed_by=g.user.id; obj.confirmed_at=utcnow(); audit('receipt.confirmed',key)
    return commit(receipt_data(obj))

@api.get('/admin/alerts')
@require('admin')
def alerts():
    low=[dump(x) for x in db.session.scalars(select(Ingredient).where(Ingredient.active==True,Ingredient.quantity<Ingredient.minimum))]
    risks=[]
    for recipe in db.session.scalars(select(Recipe).where(Recipe.active==True)):
        drink=get(Drink,recipe.drink_id); size=get(Option,recipe.size_id)
        if not drink.active or not drink.available or not size.active or not get(Category,drink.category_id).active: continue
        allowed=list(db.session.scalars(select(Option).join(DrinkOption).where(DrinkOption.drink_id==drink.id,Option.active==True)))
        if not any(option.id==size.id for option in allowed): continue
        factors={kind:max((option.factor for option in allowed if option.kind==kind),default=Decimal(1)) for kind in ['sugar','ice']}
        needs=defaultdict(Decimal)
        for line in db.session.scalars(select(RecipeLine).where(RecipeLine.recipe_id==recipe.id)):
            ing=get(Ingredient,line.ingredient_id)
            needs[ing.id]+=convert(line.quantity,line.unit,ing.unit)*factors.get(line.scales_with,Decimal(1))
        limits=[int(get(Ingredient,key).quantity//amount) if get(Ingredient,key).active else 0 for key,amount in needs.items() if amount>0]
        count=min(limits) if limits else 0
        if count<5: risks.append({'drink_id':drink.id,'name':drink.name,'size':size.name,'cups':count})
    return jsonify(low_stock=low,at_risk=risks)

@api.get('/admin/reports')
@require('admin')
def reports():
    try:
        start=date.fromisoformat(request.args.get('from',str(date.today()-timedelta(days=6))))
        end=date.fromisoformat(request.args.get('to',str(date.today())))
    except ValueError: raise DomainError('Khoảng ngày không hợp lệ.')
    if end<start or (end-start).days>366: raise DomainError('Khoảng báo cáo tối đa 367 ngày.')
    a=datetime.combine(start,datetime.min.time()); b=datetime.combine(end+timedelta(days=1),datetime.min.time())
    # Recognition uses the later of completion and COD collection; discounts are allocated proportionally.
    paid=list(db.session.execute(select(Order,Payment).join(Payment).where(Order.status=='completed',Payment.status=='paid')))
    recognized=[(o,p,max(o.completed_at or o.created_at,p.paid_at or o.created_at)) for o,p in paid]
    current=[o for o,p,when in recognized if a<=when<b]
    previous=sum(o.total for o,p,when in recognized if a-(b-a)<=when<a)
    daily=defaultdict(int); categories=defaultdict(float); sellers={}
    for o,p,when in recognized:
        if not a<=when<b: continue
        daily[when.date().isoformat()]+=o.total
        for item in order_items(o):
            key=(item['name'],item['choices']['size']['name'])
            entry=sellers.setdefault(key,{'name':key[0]+' '+key[1],'quantity':0,'revenue':0})
            revenue=item['unit_price']*item['quantity']*(o.total/o.subtotal if o.subtotal else 0)
            entry['quantity']+=item['quantity']; entry['revenue']+=revenue
            categories[get(Category,get(Drink,item['drink_id']).category_id).name]+=revenue
    created=list(db.session.scalars(select(Order).where(Order.created_at>=a,Order.created_at<b)))
    states={s:sum(o.status==s for o in created) for s in ['pending','preparing','ready','delivering','completed','cancelled']}
    consumption={}
    for tx in db.session.scalars(select(InventoryTransaction).where(InventoryTransaction.kind=='sale',InventoryTransaction.created_at>=a,InventoryTransaction.created_at<b)):
        ing=get(Ingredient,tx.ingredient_id); entry=consumption.setdefault(ing.id,{'name':ing.name,'unit':ing.unit,'quantity':0,'cost':0})
        entry['quantity']+=float(-tx.delta); entry['cost']+=float(-tx.delta*tx.unit_cost)
    revenue=sum(o.total for o in current)
    return jsonify(start=str(start),end=str(end),revenue=revenue,completed_paid=len(current),order_count=len(created),average=round(revenue/len(current)) if current else 0,previous_revenue=previous,states=states,daily=[{'date':str(start+timedelta(days=n)),'revenue':daily[str(start+timedelta(days=n))]} for n in range((end-start).days+1)],bestsellers=sorted(sellers.values(),key=lambda x:x['quantity'],reverse=True),categories=[{'name':k,'revenue':v} for k,v in categories.items()],consumption=list(consumption.values()))

@api.get('/admin/audit')
@require('admin')
def audits(): return jsonify([dump(x) for x in db.session.scalars(select(Audit).order_by(Audit.created_at.desc()).limit(500))])

@api.get('/admin/users')
@require('admin')
def users(): return jsonify([user_data(x) for x in db.session.scalars(select(User))])

@api.patch('/admin/users/<key>')
@require('admin')
def update_user(key):
    data=payload(); user=get(User,key)
    if key==g.user.id: raise DomainError('Không đổi vai trò/trạng thái của chính mình.')
    if 'role' in data:
        if data['role'] not in ['customer','staff','admin']: raise DomainError('Vai trò không hợp lệ.')
        user.role=data['role']
    if 'active' in data: user.active=boolean(data['active'],'Trạng thái')
    db.session.execute(delete(AuthSession).where(AuthSession.user_id==key)); audit('user.updated',key)
    return commit(user_data(user))

@api.get('/admin/coupons')
@require('admin')
def coupons(): return jsonify([dump(x) for x in db.session.scalars(select(Coupon))])

@api.post('/admin/coupons')
@api.patch('/admin/coupons/<key>')
@require('admin')
def save_coupon(key=None):
    data=payload(); obj=get(Coupon,key) if key else Coupon(code=text(data.get('code'),'Mã giảm giá',40).upper())
    obj.percent=integer(data.get('percent',obj.percent),'Phần trăm',1,50); obj.minimum=integer(data.get('minimum',obj.minimum or 0),'Tối thiểu')
    expires=text(data.get('expires_at'),'Ngày hết hạn',40)
    try: obj.expires_at=datetime.combine(date.fromisoformat(expires[:10]),datetime.max.time())
    except (ValueError,TypeError): raise DomainError('Ngày hết hạn không hợp lệ.')
    obj.active=boolean(data.get('active',True),'Trạng thái'); db.session.add(obj); db.session.flush(); audit('coupon.saved',obj.code)
    return commit(dump(obj))
