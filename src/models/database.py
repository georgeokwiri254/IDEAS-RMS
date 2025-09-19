import sqlite3
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Date, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class RoomType(Base):
    __tablename__ = 'room_types'

    type_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    capacity = Column(Integer, nullable=False)
    base_rate = Column(Float, nullable=False)

class Inventory(Base):
    __tablename__ = 'inventory'

    room_id = Column(Integer, primary_key=True)
    room_type = Column(String(50), nullable=False)
    hotel_id = Column(String(20), default='GM_DUBAI')
    status = Column(String(20), default='available')

class Booking(Base):
    __tablename__ = 'bookings'

    booking_id = Column(Integer, primary_key=True)
    room_type = Column(String(50), nullable=False)
    checkin = Column(Date, nullable=False)
    checkout = Column(Date, nullable=False)
    rate = Column(Float, nullable=False)
    channel = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    guest_name = Column(String(100))
    booking_status = Column(String(20), default='confirmed')

class CompetitorRate(Base):
    __tablename__ = 'competitor_rates'

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    competitor_id = Column(String(50), nullable=False)
    room_type = Column(String(50), nullable=False)
    rate = Column(Float, nullable=False)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    availability = Column(Boolean, default=True)

class PriceHistory(Base):
    __tablename__ = 'price_history'

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    room_type = Column(String(50), nullable=False)
    published_rate = Column(Float, nullable=False)
    channel = Column(String(50), nullable=False)
    floor = Column(Float)
    ceiling = Column(Float)
    source = Column(String(50), default='pricing_engine')
    created_at = Column(DateTime, default=datetime.utcnow)

class ChannelRule(Base):
    __tablename__ = 'channel_rules'

    channel_id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    commission_pct = Column(Float, nullable=False)
    loyalty_discount_pct = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)

class EventMultiplier(Base):
    __tablename__ = 'event_multipliers'

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    event_name = Column(String(200))
    multiplier = Column(Float, default=1.0)
    description = Column(Text)

class ForecastData(Base):
    __tablename__ = 'forecast_data'

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    room_type = Column(String(50), nullable=False)
    forecasted_demand = Column(Float)
    booking_pace = Column(Float)
    current_occupancy = Column(Float)
    competitor_index = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)

class PushLog(Base):
    __tablename__ = 'push_log'

    id = Column(Integer, primary_key=True)
    channel = Column(String(50), nullable=False)
    room_type = Column(String(50), nullable=False)
    date = Column(Date, nullable=False)
    rate = Column(Float, nullable=False)
    status = Column(String(20), default='pending')
    response_message = Column(Text)
    pushed_at = Column(DateTime, default=datetime.utcnow)

def create_database(db_path='data/rms.db'):
    """Create database and all tables"""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    engine = create_engine(f'sqlite:///{db_path}')
    Base.metadata.create_all(engine)

    return engine

def get_session(db_path='data/rms.db'):
    """Get database session"""
    engine = create_engine(f'sqlite:///{db_path}')
    Session = sessionmaker(bind=engine)
    return Session()

if __name__ == "__main__":
    # Create the database when run directly
    engine = create_database()
    print("Database and tables created successfully!")