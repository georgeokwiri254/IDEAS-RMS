#!/usr/bin/env python3
"""
Simple database setup script for Grand Millennium Dubai RMS
Creates SQLite database and basic data without complex dependencies
"""

import sqlite3
import random
from datetime import datetime, date, timedelta
import os

def create_database_tables(db_path='data/rms.db'):
    """Create database and all tables using raw SQL"""

    # Ensure data directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables
    print("Creating database tables...")

    # Room Types table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS room_types (
            type_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            capacity INTEGER NOT NULL,
            base_rate REAL NOT NULL
        )
    ''')

    # Inventory table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            room_id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_type TEXT NOT NULL,
            hotel_id TEXT DEFAULT 'GM_DUBAI',
            status TEXT DEFAULT 'available'
        )
    ''')

    # Bookings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            booking_id INTEGER PRIMARY KEY,
            room_type TEXT NOT NULL,
            checkin DATE NOT NULL,
            checkout DATE NOT NULL,
            rate REAL NOT NULL,
            channel TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            guest_name TEXT,
            booking_status TEXT DEFAULT 'confirmed'
        )
    ''')

    # Competitor Rates table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS competitor_rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            competitor_id TEXT NOT NULL,
            room_type TEXT NOT NULL,
            rate REAL NOT NULL,
            scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            availability BOOLEAN DEFAULT 1
        )
    ''')

    # Price History table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            room_type TEXT NOT NULL,
            published_rate REAL NOT NULL,
            channel TEXT NOT NULL,
            floor REAL,
            ceiling REAL,
            source TEXT DEFAULT 'pricing_engine',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Channel Rules table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS channel_rules (
            channel_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            commission_pct REAL NOT NULL,
            loyalty_discount_pct REAL DEFAULT 0.0,
            is_active BOOLEAN DEFAULT 1
        )
    ''')

    # Event Multipliers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS event_multipliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            event_name TEXT,
            multiplier REAL DEFAULT 1.0,
            description TEXT
        )
    ''')

    # Forecast Data table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS forecast_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            room_type TEXT NOT NULL,
            forecasted_demand REAL,
            booking_pace REAL,
            current_occupancy REAL,
            competitor_index REAL DEFAULT 1.0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Push Log table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS push_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel TEXT NOT NULL,
            room_type TEXT NOT NULL,
            date DATE NOT NULL,
            rate REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            response_message TEXT,
            pushed_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    print("✓ Database tables created successfully")
    return conn

