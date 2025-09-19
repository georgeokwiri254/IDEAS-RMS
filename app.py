import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import sys
import os

# Add src to path
sys.path.append('src')

from services.pricing_engine import PricingEngine
from models.database import *

# Page configuration
st.set_page_config(
    page_title="Grand Millennium Dubai - Revenue Management System",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'pricing_engine' not in st.session_state:
    st.session_state.pricing_engine = PricingEngine()

if 'last_reprice' not in st.session_state:
    st.session_state.last_reprice = None

# Sidebar
with st.sidebar:
    st.image("https://via.placeholder.com/300x100/1f4e79/ffffff?text=Grand+Millennium+Dubai", use_column_width=True)
    st.title("RMS Control Panel")

    st.markdown("---")
    st.subheader("Quick Actions")

    if st.button("🔄 Run Ingest", use_container_width=True):
        st.success("Data ingestion simulated!")

    if st.button("📊 Compute Forecast", use_container_width=True):
        st.success("Forecast updated!")

    if st.button("💰 Run Reprice", use_container_width=True):
        st.session_state.last_reprice = datetime.now()
        st.success("Repricing completed!")

    if st.button("📤 Push to Channels", use_container_width=True):
        st.success("Rates pushed to OTAs!")

    st.markdown("---")
    st.subheader("System Status")
    st.metric("Total Rooms", "339")
    st.metric("Target ADR", "319 AED")
    st.metric("Current Occupancy", "78.5%")

# Main content
st.title("🏨 Grand Millennium Dubai - Revenue Management System")

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["🎯 RMS", "📺 Channels", "🏨 Competitors", "🎲 Simulation"])

