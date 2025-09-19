import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
from sqlalchemy.orm import sessionmaker
from ..models.database import *
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
import warnings
warnings.filterwarnings('ignore')

class ForecastingEngine:
    """
    Forecasting engine for demand prediction and booking pace analysis

    Uses multiple models:
    - Exponential smoothing for baseline trends
    - Random Forest for complex pattern recognition
    - Lead time analysis for booking window optimization
    """

    def __init__(self, db_path='data/rms.db'):
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}')
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        # Model parameters
        self.smoothing_alpha = 0.3
        self.lookback_days = 90
        self.forecast_horizon = 30

    def calculate_demand_forecast(self, room_type, target_date, use_ml=True):
        """
        Calculate demand forecast for specific room type and date

        Args:
            room_type: Room type name
            target_date: Date to forecast for
            use_ml: Whether to use ML models (vs simple trend analysis)

        Returns:
            dict: Forecast components and final prediction
        """

        # Get historical booking data
        historical_data = self._get_historical_bookings(room_type)

        if len(historical_data) < 14:  # Need minimum data
            return self._fallback_forecast(room_type, target_date)

        # Calculate base components
        seasonality_factor = self._calculate_seasonality(target_date, historical_data)
        trend_factor = self._calculate_trend(historical_data)
        day_of_week_factor = self._calculate_dow_factor(target_date, historical_data)
        lead_time_factor = self._calculate_lead_time_impact(room_type, target_date)

        # Get external factors
        competitor_factor = self._get_competitor_impact(room_type, target_date)
        event_factor = self._get_event_impact(target_date)

        if use_ml and len(historical_data) >= 30:
            # Use ML model for complex patterns
            ml_prediction = self._ml_demand_forecast(room_type, target_date, historical_data)
            base_demand = ml_prediction
        else:
            # Use exponential smoothing
            base_demand = self._exponential_smoothing_forecast(historical_data)

        # Combine all factors
        final_demand = (base_demand *
                       seasonality_factor *
                       trend_factor *
                       day_of_week_factor *
                       competitor_factor *
                       event_factor *
                       lead_time_factor)

        # Ensure realistic bounds (0-100% occupancy)
        final_demand = np.clip(final_demand, 0.0, 1.0)

        return {
            'room_type': room_type,
            'target_date': target_date,
            'forecasted_demand': final_demand,
            'components': {
                'base_demand': base_demand,
                'seasonality_factor': seasonality_factor,
                'trend_factor': trend_factor,
                'day_of_week_factor': day_of_week_factor,
                'lead_time_factor': lead_time_factor,
                'competitor_factor': competitor_factor,
                'event_factor': event_factor
            },
            'confidence': self._calculate_confidence(historical_data, final_demand),
            'model_used': 'ml' if use_ml and len(historical_data) >= 30 else 'exponential_smoothing'
        }

    def update_forecast_accuracy(self, room_type, actual_date):
        """
        Update forecast accuracy metrics by comparing predictions with actual results

        Args:
            room_type: Room type
            actual_date: Date that has passed (to compare forecast vs actual)
        """

        # Get actual bookings for the date
        actual_bookings = self.session.query(Booking).filter_by(
            room_type=room_type,
            checkin=actual_date
        ).count()

        # Get total inventory for this room type
        total_inventory = self.session.query(Inventory).filter_by(room_type=room_type).count()
        actual_occupancy = actual_bookings / max(total_inventory, 1)

        # Get forecast that was made for this date
        forecast_record = self.session.query(ForecastData).filter_by(
            room_type=room_type,
            date=actual_date
        ).order_by(ForecastData.created_at.desc()).first()

        if forecast_record:
            predicted_demand = forecast_record.forecasted_demand
            error = abs(predicted_demand - actual_occupancy)
            error_pct = (error / max(actual_occupancy, 0.01)) * 100

            # Store accuracy metrics (in production, would have separate accuracy table)
            print(f"Forecast accuracy for {room_type} on {actual_date}:")
            print(f"  Predicted: {predicted_demand:.1%}")
            print(f"  Actual: {actual_occupancy:.1%}")
            print(f"  Error: {error:.1%} ({error_pct:.1f}%)")

            return {
                'room_type': room_type,
                'date': actual_date,
                'predicted_demand': predicted_demand,
                'actual_occupancy': actual_occupancy,
                'absolute_error': error,
                'percentage_error': error_pct,
                'accuracy_score': max(0, 100 - error_pct)
            }

        return None

    def generate_demand_scenarios(self, room_type, target_date, scenarios=['low', 'base', 'high']):
        """
        Generate multiple demand scenarios for risk assessment

        Args:
            room_type: Room type
            target_date: Target date
            scenarios: List of scenario types

        Returns:
            dict: Scenarios with probability weights
        """

        base_forecast = self.calculate_demand_forecast(room_type, target_date)
        base_demand = base_forecast['forecasted_demand']

        scenario_results = {}

        for scenario in scenarios:
            if scenario == 'low':
                # 20% reduction with market downturn factors
                demand = base_demand * 0.8
                probability = 0.2
                description = "Market downturn, increased competition"

            elif scenario == 'base':
                # Base case
                demand = base_demand
                probability = 0.6
                description = "Expected market conditions"

            elif scenario == 'high':
                # 30% increase with favorable conditions
                demand = base_demand * 1.3
                probability = 0.2
                description = "Strong market, limited competition"

            scenario_results[scenario] = {
                'demand': min(demand, 1.0),  # Cap at 100%
                'probability': probability,
                'description': description,
                'revenue_impact': self._calculate_revenue_impact(room_type, demand, base_demand)
            }

        return {
            'room_type': room_type,
            'target_date': target_date,
            'base_forecast': base_demand,
            'scenarios': scenario_results
        }

    def analyze_booking_patterns(self, room_type=None, days_back=60):
        """
        Analyze historical booking patterns for insights

        Args:
            room_type: Specific room type (None for all)
            days_back: Days to look back

        Returns:
            dict: Pattern analysis results
        """

        end_date = date.today()
        start_date = end_date - timedelta(days=days_back)

        # Get booking data
        query = self.session.query(Booking).filter(
            Booking.created_at >= start_date,
            Booking.created_at <= end_date
        )

        if room_type:
            query = query.filter(Booking.room_type == room_type)

        bookings = query.all()

        if not bookings:
            return {'error': 'No booking data found'}

        # Convert to DataFrame for analysis
        data = []
        for booking in bookings:
            lead_time = (booking.checkin - booking.created_at.date()).days
            data.append({
                'booking_date': booking.created_at.date(),
                'arrival_date': booking.checkin,
                'room_type': booking.room_type,
                'rate': booking.rate,
                'channel': booking.channel,
                'lead_time': lead_time,
                'day_of_week': booking.checkin.weekday(),
                'month': booking.checkin.month
            })

        df = pd.DataFrame(data)

        # Analyze patterns
        patterns = {
            'total_bookings': len(bookings),
            'period': f"{start_date} to {end_date}",
            'avg_lead_time': df['lead_time'].mean(),
            'lead_time_distribution': {
                'same_day': (df['lead_time'] == 0).sum(),
                '1-7_days': ((df['lead_time'] >= 1) & (df['lead_time'] <= 7)).sum(),
                '8-30_days': ((df['lead_time'] >= 8) & (df['lead_time'] <= 30)).sum(),
                '31+_days': (df['lead_time'] > 30).sum()
            },
            'channel_distribution': df['channel'].value_counts().to_dict(),
            'day_of_week_pattern': df['day_of_week'].value_counts().to_dict(),
            'seasonal_pattern': df['month'].value_counts().to_dict(),
            'avg_rate': df['rate'].mean(),
            'rate_volatility': df['rate'].std()
        }

        # Calculate booking velocity (bookings per day)
        daily_bookings = df.groupby('booking_date').size()
        patterns['avg_daily_bookings'] = daily_bookings.mean()
        patterns['booking_velocity_trend'] = self._calculate_velocity_trend(daily_bookings)

        # Room type specific patterns
        if not room_type:
            patterns['room_type_performance'] = {}
            for rt in df['room_type'].unique():
                rt_data = df[df['room_type'] == rt]
                patterns['room_type_performance'][rt] = {
                    'bookings': len(rt_data),
                    'avg_rate': rt_data['rate'].mean(),
                    'avg_lead_time': rt_data['lead_time'].mean()
                }

        return patterns

    def _get_historical_bookings(self, room_type):
        """Get historical booking data for analysis"""

        end_date = date.today()
        start_date = end_date - timedelta(days=self.lookback_days)

        bookings = self.session.query(Booking).filter(
            Booking.room_type == room_type,
            Booking.checkin >= start_date,
            Booking.checkin <= end_date
        ).all()

        # Group by date and calculate occupancy
        daily_occupancy = {}
        total_rooms = self.session.query(Inventory).filter_by(room_type=room_type).count()

        for booking in bookings:
            arrival_date = booking.checkin
            if arrival_date not in daily_occupancy:
                daily_occupancy[arrival_date] = 0
            daily_occupancy[arrival_date] += 1

        # Convert to occupancy rates
        historical_data = []
        current_date = start_date
        while current_date <= end_date:
            bookings_count = daily_occupancy.get(current_date, 0)
            occupancy_rate = bookings_count / max(total_rooms, 1)
            historical_data.append({
                'date': current_date,
                'occupancy': occupancy_rate,
                'bookings': bookings_count
            })
            current_date += timedelta(days=1)

        return historical_data

    def _calculate_seasonality(self, target_date, historical_data):
        """Calculate seasonal adjustment factor"""

        if not historical_data:
            return 1.0

        # Group by month and calculate average
        monthly_avg = {}
        for data_point in historical_data:
            month = data_point['date'].month
            if month not in monthly_avg:
                monthly_avg[month] = []
            monthly_avg[month].append(data_point['occupancy'])

        if target_date.month in monthly_avg:
            month_avg = np.mean(monthly_avg[target_date.month])
            overall_avg = np.mean([dp['occupancy'] for dp in historical_data])
            return month_avg / max(overall_avg, 0.01)

        return 1.0

    def _calculate_trend(self, historical_data):
        """Calculate trend factor using linear regression"""

        if len(historical_data) < 7:
            return 1.0

        # Prepare data for regression
        X = np.array(range(len(historical_data))).reshape(-1, 1)
        y = np.array([dp['occupancy'] for dp in historical_data])

        # Fit linear regression
        try:
            model = LinearRegression()
            model.fit(X, y)

            # Get trend direction (positive = growing, negative = declining)
            slope = model.coef_[0]

            # Convert to factor (small adjustments)
            trend_factor = 1.0 + (slope * 10)  # Scale the trend
            return np.clip(trend_factor, 0.8, 1.2)  # Limit impact

        except:
            return 1.0

    def _calculate_dow_factor(self, target_date, historical_data):
        """Calculate day-of-week adjustment factor"""

        if not historical_data:
            return 1.0

        # Group by day of week
        dow_avg = {}
        for data_point in historical_data:
            dow = data_point['date'].weekday()
            if dow not in dow_avg:
                dow_avg[dow] = []
            dow_avg[dow].append(data_point['occupancy'])

        target_dow = target_date.weekday()
        if target_dow in dow_avg:
            dow_mean = np.mean(dow_avg[target_dow])
            overall_mean = np.mean([dp['occupancy'] for dp in historical_data])
            return dow_mean / max(overall_mean, 0.01)

        return 1.0

    def _calculate_lead_time_impact(self, room_type, target_date):
        """Calculate impact of lead time on demand"""

        lead_time_days = (target_date - date.today()).days

        if lead_time_days <= 0:
            return 1.1  # Same day booking urgency

        # Analyze historical lead time patterns
        historical_lead_times = []
        bookings = self.session.query(Booking).filter(
            Booking.room_type == room_type,
            Booking.created_at >= datetime.now() - timedelta(days=60)
        ).all()

        for booking in bookings:
            lead_time = (booking.checkin - booking.created_at.date()).days
            historical_lead_times.append(lead_time)

        if historical_lead_times:
            avg_lead_time = np.mean(historical_lead_times)

            # If target lead time is much different from average, adjust demand
            if lead_time_days < avg_lead_time * 0.5:
                return 1.05  # Shorter lead time = higher urgency
            elif lead_time_days > avg_lead_time * 2:
                return 0.95  # Longer lead time = lower urgency

        return 1.0

    def _get_competitor_impact(self, room_type, target_date):
        """Get competitor impact on demand"""

        # Get competitor rates for the date
        competitor_rates = self.session.query(CompetitorRate).filter(
            CompetitorRate.room_type == room_type,
            CompetitorRate.date == target_date
        ).all()

        if not competitor_rates:
            return 1.0

        # Calculate competitor price advantage/disadvantage
        our_base_rate = self.session.query(RoomType).filter_by(name=room_type).first()
        if not our_base_rate:
            return 1.0

        competitor_avg = np.mean([cr.rate for cr in competitor_rates])
        price_ratio = competitor_avg / our_base_rate.base_rate

        # If competitors are more expensive, we get demand boost
        if price_ratio > 1.1:
            return 1.05
        elif price_ratio < 0.9:
            return 0.95

        return 1.0

    def _get_event_impact(self, target_date):
        """Get event impact on demand"""

        event = self.session.query(EventMultiplier).filter_by(date=target_date).first()
        if event:
            # Convert event multiplier to demand factor
            return min(event.multiplier, 1.5)  # Cap at 50% demand increase

        return 1.0

    def _ml_demand_forecast(self, room_type, target_date, historical_data):
        """Use ML model for demand forecasting"""

        if len(historical_data) < 30:
            return 0.75  # Default baseline

        # Prepare features
        features = []
        targets = []

        for data_point in historical_data[:-7]:  # Leave last week for validation
            date_obj = data_point['date']

            feature_vector = [
                date_obj.weekday(),          # Day of week
                date_obj.month,              # Month
                date_obj.day,                # Day of month
                (date_obj - date.today()).days,  # Days from today
            ]

            features.append(feature_vector)
            targets.append(data_point['occupancy'])

        if len(features) < 10:
            return 0.75

        # Train Random Forest model
        try:
            X = np.array(features)
            y = np.array(targets)

            model = RandomForestRegressor(n_estimators=50, random_state=42)
            model.fit(X, y)

            # Predict for target date
            target_features = [[
                target_date.weekday(),
                target_date.month,
                target_date.day,
                (target_date - date.today()).days
            ]]

            prediction = model.predict(target_features)[0]
            return np.clip(prediction, 0.0, 1.0)

        except:
            # Fallback to exponential smoothing
            return self._exponential_smoothing_forecast(historical_data)

    def _exponential_smoothing_forecast(self, historical_data):
        """Simple exponential smoothing forecast"""

        if not historical_data:
            return 0.75

        occupancy_values = [dp['occupancy'] for dp in historical_data]

        # Exponential smoothing
        smoothed = occupancy_values[0]
        for value in occupancy_values[1:]:
            smoothed = self.smoothing_alpha * value + (1 - self.smoothing_alpha) * smoothed

        return smoothed

    def _fallback_forecast(self, room_type, target_date):
        """Fallback forecast when insufficient data"""

        baseline_demand = 0.75

        # Apply basic day-of-week adjustment
        if target_date.weekday() >= 5:  # Weekend
            baseline_demand *= 1.1

        return {
            'room_type': room_type,
            'target_date': target_date,
            'forecasted_demand': baseline_demand,
            'components': {
                'base_demand': baseline_demand,
                'seasonality_factor': 1.0,
                'trend_factor': 1.0,
                'day_of_week_factor': 1.1 if target_date.weekday() >= 5 else 1.0,
                'lead_time_factor': 1.0,
                'competitor_factor': 1.0,
                'event_factor': 1.0
            },
            'confidence': 0.5,
            'model_used': 'fallback'
        }

    def _calculate_confidence(self, historical_data, forecast):
        """Calculate forecast confidence based on data quality"""

        if len(historical_data) < 7:
            return 0.3

        # Calculate variance in historical data
        occupancy_values = [dp['occupancy'] for dp in historical_data]
        variance = np.var(occupancy_values)

        # Lower variance = higher confidence
        confidence = 1.0 - min(variance * 2, 0.7)  # Cap confidence reduction

        return max(confidence, 0.3)  # Minimum confidence

    def _calculate_revenue_impact(self, room_type, scenario_demand, base_demand):
        """Calculate revenue impact of demand scenario"""

        room_type_obj = self.session.query(RoomType).filter_by(name=room_type).first()
        base_rate = room_type_obj.base_rate if room_type_obj else 300

        total_rooms = self.session.query(Inventory).filter_by(room_type=room_type).count()

        base_revenue = base_demand * total_rooms * base_rate
        scenario_revenue = scenario_demand * total_rooms * base_rate

        return {
            'base_revenue': base_revenue,
            'scenario_revenue': scenario_revenue,
            'revenue_difference': scenario_revenue - base_revenue,
            'percentage_impact': ((scenario_revenue - base_revenue) / max(base_revenue, 1)) * 100
        }

    def _calculate_velocity_trend(self, daily_bookings):
        """Calculate booking velocity trend"""

        if len(daily_bookings) < 7:
            return 'insufficient_data'

        recent_avg = daily_bookings.tail(7).mean()
        earlier_avg = daily_bookings.head(7).mean()

        if recent_avg > earlier_avg * 1.1:
            return 'accelerating'
        elif recent_avg < earlier_avg * 0.9:
            return 'decelerating'
        else:
            return 'stable'

    def close(self):
        """Close database session"""
        self.session.close()

if __name__ == "__main__":
    # Test the forecasting engine
    forecaster = ForecastingEngine()

    # Test demand forecast
    tomorrow = date.today() + timedelta(days=1)
    forecast = forecaster.calculate_demand_forecast('Deluxe', tomorrow)

    print("Forecasting Engine Test:")
    print(f"Room Type: {forecast['room_type']}")
    print(f"Target Date: {forecast['target_date']}")
    print(f"Forecasted Demand: {forecast['forecasted_demand']:.1%}")
    print(f"Model Used: {forecast['model_used']}")
    print(f"Confidence: {forecast['confidence']:.1%}")

    forecaster.close()