"""Validation, pricing, inventory transactions and immutable order snapshots."""
import json
import re
from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import datetime, timedelta
from flask import g
from sqlalchemy import select
from .models import *

class DomainError(Exception):
    def __init__(self, message, status=400, details=None):
        self.message, self.status, self.details = message, status, details

def text(value, name, maximum=120, required=True):
    if not isinstance(value, str) or len(value.strip()) > maximum or (required and not value.strip()):
        raise DomainError(f'{name} không hợp lệ (tối đa {maximum} ký tự).')
    return value.strip()

def integer(value, name, low=0, high=1000000000):
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise DomainError(f'{name} phải là số nguyên từ {low} đến {high}.')
    return value

def decimal(value, name, low=Decimal('0'), high=Decimal('100000000')):
    try: result = Decimal(str(value))
    except (InvalidOperation, ValueError): raise DomainError(f'{name} không hợp lệ.')
    if not result.is_finite() or result < low or result > high:
        raise DomainError(f'{name} ngoài khoảng cho phép.')
    return result.quantize(Decimal('.0001'), rounding=ROUND_HALF_UP)

def phone(value):
    result = re.sub(r'[ +.-]', '', text(value, 'Số điện thoại', 20))
    if not re.fullmatch(r'\d{9,15}', result): raise DomainError('Số điện thoại cần 9–15 chữ số.')
    return result

def email(value):
    if not value: return None
    result = text(value, 'Email', 254).lower()
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', result): raise DomainError('Email không hợp lệ.')
    return result

def get(model, key, active=False):
    if not isinstance(key, str) or not key.strip() or len(key) > 80:
        raise DomainError('Mã dữ liệu không hợp lệ.')
    obj = db.session.get(model, key)
    if not obj or (active and not obj.active): raise DomainError('Dữ liệu không tồn tại hoặc đã ngừng sử dụng.', 404)
    return obj

def dump(obj, exclude=()):
    result = {}
    for column in obj.__table__.columns:
        if column.name in exclude: continue
        value = getattr(obj, column.name)
        if isinstance(value, Decimal): value = float(value)
        elif isinstance(value, datetime): value = value.isoformat()+'Z'
        elif hasattr(value, 'isoformat'): value = value.isoformat()
        result[column.name] = value
    return result

def audit(action, entity_id, detail=''):
    db.session.add(Audit(actor_id=getattr(g, 'user', None).id if getattr(g, 'user', None) else None, action=action, entity_id=str(entity_id), detail=detail))

def user_data(user):
    profile = get(Profile, user.id)
    return {'id':user.id,'username':user.username,'role':user.role,'active':user.active, **dump(profile, ('user_id',))}

def json_text(value): return json.dumps(value, ensure_ascii=False)

def option_data(option):
    data = dump(option)
    data['ingredients'] = [dump(x) for x in db.session.scalars(select(ToppingLine).where(ToppingLine.option_id==option.id))]
    return data

def drink_data(drink):
    return {**dump(drink), 'category':get(Category,drink.category_id).name, 'option_ids':list(db.session.scalars(select(DrinkOption.option_id).where(DrinkOption.drink_id==drink.id)))}

UNIT = {'g':('mass',Decimal(1)),'kg':('mass',Decimal(1000)),'ml':('volume',Decimal(1)),'l':('volume',Decimal(1000)),'unit':('count',Decimal(1))}
def convert(quantity, source, target):
    if not isinstance(source, str) or not isinstance(target, str) or source not in UNIT or target not in UNIT or UNIT[source][0] != UNIT[target][0]:
        raise DomainError(f'Không thể đổi đơn vị {source} sang {target}.')
    return Decimal(str(quantity))*UNIT[source][1]/UNIT[target][1]

