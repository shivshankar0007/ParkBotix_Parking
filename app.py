import os
import uuid
import bcrypt
import qrcode
import base64
import google.generativeai as genai
import random
import threading
import time
import json
<<<<<<< HEAD
import traceback
from io import BytesIO
from datetime import datetime, timedelta, timezone
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from sqlalchemy import or_, and_
from models import db, User, ParkingLot, ParkingSlot, Booking, Payment, Penalty, ApiKey, AiActivity, PasswordReset, Setting, init_db
from models import ShadowReservation, ParkingEvent, SlotMorph, AutoExtensionLog, CongestionPrediction, VehicleFingerprint, EVChargingSlot, MarketplaceOffer, CrowdDensityLog, Coupon, UserLoyalty, SubscriptionPlan, UserSubscription, PenaltyShareLog, DynamicPricingLog
=======
from io import BytesIO
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from sqlalchemy import or_, and_
from models import db, User, ParkingLot, ParkingSlot, Booking, Payment, Penalty, ApiKey, AiActivity, PasswordReset, Setting, init_db
from models import ShadowReservation, ParkingEvent, SlotMorph, AutoExtensionLog, CongestionPrediction, VehicleFingerprint, EVChargingSlot, MarketplaceOffer, CrowdDensityLog, Coupon, UserLoyalty
>>>>>>> 7ebede44f5c73607d3c179bd817ed9f9cc955866
from functools import wraps
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'parkbotix-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parkbotix.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

<<<<<<< HEAD
# Configure Gemini
genai.configure(api_key='AIzaSyBgkgGG37691boomMAwdEzHVYvXqfA_wjM')

# ---------- Helper: naive UTC datetime (no timezone) ----------
def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)
=======
# Configure Gemini (optional – fallback if key missing)
try:
    genai.configure(api_key=os.environ.get('GEMINI_API_KEY', 'AIzaSyBgkgGG37691boomMAwdEzHVYvXqfA_wjM'))
except:
    print("Warning: Gemini API key not configured. AI features will use fallback logic.")
>>>>>>> 7ebede44f5c73607d3c179bd817ed9f9cc955866

# ---------- Helper Functions ----------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            return jsonify({'error': 'Admin required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def calculate_distance(lat1, lon1, lat2, lon2):
    from math import radians, sin, cos, sqrt, atan2
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

def generate_qr(data):
    img = qrcode.make(data)
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def generate_otp():
    return str(random.randint(100000, 999999))

def log_event(booking_id, event_type, details=''):
<<<<<<< HEAD
    try:
        event = ParkingEvent(booking_id=booking_id, event_type=event_type, details=details)
        db.session.add(event)
        db.session.commit()
    except:
        pass

# ---------- Background Thread ----------
def auto_extension_worker():
    with app.app_context():
        while True:
            try:
                now = utc_now()
                soon_end = Booking.query.filter(Booking.end_time <= now + timedelta(minutes=15),
                                                Booking.end_time > now,
                                                Booking.status == 'active',
                                                Booking.checked_in == True).all()
                for booking in soon_end:
                    next_booking = Booking.query.filter(Booking.lot_id == booking.lot_id,
                                                        Booking.slot_id == booking.slot_id,
                                                        Booking.start_time > now,
                                                        Booking.start_time < now + timedelta(hours=1)).first()
                    if not next_booking:
                        new_end = booking.end_time + timedelta(minutes=30)
                        extra_hours = 0.5
                        extra_charge = ParkingLot.query.get(booking.lot_id).price_per_hour * extra_hours
                        booking.end_time = new_end
                        booking.duration_hours += extra_hours
                        booking.amount_paid += extra_charge
                        booking.auto_extended = True
                        log = AutoExtensionLog(booking_id=booking.id, extra_hours=extra_hours, extra_charge=extra_charge)
                        db.session.add(log)
                        db.session.commit()
                        log_event(booking.id, 'EXTEND', f'Auto-extended by 30 min')
            except Exception as e:
                print(f"auto_extension_worker error: {e}")
            time.sleep(60)

threading.Thread(target=auto_extension_worker, daemon=True).start()
=======
    event = ParkingEvent(booking_id=booking_id, event_type=event_type, details=details)
    db.session.add(event)
    db.session.commit()

# ---------- Background Thread to Activate Future Reservations ----------
def activate_future_reservations():
    """Every minute, check for future bookings whose start_time has arrived and activate them."""
    with app.app_context():
        while True:
            now = datetime.utcnow()
            future_bookings = Booking.query.filter(
                Booking.start_time <= now,
                Booking.status == 'active',
                Booking.checked_in == False,
                Booking.payment_status == 'completed'
            ).all()
            for booking in future_bookings:
                slot = ParkingSlot.query.filter_by(lot_id=booking.lot_id, slot_id=booking.slot_id).first()
                if slot and slot.future_reserved_by and slot.future_reserved_until and slot.future_reserved_until <= now:
                    slot.is_available = False
                    slot.reserved_by = booking.user_id
                    slot.reserved_until = now + timedelta(minutes=15)
                    slot.locked_until = booking.end_time + timedelta(hours=1)
                    slot.future_reserved_by = None
                    slot.future_reserved_until = None
                    db.session.commit()
                    log_event(booking.id, 'ACTIVATE', 'Future reservation activated')
                    print(f"✅ Activated future reservation for booking {booking.id}")
            time.sleep(60)

# Start background thread
threading.Thread(target=activate_future_reservations, daemon=True).start()
>>>>>>> 7ebede44f5c73607d3c179bd817ed9f9cc955866

# ---------- Routes ----------
@app.route('/')
def home():
    return redirect('/dashboard')

@app.route('/dashboard')
def dashboard():
    return render_template('index.html')

@app.route('/profile')
def profile():
    return render_template('profile.html')

@app.route('/admin')
@login_required
def admin_panel():
    user = User.query.get(session['user_id'])
    if not user or not user.is_admin:
        return redirect('/dashboard')
    return render_template('admin.html')

@app.route('/admin/advanced')
@admin_required
def admin_advanced():
    return render_template('admin_advanced.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/forgot-password')
def forgot_password_page():
    return render_template('forgot_password.html')

<<<<<<< HEAD
# ---------- Authentication ----------
@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
        if not all(k in data for k in ('username', 'email', 'password')):
            return jsonify({'error': 'Missing fields'}), 400
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username exists'}), 400
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email exists'}), 400
        if '@' not in data['email'] or '.' not in data['email']:
            return jsonify({'error': 'Invalid email'}), 400
        if data.get('phone') and not data['phone'].isdigit():
            return jsonify({'error': 'Phone digits only'}), 400

        # ---------- ADMIN CREDENTIALS ----------
        # Anyone with these email, phone, or username becomes admin
        admin_emails = ['shivshankar47165@gmail.com']
        admin_phones = ['8382015045']
        admin_usernames = ['admin12345']

        is_admin = False
        if (data['email'] in admin_emails or 
            data.get('phone') in admin_phones or 
            data['username'] in admin_usernames):
            is_admin = True
        # ----------------------------------------

        password_hash = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user = User(
            username=data['username'],
            email=data['email'],
            password_hash=password_hash,
            full_name=data.get('full_name', ''),
            phone=data.get('phone', ''),
            vehicle_number=data.get('vehicle_number', ''),
            is_admin=is_admin
        )
        db.session.add(user)
        db.session.commit()
        loyalty = UserLoyalty(user_id=user.id, points=0)
        db.session.add(loyalty)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        user = User.query.filter_by(username=data['username']).first()
        if not user or not bcrypt.checkpw(data['password'].encode('utf-8'), user.password_hash.encode('utf-8')):
            return jsonify({'error': 'Invalid credentials'}), 401
        session['user_id'] = user.id
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
=======
# ---------- Authentication API ----------
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    if not all(k in data for k in ('username', 'email', 'password')):
        return jsonify({'error': 'Missing fields'}), 400
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username exists'}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email exists'}), 400
    if '@' not in data['email'] or '.' not in data['email']:
        return jsonify({'error': 'Invalid email'}), 400
    if data.get('phone') and not data['phone'].isdigit():
        return jsonify({'error': 'Phone digits only'}), 400
    password_hash = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user = User(username=data['username'], email=data['email'], password_hash=password_hash,
                full_name=data.get('full_name', ''), phone=data.get('phone', ''),
                vehicle_number=data.get('vehicle_number', ''))
    db.session.add(user)
    db.session.commit()
    loyalty = UserLoyalty(user_id=user.id, points=0)
    db.session.add(loyalty)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    if not user or not bcrypt.checkpw(data['password'].encode('utf-8'), user.password_hash.encode('utf-8')):
        return jsonify({'error': 'Invalid credentials'}), 401
    session['user_id'] = user.id
    return jsonify({'success': True})
>>>>>>> 7ebede44f5c73607d3c179bd817ed9f9cc955866

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'success': True})

@app.route('/api/me')
@login_required
def me():
<<<<<<< HEAD
    try:
        user = User.query.get(session['user_id'])
        return jsonify({'authenticated': True, 'user': {
            'id': user.id, 'username': user.username, 'email': user.email,
            'full_name': user.full_name or '', 'phone': user.phone or '',
            'vehicle_number': user.vehicle_number or '', 'is_admin': user.is_admin,
            'created_at': user.created_at.isoformat() if user.created_at else None
        }})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
=======
    user = User.query.get(session['user_id'])
    return jsonify({'authenticated': True, 'user': {
        'id': user.id, 'username': user.username, 'email': user.email,
        'full_name': user.full_name or '', 'phone': user.phone or '',
        'vehicle_number': user.vehicle_number or '', 'is_admin': user.is_admin,
        'created_at': user.created_at.isoformat() if user.created_at else None
    }})
>>>>>>> 7ebede44f5c73607d3c179bd817ed9f9cc955866

