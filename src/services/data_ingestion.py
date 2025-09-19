import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
import json
import csv
import requests
from sqlalchemy.orm import sessionmaker
from ..models.database import *
import time
import random

class DataIngestionPipeline:
    """
    Data ingestion pipeline for PMS and competitor data

    In production this would connect to:
    - PMS systems (Opera, Protel, etc.) via APIs or scheduled exports
    - Competitor rate data via scraping, APIs, or third-party services
    - External data sources (weather, events, etc.)

    For prototype: simulates realistic data ingestion processes
    """

    def __init__(self, db_path='data/rms.db'):
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}')
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        # Competitor sources configuration
        self.competitor_sources = {
            'Voco-Dubai': {
                'method': 'api',
                'url': 'https://api.voco-hotels.com/rates',
                'auth': 'api_key',
                'room_mapping': {
                    'standard': 'Deluxe',
                    'superior': 'Club King',
                    'deluxe': 'Club Twin',
                    'suite': 'One-Bedroom'
                }
            },
            'Movenpick-BB': {
                'method': 'scraping',
                'url': 'https://movenpick.com/booking',
                'selectors': {
                    'rate': '.room-rate',
                    'availability': '.availability-status'
                },
                'room_mapping': {
                    'classic': 'Deluxe',
                    'premium': 'Club King',
                    'executive': 'One-Bedroom'
                }
            },
            'Hotel Aster': {
                'method': 'csv_feed',
                'url': 'https://hotelaster.com/feeds/rates.csv',
                'format': 'csv',
                'room_mapping': {
                    'standard_room': 'Deluxe',
                    'business_room': 'Club King',
                    'suite_room': 'Two-Bedroom'
                }
            },
            'Azure Grand': {
                'method': 'xml_feed',
                'url': 'https://azuregrand.com/xml/rates.xml',
                'format': 'xml',
                'room_mapping': {
                    'economy': 'Deluxe',
                    'business': 'Club King',
                    'luxury': 'Executive Suite'
                }
            },
            'Palmview': {
                'method': 'api',
                'url': 'https://palmview-dubai.com/api/rates',
                'auth': 'oauth2',
                'room_mapping': {
                    'garden_view': 'Deluxe',
                    'city_view': 'Club King',
                    'suite': 'One-Bedroom'
                }
            }
        }

    def ingest_pms_data(self, start_date=None, end_date=None):
        """
        Ingest data from Property Management System

        In production: connects to Opera, Protel, or other PMS
        For prototype: simulates realistic PMS data extraction
        """

        if start_date is None:
            start_date = date.today() - timedelta(days=1)  # Yesterday
        if end_date is None:
            end_date = date.today() + timedelta(days=30)   # Next 30 days

        print(f"Starting PMS data ingestion for {start_date} to {end_date}")

        # Simulate PMS API connection
        time.sleep(0.5)  # Simulate network delay

        # Get room types for realistic data generation
        room_types = self.session.query(RoomType).all()

        new_bookings = 0
        updated_inventory = 0

        current_date = start_date
        while current_date <= end_date:
            # Simulate daily PMS extract
            daily_data = self._simulate_pms_extract(current_date, room_types)

            # Process bookings
            for booking_data in daily_data['bookings']:
                # Check if booking already exists
                existing = self.session.query(Booking).filter_by(
                    booking_id=booking_data['booking_id']
                ).first()

                if not existing:
                    booking = Booking(
                        booking_id=booking_data['booking_id'],
                        room_type=booking_data['room_type'],
                        checkin=booking_data['checkin'],
                        checkout=booking_data['checkout'],
                        rate=booking_data['rate'],
                        channel=booking_data['channel'],
                        created_at=booking_data['created_at'],
                        guest_name=booking_data['guest_name'],
                        booking_status=booking_data['status']
                    )
                    self.session.add(booking)
                    new_bookings += 1

            # Update inventory status
            for inv_data in daily_data['inventory_updates']:
                inventory_items = self.session.query(Inventory).filter_by(
                    room_type=inv_data['room_type']
                ).limit(inv_data['rooms_to_update']).all()

                for item in inventory_items:
                    item.status = inv_data['new_status']
                    updated_inventory += 1

            current_date += timedelta(days=1)

        # Commit changes
        self.session.commit()

        print(f"PMS ingestion completed:")
        print(f"  - New bookings: {new_bookings}")
        print(f"  - Updated inventory: {updated_inventory}")

        return {
            'status': 'success',
            'new_bookings': new_bookings,
            'updated_inventory': updated_inventory,
            'processed_dates': (end_date - start_date).days + 1
        }

    def ingest_competitor_data(self, competitors=None, days_ahead=30):
        """
        Ingest competitor rate data from various sources

        Args:
            competitors: List of competitor names (if None, all competitors)
            days_ahead: Number of days to fetch data for
        """

        if competitors is None:
            competitors = list(self.competitor_sources.keys())

        print(f"Starting competitor data ingestion for {len(competitors)} competitors")

        start_date = date.today()
        end_date = start_date + timedelta(days=days_ahead)

        total_rates = 0
        failed_sources = []

        for competitor in competitors:
            if competitor not in self.competitor_sources:
                print(f"Warning: No source configuration for {competitor}")
                continue

            source_config = self.competitor_sources[competitor]

            try:
                print(f"  Processing {competitor} via {source_config['method']}")

                # Simulate different ingestion methods
                rates_data = self._fetch_competitor_rates(competitor, source_config, start_date, end_date)

                # Save to database
                for rate_data in rates_data:
                    # Check if rate already exists
                    existing = self.session.query(CompetitorRate).filter_by(
                        competitor_id=competitor,
                        date=rate_data['date'],
                        room_type=rate_data['room_type']
                    ).first()

                    if existing:
                        # Update existing rate
                        existing.rate = rate_data['rate']
                        existing.availability = rate_data['availability']
                        existing.scraped_at = datetime.now()
                    else:
                        # Create new rate
                        comp_rate = CompetitorRate(
                            competitor_id=competitor,
                            date=rate_data['date'],
                            room_type=rate_data['room_type'],
                            rate=rate_data['rate'],
                            availability=rate_data['availability'],
                            scraped_at=datetime.now()
                        )
                        self.session.add(comp_rate)

                    total_rates += 1

                print(f"    Collected {len(rates_data)} rates")

            except Exception as e:
                print(f"    Failed to collect data: {str(e)}")
                failed_sources.append(competitor)

        # Commit changes
        self.session.commit()

        print(f"Competitor ingestion completed:")
        print(f"  - Total rates collected: {total_rates}")
        print(f"  - Failed sources: {len(failed_sources)}")

        return {
            'status': 'success' if len(failed_sources) == 0 else 'partial',
            'total_rates': total_rates,
            'successful_sources': len(competitors) - len(failed_sources),
            'failed_sources': failed_sources
        }

    def calculate_booking_pace_metrics(self, room_type=None, days_back=30):
        """
        Calculate booking pace and pickup metrics

        Args:
            room_type: Specific room type (if None, all room types)
            days_back: Number of days to look back for calculation
        """

        print(f"Calculating booking pace metrics for last {days_back} days")

        end_date = date.today()
        start_date = end_date - timedelta(days=days_back)

        # Get room types to process
        if room_type:
            room_types = [room_type]
        else:
            room_types_query = self.session.query(RoomType).all()
            room_types = [rt.name for rt in room_types_query]

        pace_metrics = []

        for rt in room_types:
            # Get bookings for this room type in the period
            bookings = self.session.query(Booking).filter(
                Booking.room_type == rt,
                Booking.created_at >= start_date,
                Booking.created_at <= end_date
            ).all()

            if not bookings:
                continue

            # Calculate metrics
            total_bookings = len(bookings)
            total_revenue = sum(b.rate for b in bookings)

            # Group by arrival date
            pickup_by_date = {}
            for booking in bookings:
                arrival_date = booking.checkin
                if arrival_date not in pickup_by_date:
                    pickup_by_date[arrival_date] = {'count': 0, 'revenue': 0}

                pickup_by_date[arrival_date]['count'] += 1
                pickup_by_date[arrival_date]['revenue'] += booking.rate

            # Calculate pace trends (last 7 days vs previous 7 days)
            recent_period = end_date - timedelta(days=7)
            recent_bookings = [b for b in bookings if b.created_at >= recent_period]
            previous_bookings = [b for b in bookings if b.created_at < recent_period and b.created_at >= recent_period - timedelta(days=7)]

            recent_pace = len(recent_bookings) / 7 if recent_bookings else 0
            previous_pace = len(previous_bookings) / 7 if previous_bookings else 0
            pace_change = ((recent_pace - previous_pace) / max(previous_pace, 0.1)) * 100

            # Calculate lead time distribution
            lead_times = [(b.checkin - b.created_at.date()).days for b in bookings if b.checkin >= b.created_at.date()]
            avg_lead_time = np.mean(lead_times) if lead_times else 0

            metrics = {
                'room_type': rt,
                'period': f"{start_date} to {end_date}",
                'total_bookings': total_bookings,
                'total_revenue': total_revenue,
                'avg_daily_pickup': total_bookings / days_back,
                'recent_pace': recent_pace,
                'pace_change_pct': pace_change,
                'avg_lead_time': avg_lead_time,
                'pickup_by_date': pickup_by_date
            }

            pace_metrics.append(metrics)

            # Update forecast data with calculated metrics
            self._update_forecast_with_pace(rt, metrics)

        print(f"Calculated pace metrics for {len(pace_metrics)} room types")

        return pace_metrics

    def run_full_ingestion_cycle(self):
        """Run complete data ingestion cycle"""

        print("=" * 50)
        print("STARTING FULL DATA INGESTION CYCLE")
        print("=" * 50)

        results = {
            'start_time': datetime.now(),
            'pms_result': None,
            'competitor_result': None,
            'pace_metrics': None,
            'status': 'running'
        }

        try:
            # 1. PMS Data Ingestion
            print("\n1. PMS DATA INGESTION")
            print("-" * 30)
            results['pms_result'] = self.ingest_pms_data()

            # 2. Competitor Data Ingestion
            print("\n2. COMPETITOR DATA INGESTION")
            print("-" * 30)
            results['competitor_result'] = self.ingest_competitor_data()

            # 3. Booking Pace Calculation
            print("\n3. BOOKING PACE ANALYTICS")
            print("-" * 30)
            results['pace_metrics'] = self.calculate_booking_pace_metrics()

            # 4. Update forecast data
            print("\n4. FORECAST DATA UPDATE")
            print("-" * 30)
            self._update_forecasts()

            results['status'] = 'completed'
            results['end_time'] = datetime.now()
            results['duration'] = results['end_time'] - results['start_time']

            print("\n" + "=" * 50)
            print("INGESTION CYCLE COMPLETED SUCCESSFULLY")
            print("=" * 50)
            print(f"Duration: {results['duration']}")

        except Exception as e:
            results['status'] = 'failed'
            results['error'] = str(e)
            print(f"\nIngestion cycle failed: {e}")

        return results

    def _simulate_pms_extract(self, target_date, room_types):
        """Simulate PMS data extraction for a specific date"""

        # Generate realistic booking data
        bookings = []
        inventory_updates = []

        # Generate 5-15 new bookings per day
        num_bookings = random.randint(5, 15)

        for i in range(num_bookings):
            room_type = random.choice(room_types)
            base_rate = room_type.base_rate

            # Add rate variation
            rate = base_rate * random.uniform(0.8, 1.2)

            # Random stay length
            stay_length = random.randint(1, 5)
            checkout_date = target_date + timedelta(days=stay_length)

            # Channel distribution
            channels = ['DIRECT', 'BOOKING_COM', 'EXPEDIA', 'AGODA', 'OTA_OTHERS']
            channel_weights = [0.3, 0.25, 0.2, 0.15, 0.1]
            channel = np.random.choice(channels, p=channel_weights)

            booking_id = int(f"{target_date.strftime('%Y%m%d')}{i:04d}")

            bookings.append({
                'booking_id': booking_id,
                'room_type': room_type.name,
                'checkin': target_date,
                'checkout': checkout_date,
                'rate': rate,
                'channel': channel,
                'created_at': datetime.now() - timedelta(hours=random.randint(1, 24)),
                'guest_name': f"Guest_{booking_id}",
                'status': 'confirmed'
            })

        # Simulate inventory updates
        for room_type in room_types:
            # Random inventory status changes
            if random.random() < 0.1:  # 10% chance of inventory update
                inventory_updates.append({
                    'room_type': room_type.name,
                    'rooms_to_update': random.randint(1, 3),
                    'new_status': random.choice(['maintenance', 'available', 'ooo'])
                })

        return {
            'bookings': bookings,
            'inventory_updates': inventory_updates
        }

    def _fetch_competitor_rates(self, competitor, config, start_date, end_date):
        """Simulate fetching competitor rates based on method"""

        rates = []
        method = config['method']

        # Simulate different collection methods
        if method == 'api':
            rates = self._simulate_api_collection(competitor, config, start_date, end_date)
        elif method == 'scraping':
            rates = self._simulate_scraping_collection(competitor, config, start_date, end_date)
        elif method == 'csv_feed':
            rates = self._simulate_csv_collection(competitor, config, start_date, end_date)
        elif method == 'xml_feed':
            rates = self._simulate_xml_collection(competitor, config, start_date, end_date)

        return rates

    def _simulate_api_collection(self, competitor, config, start_date, end_date):
        """Simulate API-based rate collection"""
        time.sleep(0.2)  # Simulate API delay

        rates = []
        room_mapping = config['room_mapping']

        current_date = start_date
        while current_date <= end_date:
            for comp_room, our_room in room_mapping.items():
                # Get our base rate for reference
                our_base = self.session.query(RoomType).filter_by(name=our_room).first()
                base_rate = our_base.base_rate if our_base else 300

                # Generate competitor rate around our rate ±30%
                comp_rate = base_rate * random.uniform(0.7, 1.3)

                rates.append({
                    'date': current_date,
                    'room_type': our_room,
                    'rate': comp_rate,
                    'availability': random.choice([True, True, True, False])  # 75% availability
                })

            current_date += timedelta(days=1)

        return rates

    def _simulate_scraping_collection(self, competitor, config, start_date, end_date):
        """Simulate web scraping rate collection"""
        time.sleep(0.5)  # Simulate scraping delay

        # Similar to API but with slightly less data coverage
        rates = []
        room_mapping = config['room_mapping']

        current_date = start_date
        while current_date <= end_date:
            # Skip some dates to simulate scraping limitations
            if random.random() < 0.1:  # 10% chance of missing data
                current_date += timedelta(days=1)
                continue

            for comp_room, our_room in room_mapping.items():
                our_base = self.session.query(RoomType).filter_by(name=our_room).first()
                base_rate = our_base.base_rate if our_base else 300

                comp_rate = base_rate * random.uniform(0.7, 1.3)

                rates.append({
                    'date': current_date,
                    'room_type': our_room,
                    'rate': comp_rate,
                    'availability': random.choice([True, True, False])  # 67% availability
                })

            current_date += timedelta(days=1)

        return rates

    def _simulate_csv_collection(self, competitor, config, start_date, end_date):
        """Simulate CSV feed collection"""
        time.sleep(0.1)  # Simulate file download

        return self._simulate_api_collection(competitor, config, start_date, end_date)

    def _simulate_xml_collection(self, competitor, config, start_date, end_date):
        """Simulate XML feed collection"""
        time.sleep(0.15)  # Simulate XML parsing

        return self._simulate_api_collection(competitor, config, start_date, end_date)

    def _update_forecast_with_pace(self, room_type, pace_metrics):
        """Update forecast data with calculated pace metrics"""

        # Update forecast for next 30 days
        start_date = date.today()
        end_date = start_date + timedelta(days=30)

        current_date = start_date
        while current_date <= end_date:
            existing_forecast = self.session.query(ForecastData).filter_by(
                room_type=room_type,
                date=current_date
            ).first()

            if existing_forecast:
                # Update booking pace
                existing_forecast.booking_pace = pace_metrics['recent_pace']
            else:
                # Create new forecast entry
                forecast = ForecastData(
                    room_type=room_type,
                    date=current_date,
                    forecasted_demand=0.75,  # Default baseline
                    booking_pace=pace_metrics['recent_pace'],
                    current_occupancy=random.uniform(0.6, 0.9),
                    competitor_index=1.0
                )
                self.session.add(forecast)

            current_date += timedelta(days=1)

    def _update_forecasts(self):
        """Update forecast data with latest intelligence"""
        print("Updating forecast models with latest data...")

        # This would run ML models in production
        # For prototype, update with realistic forecasted demand

        room_types = self.session.query(RoomType).all()
        start_date = date.today()
        end_date = start_date + timedelta(days=30)

        for room_type in room_types:
            current_date = start_date
            while current_date <= end_date:
                existing = self.session.query(ForecastData).filter_by(
                    room_type=room_type.name,
                    date=current_date
                ).first()

                if existing:
                    # Update with new forecast
                    base_demand = 0.75

                    # Weekend boost
                    if current_date.weekday() >= 5:
                        base_demand *= 1.1

                    # Add seasonality and random variation
                    existing.forecasted_demand = base_demand * random.uniform(0.8, 1.2)
                    existing.competitor_index = random.uniform(0.85, 1.15)

                current_date += timedelta(days=1)

        print("Forecast models updated")

    def close(self):
        """Close database session"""
        self.session.close()

if __name__ == "__main__":
    # Test the ingestion pipeline
    pipeline = DataIngestionPipeline()

    # Run full cycle
    results = pipeline.run_full_ingestion_cycle()
    print(f"\nFinal results: {results}")

    pipeline.close()