def requirements(drink_id, choices):
    recipe = db.session.scalar(select(Recipe).where(Recipe.drink_id==drink_id, Recipe.size_id==choices['size']['id'], Recipe.active==True))
    if not recipe: raise DomainError('Món chưa có công thức hợp lệ cho cỡ đã chọn.',409)
    lines = list(db.session.scalars(select(RecipeLine).where(RecipeLine.recipe_id==recipe.id)))
    if not lines: raise DomainError('Công thức chưa có nguyên liệu.',409)
    amounts=defaultdict(Decimal)
    for line in lines:
        ingredient=get(Ingredient,line.ingredient_id,True)
        factor=Decimal(str(choices[line.scales_with]['factor'])) if line.scales_with!='none' else Decimal(1)
        amounts[ingredient.id]+=convert(line.quantity,line.unit,ingredient.unit)*factor
    for topping in choices['toppings']:
        topping_lines=list(db.session.scalars(select(ToppingLine).where(ToppingLine.option_id==topping['id'])))
        if not topping_lines: raise DomainError('Topping chưa có định lượng nguyên liệu.',409)
        for line in topping_lines:
            ingredient=get(Ingredient,line.ingredient_id,True)
            amounts[ingredient.id]+=convert(line.quantity,line.unit,ingredient.unit)
    return {key:str(value.quantize(Decimal('.0001'),rounding=ROUND_HALF_UP)) for key,value in amounts.items() if value>0}

def price_item(data):
    if not isinstance(data,dict): raise DomainError('Dòng giỏ hàng không hợp lệ.')
    drink=get(Drink,data.get('drink_id'),True)
    if not drink.available or not get(Category,drink.category_id).active: raise DomainError('Món hiện đang tạm hết.',409)
    quantity=integer(data.get('quantity',1),'Số lượng',1,99)
    raw=data.get('choices',{})
    if not isinstance(raw,dict): raise DomainError('Tùy chọn không hợp lệ.')
    allowed=set(db.session.scalars(select(DrinkOption.option_id).where(DrinkOption.drink_id==drink.id)))
    selected={}
    for kind in ['size','sugar','ice']:
        option=get(Option,raw.get(kind),True)
        if option.kind!=kind or option.id not in allowed: raise DomainError('Tùy chọn không thuộc đồ uống này.')
        selected[kind]=dump(option)
    toppings=raw.get('toppings',[])
    if not isinstance(toppings,list) or any(not isinstance(key,str) for key in toppings) or len(toppings)>3 or len(set(toppings))!=len(toppings): raise DomainError('Chọn tối đa 3 topping khác nhau.')
    selected['toppings']=[]
    for key in toppings:
        option=get(Option,key,True)
        if option.kind!='topping' or key not in allowed: raise DomainError('Topping không hợp lệ.')
        selected['toppings'].append(dump(option))
    unit_price=drink.price+sum(selected[k]['surcharge'] for k in ['size','sugar','ice'])+sum(x['surcharge'] for x in selected['toppings'])
    return {'drink_id':drink.id,'name':drink.name,'image':drink.image,'quantity':quantity,'base_price':drink.price,'unit_price':unit_price,'choices':selected,'requirements':requirements(drink.id,selected)}

def raw_choices(snapshot):
    return {**{k:snapshot[k]['id'] for k in ['size','sugar','ice']},'toppings':[x['id'] for x in snapshot['toppings']]}

def inventory_needs(items):
    needs=defaultdict(Decimal)
    for item in items:
        for key,value in item['requirements'].items(): needs[key]+=Decimal(value)*item['quantity']
    return needs

def check_stock(items):
    missing=[]
    for key,needed in inventory_needs(items).items():
        ingredient=get(Ingredient,key,True)
        if ingredient.quantity < needed:
            missing.append({'id':key,'name':ingredient.name,'available':float(ingredient.quantity),'required':float(needed),'unit':ingredient.unit})
    if missing: raise DomainError('Không đủ nguyên liệu để xác nhận đơn.',409,missing)

