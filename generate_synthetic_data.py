import random
import sqlite3
from datetime import datetime, date, timedelta
from sqlalchemy.orm import sessionmaker
from src.models.database import *
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def generate_synthetic_data():
    """Generate synthetic data for Grand Millennium Dubai RMS prototype"""

    # Create database
    engine = create_database('data/rms.db')
    Session = sessionmaker(bind=engine)
    session = Session()

    # Clear existing data
    session.query(RoomType).delete()
    session.query(Inventory).delete()
    session.query(Booking).delete()
    session.query(CompetitorRate).delete()
    session.query(PriceHistory).delete()
    session.query(ChannelRule).delete()
    session.query(EventMultiplier).delete()
    session.query(ForecastData).delete()
    session.query(PushLog).delete()

    # Room Types Data (339 rooms total)
    room_types_data = [
        {'name': 'Deluxe', 'capacity': 2, 'base_rate': 280, 'count': 120},
        {'name': 'Club King', 'capacity': 2, 'base_rate': 350, 'count': 60},
        {'name': 'Club Twin', 'capacity': 2, 'base_rate': 330, 'count': 50},
        {'name': 'One-Bedroom', 'capacity': 3, 'base_rate': 450, 'count': 60},
        {'name': 'Two-Bedroom', 'capacity': 4, 'base_rate': 700, 'count': 40},
        {'name': 'Executive Suite', 'capacity': 2, 'base_rate': 900, 'count': 9}
    ]

    print("Creating room types...")
    room_type_id = 1
    for rt_data in room_types_data:
        room_type = RoomType(
            type_id=room_type_id,
            name=rt_data['name'],
            capacity=rt_data['capacity'],
            base_rate=rt_data['base_rate']
        )
        session.add(room_type)

        # Create inventory rooms for this type
        for i in range(rt_data['count']):
            room = Inventory(
                room_type=rt_data['name'],
                hotel_id='GM_DUBAI',
                status='available'
            )
            session.add(room)

        room_type_id += 1

    print("Created 339 rooms across 6 room types")

    # Channel Rules
    channels_data = [
        {'channel_id': 'DIRECT', 'name': 'Direct Booking', 'commission_pct': 0.0, 'loyalty_discount_pct': 0.0},
        {'channel_id': 'BOOKING_COM', 'name': 'Booking.com', 'commission_pct': 0.15, 'loyalty_discount_pct': 0.10},
        {'channel_id': 'EXPEDIA', 'name': 'Expedia', 'commission_pct': 0.18, 'loyalty_discount_pct': 0.12},
        {'channel_id': 'AGODA', 'name': 'Agoda', 'commission_pct': 0.15, 'loyalty_discount_pct': 0.08},
        {'channel_id': 'OTA_OTHERS', 'name': 'Other OTAs', 'commission_pct': 0.20, 'loyalty_discount_pct': 0.05}
    ]

    print("Creating channel rules...")
    for channel_data in channels_data:
        channel = ChannelRule(**channel_data)
        session.add(channel)

    # 5 Competitor Hotels
    competitors = [
        'Voco-Dubai',
        'Movenpick-BB',
        'Hotel Aster',
        'Azure Grand',
        'Palmview'
    ]

    # Generate bookings for past 90 days and future 90 days
    print("Generating booking history...")
    start_date = datetime.now().date() - timedelta(days=90)
    end_date = datetime.now().date() + timedelta(days=90)

    booking_id = 1
    current_date = start_date

    while current_date <= end_date:
        # Generate 10-25 bookings per day
        daily_bookings = random.randint(10, 25)

        for _ in range(daily_bookings):
            room_type = random.choice([rt['name'] for rt in room_types_data])
            base_rate = next(rt['base_rate'] for rt in room_types_data if rt['name'] == room_type)

            # Add some randomness to rates (±20%)
            rate = base_rate * random.uniform(0.8, 1.2)

            # Random stay length 1-5 nights
            stay_length = random.randint(1, 5)
            checkout_date = current_date + timedelta(days=stay_length)

            channel = random.choice(['DIRECT', 'BOOKING_COM', 'EXPEDIA', 'AGODA', 'OTA_OTHERS'])

            booking = Booking(
                booking_id=booking_id,
                room_type=room_type,
                checkin=current_date,
                checkout=checkout_date,
                rate=rate,
                channel=channel,
                created_at=datetime.now() - timedelta(days=random.randint(1, 30)),
                guest_name=f"Guest_{booking_id}",
                booking_status='confirmed'
            )
            session.add(booking)
            booking_id += 1

        current_date += timedelta(days=1)

    print(f"Generated {booking_id-1} bookings")

    # Generate competitor rates for next 60 days
    print("Generating competitor rates...")
    comp_start_date = datetime.now().date()
    comp_end_date = comp_start_date + timedelta(days=60)

    current_date = comp_start_date
    while current_date <= comp_end_date:
        for competitor in competitors:
            for rt_data in room_types_data:
                # Competitor rates around our base rates ±30%
                base_rate = rt_data['base_rate']
                comp_rate = base_rate * random.uniform(0.7, 1.3)

                comp_rate_entry = CompetitorRate(
                    date=current_date,
                    competitor_id=competitor,
                    room_type=rt_data['name'],
                    rate=comp_rate,
                    scraped_at=datetime.now(),
                    availability=random.choice([True, True, True, False])  # 75% availability
                )
                session.add(comp_rate_entry)

        current_date += timedelta(days=1)

    print("Generated competitor rates for 60 days")

    # Generate some special events
    print("Creating event multipliers...")
    events = [
        {'date': datetime.now().date() + timedelta(days=15), 'event_name': 'Dubai Shopping Festival', 'multiplier': 1.25},
        {'date': datetime.now().date() + timedelta(days=30), 'event_name': 'Business Conference Week', 'multiplier': 1.15},
        {'date': datetime.now().date() + timedelta(days=45), 'event_name': 'International Expo', 'multiplier': 1.40},
    ]

    for event in events:
        event_entry = EventMultiplier(**event)
        session.add(event_entry)

    # Generate initial price history
    print("Creating initial price history...")
    for rt_data in room_types_data:
        for channel_data in channels_data:
            # Generate price history for past 30 days
            for i in range(30):
                hist_date = datetime.now().date() - timedelta(days=i)
                base_rate = rt_data['base_rate']

                # Add some historical price variation
                published_rate = base_rate * random.uniform(0.9, 1.1)

                price_hist = PriceHistory(
                    date=hist_date,
                    room_type=rt_data['name'],
                    published_rate=published_rate,
                    channel=channel_data['channel_id'],
                    floor=base_rate * 0.7,  # 30% below base rate
                    ceiling=base_rate * 1.5,  # 50% above base rate
                    source='historical_data'
                )
                session.add(price_hist)

    # Generate initial forecast data
    print("Creating initial forecast data...")
    forecast_start = datetime.now().date()
    forecast_end = forecast_start + timedelta(days=30)

    current_date = forecast_start
    while current_date <= forecast_end:
        for rt_data in room_types_data:
            # Generate forecast based on seasonality and events
            base_demand = 0.75  # 75% occupancy baseline

            # Weekend boost
            if current_date.weekday() >= 5:  # Saturday, Sunday
                base_demand *= 1.1

            # Random variation
            forecasted_demand = base_demand * random.uniform(0.8, 1.2)

            # Booking pace (simulated)
            booking_pace = random.uniform(0.5, 1.5)

            # Current occupancy simulation
            current_occupancy = random.uniform(0.6, 0.9)

            # Competitor index (1.0 = parity)
            competitor_index = random.uniform(0.85, 1.15)

            forecast = ForecastData(
                date=current_date,
                room_type=rt_data['name'],
                forecasted_demand=forecasted_demand,
                booking_pace=booking_pace,
                current_occupancy=current_occupancy,
                competitor_index=competitor_index
            )
            session.add(forecast)

        current_date += timedelta(days=1)

    # Commit all data
    session.commit()
    session.close()

    print("\n" + "="*50)
    print("SYNTHETIC DATA GENERATION COMPLETE!")
    print("="*50)
    print(f"✓ Database created at: data/rms.db")
    print(f"✓ Room Types: 6 types totaling 339 rooms")
    print(f"✓ Bookings: {booking_id-1} historical and future bookings")
    print(f"✓ Competitors: 5 competitors with 60 days of rate data")
    print(f"✓ Channels: 5 distribution channels with rules")
    print(f"✓ Events: 3 special events configured")
    print(f"✓ Forecasts: 30 days of forecast data generated")
    print("\nNext step: Run 'streamlit run app.py' to start the RMS!")

if __name__ == "__main__":
    generate_synthetic_data()