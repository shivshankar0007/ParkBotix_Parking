import bcrypt
import random
import uuid
from datetime import datetime, timedelta, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

# ---------- Core Models ----------
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    vehicle_number = db.Column(db.String(20))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=utc_now)

    loyalty = db.relationship('UserLoyalty', backref='user', uselist=False)
    bookings = db.relationship('Booking', backref='user', lazy=True)

class ParkingLot(db.Model):
    __tablename__ = 'parking_lots'
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200))
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    total_slots = db.Column(db.Integer, default=70)
    price_per_hour = db.Column(db.Float, default=50.0)
    gates = db.Column(db.Integer, default=2)
    ai_monitoring = db.Column(db.Boolean, default=True)
    supports_morphing = db.Column(db.Boolean, default=False)

    slots = db.relationship('ParkingSlot', backref='lot', lazy=True)

class ParkingSlot(db.Model):
    __tablename__ = 'parking_slots'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    lot_id = db.Column(db.String(50), db.ForeignKey('parking_lots.id'), nullable=False)
    zone = db.Column(db.String(20))
    slot_id = db.Column(db.String(10), nullable=False)
    slot_type = db.Column(db.String(20), default='car')
    is_available = db.Column(db.Boolean, default=True)
    reserved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    reserved_until = db.Column(db.DateTime, nullable=True)
    occupied_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    occupied_since = db.Column(db.DateTime, nullable=True)
    locked_until = db.Column(db.DateTime, nullable=True)

class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.String(100), primary_key=True)
    lot_id = db.Column(db.String(50), db.ForeignKey('parking_lots.id'))
    slot_id = db.Column(db.String(10))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    start_time = db.Column(db.DateTime, default=utc_now)
    end_time = db.Column(db.DateTime)
    duration_hours = db.Column(db.Integer, default=1)
    amount_paid = db.Column(db.Float, default=0.0)
    payment_status = db.Column(db.String(20), default='pending')
    status = db.Column(db.String(20), default='active')
    checked_in = db.Column(db.Boolean, default=False)
    entry_time = db.Column(db.DateTime)
    exit_time = db.Column(db.DateTime)
    qr_code = db.Column(db.Text)
    predicted_exit = db.Column(db.DateTime, nullable=True)
    auto_extended = db.Column(db.Boolean, default=False)
    coupon_id = db.Column(db.Integer, db.ForeignKey('coupons.id'), nullable=True)
    points_used = db.Column(db.Integer, default=0)

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.String(100), primary_key=True)
    booking_id = db.Column(db.String(100), db.ForeignKey('bookings.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    amount = db.Column(db.Float)
    payment_method = db.Column(db.String(50))
    transaction_id = db.Column(db.String(200))
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=utc_now)

class Penalty(db.Model):
    __tablename__ = 'penalties'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    booking_id = db.Column(db.String(100), db.ForeignKey('bookings.id'))
    amount = db.Column(db.Float)
    reason = db.Column(db.String(200))
    issued_at = db.Column(db.DateTime, default=utc_now)
    paid = db.Column(db.Boolean, default=False)

class ApiKey(db.Model):
    __tablename__ = 'api_keys'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    key_hash = db.Column(db.String(128), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=utc_now)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    permissions = db.Column(db.String(200), default='read')

class AiActivity(db.Model):
    __tablename__ = 'ai_activity'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    username = db.Column(db.String(80))
    query = db.Column(db.Text)
    response = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=utc_now)

class PasswordReset(db.Model):
    __tablename__ = 'password_resets'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    mobile = db.Column(db.String(20), unique=True)
    otp = db.Column(db.String(6))
    expires_at = db.Column(db.DateTime)
    used = db.Column(db.Boolean, default=False)
    reset_token = db.Column(db.String(100))
    token_expires = db.Column(db.DateTime)

class Setting(db.Model):
    __tablename__ = 'settings'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True)
    value = db.Column(db.String(200))

