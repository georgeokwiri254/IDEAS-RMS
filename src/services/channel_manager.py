import json
from datetime import datetime, date, timedelta
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from ..models.database import *
import requests
import time

class ChannelManagerAdapter:
    """
    Channel Manager abstraction for pushing rates to OTAs

    In production, this would integrate with:
    - SiteMinder, RateTiger, or similar channel managers
    - Direct OTA APIs (Booking.com, Expedia, Agoda)
    - PMS integrations via OTA XML or REST APIs

    For prototype: simulates API calls and logs responses
    """

    def __init__(self, db_path='data/rms.db'):
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}')
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        # OTA endpoint configurations (simulated)
        self.ota_configs = {
            'BOOKING_COM': {
                'endpoint': 'https://supply-xml.booking.com/hotels/xml/parity',
                'auth_method': 'basic',
                'format': 'xml',
                'rate_push_method': 'batch'
            },
            'EXPEDIA': {
                'endpoint': 'https://services.expediapartnercentral.com/products/properties',
                'auth_method': 'oauth2',
                'format': 'json',
                'rate_push_method': 'individual'
            },
            'AGODA': {
                'endpoint': 'https://affiliateapi7643.agoda.com/ProviderIntegrationService.svc',
                'auth_method': 'api_key',
                'format': 'xml',
                'rate_push_method': 'batch'
            },
            'DIRECT': {
                'endpoint': 'internal',
                'auth_method': 'none',
                'format': 'json',
                'rate_push_method': 'immediate'
            },
            'OTA_OTHERS': {
                'endpoint': 'https://generic-ota-api.com/rates',
                'auth_method': 'api_key',
                'format': 'json',
                'rate_push_method': 'batch'
            }
        }

    def push_rate_to_channel(self, channel_id, room_type, target_date, rate, availability=True):
        """
        Push a single rate to specific channel

        Args:
            channel_id: Channel identifier (e.g., 'BOOKING_COM')
            room_type: Room type name
            target_date: Date for the rate
            rate: Rate in AED
            availability: Room availability boolean

        Returns:
            dict: Push result with status and message
        """

        # Get channel configuration
        if channel_id not in self.ota_configs:
            return {
                'status': 'error',
                'message': f'Unknown channel: {channel_id}',
                'pushed_at': datetime.now()
            }

        config = self.ota_configs[channel_id]

        # Apply channel-specific rate adjustments
        channel_rule = self.session.query(ChannelRule).filter_by(channel_id=channel_id).first()

        if channel_rule:
            # Calculate guest display price (after loyalty discounts)
            guest_display_price = rate * (1 - channel_rule.loyalty_discount_pct)

            # Calculate hotel net price (after commission)
            hotel_net_price = rate * (1 - channel_rule.commission_pct)
        else:
            guest_display_price = rate
            hotel_net_price = rate

        # Create payload based on channel format
        payload = self._create_payload(config, room_type, target_date, rate,
                                     guest_display_price, availability)

        # Simulate API call
        response = self._simulate_api_call(config, payload)

        # Log the push attempt
        push_log = PushLog(
            channel=channel_id,
            room_type=room_type,
            date=target_date,
            rate=rate,
            status=response['status'],
            response_message=response['message'],
            pushed_at=datetime.now()
        )

        self.session.add(push_log)
        self.session.commit()

        return response

    def push_rates_bulk(self, rates_data):
        """
        Push multiple rates in bulk

        Args:
            rates_data: List of dicts with keys: channel_id, room_type, date, rate

        Returns:
            dict: Summary of push results
        """

        results = {
            'total': len(rates_data),
            'success': 0,
            'failed': 0,
            'details': []
        }

        for rate_data in rates_data:
            try:
                result = self.push_rate_to_channel(
                    rate_data['channel_id'],
                    rate_data['room_type'],
                    rate_data['date'],
                    rate_data['rate'],
                    rate_data.get('availability', True)
                )

                if result['status'] == 'success':
                    results['success'] += 1
                else:
                    results['failed'] += 1

                results['details'].append({
                    'channel': rate_data['channel_id'],
                    'room_type': rate_data['room_type'],
                    'date': rate_data['date'],
                    'status': result['status'],
                    'message': result['message']
                })

            except Exception as e:
                results['failed'] += 1
                results['details'].append({
                    'channel': rate_data['channel_id'],
                    'room_type': rate_data['room_type'],
                    'date': rate_data['date'],
                    'status': 'error',
                    'message': str(e)
                })

        return results

    def push_all_channels_for_date_range(self, start_date, end_date, room_types=None):
        """
        Push rates for all channels and room types for a date range

        Args:
            start_date: Start date
            end_date: End date
            room_types: List of room types (if None, all room types)

        Returns:
            dict: Push summary
        """

        if room_types is None:
            room_types_query = self.session.query(RoomType).all()
            room_types = [rt.name for rt in room_types_query]

        channels = list(self.ota_configs.keys())

        # Get latest rates from price history
        rates_to_push = []

        current_date = start_date
        while current_date <= end_date:
            for room_type in room_types:
                for channel in channels:
                    # Get latest price for this combination
                    latest_price = self.session.query(PriceHistory).filter_by(
                        room_type=room_type,
                        date=current_date,
                        channel=channel
                    ).order_by(PriceHistory.created_at.desc()).first()

                    if not latest_price:
                        # Fallback to 'ALL' channel or base rate
                        latest_price = self.session.query(PriceHistory).filter_by(
                            room_type=room_type,
                            date=current_date,
                            channel='ALL'
                        ).order_by(PriceHistory.created_at.desc()).first()

                    if latest_price:
                        rates_to_push.append({
                            'channel_id': channel,
                            'room_type': room_type,
                            'date': current_date,
                            'rate': latest_price.published_rate
                        })

            current_date += timedelta(days=1)

        return self.push_rates_bulk(rates_to_push)

    def check_rate_parity(self, room_type, target_date):
        """
        Check rate parity across channels for a specific room type and date

        Returns:
            dict: Parity analysis
        """

        parity_results = {
            'room_type': room_type,
            'date': target_date,
            'channels': {},
            'parity_violations': []
        }

        # Get rates for all channels
        for channel_id in self.ota_configs.keys():
            latest_push = self.session.query(PushLog).filter_by(
                channel=channel_id,
                room_type=room_type,
                date=target_date,
                status='success'
            ).order_by(PushLog.pushed_at.desc()).first()

            if latest_push:
                channel_rule = self.session.query(ChannelRule).filter_by(channel_id=channel_id).first()

                published_rate = latest_push.rate
                guest_display_price = published_rate
                hotel_net_price = published_rate

                if channel_rule:
                    guest_display_price = published_rate * (1 - channel_rule.loyalty_discount_pct)
                    hotel_net_price = published_rate * (1 - channel_rule.commission_pct)

                parity_results['channels'][channel_id] = {
                    'published_rate': published_rate,
                    'guest_display_price': guest_display_price,
                    'hotel_net_price': hotel_net_price,
                    'last_updated': latest_push.pushed_at
                }

        # Identify parity violations
        if len(parity_results['channels']) > 1:
            rates = [info['guest_display_price'] for info in parity_results['channels'].values()]
            min_rate = min(rates)
            max_rate = max(rates)

            # Flag channels with significant rate differences (>5%)
            threshold = min_rate * 0.05

            for channel_id, info in parity_results['channels'].items():
                rate_diff = info['guest_display_price'] - min_rate
                if rate_diff > threshold:
                    parity_results['parity_violations'].append({
                        'channel': channel_id,
                        'guest_price': info['guest_display_price'],
                        'min_market_price': min_rate,
                        'difference': rate_diff,
                        'percentage': (rate_diff / min_rate) * 100
                    })

        return parity_results

    def get_push_statistics(self, days_back=7):
        """Get push statistics for the last N days"""

        since_date = datetime.now() - timedelta(days=days_back)

        # Get push logs
        push_logs = self.session.query(PushLog).filter(
            PushLog.pushed_at >= since_date
        ).all()

        stats = {
            'total_pushes': len(push_logs),
            'successful_pushes': sum(1 for log in push_logs if log.status == 'success'),
            'failed_pushes': sum(1 for log in push_logs if log.status != 'success'),
            'channels': {},
            'room_types': {},
            'daily_pushes': {}
        }

        # Channel breakdown
        for log in push_logs:
            if log.channel not in stats['channels']:
                stats['channels'][log.channel] = {'total': 0, 'success': 0, 'failed': 0}

            stats['channels'][log.channel]['total'] += 1
            if log.status == 'success':
                stats['channels'][log.channel]['success'] += 1
            else:
                stats['channels'][log.channel]['failed'] += 1

        # Room type breakdown
        for log in push_logs:
            if log.room_type not in stats['room_types']:
                stats['room_types'][log.room_type] = {'total': 0, 'success': 0, 'failed': 0}

            stats['room_types'][log.room_type]['total'] += 1
            if log.status == 'success':
                stats['room_types'][log.room_type]['success'] += 1
            else:
                stats['room_types'][log.room_type]['failed'] += 1

        # Daily breakdown
        for log in push_logs:
            day = log.pushed_at.date()
            if day not in stats['daily_pushes']:
                stats['daily_pushes'][day] = {'total': 0, 'success': 0, 'failed': 0}

            stats['daily_pushes'][day]['total'] += 1
            if log.status == 'success':
                stats['daily_pushes'][day]['success'] += 1
            else:
                stats['daily_pushes'][day]['failed'] += 1

        # Calculate success rates
        stats['success_rate'] = (stats['successful_pushes'] / max(stats['total_pushes'], 1)) * 100

        return stats

    def _create_payload(self, config, room_type, target_date, rate, guest_display_price, availability):
        """Create API payload based on channel configuration"""

        base_payload = {
            'hotel_id': 'GM_DUBAI_001',
            'room_type': room_type,
            'date': target_date.isoformat(),
            'rate': rate,
            'guest_display_price': guest_display_price,
            'availability': availability,
            'currency': 'AED'
        }

        if config['format'] == 'xml':
            # Convert to XML structure (simplified)
            return f"""
            <RateUpdate>
                <HotelId>{base_payload['hotel_id']}</HotelId>
                <RoomType>{base_payload['room_type']}</RoomType>
                <Date>{base_payload['date']}</Date>
                <Rate currency="{base_payload['currency']}">{base_payload['rate']}</Rate>
                <Availability>{str(base_payload['availability']).lower()}</Availability>
            </RateUpdate>
            """
        else:
            return json.dumps(base_payload)

    def _simulate_api_call(self, config, payload):
        """Simulate API call to OTA"""

        import random

        # Simulate network delay
        time.sleep(0.1)

        # Simulate success/failure (95% success rate)
        if random.random() < 0.95:
            return {
                'status': 'success',
                'message': f'Rate updated successfully via {config["format"].upper()}',
                'response_code': 200,
                'timestamp': datetime.now().isoformat()
            }
        else:
            error_messages = [
                'Rate outside acceptable range',
                'Authentication failed',
                'Hotel not found',
                'Room type mapping error',
                'Network timeout'
            ]

            return {
                'status': 'failed',
                'message': random.choice(error_messages),
                'response_code': random.choice([400, 401, 404, 500, 503]),
                'timestamp': datetime.now().isoformat()
            }

    def close(self):
        """Close database session"""
        self.session.close()

if __name__ == "__main__":
    # Test the channel manager
    cm = ChannelManagerAdapter()

    # Test single rate push
    result = cm.push_rate_to_channel(
        'BOOKING_COM',
        'Deluxe',
        date.today() + timedelta(days=1),
        285.0
    )

    print("Channel Manager Test:")
    print(f"Push result: {result}")

    # Test parity check
    parity = cm.check_rate_parity('Deluxe', date.today() + timedelta(days=1))
    print(f"Parity check: {parity}")

    cm.close()