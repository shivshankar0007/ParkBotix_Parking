# migrate_db.py
from app import app
from models import db
from sqlalchemy import text

with app.app_context():
    try:
        db.session.execute(text("ALTER TABLE parking_slots ADD COLUMN future_reserved_by INTEGER REFERENCES users(id)"))
        print("✅ Added future_reserved_by")
    except Exception as e:
        print(f"future_reserved_by already exists: {e}")
    
    try:
        db.session.execute(text("ALTER TABLE parking_slots ADD COLUMN future_reserved_until DATETIME"))
        print("✅ Added future_reserved_until")
    except Exception as e:
        print(f"future_reserved_until already exists: {e}")
    
    db.session.commit()
    print("Migration complete!")