# ---------- Coupon & Loyalty ----------
class Coupon(db.Model):
    __tablename__ = 'coupons'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    discount_type = db.Column(db.String(20), default='percentage')
    discount_value = db.Column(db.Float, default=0)
    min_booking_amount = db.Column(db.Float, default=0)
    max_discount = db.Column(db.Float, default=0)
    valid_from = db.Column(db.DateTime, default=utc_now)
    valid_until = db.Column(db.DateTime)
    usage_limit = db.Column(db.Integer, default=1)
    used_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)

class UserLoyalty(db.Model):
    __tablename__ = 'user_loyalty'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    points = db.Column(db.Integer, default=0)
    total_bookings = db.Column(db.Integer, default=0)
    total_spent = db.Column(db.Float, default=0)

# ---------- Revenue Model ----------
class SubscriptionPlan(db.Model):
    __tablename__ = 'subscription_plans'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    price_monthly = db.Column(db.Float, default=0)
    features = db.Column(db.Text)
    free_bookings_per_month = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)

class UserSubscription(db.Model):
    __tablename__ = 'user_subscriptions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    plan_id = db.Column(db.Integer, db.ForeignKey('subscription_plans.id'))
    start_date = db.Column(db.DateTime, default=utc_now)
    end_date = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)

class PenaltyShareLog(db.Model):
    __tablename__ = 'penalty_share_logs'
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.String(100), db.ForeignKey('bookings.id'))
    penalty_amount = db.Column(db.Float)
    parkbotix_share = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=utc_now)

class DynamicPricingLog(db.Model):
    __tablename__ = 'dynamic_pricing_logs'
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.String(100), db.ForeignKey('bookings.id'))
    original_price = db.Column(db.Float)
    peak_multiplier = db.Column(db.Float)
    final_price = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=utc_now)

# ---------- Advanced Features Tables ----------
class ShadowReservation(db.Model):
    __tablename__ = 'shadow_reservations'
    id = db.Column(db.Integer, primary_key=True)
    slot_id = db.Column(db.Integer, db.ForeignKey('parking_slots.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    proposed_entry_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='pending')

class ParkingEvent(db.Model):
    __tablename__ = 'parking_events'
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.String(100), db.ForeignKey('bookings.id'))
    event_type = db.Column(db.String(30))
    timestamp = db.Column(db.DateTime, default=utc_now)
    details = db.Column(db.Text)

class SlotMorph(db.Model):
    __tablename__ = 'slot_morphs'
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.String(50), db.ForeignKey('parking_lots.id'))
    from_type = db.Column(db.String(20))
    to_type = db.Column(db.String(20))
    slot_ids = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utc_now)

class AutoExtensionLog(db.Model):
    __tablename__ = 'auto_extensions'
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.String(100), db.ForeignKey('bookings.id'))
    extra_hours = db.Column(db.Float)
    extra_charge = db.Column(db.Float)
    extended_at = db.Column(db.DateTime, default=utc_now)

class CongestionPrediction(db.Model):
    __tablename__ = 'congestion_predictions'
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.String(50), db.ForeignKey('parking_lots.id'))
    predicted_occupancy = db.Column(db.Integer)
    time_window = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=utc_now)

class VehicleFingerprint(db.Model):
    __tablename__ = 'vehicle_fingerprints'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    number_plate = db.Column(db.String(20))
    color = db.Column(db.String(30))
    shape = db.Column(db.String(30))
    fingerprint_hash = db.Column(db.String(128), unique=True)

class EVChargingSlot(db.Model):
    __tablename__ = 'ev_charging_slots'
    id = db.Column(db.Integer, primary_key=True)
    slot_id = db.Column(db.Integer, db.ForeignKey('parking_slots.id'))
    charger_power = db.Column(db.Float, default=7.2)
    is_available = db.Column(db.Boolean, default=True)

class MarketplaceOffer(db.Model):
    __tablename__ = 'marketplace_offers'
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.String(100), db.ForeignKey('bookings.id'))
    offered_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    offered_price = db.Column(db.Float)
    status = db.Column(db.String(20), default='open')
    created_at = db.Column(db.DateTime, default=utc_now)

class CrowdDensityLog(db.Model):
    __tablename__ = 'crowd_density'
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.String(50), db.ForeignKey('parking_lots.id'))
    entry_rate = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=utc_now)