# ---------- Forgot Password ----------
@app.route('/api/forgot-password', methods=['POST'])
def forgot_password():
<<<<<<< HEAD
    try:
        data = request.json
        mobile = data.get('mobile')
        if not mobile:
            return jsonify({'error': 'Mobile required'}), 400
        user = User.query.filter_by(phone=mobile).first()
        if not user:
            return jsonify({'error': 'No account found'}), 404
        otp = generate_otp()
        expiry = utc_now() + timedelta(minutes=5)
        reset = PasswordReset.query.filter_by(mobile=mobile).first()
        if reset:
            reset.otp = otp
            reset.expires_at = expiry
            reset.used = False
        else:
            reset = PasswordReset(mobile=mobile, otp=otp, expires_at=expiry)
            db.session.add(reset)
        db.session.commit()
        print(f"OTP for {mobile}: {otp}")
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    try:
        data = request.json
        mobile, otp = data.get('mobile'), data.get('otp')
        if not mobile or not otp:
            return jsonify({'error': 'Mobile and OTP required'}), 400
        reset = PasswordReset.query.filter_by(mobile=mobile).first()
        if not reset or reset.used or reset.otp != otp or utc_now() > reset.expires_at:
            return jsonify({'error': 'Invalid or expired OTP'}), 400
        reset.used = True
        reset_token = str(uuid.uuid4())
        reset.reset_token = reset_token
        reset.token_expires = utc_now() + timedelta(minutes=30)
        db.session.commit()
        return jsonify({'success': True, 'reset_token': reset_token})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    try:
        data = request.json
        reset_token = data.get('reset_token')
        new_password = data.get('new_password')
        if not reset_token or not new_password:
            return jsonify({'error': 'Missing data'}), 400
        reset = PasswordReset.query.filter_by(reset_token=reset_token).first()
        if not reset or utc_now() > reset.token_expires:
            return jsonify({'error': 'Invalid token'}), 400
        user = User.query.filter_by(phone=reset.mobile).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        user.password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        db.session.delete(reset)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ---------- Parking & Booking ----------
@app.route('/api/nearby_lots', methods=['POST'])
@login_required
def nearby_lots():
    try:
        data = request.json
        lat, lon = data.get('lat'), data.get('lon')
        radius = data.get('radius', 10)
        if lat is None or lon is None:
            return jsonify({'error': 'Missing coordinates'}), 400
        lots = ParkingLot.query.all()
        nearby = []
        for lot in lots:
            dist = calculate_distance(lat, lon, lot.latitude, lot.longitude)
            if dist <= radius:
                total_slots = ParkingSlot.query.filter_by(lot_id=lot.id).count()
                available_slots = ParkingSlot.query.filter_by(lot_id=lot.id, is_available=True).count()
                nearby.append({
                    'lot_id': lot.id, 'name': lot.name, 'location': lot.location or '',
                    'latitude': lot.latitude, 'longitude': lot.longitude,
                    'total_slots': total_slots, 'available_slots': available_slots,
                    'price_per_hour': lot.price_per_hour, 'gates': lot.gates,
                    'ai_monitoring': lot.ai_monitoring, 'distance_km': round(dist, 2)
                })
        return jsonify(nearby)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
=======
    data = request.json
    mobile = data.get('mobile')
    if not mobile:
        return jsonify({'error': 'Mobile required'}), 400
    user = User.query.filter_by(phone=mobile).first()
    if not user:
        return jsonify({'error': 'No account found'}), 404
    otp = generate_otp()
    expiry = datetime.utcnow() + timedelta(minutes=5)
    reset = PasswordReset.query.filter_by(mobile=mobile).first()
    if reset:
        reset.otp = otp
        reset.expires_at = expiry
        reset.used = False
    else:
        reset = PasswordReset(mobile=mobile, otp=otp, expires_at=expiry)
        db.session.add(reset)
    db.session.commit()
    print(f"OTP for {mobile}: {otp}")
    return jsonify({'success': True})

@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    data = request.json
    mobile, otp = data.get('mobile'), data.get('otp')
    if not mobile or not otp:
        return jsonify({'error': 'Mobile and OTP required'}), 400
    reset = PasswordReset.query.filter_by(mobile=mobile).first()
    if not reset or reset.used or reset.otp != otp or datetime.utcnow() > reset.expires_at:
        return jsonify({'error': 'Invalid or expired OTP'}), 400
    reset.used = True
    reset_token = str(uuid.uuid4())
    reset.reset_token = reset_token
    reset.token_expires = datetime.utcnow() + timedelta(minutes=30)
    db.session.commit()
    return jsonify({'success': True, 'reset_token': reset_token})

@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    data = request.json
    reset_token = data.get('reset_token')
    new_password = data.get('new_password')
    if not reset_token or not new_password:
        return jsonify({'error': 'Missing data'}), 400
    reset = PasswordReset.query.filter_by(reset_token=reset_token).first()
    if not reset or datetime.utcnow() > reset.token_expires:
        return jsonify({'error': 'Invalid token'}), 400
    user = User.query.filter_by(phone=reset.mobile).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    user.password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    db.session.delete(reset)
    db.session.commit()
    return jsonify({'success': True})

# ---------- Parking & Booking (core) ----------
@app.route('/api/nearby_lots', methods=['POST'])
@login_required
def nearby_lots():
    data = request.json
    lat, lon = data.get('lat'), data.get('lon')
    radius = data.get('radius', 10)
    if lat is None or lon is None:
        return jsonify({'error': 'Missing coordinates'}), 400
    lots = ParkingLot.query.all()
    nearby = []
    for lot in lots:
        dist = calculate_distance(lat, lon, lot.latitude, lot.longitude)
        if dist <= radius:
            total_slots = ParkingSlot.query.filter_by(lot_id=lot.id).count()
            available_slots = ParkingSlot.query.filter_by(lot_id=lot.id, is_available=True).count()
            nearby.append({
                'lot_id': lot.id, 'name': lot.name, 'location': lot.location or '',
                'latitude': lot.latitude, 'longitude': lot.longitude,
                'total_slots': total_slots, 'available_slots': available_slots,
                'price_per_hour': lot.price_per_hour, 'gates': lot.gates,
                'ai_monitoring': lot.ai_monitoring, 'distance_km': round(dist, 2)
            })
    return jsonify(nearby)
>>>>>>> 7ebede44f5c73607d3c179bd817ed9f9cc955866

@app.route('/api/lots/<lot_id>/slots')
@login_required
def get_slots(lot_id):
    try:
        slots = ParkingSlot.query.filter_by(lot_id=lot_id).all()
        if not slots:
            return jsonify({'error': 'No slots found for this lot'}), 404
        result = []
<<<<<<< HEAD
        now = utc_now()
        for slot in slots:
=======
        now = datetime.utcnow()
        for slot in slots:
            # Determine status: occupied > reserved (active) > future_reserved > available
>>>>>>> 7ebede44f5c73607d3c179bd817ed9f9cc955866
            if slot.occupied_by:
                status = 'occupied'
            elif slot.reserved_by and slot.reserved_until and slot.reserved_until > now:
                status = 'reserved'
<<<<<<< HEAD
=======
            elif slot.future_reserved_by and slot.future_reserved_until and slot.future_reserved_until > now:
                status = 'future_reserved'   # Shows as "Future Reserved" in UI