def populate_basic_data(conn):
    """Populate database with basic data for Grand Millennium Dubai"""

    cursor = conn.cursor()

    print("Populating basic data...")

    # Clear existing data
    tables = ['room_types', 'inventory', 'bookings', 'competitor_rates',
              'price_history', 'channel_rules', 'event_multipliers', 'forecast_data', 'push_log']

    for table in tables:
        cursor.execute(f'DELETE FROM {table}')

    # Room Types Data (339 rooms total)
    room_types_data = [
        (1, 'Deluxe', 2, 280, 120),
        (2, 'Club King', 2, 350, 60),
        (3, 'Club Twin', 2, 330, 50),
        (4, 'One-Bedroom', 3, 450, 60),
        (5, 'Two-Bedroom', 4, 700, 40),
        (6, 'Executive Suite', 2, 900, 9)
    ]

    print("Creating room types and inventory...")
    total_rooms = 0
    for type_id, name, capacity, base_rate, count in room_types_data:
        # Insert room type
        cursor.execute('''
            INSERT INTO room_types (type_id, name, capacity, base_rate)
            VALUES (?, ?, ?, ?)
        ''', (type_id, name, capacity, base_rate))

        # Create inventory rooms for this type
        for i in range(count):
            cursor.execute('''
                INSERT INTO inventory (room_type, hotel_id, status)
                VALUES (?, ?, ?)
            ''', (name, 'GM_DUBAI', 'available'))
            total_rooms += 1

    print(f"✓ Created {total_rooms} rooms across 6 room types")

    # Channel Rules
    channels_data = [
        ('DIRECT', 'Direct Booking', 0.0, 0.0, 1),
        ('BOOKING_COM', 'Booking.com', 0.15, 0.10, 1),
        ('EXPEDIA', 'Expedia', 0.18, 0.12, 1),
        ('AGODA', 'Agoda', 0.15, 0.08, 1),
        ('OTA_OTHERS', 'Other OTAs', 0.20, 0.05, 1)
    ]

    print("Creating channel rules...")
    for channel_id, name, commission, loyalty_discount, is_active in channels_data:
        cursor.execute('''
            INSERT INTO channel_rules (channel_id, name, commission_pct, loyalty_discount_pct, is_active)
            VALUES (?, ?, ?, ?, ?)
        ''', (channel_id, name, commission, loyalty_discount, is_active))

    # 5 Competitor Hotels
    competitors = [
        'Voco-Dubai',
        'Movenpick-BB',
        'Hotel Aster',
        'Azure Grand',
        'Palmview'
    ]

    # Generate sample bookings for past 30 days
    print("Generating sample bookings...")
    booking_id = 1
    start_date = date.today() - timedelta(days=30)
    end_date = date.today() + timedelta(days=30)

    current_date = start_date
    while current_date <= end_date:
        # Generate 5-15 bookings per day
        daily_bookings = random.randint(5, 15)

        for _ in range(daily_bookings):
            room_type_data = random.choice(room_types_data)
            room_type = room_type_data[1]
            base_rate = room_type_data[3]

            # Add some randomness to rates (±20%)
            rate = base_rate * random.uniform(0.8, 1.2)

            # Random stay length 1-4 nights
            stay_length = random.randint(1, 4)
            checkout_date = current_date + timedelta(days=stay_length)

            channel = random.choice(['DIRECT', 'BOOKING_COM', 'EXPEDIA', 'AGODA', 'OTA_OTHERS'])

            cursor.execute('''
                INSERT INTO bookings (booking_id, room_type, checkin, checkout, rate, channel, guest_name, booking_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (booking_id, room_type, current_date, checkout_date, rate, channel, f"Guest_{booking_id}", 'confirmed'))

            booking_id += 1

        current_date += timedelta(days=1)

    print(f"✓ Generated {booking_id-1} bookings")

    # Generate competitor rates for next 30 days
    print("Generating competitor rates...")
    comp_start_date = date.today()
    comp_end_date = comp_start_date + timedelta(days=30)

    current_date = comp_start_date
    while current_date <= comp_end_date:
        for competitor in competitors:
            for _, room_type, _, base_rate, _ in room_types_data:
                # Competitor rates around our base rates ±30%
                comp_rate = base_rate * random.uniform(0.7, 1.3)
                availability = random.choice([1, 1, 1, 0])  # 75% availability

                cursor.execute('''
                    INSERT INTO competitor_rates (date, competitor_id, room_type, rate, availability)
                    VALUES (?, ?, ?, ?, ?)
                ''', (current_date, competitor, room_type, comp_rate, availability))

        current_date += timedelta(days=1)

    print("✓ Generated competitor rates for 30 days")

    # Generate some special events
    print("Creating event multipliers...")
    events = [
        (date.today() + timedelta(days=15), 'Dubai Shopping Festival', 1.25, 'Annual shopping festival'),
        (date.today() + timedelta(days=30), 'Business Conference Week', 1.15, 'Major business conference'),
        (date.today() + timedelta(days=45), 'International Expo', 1.40, 'International trade expo'),
    ]

    for event_date, event_name, multiplier, description in events:
        cursor.execute('''
            INSERT INTO event_multipliers (date, event_name, multiplier, description)
            VALUES (?, ?, ?, ?)
        ''', (event_date, event_name, multiplier, description))

    # Generate initial forecast data for next 30 days
    print("Creating initial forecast data...")
    forecast_start = date.today()
    forecast_end = forecast_start + timedelta(days=30)

    current_date = forecast_start
    while current_date <= forecast_end:
        for _, room_type, _, _, _ in room_types_data:
            # Generate forecast based on seasonality and events
            base_demand = 0.75  # 75% occupancy baseline

            # Weekend boost
            if current_date.weekday() >= 5:  # Saturday, Sunday
                base_demand *= 1.1

            # Random variation
            forecasted_demand = base_demand * random.uniform(0.8, 1.2)
            booking_pace = random.uniform(0.5, 1.5)
            current_occupancy = random.uniform(0.6, 0.9)
            competitor_index = random.uniform(0.85, 1.15)

            cursor.execute('''
                INSERT INTO forecast_data (date, room_type, forecasted_demand, booking_pace, current_occupancy, competitor_index)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (current_date, room_type, forecasted_demand, booking_pace, current_occupancy, competitor_index))

        current_date += timedelta(days=1)

    conn.commit()
    print("✓ All data populated successfully")

def verify_data(conn):
    """Verify the populated data"""

    cursor = conn.cursor()

    print("\nVerifying database content:")
    print("-" * 40)

    # Check room types and inventory
    cursor.execute('SELECT COUNT(*) FROM room_types')
    room_type_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM inventory')
    inventory_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM bookings')
    booking_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM competitor_rates')
    competitor_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM channel_rules')
    channel_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM event_multipliers')
    event_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM forecast_data')
    forecast_count = cursor.fetchone()[0]

    print(f"✓ Room Types: {room_type_count}")
    print(f"✓ Inventory: {inventory_count} rooms")
    print(f"✓ Bookings: {booking_count}")
    print(f"✓ Competitor Rates: {competitor_count}")
    print(f"✓ Channels: {channel_count}")
    print(f"✓ Events: {event_count}")
    print(f"✓ Forecasts: {forecast_count}")

    # Show room type breakdown
    print("\nRoom Type Distribution:")
    cursor.execute('SELECT room_type, COUNT(*) FROM inventory GROUP BY room_type ORDER BY COUNT(*) DESC')
    for room_type, count in cursor.fetchall():
        cursor.execute('SELECT base_rate FROM room_types WHERE name = ?', (room_type,))
        result = cursor.fetchone()
        if result:
            base_rate = result[0]
            print(f"  {room_type}: {count} rooms @ {base_rate} AED base rate")

def main():
    """Main setup function"""

    print("=" * 60)
    print("GRAND MILLENNIUM DUBAI RMS - DATABASE SETUP")
    print("=" * 60)

    db_path = 'data/rms.db'

    try:
        # Create database and tables
        conn = create_database_tables(db_path)

        # Populate with sample data
        populate_basic_data(conn)

        # Verify everything was created correctly
        verify_data(conn)

        conn.close()

        print("\n" + "=" * 60)
        print("DATABASE SETUP COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"Database created at: {db_path}")
        print("Ready to run the RMS application!")
        print("\nNext steps:")
        print("1. Install required packages: pip install streamlit pandas numpy sqlalchemy plotly")
        print("2. Run the app: streamlit run app.py")

    except Exception as e:
        print(f"Error during setup: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())