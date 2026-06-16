from fastapi import FastAPI, Depends, Request, Form, responses
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta
import random
import os # تم إضافة المكتبة

# ==================== إعداد المسارات (إضافة جديدة) ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# استخدام المسار الكامل لقاعدة البيانات لضمان عدم حدوث أخطاء
SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'drone.db')}"

# ==================== إعداد قاعدة البيانات ====================
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==================== نماذج قاعدة البيانات ====================
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, unique=True, index=True)
    password = Column(String)
    withdraw_password = Column(String, default="") # حقل كلمة مرور السحب
    balance = Column(Float, default=0.0)
    vip_level = Column(Integer, default=0)
    referrer_id = Column(Integer, nullable=True)
    referral_code = Column(String, nullable=True) # --- إضافة جديدة ---
    start_date = Column(String, default=datetime.now().strftime("%Y-%m-%d"))
    last_claim_date = Column(String, default="0")
    total_earned = Column(Float, default=0.0)
    spins = Column(Integer, default=0)

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    amount = Column(Float)
    type = Column(String)  # "deposit" or "withdraw"
    status = Column(String)  # "pending", "approved"
    wallet = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

class UserProduct(Base):
    __tablename__ = "user_products"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    product_id = Column(Integer)
    last_claim_date = Column(String, default="0")

# جدول المنتجات الجديد للتحكم في الحالة
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    price = Column(Float)
    image = Column(String)
    is_active = Column(Boolean, default=True)

# إنشاء الجداول
Base.metadata.create_all(bind=engine)

# ==================== إعداد FastAPI ====================
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ==================== دالة التشغيل التلقائي الجديدة ====================
@app.on_event("startup")
async def startup_event():
    db = SessionLocal()
    # نتحقق إذا كان الجدول فارغاً
    if not db.query(Product).first():
        for p_id, p_info in PLANS.items():
            # المنطق الجديد: إذا كان رقم المنتج أكبر من 2، نجعله مغلقاً (is_active = False)
            is_active_status = True if p_id <= 2 else False
            
            new_prod = Product(
                id=p_id, 
                name=p_info["name"], 
                price=p_info["cost"], 
                is_active=is_active_status
            )
            db.add(new_prod)
        db.commit()
    db.close()

# ==================== البيانات الثابتة ====================
WALLETS = ["01019316792", "01289332726", "01552406916"]
ADMIN_SECRET_KEY = "ahmed552007" # يمكنك تغييرها لأي كلمة سر قوية

PLANS = {
    1: {"name": "درون المبتدئ", "cost": 300, "daily": 45, "days": 60},
    2: {"name": "درون المسح", "cost": 600, "daily": 95, "days": 60},
    3: {"name": "درون الشحن", "cost": 1200, "daily": 200, "days": 60},
    4: {"name": "درون التصوير", "cost": 2500, "daily": 450, "days": 60},
    5: {"name": "درون الإنقاذ", "cost": 5000, "daily": 950, "days": 60},
    6: {"name": "درون المراقبة", "cost": 10000, "daily": 2000, "days": 60},
    7: {"name": "أسطول الدرون الملكي", "cost": 20000, "daily": 4500, "days": 60},
}

# ==================== دوال مساعدة ====================
def get_current_user(request: Request, db: Session = Depends(get_db)):
    user_id = request.cookies.get("user_id")
    if user_id:
        return db.query(User).filter(User.id == int(user_id)).first()
    return None

def distribute_referral_commission(user_id, deposit_amount, db: Session):
    u1 = db.query(User).filter(User.id == user_id).first()
    if u1 and u1.referrer_id:
        p1 = db.query(User).filter(User.id == u1.referrer_id).first()
        if p1:
            p1.balance += deposit_amount * 0.30
            p1.total_earned += deposit_amount * 0.30 # --- تحديث إجمالي الربح ---
            if p1.referrer_id:
                p2 = db.query(User).filter(User.id == p1.referrer_id).first()
                if p2:
                    p2.balance += deposit_amount * 0.20
                    p2.total_earned += deposit_amount * 0.20 # --- تحديث إجمالي الربح ---
                    if p2.referrer_id:
                        p3 = db.query(User).filter(User.id == p2.referrer_id).first()
                        if p3:
                            p3.balance += deposit_amount * 0.10
                            p3.total_earned += deposit_amount * 0.10 # --- تحديث إجمالي الربح ---
    db.commit()