>>>>>>> 7ebede44f5c73607d3c179bd817ed9f9cc955866
            elif not slot.is_available:
                status = 'occupied'
            else:
                status = 'available'
            result.append({
                'slot_id': slot.slot_id,
                'zone': slot.zone or '',
                'is_available': slot.is_available,
                'status': status
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reserve', methods=['POST'])
@login_required
def reserve():
<<<<<<< HEAD
    try:
        data = request.json
        lot_id = data.get('lot_id')
        slot_id = data.get('slot_id')
        duration_hours = data.get('duration_hours', 1)
        user_id = session['user_id']
        coupon_id = data.get('coupon_id')
        points_used = data.get('points_used', 0)
        
        slot = ParkingSlot.query.filter_by(lot_id=lot_id, slot_id=slot_id).first()
        if not slot:
            return jsonify({'error': 'Slot not found'}), 404
        
        now = utc_now()
        start_time = now
        
        if not slot.is_available:
            if slot.reserved_by and slot.reserved_until and slot.reserved_until > now:
                return jsonify({'error': 'Slot already reserved'}), 400
            if slot.occupied_by:
                return jsonify({'error': 'Slot occupied'}), 400
        
        lot = ParkingLot.query.get(lot_id)
        amount = lot.price_per_hour * duration_hours
        final_amount = amount
        
        if coupon_id:
            coupon = Coupon.query.get(coupon_id)
            if coupon and coupon.is_active and (not coupon.valid_until or utc_now() <= coupon.valid_until):
                if coupon.discount_type == 'percentage':
                    discount = (coupon.discount_value / 100) * amount
                    if coupon.max_discount and discount > coupon.max_discount:
                        discount = coupon.max_discount
                    final_amount = amount - discount
                elif coupon.discount_type == 'fixed':
                    discount = coupon.discount_value
                    final_amount = max(0, amount - discount)
                elif coupon.discount_type == 'free':
                    final_amount = 0
                coupon.used_count += 1
                if coupon.usage_limit and coupon.used_count >= coupon.usage_limit:
                    coupon.is_active = False
                db.session.commit()
        
        if points_used > 0:
            points_discount = points_used * 0.5
            final_amount = max(0, final_amount - points_discount)
            loyalty = UserLoyalty.query.filter_by(user_id=user_id).first()
            if loyalty:
                loyalty.points -= points_used
                db.session.commit()
        
        booking_id = str(uuid.uuid4())
        booking = Booking(
            id=booking_id, lot_id=lot_id, slot_id=slot_id, user_id=user_id,
            start_time=start_time, end_time=start_time + timedelta(hours=duration_hours),
            duration_hours=duration_hours, amount_paid=final_amount, coupon_id=coupon_id, points_used=points_used,
            payment_status='pending'
        )
        db.session.add(booking)
        
        slot.is_available = False
        slot.reserved_by = user_id
        slot.reserved_until = now + timedelta(minutes=15)
        slot.locked_until = start_time + timedelta(hours=duration_hours) + timedelta(hours=1)
        
        db.session.commit()
        log_event(booking_id, 'BOOK', f'Reserved immediately for {duration_hours} hours, amount {final_amount}')
        return jsonify({'success': True, 'booking_id': booking_id, 'amount': final_amount})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
=======
    data = request.json
    lot_id = data.get('lot_id')
    slot_id = data.get('slot_id')
    duration_hours = data.get('duration_hours', 1)
    user_id = session['user_id']
    coupon_id = data.get('coupon_id')
    points_used = data.get('points_used', 0)
    
    slot = ParkingSlot.query.filter_by(lot_id=lot_id, slot_id=slot_id).first()
    if not slot:
        return jsonify({'error': 'Slot not found'}), 404
    
    now = datetime.utcnow()
    start_time = now  # Always book for current time (immediate booking)
    
    # Check immediate availability
    if not slot.is_available:
        if slot.reserved_by and slot.reserved_until and slot.reserved_until > now:
            return jsonify({'error': 'Slot already reserved'}), 400
        if slot.occupied_by:
            return jsonify({'error': 'Slot occupied'}), 400
        if slot.future_reserved_until and slot.future_reserved_until > now:
            return jsonify({'error': 'Slot has future reservation'}), 400
    
    lot = ParkingLot.query.get(lot_id)
    amount = lot.price_per_hour * duration_hours
    final_amount = amount
    
    # Apply coupon discount if provided
    if coupon_id:
        coupon = Coupon.query.get(coupon_id)
        if coupon and coupon.is_active and (not coupon.valid_until or datetime.utcnow() <= coupon.valid_until):
            if coupon.discount_type == 'percentage':
                discount = (coupon.discount_value / 100) * amount
                if coupon.max_discount and discount > coupon.max_discount:
                    discount = coupon.max_discount
                final_amount = amount - discount
            elif coupon.discount_type == 'fixed':
                discount = coupon.discount_value
                final_amount = max(0, amount - discount)
            elif coupon.discount_type == 'free':
                final_amount = 0
            coupon.used_count += 1
            if coupon.usage_limit and coupon.used_count >= coupon.usage_limit:
                coupon.is_active = False
            db.session.commit()
    
    # Apply points discount
    if points_used > 0:
        points_discount = points_used * 0.5
        final_amount = max(0, final_amount - points_discount)
        loyalty = UserLoyalty.query.filter_by(user_id=user_id).first()
        if loyalty:
            loyalty.points -= points_used
            db.session.commit()
    
    booking_id = str(uuid.uuid4())
    booking = Booking(
        id=booking_id, lot_id=lot_id, slot_id=slot_id, user_id=user_id,
        start_time=start_time, end_time=start_time + timedelta(hours=duration_hours),
        duration_hours=duration_hours, amount_paid=final_amount, coupon_id=coupon_id, points_used=points_used
    )
    db.session.add(booking)
    
    # Immediate booking: lock slot now
    slot.is_available = False
    slot.reserved_by = user_id
    slot.reserved_until = now + timedelta(minutes=15)
    slot.locked_until = start_time + timedelta(hours=duration_hours) + timedelta(hours=1)
    
    db.session.commit()
    log_event(booking_id, 'BOOK', f'Reserved immediately for {duration_hours} hours, amount {final_amount}')
    return jsonify({'success': True, 'booking_id': booking_id, 'amount': final_amount})
>>>>>>> 7ebede44f5c73607d3c179bd817ed9f9cc955866

@app.route('/api/payment/initiate', methods=['POST'])
@login_required
def initiate_payment():
<<<<<<< HEAD
    try:
        data = request.json
        booking_id = data.get('booking_id')
        booking = Booking.query.filter_by(id=booking_id, user_id=session['user_id']).first()
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        payment_id = str(uuid.uuid4())
        payment = Payment(id=payment_id, booking_id=booking_id, user_id=session['user_id'],
                          amount=booking.amount_paid, payment_method=data.get('payment_method', 'upi'))
        db.session.add(payment)
        db.session.commit()
        return jsonify({'payment_id': payment_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
=======
    data = request.json
    booking_id = data.get('booking_id')
    booking = Booking.query.filter_by(id=booking_id, user_id=session['user_id']).first()
    if not booking:
        return jsonify({'error': 'Booking not found'}), 404
    payment_id = str(uuid.uuid4())
    payment = Payment(id=payment_id, booking_id=booking_id, user_id=session['user_id'],
                      amount=booking.amount_paid, payment_method=data.get('payment_method', 'upi'))
    db.session.add(payment)
    db.session.commit()
    return jsonify({'payment_id': payment_id})
>>>>>>> 7ebede44f5c73607d3c179bd817ed9f9cc955866

@app.route('/api/payment/process/<payment_id>', methods=['POST'])
@login_required
def process_payment(payment_id):
<<<<<<< HEAD
    try:
        payment = Payment.query.filter_by(id=payment_id, user_id=session['user_id']).first()
        if not payment:
            return jsonify({'error': 'Payment not found'}), 404
        payment.status = 'completed'
        payment.transaction_id = str(uuid.uuid4())
        booking = Booking.query.get(payment.booking_id)
        booking.payment_status = 'completed'
        qr_data = f"ENTRY:{booking.id}:{booking.user_id}"
        qr_base64 = generate_qr(qr_data)
        booking.qr_code = qr_base64
        db.session.commit()
        log_event(booking.id, 'PAY', f'Payment completed: {payment.transaction_id}')
        return jsonify({'success': True, 'qr_code': qr_base64})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ---------- QR Entry (with payment check) ----------
@app.route('/api/entry', methods=['POST'])
def entry():
    try:
        data = request.json
        qr_data = data.get('qr_data')
        if not qr_data:
            return jsonify({'error': 'QR missing'}), 400
=======
    payment = Payment.query.filter_by(id=payment_id, user_id=session['user_id']).first()
    if not payment:
        return jsonify({'error': 'Payment not found'}), 404
    payment.status = 'completed'
    payment.transaction_id = str(uuid.uuid4())
    booking = Booking.query.get(payment.booking_id)
    booking.payment_status = 'completed'
    qr_data = f"ENTRY:{booking.id}:{booking.user_id}"
    qr_base64 = generate_qr(qr_data)
    booking.qr_code = qr_base64
    db.session.commit()
    log_event(booking.id, 'PAY', f'Payment completed: {payment.transaction_id}')
    return jsonify({'success': True, 'qr_code': qr_base64})

@app.route('/api/entry', methods=['POST'])
def entry():
    data = request.json
    qr_data = data.get('qr_data')
    if not qr_data:
        return jsonify({'error': 'QR missing'}), 400
    try:
>>>>>>> 7ebede44f5c73607d3c179bd817ed9f9cc955866
        parts = qr_data.split(':')
        if parts[0] != 'ENTRY':
            return jsonify({'error': 'Invalid QR'}), 400
        booking_id, user_id = parts[1], parts[2]
<<<<<<< HEAD
        booking = Booking.query.get(booking_id)
        if not booking or booking.user_id != int(user_id):
            return jsonify({'error': 'Invalid booking'}), 404
        
        if booking.payment_status != 'completed':
            return jsonify({'error': 'Payment not completed. Please complete payment first.'}), 402
        
        if booking.status != 'active' or booking.checked_in:
            return jsonify({'error': 'Booking not active or already checked in'}), 400
        
        now = utc_now()
        if now < booking.start_time:
            return jsonify({'error': 'Booking start time not yet reached'}), 400
        
        slot = ParkingSlot.query.filter_by(lot_id=booking.lot_id, slot_id=booking.slot_id).first()
        if not slot:
            return jsonify({'error': 'Slot not found'}), 404
        
        if slot.reserved_until and now > slot.reserved_until:
            return jsonify({'error': 'Reservation expired'}), 400
        if slot.occupied_by:
            return jsonify({'error': 'Slot already occupied'}), 400
        
        slot.is_available = False
        slot.occupied_by = user_id
        slot.occupied_since = now
        slot.reserved_by = None
        slot.reserved_until = None
        booking.checked_in = True
        booking.entry_time = now
        db.session.commit()
        log_event(booking.id, 'QR_ENTER', 'Entry via QR scan')
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/exit', methods=['POST'])
def exit():
    try:
        data = request.json
        qr_data = data.get('qr_data')
        if not qr_data:
            return jsonify({'error': 'QR missing'}), 400
=======
    except:
        return jsonify({'error': 'Invalid QR data'}), 400
    booking = Booking.query.get(booking_id)
    if not booking or booking.user_id != int(user_id):
        return jsonify({'error': 'Invalid booking'}), 404
    if booking.status != 'active' or booking.checked_in:
        return jsonify({'error': 'Booking not active or already checked in'}), 400
    now = datetime.utcnow()
    if now < booking.start_time:
        return jsonify({'error': 'Booking start time not yet reached'}), 400
    
    slot = ParkingSlot.query.filter_by(lot_id=booking.lot_id, slot_id=booking.slot_id).first()
    if not slot:
        return jsonify({'error': 'Slot not found'}), 404
    
    # If still in future_reserved state (shouldn't happen for immediate bookings, but just in case)
    if slot.future_reserved_by and slot.future_reserved_until and slot.future_reserved_until <= now:
        slot.is_available = False
        slot.reserved_by = booking.user_id
        slot.reserved_until = now + timedelta(minutes=15)
        slot.locked_until = booking.end_time + timedelta(hours=1)
        slot.future_reserved_by = None
        slot.future_reserved_until = None
        db.session.commit()
    
    if slot.reserved_until and now > slot.reserved_until:
        return jsonify({'error': 'Reservation expired'}), 400
    if slot.occupied_by:
        return jsonify({'error': 'Slot already occupied'}), 400
    
    slot.is_available = False
    slot.occupied_by = user_id
    slot.occupied_since = now
    slot.reserved_by = None
    slot.reserved_until = None
    booking.checked_in = True
    booking.entry_time = now
    db.session.commit()
    log_event(booking.id, 'ENTER', f'Entry at gate')
    return jsonify({'success': True})

@app.route('/api/exit', methods=['POST'])
def exit():
    data = request.json
    qr_data = data.get('qr_data')
    if not qr_data:
        return jsonify({'error': 'QR missing'}), 400
    try:
>>>>>>> 7ebede44f5c73607d3c179bd817ed9f9cc955866
        parts = qr_data.split(':')
        if parts[0] != 'ENTRY':
            return jsonify({'error': 'Invalid QR'}), 400
        booking_id, user_id = parts[1], parts[2]
<<<<<<< HEAD
        booking = Booking.query.get(booking_id)
        if not booking or booking.user_id != int(user_id):
            return jsonify({'error': 'Invalid booking'}), 404
        if booking.status != 'active' or not booking.checked_in:
            return jsonify({'error': 'Not checked in'}), 400
        entry_time = booking.entry_time
        exit_time = utc_now()
        duration_actual = (exit_time - entry_time).total_seconds() / 3600
        booked_hours = booking.duration_hours
        extra_hours = max(0, duration_actual - booked_hours)
        lot = ParkingLot.query.get(booking.lot_id)
        extra_amount = 0
        if extra_hours > 0:
            extra_amount = extra_hours * lot.price_per_hour
            penalty = Penalty(user_id=booking.user_id, booking_id=booking.id, amount=extra_amount,
                              reason=f'Extra {extra_hours:.1f} hours')
            db.session.add(penalty)
        slot = ParkingSlot.query.filter_by(lot_id=booking.lot_id, slot_id=booking.slot_id).first()
        if slot:
            slot.is_available = True
            slot.occupied_by = None
            slot.occupied_since = None
            slot.locked_until = None
            slot.reserved_by = None
            slot.reserved_until = None
        booking.status = 'completed'
        booking.exit_time = exit_time
        db.session.commit()
        log_event(booking.id, 'QR_EXIT', f'Exit via QR after {duration_actual:.2f} hours')
        return jsonify({'success': True, 'extra_amount': extra_amount})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ---------- Manual Entry & Exit (ADMIN ONLY) ----------
@app.route('/api/manual-entry', methods=['POST'])
@admin_required
def manual_entry():
    try:
        data = request.json
        booking_id = data.get('booking_id')
        booking = Booking.query.get(booking_id)
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        if booking.payment_status != 'completed':
            return jsonify({'error': 'Payment not completed. User must complete payment first.'}), 402
        
        if booking.status != 'active' or booking.checked_in:
            return jsonify({'error': 'Booking not active or already checked in'}), 400
        
        now = utc_now()
        if now < booking.start_time:
            return jsonify({'error': 'Booking start time not yet reached'}), 400
        
        slot = ParkingSlot.query.filter_by(lot_id=booking.lot_id, slot_id=booking.slot_id).first()
        if not slot:
            return jsonify({'error': 'Slot not found'}), 404
        
        if slot.reserved_until and now > slot.reserved_until:
            return jsonify({'error': 'Reservation expired'}), 400
        if slot.occupied_by:
            return jsonify({'error': 'Slot already occupied'}), 400
        
        slot.is_available = False
        slot.occupied_by = booking.user_id
        slot.occupied_since = now
        slot.reserved_by = None
        slot.reserved_until = None
        booking.checked_in = True
        booking.entry_time = now
        db.session.commit()
        log_event(booking.id, 'MANUAL_ENTER', f'Manual entry by admin')
        return jsonify({'success': True, 'message': 'Entry marked successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/manual-exit', methods=['POST'])
@admin_required
def manual_exit():
    try:
        data = request.json
        booking_id = data.get('booking_id')
        booking = Booking.query.get(booking_id)
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        if booking.status != 'active' or not booking.checked_in:
            return jsonify({'error': 'Booking not checked in'}), 400
        
        entry_time = booking.entry_time
        exit_time = utc_now()
        duration_actual = (exit_time - entry_time).total_seconds() / 3600
        booked_hours = booking.duration_hours
        extra_hours = max(0, duration_actual - booked_hours)
        lot = ParkingLot.query.get(booking.lot_id)
        extra_amount = 0
        if extra_hours > 0:
            extra_amount = extra_hours * lot.price_per_hour
            penalty = Penalty(user_id=booking.user_id, booking_id=booking.id, amount=extra_amount,
                              reason=f'Extra {extra_hours:.1f} hours')
            db.session.add(penalty)
        
        slot = ParkingSlot.query.filter_by(lot_id=booking.lot_id, slot_id=booking.slot_id).first()
        if slot:
            slot.is_available = True
            slot.occupied_by = None
            slot.occupied_since = None
            slot.locked_until = None
            slot.reserved_by = None
            slot.reserved_until = None
        booking.status = 'completed'
        booking.exit_time = exit_time
        db.session.commit()
        log_event(booking.id, 'MANUAL_EXIT', f'Manual exit by admin after {duration_actual:.2f} hours')
        return jsonify({'success': True, 'message': 'Exit marked successfully', 'extra_amount': extra_amount})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ---------- User Bookings ----------
@app.route('/api/user/bookings')
@login_required
def user_bookings():
    try:
        bookings = Booking.query.filter_by(user_id=session['user_id']).order_by(Booking.start_time.desc()).all()
        result = []
        for b in bookings:
            lot = ParkingLot.query.get(b.lot_id)
            result.append({
                'id': b.id, 'lot_name': lot.name if lot else 'Unknown', 'lot_id': b.lot_id,
                'lot_lat': lot.latitude if lot else None, 'lot_lon': lot.longitude if lot else None,
                'slot_id': b.slot_id, 'start_time': b.start_time.isoformat(),
                'end_time': b.end_time.isoformat() if b.end_time else None,
                'duration_hours': b.duration_hours, 'amount_paid': b.amount_paid,
                'status': b.status, 'qr_code': b.qr_code, 'checked_in': b.checked_in,
                'payment_status': b.payment_status
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
=======
    except:
        return jsonify({'error': 'Invalid QR data'}), 400
    booking = Booking.query.get(booking_id)
    if not booking or booking.user_id != int(user_id):
        return jsonify({'error': 'Invalid booking'}), 404
    if booking.status != 'active' or not booking.checked_in:
        return jsonify({'error': 'Not checked in'}), 400
    entry_time = booking.entry_time
    exit_time = datetime.utcnow()
    duration_actual = (exit_time - entry_time).total_seconds() / 3600
    booked_hours = booking.duration_hours
    extra_hours = max(0, duration_actual - booked_hours)
    lot = ParkingLot.query.get(booking.lot_id)
    extra_amount = 0
    if extra_hours > 0:
        extra_amount = extra_hours * lot.price_per_hour
        penalty = Penalty(user_id=booking.user_id, booking_id=booking.id, amount=extra_amount,
                          reason=f'Extra {extra_hours:.1f} hours')
        db.session.add(penalty)
    slot = ParkingSlot.query.filter_by(lot_id=booking.lot_id, slot_id=booking.slot_id).first()
    slot.is_available = True
    slot.occupied_by = None
    slot.occupied_since = None
    slot.locked_until = None
    slot.reserved_by = None
    slot.reserved_until = None
    slot.future_reserved_by = None
    slot.future_reserved_until = None
    booking.status = 'completed'
    booking.exit_time = exit_time
    db.session.commit()
    log_event(booking.id, 'EXIT', f'Exit after {duration_actual:.2f} hours')
    return jsonify({'success': True, 'extra_amount': extra_amount})

@app.route('/api/user/bookings')
@login_required
def user_bookings():
    bookings = Booking.query.filter_by(user_id=session['user_id']).order_by(Booking.start_time.desc()).all()
    result = []
    for b in bookings:
        lot = ParkingLot.query.get(b.lot_id)
        result.append({
            'id': b.id, 'lot_name': lot.name if lot else 'Unknown', 'lot_id': b.lot_id,
            'lot_lat': lot.latitude if lot else None, 'lot_lon': lot.longitude if lot else None,
            'slot_id': b.slot_id, 'start_time': b.start_time.isoformat(),
            'end_time': b.end_time.isoformat() if b.end_time else None,
            'duration_hours': b.duration_hours, 'amount_paid': b.amount_paid,
            'status': b.status, 'qr_code': b.qr_code
        })
    return jsonify(result)
>>>>>>> 7ebede44f5c73607d3c179bd817ed9f9cc955866

@app.route('/api/settings', methods=['GET'])
@login_required
def get_settings():
<<<<<<< HEAD
    try:
        upi = Setting.query.filter_by(key='upi_id').first()
        upi_id = upi.value if upi else 'shivshankar47165@oksbi'
        return jsonify({'upi_id': upi_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ---------- Coupon & Loyalty ----------
@app.route('/api/coupons/validate', methods=['POST'])
@login_required
def validate_coupon():
    try:
        data = request.json
        code = data.get('code')
        amount = data.get('amount', 0)
        coupon = Coupon.query.filter_by(code=code, is_active=True).first()
        if not coupon:
            return jsonify({'error': 'Invalid coupon code'}), 404
        now = utc_now()
        if coupon.valid_until and now > coupon.valid_until:
            return jsonify({'error': 'Coupon expired'}), 400
        if coupon.usage_limit and coupon.used_count >= coupon.usage_limit:
            return jsonify({'error': 'Coupon usage limit reached'}), 400
        if amount < coupon.min_booking_amount:
            return jsonify({'error': f'Minimum booking amount ₹{coupon.min_booking_amount} required'}), 400
        
        discount = 0
        final_amount = amount
        if coupon.discount_type == 'percentage':
            discount = (coupon.discount_value / 100) * amount
            if coupon.max_discount and discount > coupon.max_discount:
                discount = coupon.max_discount
            final_amount = amount - discount
        elif coupon.discount_type == 'fixed':
            discount = coupon.discount_value
            final_amount = max(0, amount - discount)
        elif coupon.discount_type == 'free':
            final_amount = 0
            discount = amount
        
        return jsonify({
            'valid': True,
            'discount': round(discount, 2),
            'final_amount': round(final_amount, 2),
            'coupon_id': coupon.id,
            'discount_type': coupon.discount_type
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
=======
    upi = Setting.query.filter_by(key='upi_id').first()
    upi_id = upi.value if upi else 'parkbotix@okhdfcbank'
    return jsonify({'upi_id': upi_id})

# ---------- Coupon & Loyalty API ----------
@app.route('/api/coupons/validate', methods=['POST'])
@login_required
def validate_coupon():
    data = request.json
    code = data.get('code')
    amount = data.get('amount', 0)
    coupon = Coupon.query.filter_by(code=code, is_active=True).first()
    if not coupon:
        return jsonify({'error': 'Invalid coupon code'}), 404
    now = datetime.utcnow()
    if coupon.valid_until and now > coupon.valid_until:
        return jsonify({'error': 'Coupon expired'}), 400
    if coupon.usage_limit and coupon.used_count >= coupon.usage_limit:
        return jsonify({'error': 'Coupon usage limit reached'}), 400
    if amount < coupon.min_booking_amount:
        return jsonify({'error': f'Minimum booking amount ₹{coupon.min_booking_amount} required'}), 400
    
    discount = 0
    final_amount = amount
    if coupon.discount_type == 'percentage':
        discount = (coupon.discount_value / 100) * amount
        if coupon.max_discount and discount > coupon.max_discount:
            discount = coupon.max_discount
        final_amount = amount - discount
    elif coupon.discount_type == 'fixed':
        discount = coupon.discount_value
        final_amount = max(0, amount - discount)
    elif coupon.discount_type == 'free':
        final_amount = 0
        discount = amount
    
    return jsonify({
        'valid': True,
        'discount': round(discount, 2),
        'final_amount': round(final_amount, 2),
        'coupon_id': coupon.id,
        'discount_type': coupon.discount_type
    })
>>>>>>> 7ebede44f5c73607d3c179bd817ed9f9cc955866

@app.route('/api/loyalty/points', methods=['GET'])
@login_required
def get_loyalty_points():
<<<<<<< HEAD
    try:
        loyalty = UserLoyalty.query.filter_by(user_id=session['user_id']).first()
        if not loyalty:
            loyalty = UserLoyalty(user_id=session['user_id'], points=0)
            db.session.add(loyalty)
            db.session.commit()
        return jsonify({'points': loyalty.points})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
=======
    loyalty = UserLoyalty.query.filter_by(user_id=session['user_id']).first()
    if not loyalty:
        loyalty = UserLoyalty(user_id=session['user_id'], points=0)
        db.session.add(loyalty)
        db.session.commit()
    return jsonify({'points': loyalty.points})
>>>>>>> 7ebede44f5c73607d3c179bd817ed9f9cc955866

@app.route('/api/loyalty/redeem', methods=['POST'])
@login_required
def redeem_points():
<<<<<<< HEAD
    try:
        data = request.json
        points_to_redeem = data.get('points', 0)
        amount = data.get('amount', 0)
        loyalty = UserLoyalty.query.filter_by(user_id=session['user_id']).first()
        if not loyalty or loyalty.points < points_to_redeem:
            return jsonify({'error': 'Insufficient points'}), 400
        discount = points_to_redeem * 0.5
        if discount > amount:
            discount = amount
            points_to_redeem = int(discount / 0.5)
        final_amount = amount - discount
        return jsonify({
            'success': True,
            'discount': discount,
            'final_amount': round(final_amount, 2),
            'points_used': points_to_redeem,
            'remaining_points': loyalty.points - points_to_redeem
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ---------- Free Booking ----------
@app.route('/api/free-booking', methods=['POST'])
@login_required
def free_booking():
    try:
        data = request.json
        lot_id = data.get('lot_id')
        slot_id = data.get('slot_id')
        duration_hours = data.get('duration_hours', 1)
        coupon_code = data.get('coupon_code')
        use_points = data.get('use_points', False)
        
        slot = ParkingSlot.query.filter_by(lot_id=lot_id, slot_id=slot_id).first()
        if not slot:
            return jsonify({'error': 'Slot not found'}), 404
        
        now = utc_now()
        if not slot.is_available or slot.reserved_by or slot.occupied_by:
            return jsonify({'error': 'Slot not available now'}), 400
        
        lot = ParkingLot.query.get(lot_id)
        amount = lot.price_per_hour * duration_hours
        final_amount = amount
        
        if coupon_code:
            coupon = Coupon.query.filter_by(code=coupon_code, is_active=True).first()
            if coupon and coupon.discount_type == 'free':
                final_amount = 0
                coupon.used_count += 1
                db.session.commit()
            elif coupon:
                if coupon.discount_type == 'percentage':
                    discount = (coupon.discount_value / 100) * amount
                    if discount >= amount:
                        final_amount = 0
                elif coupon.discount_type == 'fixed' and coupon.discount_value >= amount:
                    final_amount = 0
        
        if use_points and final_amount > 0:
            loyalty = UserLoyalty.query.filter_by(user_id=session['user_id']).first()
            if loyalty:
                points_needed = int(amount / 0.5) + 1
                if loyalty.points >= points_needed:
                    final_amount = 0
                    loyalty.points -= points_needed
                    db.session.commit()
        
        if final_amount > 0:
            return jsonify({'error': 'Cannot book for free without valid offer'}), 400
        
        booking_id = str(uuid.uuid4())
        end_time = now + timedelta(hours=duration_hours)
        booking = Booking(
            id=booking_id, lot_id=lot_id, slot_id=slot_id, user_id=session['user_id'],
            start_time=now, end_time=end_time, duration_hours=duration_hours,
            amount_paid=0, payment_status='completed'
        )
        db.session.add(booking)
        
        slot.is_available = False
        slot.reserved_by = session['user_id']
        slot.reserved_until = now + timedelta(minutes=15)
        slot.locked_until = end_time + timedelta(hours=1)
        
        db.session.commit()
        qr_data = f"ENTRY:{booking.id}:{booking.user_id}"
        qr_base64 = generate_qr(qr_data)
        booking.qr_code = qr_base64
        db.session.commit()
        log_event(booking.id, 'FREE_BOOK', 'Booked using offer')
        return jsonify({'success': True, 'booking_id': booking_id, 'qr_code': qr_base64})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
=======
    data = request.json
    points_to_redeem = data.get('points', 0)
    amount = data.get('amount', 0)
    loyalty = UserLoyalty.query.filter_by(user_id=session['user_id']).first()
    if not loyalty or loyalty.points < points_to_redeem:
        return jsonify({'error': 'Insufficient points'}), 400
    discount = points_to_redeem * 0.5
    if discount > amount:
        discount = amount
        points_to_redeem = int(discount / 0.5)
    final_amount = amount - discount
    return jsonify({
        'success': True,
        'discount': discount,
        'final_amount': round(final_amount, 2),
        'points_used': points_to_redeem,
        'remaining_points': loyalty.points - points_to_redeem
    })

# ---------- Free booking (immediate only) ----------
@app.route('/api/free-booking', methods=['POST'])
@login_required
def free_booking():
    data = request.json
    lot_id = data.get('lot_id')
    slot_id = data.get('slot_id')
    duration_hours = data.get('duration_hours', 1)
    coupon_code = data.get('coupon_code')
    use_points = data.get('use_points', False)
    
    slot = ParkingSlot.query.filter_by(lot_id=lot_id, slot_id=slot_id).first()
    if not slot:
        return jsonify({'error': 'Slot not found'}), 404
    
    now = datetime.utcnow()
    # Always book for current time (immediate)
    start_time = now
    
    if not slot.is_available or slot.reserved_by or slot.occupied_by:
        return jsonify({'error': 'Slot not available now'}), 400
    
    lot = ParkingLot.query.get(lot_id)
    amount = lot.price_per_hour * duration_hours
    final_amount = amount
    
    if coupon_code:
        coupon = Coupon.query.filter_by(code=coupon_code, is_active=True).first()
        if coupon and coupon.discount_type == 'free':
            final_amount = 0
            coupon.used_count += 1
            db.session.commit()
        elif coupon:
            if coupon.discount_type == 'percentage':
                discount = (coupon.discount_value / 100) * amount
                if discount >= amount:
                    final_amount = 0
            elif coupon.discount_type == 'fixed' and coupon.discount_value >= amount:
                final_amount = 0
    
    if use_points and final_amount > 0:
        loyalty = UserLoyalty.query.filter_by(user_id=session['user_id']).first()
        if loyalty:
            points_needed = int(amount / 0.5) + 1
            if loyalty.points >= points_needed:
                final_amount = 0
                loyalty.points -= points_needed
                db.session.commit()
    
    if final_amount > 0:
        return jsonify({'error': 'Cannot book for free without valid offer'}), 400
    
    booking_id = str(uuid.uuid4())
    end_time = start_time + timedelta(hours=duration_hours)
    booking = Booking(
        id=booking_id, lot_id=lot_id, slot_id=slot_id, user_id=session['user_id'],
        start_time=start_time, end_time=end_time, duration_hours=duration_hours,
        amount_paid=0, payment_status='completed'
    )
    db.session.add(booking)
    
    slot.is_available = False
    slot.reserved_by = session['user_id']
    slot.reserved_until = now + timedelta(minutes=15)
    slot.locked_until = end_time + timedelta(hours=1)
    
    db.session.commit()
    qr_data = f"ENTRY:{booking.id}:{booking.user_id}"
    qr_base64 = generate_qr(qr_data)
    booking.qr_code = qr_base64
    db.session.commit()
    log_event(booking.id, 'FREE_BOOK', 'Booked using offer (immediate)')
    return jsonify({'success': True, 'booking_id': booking_id, 'qr_code': qr_base64})
>>>>>>> 7ebede44f5c73607d3c179bd817ed9f9cc955866

# ---------- AI Advice ----------
@app.route('/api/ai/advice', methods=['POST'])
@login_required
def ai_advice():
<<<<<<< HEAD
    try:
        data = request.json
        lat, lon = data.get('lat'), data.get('lon')
        if lat is None or lon is None:
            return jsonify({'advice': 'Please provide location coordinates.'})
        lots = ParkingLot.query.all()
        nearby = []
        radius_km = 20
        for lot in lots:
            dist = calculate_distance(lat, lon, lot.latitude, lot.longitude)
            if dist <= radius_km:
                total = ParkingSlot.query.filter_by(lot_id=lot.id).count()
                available = ParkingSlot.query.filter_by(lot_id=lot.id, is_available=True).count()
                occupancy = int((total - available) / total * 100) if total else 0
                nearby.append({
                    'name': lot.name, 'distance_km': round(dist, 2), 'price_per_hour': lot.price_per_hour,
                    'available_slots': available, 'total_slots': total, 'occupancy': occupancy,
                    'ai_monitoring': lot.ai_monitoring, 'location': lot.location or ''
                })
        if not nearby:
            return jsonify({'advice': f'No parking lots within {radius_km} km of your location.'})
        lots_text = "\n".join([f"- {l['name']}: {l['distance_km']} km, ₹{l['price_per_hour']}/hr, {l['available_slots']} free" for l in nearby[:10]])
        prompt = f"User at ({lat},{lon}). Nearby:\n{lots_text}\nFuel cost ₹10/km. Suggest best lot and tips in 2-3 sentences."
=======
    data = request.json
    lat, lon = data.get('lat'), data.get('lon')
    if lat is None or lon is None:
        return jsonify({'advice': 'Please provide location coordinates.'})
    lots = ParkingLot.query.all()
    nearby = []
    radius_km = 20
    for lot in lots:
        dist = calculate_distance(lat, lon, lot.latitude, lot.longitude)
        if dist <= radius_km:
            total = ParkingSlot.query.filter_by(lot_id=lot.id).count()
            available = ParkingSlot.query.filter_by(lot_id=lot.id, is_available=True).count()
            occupancy = int((total - available) / total * 100) if total else 0
            nearby.append({
                'name': lot.name, 'distance_km': round(dist, 2), 'price_per_hour': lot.price_per_hour,
                'available_slots': available, 'total_slots': total, 'occupancy': occupancy,
                'ai_monitoring': lot.ai_monitoring, 'location': lot.location or ''
            })
    if not nearby:
        return jsonify({'advice': f'No parking lots within {radius_km} km of your location.'})
    lots_text = "\n".join([f"- {l['name']}: {l['distance_km']} km, ₹{l['price_per_hour']}/hr, {l['available_slots']} free" for l in nearby[:10]])
    prompt = f"User at ({lat},{lon}). Nearby:\n{lots_text}\nFuel cost ₹10/km. Suggest best lot and tips in 2-3 sentences."
    try:
>>>>>>> 7ebede44f5c73607d3c179bd817ed9f9cc955866
        model = genai.GenerativeModel('models/gemini-2.0-flash')
        response = model.generate_content(prompt)
        advice = response.text
        activity = AiActivity(user_id=session['user_id'], username=User.query.get(session['user_id']).username,
                              query=prompt[:500], response=advice[:1000])
        db.session.add(activity)
        db.session.commit()
<<<<<<< HEAD
        return jsonify({'advice': advice})
    except Exception as e:
        return jsonify({'advice': f"AI service temporarily unavailable. Error: {str(e)}"})
=======
    except Exception as e:
        best = min(nearby, key=lambda x: x['distance_km'])
        advice = f"AI service temporarily unavailable. Based on distance, {best['name']} is {best['distance_km']} km away with {best['available_slots']} slots available at ₹{best['price_per_hour']}/hr."
    return jsonify({'advice': advice})
>>>>>>> 7ebede44f5c73607d3c179bd817ed9f9cc955866

# ---------- Congestion Prediction ----------
@app.route('/api/pcde/advise', methods=['POST'])
@login_required
def congestion_advice():
<<<<<<< HEAD
    try:
        data = request.json
        lat, lon = data.get('lat'), data.get('lon')
        if lat is None or lon is None:
            return jsonify({'advice': 'Please provide location coordinates.'})
=======
    data = request.json
    lat, lon = data.get('lat'), data.get('lon')
    if lat is None or lon is None:
        return jsonify({'advice': 'Please provide location coordinates.'})
    try:
>>>>>>> 7ebede44f5c73607d3c179bd817ed9f9cc955866
        lots = ParkingLot.query.all()
        nearby = []
        for lot in lots:
            dist = calculate_distance(lat, lon, lot.latitude, lot.longitude)
            if dist <= 10:
                occupied = ParkingSlot.query.filter_by(lot_id=lot.id, is_available=False).count()
                total = ParkingSlot.query.filter_by(lot_id=lot.id).count()
                occupancy_rate = occupied / total if total else 0
                nearby.append({'name': lot.name, 'distance': round(dist,2), 'occupancy_rate': round(occupancy_rate*100)})
        if not nearby:
            return jsonify({'advice': 'No parking lots within 10 km for congestion prediction.'})
<<<<<<< HEAD
        prompt = f"Based on these occupancy rates: {nearby}, which lot will likely become congested in the next hour? Suggest an alternate lot with lower occupancy."
        model = genai.GenerativeModel('models/gemini-2.0-flash')
        response = model.generate_content(prompt)
        advice = response.text
        return jsonify({'advice': advice})
    except Exception as e:
        return jsonify({'advice': f"Prediction unavailable. Error: {str(e)}"})

# ---------- Other Advanced Features (POLP, AERR, IPRE, etc.) ----------
@app.route('/api/slot/lock', methods=['POST'])
@login_required
def lock_slot():
    try:
        data = request.json
        booking_id = data.get('booking_id')
        booking = Booking.query.filter_by(id=booking_id, user_id=session['user_id']).first()
        if not booking or booking.status != 'active':
            return jsonify({'error': 'Invalid booking'}), 400
        slot = ParkingSlot.query.filter_by(lot_id=booking.lot_id, slot_id=booking.slot_id).first()
        if slot:
            slot.locked_until = booking.end_time + timedelta(hours=1)
            db.session.commit()
            return jsonify({'success': True, 'locked_until': slot.locked_until.isoformat()})
        return jsonify({'error': 'Slot not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def predict_exit_time(booking_id):
    try:
        booking = Booking.query.get(booking_id)
        if not booking:
            return booking.end_time
        prompt = f"Predict realistic extra minutes beyond {booking.duration_hours} hours for parking exit. Return only number."
=======
        prompt = f"Based on these occupancy rates: {nearby}, which lot will likely become congested in the next hour? Suggest an alternate lot with lower occupancy. Keep response short (2-3 sentences)."
        model = genai.GenerativeModel('models/gemini-2.0-flash')
        response = model.generate_content(prompt)
        advice = response.text
    except Exception as e:
        if nearby:
            best = min(nearby, key=lambda x: x['occupancy_rate'])
            advice = f"AI prediction unavailable. Based on current data, {best['name']} has the lowest occupancy ({best['occupancy_rate']}%) and may be a good alternative."
        else:
            advice = "No congestion data available at this time."
    return jsonify({'advice': advice})

# ---------- Other Advanced Features ----------
@app.route('/api/slot/lock', methods=['POST'])
@login_required
def lock_slot():
    data = request.json
    booking_id = data.get('booking_id')
    booking = Booking.query.filter_by(id=booking_id, user_id=session['user_id']).first()
    if not booking or booking.status != 'active':
        return jsonify({'error': 'Invalid booking'}), 400
    slot = ParkingSlot.query.filter_by(lot_id=booking.lot_id, slot_id=booking.slot_id).first()
    if slot:
        slot.locked_until = booking.end_time + timedelta(hours=1)
        db.session.commit()
        return jsonify({'success': True, 'locked_until': slot.locked_until.isoformat()})
    return jsonify({'error': 'Slot not found'}), 404

def predict_exit_time(booking_id):
    booking = Booking.query.get(booking_id)
    if not booking:
        return booking.end_time
    prompt = f"Predict realistic extra minutes beyond {booking.duration_hours} hours for parking exit. Return only number."
    try:
>>>>>>> 7ebede44f5c73607d3c179bd817ed9f9cc955866
        model = genai.GenerativeModel('models/gemini-2.0-flash')
        response = model.generate_content(prompt)
        extra_min = int(response.text.strip()) if response.text.strip().isdigit() else 0
        predicted = booking.start_time + timedelta(hours=booking.duration_hours, minutes=extra_min)
<<<<<<< HEAD
        booking.predicted_exit = predicted
        db.session.commit()
        return predicted
    except:
        return booking.end_time
=======
    except:
        predicted = booking.end_time
    booking.predicted_exit = predicted
    db.session.commit()
    return predicted
>>>>>>> 7ebede44f5c73607d3c179bd817ed9f9cc955866

@app.route('/api/aerr/predict', methods=['POST'])
@login_required
def aerr_predict():
<<<<<<< HEAD
    try:
        data = request.json
        booking_id = data.get('booking_id')
        predicted = predict_exit_time(booking_id)
        booking = Booking.query.get(booking_id)
        slot = ParkingSlot.query.filter_by(lot_id=booking.lot_id, slot_id=booking.slot_id).first()
        shadow = ShadowReservation(slot_id=slot.id, user_id=session['user_id'],
                                   proposed_entry_time=predicted + timedelta(minutes=5), status='pending')
        db.session.add(shadow)
        db.session.commit()
        return jsonify({'predicted_exit': predicted.isoformat(), 'shadow_id': shadow.id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
=======
    data = request.json
    booking_id = data.get('booking_id')
    predicted = predict_exit_time(booking_id)
    booking = Booking.query.get(booking_id)
    slot = ParkingSlot.query.filter_by(lot_id=booking.lot_id, slot_id=booking.slot_id).first()
    shadow = ShadowReservation(slot_id=slot.id, user_id=session['user_id'],
                               proposed_entry_time=predicted + timedelta(minutes=5), status='pending')
    db.session.add(shadow)
    db.session.commit()
    return jsonify({'predicted_exit': predicted.isoformat(), 'shadow_id': shadow.id})
>>>>>>> 7ebede44f5c73607d3c179bd817ed9f9cc955866

@app.route('/api/ipre/suggest', methods=['POST'])
@login_required
def ipre_suggest():
<<<<<<< HEAD
    try:
        data = request.json
        lot_id = data.get('lot_id')
        past = Booking.query.filter_by(user_id=session['user_id']).all()
        avg_duration = sum(b.duration_hours for b in past) / len(past) if past else 1
        suggested = max(1, min(4, round(avg_duration)))
        available = ParkingSlot.query.filter_by(lot_id=lot_id, is_available=True).count()
        return jsonify({'suggested_duration': suggested, 'available_slots': available})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
=======
    data = request.json
    lot_id = data.get('lot_id')
    past = Booking.query.filter_by(user_id=session['user_id']).all()
    avg_duration = sum(b.duration_hours for b in past) / len(past) if past else 1
    suggested = max(1, min(4, round(avg_duration)))
    available = ParkingSlot.query.filter_by(lot_id=lot_id, is_available=True).count()
    return jsonify({'suggested_duration': suggested, 'available_slots': available})
>>>>>>> 7ebede44f5c73607d3c179bd817ed9f9cc955866

@app.route('/api/gsd/detect', methods=['POST'])
@admin_required
def detect_ghost_slots():
<<<<<<< HEAD
    try:
        ghost_slots = []
        slots = ParkingSlot.query.filter_by(is_available=False).all()
        for slot in slots:
            booking = Booking.query.filter_by(lot_id=slot.lot_id, slot_id=slot.slot_id, status='active').first()
            if not booking and slot.occupied_since and (utc_now() - slot.occupied_since).seconds > 3600:
                ghost_slots.append(slot.slot_id)
                slot.is_available = True
                slot.occupied_by = None
                slot.occupied_since = None
        db.session.commit()
        return jsonify({'ghost_slots_detected': ghost_slots, 'corrected': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
=======
    ghost_slots = []
    slots = ParkingSlot.query.filter_by(is_available=False).all()
    for slot in slots:
        booking = Booking.query.filter_by(lot_id=slot.lot_id, slot_id=slot.slot_id, status='active').first()
        if not booking and slot.occupied_since and (datetime.utcnow() - slot.occupied_since).seconds > 3600:
            ghost_slots.append(slot.slot_id)
            slot.is_available = True
            slot.occupied_by = None
            slot.occupied_since = None
    db.session.commit()
    return jsonify({'ghost_slots_detected': ghost_slots, 'corrected': True})
>>>>>>> 7ebede44f5c73607d3c179bd817ed9f9cc955866

@app.route('/api/easdl/process', methods=['POST'])
@login_required
def edge_ai_process():
    data = request.json
<<<<<<< HEAD
    decision = {'action': 'approve_entry', 'reason': 'Local AI: low congestion', 'timestamp': utc_now().isoformat()}
=======
    decision = {'action': 'approve_entry', 'reason': 'Local AI: low congestion', 'timestamp': datetime.utcnow().isoformat()}
>>>>>>> 7ebede44f5c73607d3c179bd817ed9f9cc955866
    ai_activity = AiActivity(user_id=session['user_id'], username=User.query.get(session['user_id']).username,
                             query=str(data), response=json.dumps(decision))
    db.session.add(ai_activity)
    db.session.commit()
    return jsonify(decision)

@app.route('/api/dnlrp/adjust', methods=['POST'])
@login_required
def adjust_reservation_for_traffic():
<<<<<<< HEAD
    try:
        data = request.json
        booking_id = data.get('booking_id')
        traffic_delay_min = data.get('traffic_delay_min', 0)
        booking = Booking.query.get(booking_id)
        if not booking or booking.user_id != session['user_id']:
            return jsonify({'error': 'Invalid booking'}), 400
        slot = ParkingSlot.query.filter_by(lot_id=booking.lot_id, slot_id=booking.slot_id).first()
        if slot and slot.reserved_until:
            slot.reserved_until += timedelta(minutes=traffic_delay_min)
            db.session.commit()
            return jsonify({'new_reserved_until': slot.reserved_until.isoformat()})
        return jsonify({'message': 'No active reservation to adjust'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
=======
    data = request.json
    booking_id = data.get('booking_id')
    traffic_delay_min = data.get('traffic_delay_min', 0)
    booking = Booking.query.get(booking_id)
    if not booking or booking.user_id != session['user_id']:
        return jsonify({'error': 'Invalid booking'}), 400
    slot = ParkingSlot.query.filter_by(lot_id=booking.lot_id, slot_id=booking.slot_id).first()
    if slot and slot.reserved_until:
        slot.reserved_until += timedelta(minutes=traffic_delay_min)
        db.session.commit()
        return jsonify({'new_reserved_until': slot.reserved_until.isoformat()})
    return jsonify({'message': 'No active reservation to adjust'})
>>>>>>> 7ebede44f5c73607d3c179bd817ed9f9cc955866

@app.route('/api/rsms/morph', methods=['POST'])
@admin_required
def morph_slots():
<<<<<<< HEAD
    try:
        data = request.json
        lot_id, from_type, to_type = data.get('lot_id'), data.get('from_type'), data.get('to_type')
        count = data.get('count', 1)
        lot = ParkingLot.query.get(lot_id)
        if not lot or not lot.supports_morphing:
            return jsonify({'error': 'Morphing not supported'}), 400
        slots = ParkingSlot.query.filter_by(lot_id=lot_id, slot_type=from_type, is_available=True).limit(count).all()
        if len(slots) < count:
            return jsonify({'error': f'Not enough {from_type} slots'}), 400
        for slot in slots:
            slot.slot_type = to_type
        morph_log = SlotMorph(lot_id=lot_id, from_type=from_type, to_type=to_type,
                              slot_ids=json.dumps([s.slot_id for s in slots]))
        db.session.add(morph_log)
        db.session.commit()
        return jsonify({'success': True, 'morphed': len(slots)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
=======
    data = request.json
    lot_id, from_type, to_type = data.get('lot_id'), data.get('from_type'), data.get('to_type')
    count = data.get('count', 1)
    lot = ParkingLot.query.get(lot_id)
    if not lot or not lot.supports_morphing:
        return jsonify({'error': 'Morphing not supported'}), 400
    slots = ParkingSlot.query.filter_by(lot_id=lot_id, slot_type=from_type, is_available=True).limit(count).all()
    if len(slots) < count:
        return jsonify({'error': f'Not enough {from_type} slots'}), 400
    for slot in slots:
        slot.slot_type = to_type
    morph_log = SlotMorph(lot_id=lot_id, from_type=from_type, to_type=to_type,
                          slot_ids=json.dumps([s.slot_id for s in slots]))
    db.session.add(morph_log)
    db.session.commit()
    return jsonify({'success': True, 'morphed': len(slots)})

# SAEP background thread
def auto_extension_worker():
    with app.app_context():
        while True:
            now = datetime.utcnow()
            soon_end = Booking.query.filter(Booking.end_time <= now + timedelta(minutes=15),
                                            Booking.end_time > now,
                                            Booking.status == 'active',
                                            Booking.checked_in == True).all()
            for booking in soon_end:
                next_booking = Booking.query.filter(Booking.lot_id == booking.lot_id,
                                                    Booking.slot_id == booking.slot_id,
                                                    Booking.start_time > now,
                                                    Booking.start_time < now + timedelta(hours=1)).first()
                if not next_booking:
                    new_end = booking.end_time + timedelta(minutes=30)
                    extra_hours = 0.5
                    extra_charge = ParkingLot.query.get(booking.lot_id).price_per_hour * extra_hours
                    booking.end_time = new_end
                    booking.duration_hours += extra_hours
                    booking.amount_paid += extra_charge
                    booking.auto_extended = True
                    log = AutoExtensionLog(booking_id=booking.id, extra_hours=extra_hours, extra_charge=extra_charge)
                    db.session.add(log)
                    db.session.commit()
                    log_event(booking.id, 'EXTEND', f'Auto-extended by 30 min')
            time.sleep(60)

threading.Thread(target=auto_extension_worker, daemon=True).start()
>>>>>>> 7ebede44f5c73607d3c179bd817ed9f9cc955866

@app.route('/api/vfap/register', methods=['POST'])
@login_required
def register_fingerprint():
<<<<<<< HEAD
    try:
        data = request.json
        number_plate, color, shape = data.get('number_plate'), data.get('color'), data.get('shape')
        if not all([number_plate, color, shape]):
            return jsonify({'error': 'Missing fields'}), 400
        fingerprint = f"{number_plate}|{color}|{shape}"
        fp_hash = bcrypt.hashpw(fingerprint.encode(), bcrypt.gensalt()).decode()
        existing = VehicleFingerprint.query.filter_by(user_id=session['user_id']).first()
        if existing:
            existing.number_plate = number_plate
            existing.color = color
            existing.shape = shape
            existing.fingerprint_hash = fp_hash
        else:
            vf = VehicleFingerprint(user_id=session['user_id'], number_plate=number_plate,
                                    color=color, shape=shape, fingerprint_hash=fp_hash)
            db.session.add(vf)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vfap/verify', methods=['POST'])
def verify_fingerprint():
    try:
        data = request.json
        number_plate, color, shape = data.get('number_plate'), data.get('color'), data.get('shape')
        candidates = VehicleFingerprint.query.all()
        for vf in candidates:
            if bcrypt.checkpw(f"{number_plate}|{color}|{shape}".encode(), vf.fingerprint_hash.encode()):
                return jsonify({'verified': True, 'user_id': vf.user_id})
        return jsonify({'verified': False}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500
=======
    data = request.json
    number_plate, color, shape = data.get('number_plate'), data.get('color'), data.get('shape')
    if not all([number_plate, color, shape]):
        return jsonify({'error': 'Missing fields'}), 400
    fingerprint = f"{number_plate}|{color}|{shape}"
    fp_hash = bcrypt.hashpw(fingerprint.encode(), bcrypt.gensalt()).decode()
    existing = VehicleFingerprint.query.filter_by(user_id=session['user_id']).first()
    if existing:
        existing.number_plate = number_plate
        existing.color = color
        existing.shape = shape
        existing.fingerprint_hash = fp_hash
    else:
        vf = VehicleFingerprint(user_id=session['user_id'], number_plate=number_plate,
                                color=color, shape=shape, fingerprint_hash=fp_hash)
        db.session.add(vf)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/vfap/verify', methods=['POST'])
def verify_fingerprint():
    data = request.json
    number_plate, color, shape = data.get('number_plate'), data.get('color'), data.get('shape')
    candidates = VehicleFingerprint.query.all()
    for vf in candidates:
        if bcrypt.checkpw(f"{number_plate}|{color}|{shape}".encode(), vf.fingerprint_hash.encode()):
            return jsonify({'verified': True, 'user_id': vf.user_id})
    return jsonify({'verified': False}), 401
>>>>>>> 7ebede44f5c73607d3c179bd817ed9f9cc955866

@app.route('/api/easas/assign', methods=['POST'])
@login_required
def assign_ev_slot():
<<<<<<< HEAD
    try:
        data = request.json
        lot_id = data.get('lot_id')
        is_ev = data.get('is_ev', False)
        if is_ev:
            ev_slot = EVChargingSlot.query.join(ParkingSlot).filter(ParkingSlot.lot_id == lot_id,
                                                                    EVChargingSlot.is_available == True).first()
            if ev_slot:
                slot = ParkingSlot.query.get(ev_slot.slot_id)
            else:
                slot = ParkingSlot.query.filter_by(lot_id=lot_id, slot_type='car', is_available=True).first()
        else:
            slot = ParkingSlot.query.filter_by(lot_id=lot_id, slot_type='car', is_available=True).first()
        if not slot:
            return jsonify({'error': 'No slot available'}), 400
        return jsonify({'slot_id': slot.slot_id, 'slot_type': slot.slot_type})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
=======
    data = request.json
    lot_id = data.get('lot_id')
    is_ev = data.get('is_ev', False)
    if is_ev:
        ev_slot = EVChargingSlot.query.join(ParkingSlot).filter(ParkingSlot.lot_id == lot_id,
                                                                EVChargingSlot.is_available == True).first()
        if ev_slot:
            slot = ParkingSlot.query.get(ev_slot.slot_id)
        else:
            slot = ParkingSlot.query.filter_by(lot_id=lot_id, slot_type='car', is_available=True).first()
    else:
        slot = ParkingSlot.query.filter_by(lot_id=lot_id, slot_type='car', is_available=True).first()
    if not slot:
        return jsonify({'error': 'No slot available'}), 400
    return jsonify({'slot_id': slot.slot_id, 'slot_type': slot.slot_type})
>>>>>>> 7ebede44f5c73607d3c179bd817ed9f9cc955866

@app.route('/api/rrm/offer', methods=['POST'])
@login_required
def create_marketplace_offer():
<<<<<<< HEAD
    try:
        data = request.json
        booking_id = data.get('booking_id')
        price = data.get('price')
        booking = Booking.query.filter_by(id=booking_id, user_id=session['user_id'], status='active').first()
        if not booking:
            return jsonify({'error': 'Active booking not found'}), 400
        offer = MarketplaceOffer(booking_id=booking_id, offered_by=session['user_id'], offered_price=price, status='open')
        db.session.add(offer)
        db.session.commit()
        return jsonify({'offer_id': offer.id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
=======
    data = request.json
    booking_id = data.get('booking_id')
    price = data.get('price')
    booking = Booking.query.filter_by(id=booking_id, user_id=session['user_id'], status='active').first()
    if not booking:
        return jsonify({'error': 'Active booking not found'}), 400
    offer = MarketplaceOffer(booking_id=booking_id, offered_by=session['user_id'], offered_price=price, status='open')
    db.session.add(offer)
    db.session.commit()
    return jsonify({'offer_id': offer.id})
>>>>>>> 7ebede44f5c73607d3c179bd817ed9f9cc955866

@app.route('/api/rrm/take/<int:offer_id>', methods=['POST'])
@login_required
def take_offer(offer_id):
<<<<<<< HEAD
    try:
        offer = MarketplaceOffer.query.get(offer_id)
        if not offer or offer.status != 'open':
            return jsonify({'error': 'Offer not available'}), 400
        booking = Booking.query.get(offer.booking_id)
        booking.user_id = session['user_id']
        refund_amount = offer.offered_price * 0.8
        offer.status = 'taken'
        db.session.commit()
        return jsonify({'success': True, 'refund_to_original': refund_amount})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cdaec/status', methods=['GET'])
def crowd_density_status():
    try:
        lot_id = request.args.get('lot_id')
        entries = ParkingEvent.query.filter(ParkingEvent.event_type == 'ENTER',
                                            ParkingEvent.timestamp > utc_now() - timedelta(minutes=10)).count()
        rate = entries / 10.0
        if rate > 5:
            action = "SLOW_ENTRY"
        elif rate > 2:
            action = "NORMAL"
        else:
            action = "FAST"
        density = CrowdDensityLog(lot_id=lot_id, entry_rate=rate, timestamp=utc_now())
        db.session.add(density)
        db.session.commit()
        return jsonify({'entry_rate_per_min': rate, 'action': action})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
=======
    offer = MarketplaceOffer.query.get(offer_id)
    if not offer or offer.status != 'open':
        return jsonify({'error': 'Offer not available'}), 400
    booking = Booking.query.get(offer.booking_id)
    booking.user_id = session['user_id']
    refund_amount = offer.offered_price * 0.8
    offer.status = 'taken'
    db.session.commit()
    return jsonify({'success': True, 'refund_to_original': refund_amount})

@app.route('/api/cdaec/status', methods=['GET'])
def crowd_density_status():
    lot_id = request.args.get('lot_id')
    entries = ParkingEvent.query.filter(ParkingEvent.event_type == 'ENTER',
                                        ParkingEvent.timestamp > datetime.utcnow() - timedelta(minutes=10)).count()
    rate = entries / 10.0
    if rate > 5:
        action = "SLOW_ENTRY"
    elif rate > 2:
        action = "NORMAL"
    else:
        action = "FAST"
    density = CrowdDensityLog(lot_id=lot_id, entry_rate=rate, timestamp=datetime.utcnow())
    db.session.add(density)
    db.session.commit()
    return jsonify({'entry_rate_per_min': rate, 'action': action})
>>>>>>> 7ebede44f5c73607d3c179bd817ed9f9cc955866

# ---------- Admin Endpoints ----------
@app.route('/admin/users')
@admin_required
def admin_users():
    users = User.query.all()
    return jsonify([{'id': u.id, 'username': u.username, 'email': u.email, 'full_name': u.full_name or '', 'is_admin': u.is_admin} for u in users])

@app.route('/admin/bookings')
@admin_required
def admin_bookings():
    bookings = Booking.query.order_by(Booking.start_time.desc()).all()
<<<<<<< HEAD
    return jsonify([{'id': b.id, 'lot_id': b.lot_id, 'slot_id': b.slot_id, 'user_id': b.user_id, 'amount_paid': b.amount_paid, 'status': b.status, 'checked_in': b.checked_in, 'qr_code': b.qr_code, 'payment_status': b.payment_status} for b in bookings])
=======
    return jsonify([{'id': b.id, 'lot_id': b.lot_id, 'slot_id': b.slot_id, 'user_id': b.user_id, 'amount_paid': b.amount_paid, 'status': b.status} for b in bookings])
>>>>>>> 7ebede44f5c73607d3c179bd817ed9f9cc955866

@app.route('/admin/keys')
@admin_required
def admin_keys():
    keys = ApiKey.query.all()
    return jsonify([{'user_id': k.user_id, 'user_name': k.user_name, 'expires_at': k.expires_at.isoformat(), 'permissions': k.permissions, 'is_active': k.is_active} for k in keys])

@app.route('/admin/generate-key', methods=['POST'])
@admin_required
def generate_key():
    data = request.json
    key = str(uuid.uuid4())
    api_key = ApiKey(key_hash=bcrypt.hashpw(key.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
                     user_id=data.get('user_id'), user_name=data.get('user_name'),
<<<<<<< HEAD
                     expires_at=utc_now() + timedelta(days=365), permissions=data.get('permissions', 'read'))
=======
                     expires_at=datetime.utcnow() + timedelta(days=365), permissions=data.get('permissions', 'read'))
>>>>>>> 7ebede44f5c73607d3c179bd817ed9f9cc955866
    db.session.add(api_key)
    db.session.commit()
    return jsonify({'key': key})

@app.route('/admin/keys/<int:user_id>', methods=['DELETE'])
@admin_required
def deactivate_key(user_id):
    api_key = ApiKey.query.filter_by(user_id=user_id).first()
    if api_key:
        api_key.is_active = False
        db.session.commit()
    return jsonify({'success': True})

@app.route('/admin/ai-insight/<lot_id>', methods=['GET'])
@admin_required
def ai_insight(lot_id):
    lot = ParkingLot.query.get(lot_id)
    if not lot:
        return jsonify({'error': 'Lot not found'}), 404
    total = ParkingSlot.query.filter_by(lot_id=lot.id).count()
    occupied = ParkingSlot.query.filter_by(lot_id=lot.id, is_available=False).count()
    prompt = f"Insight for {lot.name} (location {lot.location}): total {total}, occupied {occupied}. Suggest improvements."
    try:
        model = genai.GenerativeModel('models/gemini-2.0-flash')
        response = model.generate_content(prompt)
        insight = response.text
<<<<<<< HEAD
    except:
=======
    except Exception as e:
>>>>>>> 7ebede44f5c73607d3c179bd817ed9f9cc955866
        insight = f"AI insight unavailable. Current occupancy: {occupied}/{total} slots filled."
    return jsonify({'insight': insight})

@app.route('/admin/ai-activity')
@admin_required
def ai_activity_log():
    logs = AiActivity.query.order_by(AiActivity.timestamp.desc()).limit(100).all()
    return jsonify([{'username': log.username, 'query': log.query[:100], 'response': log.response[:200], 'timestamp': log.timestamp.isoformat()} for log in logs])

@app.route('/admin/settings', methods=['POST'])
@admin_required
def update_settings():
    data = request.json
    upi_id = data.get('upi_id')
    if not upi_id:
        return jsonify({'error': 'UPI ID required'}), 400
    setting = Setting.query.filter_by(key='upi_id').first()
    if setting:
        setting.value = upi_id
    else:
        setting = Setting(key='upi_id', value=upi_id)
        db.session.add(setting)
    db.session.commit()
    return jsonify({'success': True})

# ---------- Sensor Update ----------
@app.route('/sensor/update', methods=['POST'])
def sensor_update():
    api_key = request.headers.get('X-API-Key')
    if not api_key or ApiKey.query.filter_by(is_active=True).first() is None:
        return jsonify({'error': 'Invalid API key'}), 401
    data = request.json
    lot_id, slot_id, status = data.get('lot_id'), data.get('slot_id'), data.get('status')
    if not all([lot_id, slot_id, status]):
        return jsonify({'error': 'Missing data'}), 400
    slot = ParkingSlot.query.filter_by(lot_id=lot_id, slot_id=slot_id).first()
    if slot:
        slot.is_available = (status == 'FREE')
        if not slot.is_available:
            slot.occupied_by = 'sensor'
<<<<<<< HEAD
            slot.occupied_since = utc_now()
=======
            slot.occupied_since = datetime.utcnow()
>>>>>>> 7ebede44f5c73607d3c179bd817ed9f9cc955866
        else:
            slot.occupied_by = None
            slot.occupied_since = None
            slot.reserved_by = None
            slot.reserved_until = None
<<<<<<< HEAD
=======
            slot.future_reserved_by = None
            slot.future_reserved_until = None
>>>>>>> 7ebede44f5c73607d3c179bd817ed9f9cc955866
        db.session.commit()
    return jsonify({'success': True})

if __name__ == '__main__':
    with app.app_context():
        init_db()
<<<<<<< HEAD
    app.run(host='0.0.0.0', debug=False, port=5000)
=======
    app.run(debug=True, port=5001)
>>>>>>> 7ebede44f5c73607d3c179bd817ed9f9cc955866