def stock_change(ingredient, delta, kind, actor, reason, order_id=None, receipt_id=None):
    next_quantity=ingredient.quantity+Decimal(delta)
    if next_quantity<0: raise DomainError('Không được để tồn kho âm.',409)
    ingredient.quantity=next_quantity
    db.session.add(InventoryTransaction(ingredient_id=ingredient.id,kind=kind,delta=delta,balance=next_quantity,unit_cost=ingredient.last_price,order_id=order_id,receipt_id=receipt_id,actor_id=actor,reason=reason))

def order_items(order):
    return [{**dump(i),'choices':json.loads(i.choices),'requirements':json.loads(i.requirements)} for i in db.session.scalars(select(OrderItem).where(OrderItem.order_id==order.id))]

CANCELLATION_SECONDS = 60

def cancellation_deadline(order):
    return order.created_at + timedelta(seconds=CANCELLATION_SECONDS)

def in_cancel_window(order):
    """Đơn mới còn trong 60 giây hủy: chỉ khách thấy, nhân viên/quản lý chưa thấy."""
    return order.status=='pending' and utcnow() < cancellation_deadline(order)

def order_data(order):
    items=order_items(order)
    for item in items: item.pop('requirements',None)
    history=[{**dump(h),'actor':get(Profile,h.actor_id).name} for h in db.session.scalars(select(StatusHistory).where(StatusHistory.order_id==order.id).order_by(StatusHistory.created_at))]
    payment=db.session.scalar(select(Payment).where(Payment.order_id==order.id))
    return {**dump(order,('request_key',)),'items':items,'history':history,'payment':dump(payment) if payment else None, 'cancel_deadline':cancellation_deadline(order).isoformat()+'Z', 'server_time':utcnow().isoformat()+'Z'}

def cart_for(user):
    cart=db.session.scalar(select(Cart).where(Cart.user_id==user.id))
    if not cart:
        cart=Cart(user_id=user.id); db.session.add(cart); db.session.flush()
    return cart

def cart_data(cart):
    items=[]
    for row in db.session.scalars(select(CartItem).where(CartItem.cart_id==cart.id)):
        raw={'drink_id':row.drink_id,'quantity':row.quantity,'choices':json.loads(row.choices)}
        try:
            priced=price_item(raw); priced.pop('requirements',None)
            items.append({**priced,'id':row.id,'valid':True,'raw_choices':raw['choices']})
        except DomainError as e:
            drink=get(Drink,row.drink_id)
            items.append({**raw,'id':row.id,'name':drink.name,'image':drink.image,'unit_price':0,'valid':False,'error':e.message,'raw_choices':raw['choices']})
    return {'id':cart.id,'items':items,'subtotal':sum(i['unit_price']*i['quantity'] for i in items)}

def create_order(user, data, request_key):
    existing=db.session.scalar(select(Order).where(Order.user_id==user.id,Order.request_key==request_key))
    if existing: return existing
    cart=cart_for(user)
    rows=list(db.session.scalars(select(CartItem).where(CartItem.cart_id==cart.id)))
    if not rows: raise DomainError('Giỏ hàng đang trống.')
    items=[price_item({'drink_id':r.drink_id,'quantity':r.quantity,'choices':json.loads(r.choices)}) for r in rows]
    check_stock(items)
    subtotal=integer(sum(i['quantity']*i['unit_price'] for i in items),'Tổng giá trị đơn',0,2000000000)
    discount=0; coupon_code=None
    if data.get('coupon'):
        coupon=get(Coupon,text(data['coupon'],'Mã giảm giá',40).upper(),True)
        if coupon.expires_at<utcnow() or subtotal<coupon.minimum: raise DomainError('Mã đã hết hạn hoặc chưa đủ giá trị đơn.')
        discount=subtotal*coupon.percent//100; coupon_code=coupon.code
    order=Order(code='MY'+uid().replace('-','')[:16].upper(),user_id=user.id,recipient=text(data.get('recipient'),'Người nhận'),phone=phone(data.get('phone')),address=text(data.get('address'),'Địa chỉ',500),note=text(data.get('note',''),'Ghi chú',1000,False),subtotal=subtotal,discount=discount,total=subtotal-discount,coupon_code=coupon_code,request_key=request_key)
    db.session.add(order); db.session.flush()
    for item in items:
        db.session.add(OrderItem(order_id=order.id,**{k:v for k,v in item.items() if k not in ['choices','requirements']},choices=json_text(item['choices']),requirements=json_text(item['requirements'])))
    db.session.add(Payment(order_id=order.id,amount=order.total))
    db.session.add(StatusHistory(order_id=order.id,status='pending',actor_id=user.id,note='Khách gửi đơn; chưa trừ nguyên liệu.'))
    for row in rows: db.session.delete(row)
    audit('order.created',order.id)
    db.session.flush()
    return order