# ==================== مسارات الأمان الجديدة ====================
@app.get("/security")
async def security_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return responses.RedirectResponse(url="/login")
    
    has_password = True if user.withdraw_password and user.withdraw_password != "" else False
    
    return templates.TemplateResponse("security.html", {
        "request": request, 
        "user": user, 
        "has_password": has_password
    })

@app.post("/security")
async def update_withdraw_password(
    request: Request, 
    old_password: str = Form(None),
    new_withdraw_password: str = Form(...), 
    confirm_password: str = Form(...), 
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user:
        return responses.RedirectResponse(url="/login")
    
    if new_withdraw_password != confirm_password:
        has_password = True if user.withdraw_password and user.withdraw_password != "" else False
        return templates.TemplateResponse("security.html", {
            "request": request, "user": user, "error": "كلمات المرور الجديدة غير متطابقة", "has_password": has_password
        })
    
    if user.withdraw_password and user.withdraw_password != "" and user.withdraw_password != old_password:
        has_password = True
        return templates.TemplateResponse("security.html", {
            "request": request, "user": user, "error": "كلمة مرور السحب القديمة غير صحيحة", "has_password": has_password
        })
    
    user.withdraw_password = new_withdraw_password
    db.commit()
    return responses.RedirectResponse(url="/?success=تم تغيير كلمة المرور", status_code=303)

# ==================== مسارات المدير (معدلة للاستقرار) ====================
@app.get("/admin")
async def admin_panel(request: Request, db: Session = Depends(get_db)):
    is_admin = request.cookies.get("admin_auth") == "true"
    if not is_admin:
        return templates.TemplateResponse("admin.html", {
            "request": request, 
            "transactions": [], 
            "users": [], 
            "user_products": [], 
            "products": [], 
            "PLANS": PLANS
        })
    transactions = db.query(Transaction).filter(Transaction.status == "pending").all()
    users = db.query(User).all() 
    user_products = db.query(UserProduct).all()
    products_status = db.query(Product).all()
    
    return templates.TemplateResponse("admin.html", {
        "request": request, 
        "transactions": transactions,
        "users": users,
        "user_products": user_products,
        "products": products_status,
        "PLANS": PLANS
    })

@app.post("/admin/login")
async def admin_login(admin_secret: str = Form(...)):
    if admin_secret == "ahmed552007":
        response = responses.RedirectResponse(url="/admin", status_code=303)
        response.set_cookie(key="admin_auth", value="true", path="/", httponly=True)
        return response
    return responses.HTMLResponse("كلمة سر خاطئة")

@app.get("/admin/toggle-product/{product_id}/{action}")
async def toggle_product_status(product_id: int, action: str, db: Session = Depends(get_db)):
    prod = db.query(Product).filter(Product.id == product_id).first()
    if prod:
        if action == "close":
            prod.is_active = False
        elif action == "open":
            prod.is_active = True
        db.commit()
    return responses.RedirectResponse(url="/admin", status_code=303)

@app.post("/admin/approve/{trans_id}")
async def approve_transaction(trans_id: int, db: Session = Depends(get_db)):
    trans = db.query(Transaction).filter(Transaction.id == trans_id).first()
    if trans and trans.status == "pending":
        user = db.query(User).filter(User.id == trans.user_id).first()
        if user:
            if trans.type == "deposit":
                user.balance += trans.amount
                user.spins += 1
                distribute_referral_commission(user.id, trans.amount, db)
            trans.status = "approved"
            db.commit()
    return responses.RedirectResponse(url="/admin", status_code=303)

@app.get("/admin/users")
async def admin_users(request: Request, db: Session = Depends(get_db)):
    users = db.query(User).all()
    user_products = db.query(UserProduct).all()
    return templates.TemplateResponse("admin_users.html", {
        "request": request, 
        "users": users, 
        "user_products": user_products,
        "PLANS": PLANS
    })

# ==================== منطق عجلة الحظ ====================
@app.post("/spin-wheel")
async def spin_wheel(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.spins <= 0:
        return {"status": "error", "message": "لا تملك لفات"}
    choices = ([10] * 45) + ([20] * 45) + [30, 100, 3000, "VIP2", 30, 100]
    prize = random.choice(choices)
    user.spins -= 1
    if isinstance(prize, int):
        user.balance += prize
    elif prize == "VIP2":
        user.vip_level = 2
    db.commit()
    return {"status": "success", "prize": prize}

@app.get("/spin-wheel")
async def spin_wheel_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return responses.RedirectResponse(url="/login")
    return templates.TemplateResponse("spin.html", {"request": request, "user": user})

# ==================== نظام السحب (معدل) ====================
@app.post("/withdraw")
async def create_withdraw(
    request: Request, 
    amount: float = Form(...), 
    wallet: str = Form(...), 
    withdraw_password: str = Form(...), 
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if user.withdraw_password != withdraw_password:
        return responses.RedirectResponse(url="/withdraw?error=كلمة مرور السحب غير صحيحة", status_code=303)
    
    has_product = db.query(UserProduct).filter(UserProduct.user_id == user.id).first()
    
    if not user or not has_product:
        return responses.RedirectResponse(url="/profile?error=يجب شراء منتج واحد على الأقل للسحب", status_code=303)
    if amount < 90:
        return responses.RedirectResponse(url="/withdraw?error=الحد الأدنى للسحب هو 90 ج.م", status_code=303)
    if user.balance < amount:
        return responses.RedirectResponse(url="/withdraw?error=رصيدك غير كافٍ لإتمام عملية السحب", status_code=303)
    user.balance -= amount
    new_trans = Transaction(user_id=user.id, amount=amount, type="withdraw", status="pending", wallet=wallet)
    db.add(new_trans)
    db.commit()
    return responses.RedirectResponse(url="/profile", status_code=303)

@app.get("/withdraw")
async def withdraw_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return responses.RedirectResponse(url="/login")
    return templates.TemplateResponse("withdraw.html", {"request": request, "user": user})

# ==================== باقي المسارات ====================
@app.post("/claim-daily")
async def claim_daily(request: Request, product_id: int = Form(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user: return responses.RedirectResponse(url="/login")
    item = db.query(UserProduct).filter(UserProduct.id == product_id, UserProduct.user_id == user.id).first()
    if item:
        now = datetime.now()
        last_claim = datetime.strptime(item.last_claim_date, "%Y-%m-%d %H:%M:%S") if item.last_claim_date != "0" else None
        if not last_claim or (now - last_claim) >= timedelta(hours=24):
            daily_profit = PLANS[item.product_id]["daily"]
            user.balance += daily_profit
            item.last_claim_date = now.strftime("%Y-%m-%d %H:%M:%S")
            db.commit()
    return responses.RedirectResponse(url="/products", status_code=303)

@app.get("/")
async def home(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return responses.RedirectResponse(url="/login")
    return templates.TemplateResponse("home.html", {"request": request, "user": user})

@app.get("/deposit")
async def deposit_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return responses.RedirectResponse(url="/login")
    total_transactions = db.query(Transaction).count()
    selected_wallet = WALLETS[total_transactions % len(WALLETS)]
    return templates.TemplateResponse("deposit.html", {"request": request, "user": user, "wallet": selected_wallet})

@app.post("/deposit")
async def create_deposit(request: Request, amount: float = Form(...), transaction_id: str = Form(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        new_trans = Transaction(user_id=user.id, amount=amount, type="deposit", status="pending")
        db.add(new_trans)
        db.commit()
    return responses.RedirectResponse(url="/", status_code=303)

@app.get("/products")
async def products(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return responses.RedirectResponse(url="/login")
    
    # --- هذا هو الجزء الناقص ---
    all_products = db.query(Product).all() 
    # --------------------------

    my_products_raw = db.query(UserProduct).filter(UserProduct.user_id == user.id).all()
    products_data = []
    now = datetime.now()
    for item in my_products_raw:
        last_claim = datetime.strptime(item.last_claim_date, "%Y-%m-%d %H:%M:%S") if item.last_claim_date != "0" else None
        can_claim = True
        if last_claim and (now - last_claim) < timedelta(hours=24):
            can_claim = False
        products_data.append({"id": item.id, "product_id": item.product_id, "name": PLANS[item.product_id]["name"], "can_claim": can_claim, "last_claim": item.last_claim_date})
    
    # تأكد من تمرير products: all_products هنا
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "user": user, 
        "plans": PLANS, 
        "my_products": products_data,
        "products": all_products 
    })

@app.post("/buy-product/{product_id}")
async def buy_product(product_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or product_id not in PLANS:
        return {"status": "error"}
    
    prod_status = db.query(Product).filter(Product.id == product_id).first()
    if prod_status and not prod_status.is_active:
        return responses.RedirectResponse(url="/products?error=المنتج مغلق حالياً", status_code=303)
        
    cost = PLANS[product_id]["cost"]
    if user.balance >= cost:
        user.balance -= cost
        new_purchase = UserProduct(user_id=user.id, product_id=product_id)
        db.add(new_purchase)
        db.commit()
        return responses.RedirectResponse(url="/products", status_code=303)
    return responses.RedirectResponse(url="/products?error=رصيد غير كاف", status_code=303)

@app.get("/team")
async def team(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return responses.RedirectResponse(url="/login")
    
    # --- إضافة جديدة ---
    referral_link = f"{request.base_url}register?ref={user.referral_code}"
    # ------------------
    
    team_members = db.query(User).filter(User.referrer_id == user.id).all()
    team_size = len(team_members)
    total_commission = user.total_earned 
    
    return templates.TemplateResponse("team.html", {
        "request": request, 
        "user": user, 
        "team_size": team_size,
        "total_commission": total_commission,
        "referral_link": referral_link # --- إضافة جديدة ---
    })

@app.get("/profile")
async def profile(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return responses.RedirectResponse(url="/login")
    user_transactions = db.query(Transaction).filter(Transaction.user_id == user.id).order_by(Transaction.created_at.desc()).all()
    my_products = db.query(UserProduct).filter(UserProduct.user_id == user.id).all()
    products_info = [{"name": PLANS[p.product_id]["name"]} for p in my_products]

    return templates.TemplateResponse("profile.html", {
        "request": request, 
        "user": user, 
        "my_products": products_info,
        "transactions": user_transactions 
    })

@app.get("/register")
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register/")
async def register(request: Request, phone: str = Form(...), password: str = Form(...), invite_code: int = Form(None), db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.phone == phone).first()
    if existing_user:
        return templates.TemplateResponse("register.html", {"request": request, "error": "رقم الهاتف مسجل بالفعل!"})
    new_user = User(phone=phone, password=password, referrer_id=invite_code, spins=1)
    db.add(new_user)
    db.commit()
    # --- إضافة جديدة ---
    new_user.referral_code = str(new_user.id + 1000)
    db.commit()
    # ------------------
    return responses.RedirectResponse(url="/login", status_code=303)

@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login/")
async def login(request: Request, phone: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == phone, User.password == password).first()
    if user:
        response = responses.RedirectResponse(url="/", status_code=303)
        response.set_cookie(key="user_id", value=str(user.id))
        return response
    return templates.TemplateResponse("login.html", {"request": request, "error": "بيانات الدخول خطأ"})

@app.post("/buy-vip/{level}")
async def buy_vip(level: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user and user.balance >= PLANS[level]["cost"]:
        user.balance -= PLANS[level]["cost"]
        user.vip_level = level
        user.start_date = datetime.now().strftime("%Y-%m-%d")
        db.commit()
    return responses.RedirectResponse(url="/products", status_code=303)

@app.get("/logout")
async def logout():
    response = responses.RedirectResponse(url="/login")
    response.delete_cookie("user_id")
    response.delete_cookie("admin_auth")
    return response