# Tab 1: RMS (Main)
with tab1:
    st.header("Revenue Management System")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Room Type Pricing Controls")

        # Get room types
        engine = create_engine('sqlite:///data/rms.db')
        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            room_types = session.query(RoomType).all()

            for room_type in room_types:
                with st.expander(f"{room_type.name} - Base Rate: {room_type.base_rate} AED"):
                    col_a, col_b, col_c = st.columns(3)

                    with col_a:
                        floor_price = st.number_input(
                            "Floor Price",
                            min_value=100,
                            max_value=1000,
                            value=int(room_type.base_rate * 0.7),
                            key=f"floor_{room_type.name}"
                        )

                    with col_b:
                        ceiling_price = st.number_input(
                            "Ceiling Price",
                            min_value=200,
                            max_value=2000,
                            value=int(room_type.base_rate * 1.5),
                            key=f"ceiling_{room_type.name}"
                        )

                    with col_c:
                        manual_override = st.number_input(
                            "Manual Override",
                            min_value=0,
                            max_value=2000,
                            value=0,
                            key=f"override_{room_type.name}"
                        )

                    # Show current pricing for next 7 days
                    pricing_summary = st.session_state.pricing_engine.get_pricing_summary(room_type.name, 7)

                    st.markdown("**Next 7 Days Pricing:**")
                    price_data = []
                    for day_price in pricing_summary['daily_prices']:
                        price_data.append({
                            'Date': day_price['date'],
                            'Price (AED)': day_price['final_price'],
                            'Demand': f"{day_price['components']['forecasted_demand']:.1%}",
                            'Competitor Index': f"{day_price['components']['competitor_index']:.2f}"
                        })

                    st.dataframe(pd.DataFrame(price_data), use_container_width=True)

        except Exception as e:
            st.error(f"Database connection error: {e}")
        finally:
            session.close()

    with col2:
        st.subheader("Pricing Coefficients")

        st.markdown("**Adjust sensitivity parameters:**")

        alpha = st.slider("α (Demand Sensitivity)", 0.0, 1.0, 0.3, 0.05)
        beta = st.slider("β (Competitor Sensitivity)", 0.0, 1.0, 0.25, 0.05)
        gamma = st.slider("γ (Time Decay)", 0.0, 0.1, 0.02, 0.01)
        delta = st.slider("δ (Event Multiplier)", 0.0, 2.0, 1.0, 0.1)

        if st.button("Update Coefficients"):
            st.session_state.pricing_engine.update_coefficients(alpha, beta, gamma, delta)
            st.success("Coefficients updated!")

        st.markdown("---")

        st.subheader("Forecast Overview")
        # Simulated forecast data
        forecast_dates = pd.date_range(start=date.today(), periods=14, freq='D')
        forecast_occupancy = [75 + (i % 7) * 3 + np.random.normal(0, 2) for i in range(14)]

        fig = px.line(
            x=forecast_dates,
            y=forecast_occupancy,
            title="14-Day Occupancy Forecast",
            labels={'x': 'Date', 'y': 'Occupancy %'}
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

# Tab 2: Channels
with tab2:
    st.header("Channel Management")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Channel Rules & Commission")

        # Get channel data
        try:
            session = Session()
            channels = session.query(ChannelRule).all()

            channel_data = []
            for channel in channels:
                channel_data.append({
                    'Channel': channel.name,
                    'Commission %': f"{channel.commission_pct:.1%}",
                    'Loyalty Discount %': f"{channel.loyalty_discount_pct:.1%}",
                    'Status': "Active" if channel.is_active else "Inactive"
                })

            st.dataframe(pd.DataFrame(channel_data), use_container_width=True)
            session.close()

        except Exception as e:
            st.error(f"Error loading channel data: {e}")

        st.subheader("Rate Parity Monitor")

        # Simulated parity data
        parity_data = {
            'Channel': ['Booking.com', 'Expedia', 'Agoda', 'Direct', 'Others'],
            'Our Rate': [285, 285, 285, 285, 285],
            'Display Rate': [256, 251, 262, 285, 271],
            'Parity Status': ['⚠️ Under', '❌ Under', '⚠️ Under', '✅ OK', '⚠️ Under']
        }

        st.dataframe(pd.DataFrame(parity_data), use_container_width=True)

    with col2:
        st.subheader("Recent Push Log")

        # Simulated push log
        push_times = pd.date_range(start=datetime.now() - timedelta(hours=24), periods=10, freq='2H')
        push_data = []

        for i, push_time in enumerate(push_times):
            push_data.append({
                'Timestamp': push_time.strftime('%H:%M'),
                'Channel': ['Booking.com', 'Expedia', 'Agoda'][i % 3],
                'Room Type': ['Deluxe', 'Club King'][i % 2],
                'Rate': f"{280 + (i % 5) * 10} AED",
                'Status': '✅ Success' if i % 4 != 0 else '⚠️ Retry'
            })

        st.dataframe(pd.DataFrame(push_data), use_container_width=True)

        st.subheader("Channel Performance")

        # Channel performance chart
        channels = ['Direct', 'Booking.com', 'Expedia', 'Agoda', 'Others']
        bookings = [45, 32, 28, 18, 12]
        revenue = [12825, 8320, 7560, 4860, 3240]

        fig = go.Figure()
        fig.add_trace(go.Bar(name='Bookings', x=channels, y=bookings, yaxis='y'))
        fig.add_trace(go.Scatter(name='Revenue (AED)', x=channels, y=revenue, yaxis='y2', mode='lines+markers'))

        fig.update_layout(
            title='Channel Performance (Last 30 Days)',
            xaxis_title='Channel',
            yaxis=dict(title='Bookings', side='left'),
            yaxis2=dict(title='Revenue (AED)', side='right', overlaying='y'),
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

# Tab 3: Competitors
with tab3:
    st.header("Competitor Analysis")

    competitors = ['Voco-Dubai', 'Movenpick-BB', 'Hotel Aster', 'Azure Grand', 'Palmview']

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Current Competitor Rates")

        # Get competitor rates
        try:
            session = Session()
            today = date.today()

            comp_data = []
            for competitor in competitors:
                rates = session.query(CompetitorRate).filter_by(
                    competitor_id=competitor,
                    date=today
                ).all()

                if rates:
                    avg_rate = sum(r.rate for r in rates) / len(rates)
                    availability = sum(1 for r in rates if r.availability) / len(rates)
                else:
                    avg_rate = 300 + np.random.normal(0, 50)  # Fallback
                    availability = 0.8

                comp_data.append({
                    'Competitor': competitor,
                    'Avg Rate (AED)': f"{avg_rate:.0f}",
                    'Availability': f"{availability:.0%}",
                    'Position': '↑' if avg_rate > 319 else '↓'
                })

            st.dataframe(pd.DataFrame(comp_data), use_container_width=True)
            session.close()

        except Exception as e:
            st.error(f"Error loading competitor data: {e}")

        st.subheader("Rate Positioning")

        our_rate = 319
        comp_rates = [295, 310, 285, 340, 305]

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=competitors,
            y=comp_rates,
            name='Competitor Rates',
            marker_color='lightblue'
        ))

        fig.add_hline(
            y=our_rate,
            line_dash="dash",
            line_color="red",
            annotation_text="Our Rate (319 AED)"
        )

        fig.update_layout(
            title='Rate Positioning vs Competitors',
            xaxis_title='Competitor',
            yaxis_title='Rate (AED)',
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Rate Volatility (Last 30 Days)")

        # Generate volatility data
        dates = pd.date_range(start=date.today() - timedelta(days=30), end=date.today(), freq='D')

        fig = go.Figure()

        for i, competitor in enumerate(competitors):
            base_rate = 280 + i * 15
            rates = [base_rate + np.random.normal(0, 15) for _ in dates]

            fig.add_trace(go.Scatter(
                x=dates,
                y=rates,
                mode='lines',
                name=competitor,
                line=dict(width=2)
            ))

        # Add our rate line
        our_rates = [319 + np.random.normal(0, 8) for _ in dates]
        fig.add_trace(go.Scatter(
            x=dates,
            y=our_rates,
            mode='lines',
            name='Grand Millennium (Us)',
            line=dict(width=3, color='red', dash='dash')
        ))

        fig.update_layout(
            title='Rate Volatility Comparison',
            xaxis_title='Date',
            yaxis_title='Rate (AED)',
            height=500
        )

        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Competitive Intelligence")

        intel_data = {
            'Competitor': competitors,
            'Strategy': ['Premium', 'Value', 'Economy', 'Luxury', 'Mid-range'],
            'Promo Activity': ['High', 'Medium', 'Low', 'Low', 'Medium'],
            'Market Share': ['18%', '15%', '12%', '8%', '10%']
        }

        st.dataframe(pd.DataFrame(intel_data), use_container_width=True)

# Tab 4: Simulation
with tab4:
    st.header("Market Simulation")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Event Impact Simulation")

        event_date = st.date_input(
            "Event Date",
            value=date.today() + timedelta(days=14),
            min_value=date.today(),
            max_value=date.today() + timedelta(days=90)
        )

        event_type = st.selectbox(
            "Event Type",
            ["Dubai Shopping Festival", "Business Conference", "International Expo", "Ramadan", "Custom Event"]
        )

        event_impact = st.slider("Event Impact Multiplier", 0.5, 2.0, 1.25, 0.05)

        room_type_sim = st.selectbox(
            "Room Type for Simulation",
            ["Deluxe", "Club King", "Club Twin", "One-Bedroom", "Two-Bedroom", "Executive Suite"]
        )

        if st.button("Run Event Simulation"):
            # Calculate pricing impact
            normal_price = st.session_state.pricing_engine.calculate_dynamic_price(room_type_sim, event_date)
            event_price = st.session_state.pricing_engine.calculate_dynamic_price(
                room_type_sim,
                event_date,
                override_params={'delta': event_impact}
            )

            st.success("Event simulation completed!")

            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Normal Price", f"{normal_price['final_price']} AED")
            with col_b:
                st.metric("Event Price", f"{event_price['final_price']} AED")
            with col_c:
                price_diff = event_price['final_price'] - normal_price['final_price']
                st.metric("Price Impact", f"+{price_diff:.0f} AED")

    with col2:
        st.subheader("Competitor Response Simulation")

        competitor_drop = st.selectbox("Competitor Drops Price", competitors)
        price_drop_pct = st.slider("Price Drop %", 5, 50, 15)

        if st.button("Simulate Competitor Drop"):
            st.warning(f"{competitor_drop} dropped prices by {price_drop_pct}%!")

            # Simulate our response
            st.info("Recommended response: Maintain rates, monitor for 24h")

        st.subheader("Demand Scenario Testing")

        occupancy_scenario = st.selectbox(
            "Occupancy Scenario",
            ["Low Demand (60%)", "Normal Demand (75%)", "High Demand (90%)", "Sold Out (95%+)"]
        )

        if st.button("Test Demand Scenario"):
            demand_mapping = {
                "Low Demand (60%)": 0.6,
                "Normal Demand (75%)": 0.75,
                "High Demand (90%)": 0.9,
                "Sold Out (95%+)": 0.95
            }

            forecasted_demand = demand_mapping[occupancy_scenario]

            # Calculate price for different demand levels
            tomorrow = date.today() + timedelta(days=1)
            price_scenarios = []

            for demand_level in [0.6, 0.75, 0.9, 0.95]:
                # Simulate different demand by adjusting in the pricing calculation
                scenario_name = f"{demand_level:.0%} Occupancy"
                # This is a simplified simulation - in practice, you'd update forecast data
                base_price = st.session_state.pricing_engine.calculate_dynamic_price('Deluxe', tomorrow)
                price_scenarios.append({
                    'Scenario': scenario_name,
                    'Price (AED)': base_price['final_price'] * (1 + 0.3 * (demand_level - 0.75))
                })

            st.dataframe(pd.DataFrame(price_scenarios), use_container_width=True)

        st.subheader("Real-time Market Monitor")

        # Simulated real-time data
        if st.button("Refresh Market Data"):
            current_time = datetime.now().strftime("%H:%M:%S")
            st.success(f"Market data refreshed at {current_time}")

            metrics_col1, metrics_col2, metrics_col3 = st.columns(3)

            with metrics_col1:
                st.metric("Pickup Rate", "12 bookings/hour", "+3")

            with metrics_col2:
                st.metric("ADR Trend", "↗️ +2.3%", "+7 AED")

            with metrics_col3:
                st.metric("Competitor Activity", "2 price changes", "+1")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
    Grand Millennium Dubai RMS Prototype v1.0 |
    Built with Streamlit |
    Target ADR: 319 AED |
    339 Rooms Total
    </div>
    """,
    unsafe_allow_html=True
)

# Auto-refresh sidebar metrics every 30 seconds
if st.session_state.last_reprice:
    time_since_reprice = datetime.now() - st.session_state.last_reprice
    if time_since_reprice.seconds < 5:
        st.rerun()