NEXT={'pending':{'preparing'},'preparing':{'ready'},'ready':{'completed'}}
def transition(order,user,target,reason=''):
    if not isinstance(target,str) or target not in ['pending','preparing','ready','completed','cancelled']:
        raise DomainError('Trạng thái đơn không hợp lệ.')
    if target=='cancelled' and user.role!='customer':
        raise DomainError('Chỉ khách hàng được hủy đơn của mình.',403)
    if target==order.status: return order
    if target=='cancelled':
        if order.status in ['completed','cancelled']: raise DomainError('Không thể hủy đơn này.',409)
        if user.role=='customer' and (order.user_id!=user.id or order.status!='pending'): raise DomainError('Chỉ được hủy đơn của mình trước khi pha chế.',403)
        if utcnow() >= cancellation_deadline(order):
            raise DomainError('Đã hết thời hạn hủy đơn 60 giây.',409)
        reason=text(reason,'Lý do hủy',1000)
        payment=db.session.scalar(select(Payment).where(Payment.order_id==order.id))
        if payment.status=='paid': raise DomainError('Đơn đã thu tiền không thể hủy trong phạm vi COD này.',409)
    else:
        if user.role not in ['staff','admin']: raise DomainError('Không có quyền cập nhật trạng thái.',403)
        if target not in NEXT.get(order.status,set()): raise DomainError('Chuyển trạng thái sai thứ tự.',409)
        if target=='preparing':
            items=order_items(order)
            check_stock(items)
            if order.stock_deducted: raise DomainError('Đơn đã được trừ nguyên liệu.',409)
            for key,needed in sorted(inventory_needs(items).items()):
                stock_change(get(Ingredient,key),-needed,'sale',user.id,'Pha chế '+order.code,order_id=order.id)
            order.stock_deducted=True
        if target=='completed': order.completed_at=utcnow()
    order.status=target
    note=reason or 'Cập nhật tiến trình'
    if target=='cancelled' and order.stock_deducted: note+='; nguyên liệu đã sử dụng, không hoàn kho.'
    db.session.add(StatusHistory(order_id=order.id,status=target,actor_id=user.id,note=note))
    audit('order.'+target,order.id,note)
    db.session.flush()
    return order

def receipt_data(receipt):
    lines=[{**dump(x),'name':get(Ingredient,x.ingredient_id).name,'unit':get(Ingredient,x.ingredient_id).unit} for x in db.session.scalars(select(ReceiptLine).where(ReceiptLine.receipt_id==receipt.id))]
    return {**dump(receipt),'lines':lines,'total':sum(x['quantity']*x['price'] for x in lines),'actor':get(Profile,receipt.actor_id).name}

def recipe_data(recipe):
    lines=[{**dump(x),'name':get(Ingredient,x.ingredient_id).name,'cost':float(convert(x.quantity,x.unit,get(Ingredient,x.ingredient_id).unit)*get(Ingredient,x.ingredient_id).last_price)} for x in db.session.scalars(select(RecipeLine).where(RecipeLine.recipe_id==recipe.id))]
    return {**dump(recipe),'drink':get(Drink,recipe.drink_id).name,'size':get(Option,recipe.size_id).name,'lines':lines,'cost':sum(x['cost'] for x in lines)}