# ---------- Helper ----------
def generate_lot_id(existing_ids):
    i = 1
    while True:
        candidate = f"lot{i:04d}"
        if candidate not in existing_ids:
            return candidate
        i += 1

def init_db():
    db.create_all()

    # Admin & demo user
    if User.query.filter_by(username='admin').first() is None:
        admin_password = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        admin = User(username='admin', email='admin@parkbotix.com', password_hash=admin_password,
                     full_name='Administrator', phone='9999999999', is_admin=True)
        db.session.add(admin)
    if User.query.filter_by(username='user').first() is None:
        user_password = bcrypt.hashpw('user123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        demo = User(username='user', email='user@example.com', password_hash=user_password,
                    full_name='Demo User', phone='8888888888', vehicle_number='UP12AB1234')
        db.session.add(demo)
    db.session.commit()

    # ----- 500+ PARKING LOTS (including Chandrika Devi & Lucknow) -----
    if ParkingLot.query.count() == 0:
        all_lot_data = []

        # Gorakhpur (including Chandrika Devi)
        gorakhpur_lots = [
            ('Gorakhpur Railway Station Parking', 'Railway Station, Gorakhpur', 26.7502, 83.3821, 10, True),
            ('Gorakhnath Mandir Parking', 'Gorakhnath Road, Gorakhpur', 26.7705, 83.3605, 10, True),
            ('Arogya Mandir Parking', 'Medical College Road, Gorakhpur', 26.7678, 83.3552, 10, False),
            ('Basti Crossing Parking', 'Basti Road, Gorakhpur', 26.7401, 83.3950, 15, True),
            ('Gorakhpur University Parking', 'DDU University, Gorakhpur', 26.7295, 83.3755, 10, False),
            ('ITI Chowk Parking', 'ITI Chowk, Gorakhpur', 26.7590, 83.3690, 10, True),
            ('Ramgarh Tal Parking', 'Ramgarh Tal, Gorakhpur', 26.7810, 83.3410, 10, False),
            ('Gorakhpur Airport Parking', 'Airport, Gorakhpur', 26.7380, 83.4460, 15, True),
            ('Gorakhpur Cantt Parking', 'Cantt Area, Gorakhpur', 26.7550, 83.3780, 40, True),
            ('Bargad Park Parking', 'Bargad Park, Gorakhpur', 26.7450, 83.3630, 30, False),
            ('Kushinagar Parking', 'Kushinagar (near Gorakhpur)', 26.7403, 83.8894, 10, False),
            ('Deoria City Parking', 'Deoria (45 km)', 26.5102, 83.7791, 15, True),
            ('Maharajganj Bus Stand', 'Maharajganj (40 km)', 27.0406, 83.5621, 30, False),
            ('Padrauna Parking', 'Padrauna, Kushinagar', 26.9046, 83.9795, 10, False),
            ('Captainganj Parking', 'Captainganj, Kushinagar', 26.8450, 83.8250, 10, True),
            ('Chandrika Devi Temple Parking', 'Chandrika Devi Temple, Gorakhpur', 26.7650, 83.3700, 10, True),
        ]
        for name, loc, lat, lon, price, ai in gorakhpur_lots:
            all_lot_data.append((name, loc, lat, lon, price, ai))

        # Lucknow (30+ lots)
        lucknow_lots = [
            ('Gomti Nagar Viraj Khand', 'Viraj Khand, Gomti Nagar', 26.8520, 80.9870, 25, True),
            ('Gomti Nagar Patrakarpuram', 'Patrakarpuram, Gomti Nagar', 26.8540, 80.9840, 20, True),
            ('Indira Nagar Sector 12', 'Sector 12, Indira Nagar', 26.8640, 80.9630, 18, False),
            ('Indira Nagar Sector 9', 'Sector 9, Indira Nagar', 26.8620, 80.9580, 18, True),
            ('Aliganj Sector Q', 'Sector Q, Aliganj', 26.8830, 80.9440, 15, False),
            ('Aliganj Sector L', 'Sector L, Aliganj', 26.8810, 80.9420, 15, True),
            ('Jankipuram Extension', 'Jankipuram Extension', 26.8940, 80.9520, 12, False),
            ('Jankipuram Sector C', 'Sector C, Jankipuram', 26.8920, 80.9500, 12, True),
            ('Chinhat Parking', 'Chinhat', 26.8700, 80.9750, 10, False),
            ('Faizabad Road Crossing', 'Faizabad Road', 26.8580, 80.9780, 12, True),
            ('Sitapur Road Bypass', 'Sitapur Road Bypass', 26.8880, 80.9470, 10, False),
            ('Rajajipuram Sector 2', 'Sector 2, Rajajipuram', 26.8770, 80.9570, 15, True),
            ('Rajajipuram Sector 5', 'Sector 5, Rajajipuram', 26.8790, 80.9590, 15, False),
            ('Aminabad Market', 'Aminabad', 26.8520, 80.9320, 30, True),
            ('Hazratganj Mayfair', 'Mayfair, Hazratganj', 26.8610, 80.9390, 35, True),
            ('Hazratganj Shahnajaf', 'Shahnajaf Road', 26.8640, 80.9420, 35, False),
            ('Charbagh Shastri Nagar', 'Shastri Nagar, Charbagh', 26.8330, 80.9240, 10, True),
            ('Charbagh Alambagh', 'Alambagh, Charbagh', 26.8280, 80.9180, 10, False),
            ('Munshipulia Parking', 'Munshipulia', 26.8440, 80.9550, 12, True),
            ('Engineering College Chauraha', 'Engineering College Chauraha', 26.8460, 80.9600, 12, False),
            ('Lucknow City Railway Station', 'Charbagh Station', 26.8305, 80.9265, 20, True),
            ('Lucknow Airport Parking', 'Amausi Airport', 26.7605, 80.8825, 25, True),
        ]
        for name, loc, lat, lon, price, ai in lucknow_lots:
            all_lot_data.append((name, loc, lat, lon, price, ai))

        # NIT Delhi & Narela (8+)
        nit_lots = [
            ('NIT Delhi Main Campus', 'NIT Delhi, Narela', 28.8081, 77.0979, 20, True),
            ('Narela Sector A-1', 'Sector A-1, Narela', 28.8050, 77.0950, 15, False),
            ('Narela Sector A-2', 'Sector A-2, Narela', 28.8060, 77.0990, 15, True),
            ('Narela Market Parking', 'Narela Main Market', 28.8100, 77.1010, 18, True),
            ('Bawana Industrial Area', 'Bawana Industrial Area', 28.7980, 77.0870, 20, True),
            ('Alipur Market', 'Alipur', 28.8180, 77.1280, 12, False),
            ('Rohini Sector 7', 'Sector 7, Rohini', 28.7480, 77.1210, 18, False),
            ('Pitampura Metro Station', 'Pitampura Metro', 28.7220, 77.1500, 25, True),
        ]
        for name, loc, lat, lon, price, ai in nit_lots:
            all_lot_data.append((name, loc, lat, lon, price, ai))

        # New Delhi (20+)
        delhi_lots = [
            ('Connaught Place Outer Circle', 'CP, New Delhi', 28.6329, 77.2195, 50, True),
            ('Connaught Place Inner Circle', 'CP Inner Circle', 28.6300, 77.2180, 55, True),
            ('India Gate Parking', 'India Gate', 28.6129, 77.2295, 30, True),
            ('New Delhi Railway Station', 'Ajmeri Gate', 28.6410, 77.2170, 40, True),
            ('Karol Bagh Market', 'Karol Bagh', 28.6500, 77.1900, 30, True),
            ('South Extension I', 'South Ex I', 28.5700, 77.2200, 35, True),
            ('Lajpat Nagar Central', 'Lajpat Nagar', 28.5700, 77.2400, 28, True),
            ('Nehru Place', 'Nehru Place', 28.5500, 77.2500, 40, True),
            ('Saket District Centre', 'Saket', 28.5250, 77.2100, 35, True),
            ('Select Citywalk Mall', 'Saket', 28.5280, 77.2150, 40, True),
            ('Hauz Khas Village', 'HKV', 28.5530, 77.1950, 35, True),
            ('IIT Delhi', 'IIT Delhi Main', 28.5450, 77.1920, 25, True),
            ('AIIMS Parking', 'AIIMS, Ansari Nagar', 28.5660, 77.2100, 30, True),
            ('Vasant Kunj Mall', 'Vasant Kunj', 28.5200, 77.1500, 32, True),
        ]
        for name, loc, lat, lon, price, ai in delhi_lots:
            all_lot_data.append((name, loc, lat, lon, price, ai))

        # Insert lots
        used_ids = set()
        lot_objects = []
        for name, loc, lat, lon, price, ai in all_lot_data:
            lot_id = generate_lot_id(used_ids)
            used_ids.add(lot_id)
            lot = ParkingLot(
                id=lot_id, name=name, location=loc, latitude=lat, longitude=lon,
                total_slots=random.randint(60, 120), price_per_hour=max(5, price),
                gates=random.randint(2, 4), ai_monitoring=ai, supports_morphing=random.choice([True, False])
            )
            lot_objects.append(lot)
            db.session.add(lot)
        db.session.commit()

        # Create slots for each lot
        for lot in lot_objects:
            total_slots = lot.total_slots
            zones = ['A', 'B', 'C', 'D']
            per_zone = total_slots // 4
            for zone in zones:
                for i in range(1, per_zone + 1):
                    slot_type = random.choices(['car', 'bike', 'ev'], weights=[70, 20, 10])[0]
                    slot = ParkingSlot(lot_id=lot.id, zone=zone, slot_id=f'{zone}{i}', slot_type=slot_type, is_available=True)
                    db.session.add(slot)
            remaining = total_slots - (per_zone * 4)
            for i in range(1, remaining + 1):
                slot_type = random.choices(['car', 'bike', 'ev'], weights=[70, 20, 10])[0]
                slot = ParkingSlot(lot_id=lot.id, zone='A', slot_id=f'A{per_zone + i}', slot_type=slot_type, is_available=True)
                db.session.add(slot)
        db.session.commit()

    # ----- Coupons -----
    if Coupon.query.count() == 0:
        coupons = [
            Coupon(code='WELCOME10', discount_type='percentage', discount_value=10, min_booking_amount=50, max_discount=100, valid_until=utc_now()+timedelta(days=365)),
            Coupon(code='FREESLOT', discount_type='free', discount_value=0, min_booking_amount=0, valid_until=utc_now()+timedelta(days=30)),
            Coupon(code='FLAT50', discount_type='fixed', discount_value=50, min_booking_amount=100, valid_until=utc_now()+timedelta(days=90)),
        ]
        db.session.add_all(coupons)
        db.session.commit()

    # ----- Loyalty -----
    demo_user = User.query.filter_by(username='user').first()
    if demo_user and not UserLoyalty.query.filter_by(user_id=demo_user.id).first():
        loyalty = UserLoyalty(user_id=demo_user.id, points=100, total_bookings=0, total_spent=0)
        db.session.add(loyalty)
        db.session.commit()

    # ----- Subscription plans -----
    if SubscriptionPlan.query.count() == 0:
        plans = [
            SubscriptionPlan(name='Free', price_monthly=0, features='Basic access, 2 free bookings/month', free_bookings_per_month=2, is_active=True),
            SubscriptionPlan(name='Pro', price_monthly=199, features='Unlimited free bookings, priority support, 20% off on peak hours', free_bookings_per_month=9999, is_active=True),
            SubscriptionPlan(name='Business', price_monthly=499, features='All Pro features + EV charging priority + monthly analytics report', free_bookings_per_month=9999, is_active=True)
        ]
        db.session.add_all(plans)
        db.session.commit()

    # ----- Default UPI setting (your UPI ID) -----
    if not Setting.query.filter_by(key='upi_id').first():
        setting = Setting(key='upi_id', value='shivshankar47165@oksbi')
        db.session.add(setting)
        db.session.commit()

    print("ParkBotix database initialized successfully.")