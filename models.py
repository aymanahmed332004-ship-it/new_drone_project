from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from database import Base

class User(Base):
    __tablename__ = "users"

    # المعرف الفريد للمستخدم
    id = Column(Integer, primary_key=True, index=True)

    # بيانات تسجيل الدخول
    phone = Column(String, unique=True, index=True)
    password = Column(String)
    
    # حقل كلمة مرور السحب الجديد
    withdraw_password = Column(String, default="")

    # الرصيد المالي
    balance = Column(Float, default=0.0)

    # مستوى الـ VIP الحالي (من 0 إلى 7)
    vip_level = Column(Integer, default=0)

    # إجمالي الأرباح المحققة
    total_earned = Column(Float, default=0.0)

    # لتخزين تاريخ آخر عملية استلام أرباح (كـ نص كما كان سابقاً)
    last_claim_date = Column(String, default="0")
    
    # حقل جديد لتخزين الوقت بدقة (كما طلبت)
    last_claim_time = Column(DateTime, nullable=True)
    
    # لتخزين تاريخ شراء الباقة (لحساب الـ 60 يوم)
    start_date = Column(String, default="0")

    # حقل جديد لتخزين معرف الشخص الذي دعاه (لعمل نظام العمولات)
    referrer_id = Column(Integer, nullable=True)

    # حقل جديد خاص بعجلة الحظ (عدد اللفات المتاحة)
    spins = Column(Integer, default=0)

# جدول العمليات المالية (إيداع وسحب)
class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer) # معرف المستخدم صاحب العملية
    amount = Column(Float)    # مبلغ العملية
    type = Column(String)     # "deposit" أو "withdraw"
    status = Column(String, default="pending") # الحالة: "pending" أو "approved"
    
    # حقل رقم المحفظة (مهم جداً لنظام السحب)
    wallet = Column(String, default="0")

# جدول المنتجات للتحكم في ظهورها وإمكانية شرائها
class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    price = Column(Float)
    image = Column(String)
    
    # حقل التحكم في حالة المنتج (True = متاح للشراء، False = مقفول)
    is_active = Column(Boolean, default=True)
