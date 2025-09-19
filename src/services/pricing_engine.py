import numpy as np
from datetime import datetime, date, timedelta
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from ..models.database import *
import math

class PricingEngine:
    """
    Dynamic pricing engine for Grand Millennium Dubai RMS

    Formula: price = clip(base_rate * (1 + α*(forecasted_demand - baseline_demand))
                          * (1 + β*(competitor_index - 1))
                          * (1 + δ*event_multiplier)
                          * (1 - γ*time_to_arrival_factor),
                          floor, ceiling)
    """

    def __init__(self, db_path='data/rms.db'):
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}')
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        # Pricing coefficients (tunable parameters)
        self.alpha = 0.3    # Demand sensitivity
        self.beta = 0.25    # Competitor sensitivity
        self.gamma = 0.02   # Time decay factor
        self.delta = 1.0    # Event multiplier impact

        # Baseline settings
        self.baseline_demand = 0.75  # 75% occupancy baseline
        self.max_lead_time = 365     # Maximum lead time for pricing

    def get_base_rate(self, room_type):
        """Get base rate for room type"""
        room_type_obj = self.session.query(RoomType).filter_by(name=room_type).first()
        return room_type_obj.base_rate if room_type_obj else 300

    def get_forecasted_demand(self, room_type, target_date):
        """Get forecasted demand for specific room type and date"""
        forecast = self.session.query(ForecastData).filter_by(
            room_type=room_type,
            date=target_date
        ).first()

        if forecast:
            return forecast.forecasted_demand
        else:
            # Fallback: calculate based on recent booking pace
            return self._calculate_demand_fallback(room_type, target_date)

    def get_competitor_index(self, room_type, target_date):
        """Calculate competitor index (median competitor rate / our base rate)"""
        base_rate = self.get_base_rate(room_type)

        # Get competitor rates for the date
        competitor_rates = self.session.query(CompetitorRate).filter_by(
            room_type=room_type,
            date=target_date
        ).all()

        if competitor_rates:
            rates = [cr.rate for cr in competitor_rates if cr.availability]
            if rates:
                median_comp_rate = np.median(rates)
                return median_comp_rate / base_rate

        return 1.0  # Default to parity

    def get_event_multiplier(self, target_date):
        """Get event multiplier for specific date"""
        event = self.session.query(EventMultiplier).filter_by(date=target_date).first()
        return event.multiplier if event else 1.0

    def calculate_time_factor(self, target_date, lead_time_days=None):
        """Calculate time-to-arrival factor (closer dates = higher urgency)"""
        if lead_time_days is None:
            lead_time_days = (target_date - date.today()).days

        if lead_time_days <= 0:
            return 0  # Same day or past

        # Normalize lead time (closer dates get lower discount)
        normalized_lead_time = min(lead_time_days / self.max_lead_time, 1.0)
        return normalized_lead_time * 0.1  # Max 10% time-based discount

    def get_floor_ceiling(self, room_type):
        """Get floor and ceiling prices for room type"""
        base_rate = self.get_base_rate(room_type)

        # Default floor/ceiling (30% below, 50% above base rate)
        floor = base_rate * 0.7
        ceiling = base_rate * 1.5

        return floor, ceiling

    def calculate_dynamic_price(self, room_type, target_date, override_params=None):
        """
        Calculate dynamic price using the pricing formula

        Args:
            room_type: Room type (e.g., 'Deluxe', 'Club King')
            target_date: Date to price for
            override_params: Optional dict to override default coefficients

        Returns:
            dict with pricing details
        """
        # Use override parameters if provided
        alpha = override_params.get('alpha', self.alpha) if override_params else self.alpha
        beta = override_params.get('beta', self.beta) if override_params else self.beta
        gamma = override_params.get('gamma', self.gamma) if override_params else self.gamma
        delta = override_params.get('delta', self.delta) if override_params else self.delta

        # Get base components
        base_rate = self.get_base_rate(room_type)
        forecasted_demand = self.get_forecasted_demand(room_type, target_date)
        competitor_index = self.get_competitor_index(room_type, target_date)
        event_multiplier = self.get_event_multiplier(target_date)
        time_factor = self.calculate_time_factor(target_date)
        floor, ceiling = self.get_floor_ceiling(room_type)

        # Apply pricing formula
        demand_factor = 1 + alpha * (forecasted_demand - self.baseline_demand)
        competitor_factor = 1 + beta * (competitor_index - 1)
        event_factor = 1 + delta * (event_multiplier - 1)
        time_discount_factor = 1 - gamma * time_factor

        # Calculate raw price
        raw_price = (base_rate * demand_factor * competitor_factor *
                    event_factor * time_discount_factor)

        # Apply floor and ceiling constraints
        final_price = np.clip(raw_price, floor, ceiling)

        # Return detailed pricing breakdown
        return {
            'room_type': room_type,
            'date': target_date,
            'base_rate': base_rate,
            'final_price': round(final_price, 2),
            'raw_price': round(raw_price, 2),
            'floor': floor,
            'ceiling': ceiling,
            'components': {
                'forecasted_demand': round(forecasted_demand, 3),
                'competitor_index': round(competitor_index, 3),
                'event_multiplier': round(event_multiplier, 3),
                'time_factor': round(time_factor, 3),
                'demand_factor': round(demand_factor, 3),
                'competitor_factor': round(competitor_factor, 3),
                'event_factor': round(event_factor, 3),
                'time_discount_factor': round(time_discount_factor, 3)
            },
            'coefficients': {
                'alpha': alpha,
                'beta': beta,
                'gamma': gamma,
                'delta': delta
            }
        }

    def calculate_prices_for_period(self, room_type, start_date, end_date, override_params=None):
        """Calculate prices for a date range"""
        prices = []
        current_date = start_date

        while current_date <= end_date:
            price_data = self.calculate_dynamic_price(room_type, current_date, override_params)
            prices.append(price_data)
            current_date += timedelta(days=1)

        return prices

    def reprice_all_rooms(self, target_date=None, days_ahead=30):
        """Reprice all room types for specified period"""
        if target_date is None:
            target_date = date.today()

        end_date = target_date + timedelta(days=days_ahead)

        # Get all room types
        room_types = self.session.query(RoomType).all()

        results = {}
        for room_type in room_types:
            prices = self.calculate_prices_for_period(
                room_type.name, target_date, end_date
            )
            results[room_type.name] = prices

        return results

    def save_pricing_to_history(self, pricing_data, channel='ALL', source='pricing_engine'):
        """Save calculated prices to price history table"""
        for price_info in pricing_data:
            price_history = PriceHistory(
                date=price_info['date'],
                room_type=price_info['room_type'],
                published_rate=price_info['final_price'],
                channel=channel,
                floor=price_info['floor'],
                ceiling=price_info['ceiling'],
                source=source
            )
            self.session.add(price_history)

        self.session.commit()

    def _calculate_demand_fallback(self, room_type, target_date):
        """Fallback demand calculation based on historical booking patterns"""
        # Look at bookings for same day of week in past 4 weeks
        day_of_week = target_date.weekday()
        past_dates = []

        for weeks_back in range(1, 5):
            past_date = target_date - timedelta(weeks=weeks_back)
            past_dates.append(past_date)

        # Count bookings for these dates
        booking_counts = []
        for past_date in past_dates:
            count = self.session.query(Booking).filter_by(
                room_type=room_type,
                checkin=past_date
            ).count()
            booking_counts.append(count)

        if booking_counts:
            avg_bookings = np.mean(booking_counts)
            # Get total inventory for this room type
            total_rooms = self.session.query(Inventory).filter_by(room_type=room_type).count()
            return min(avg_bookings / max(total_rooms, 1), 1.0)

        return self.baseline_demand

    def update_coefficients(self, alpha=None, beta=None, gamma=None, delta=None):
        """Update pricing coefficients"""
        if alpha is not None:
            self.alpha = alpha
        if beta is not None:
            self.beta = beta
        if gamma is not None:
            self.gamma = gamma
        if delta is not None:
            self.delta = delta

    def get_pricing_summary(self, room_type, days_ahead=7):
        """Get pricing summary for next N days"""
        start_date = date.today()
        end_date = start_date + timedelta(days=days_ahead)

        prices = self.calculate_prices_for_period(room_type, start_date, end_date)

        summary = {
            'room_type': room_type,
            'period': f"{start_date} to {end_date}",
            'avg_price': round(np.mean([p['final_price'] for p in prices]), 2),
            'min_price': min([p['final_price'] for p in prices]),
            'max_price': max([p['final_price'] for p in prices]),
            'base_rate': prices[0]['base_rate'] if prices else 0,
            'price_variance': round(np.std([p['final_price'] for p in prices]), 2),
            'daily_prices': prices
        }

        return summary

    def close(self):
        """Close database session"""
        self.session.close()

if __name__ == "__main__":
    # Test the pricing engine
    engine = PricingEngine()

    # Test pricing for Deluxe room tomorrow
    tomorrow = date.today() + timedelta(days=1)
    price_info = engine.calculate_dynamic_price('Deluxe', tomorrow)

    print("Pricing Engine Test:")
    print(f"Room Type: {price_info['room_type']}")
    print(f"Date: {price_info['date']}")
    print(f"Base Rate: {price_info['base_rate']} AED")
    print(f"Final Price: {price_info['final_price']} AED")
    print(f"Components: {price_info['components']}")

    engine.close()