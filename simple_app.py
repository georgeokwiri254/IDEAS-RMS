#!/usr/bin/env python3
"""
Simple Streamlit app for Grand Millennium Dubai RMS
This version uses minimal dependencies to ensure it runs
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date, timedelta
import random

# Page configuration
st.set_page_config(
    page_title="Grand Millennium Dubai - Revenue Management System",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database connection
@st.cache_resource
def get_database_connection():
    return sqlite3.connect('data/rms.db', check_same_thread=False)

# Sidebar
with st.sidebar:
    st.markdown("""
    <div style='text-align: center; background: linear-gradient(90deg, #1f4e79, #2e6da4); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
        <h2>🏨 Grand Millennium Dubai</h2>
        <p style='margin: 0;'>Revenue Management System</p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("Quick Actions")

    if st.button("🔄 Run Ingest", use_container_width=True):
        st.success("Data ingestion simulated!")

    if st.button("📊 Compute Forecast", use_container_width=True):
        st.success("Forecast updated!")

    if st.button("💰 Run Reprice", use_container_width=True):
        st.success("Repricing completed!")

    if st.button("📤 Push to Channels", use_container_width=True):
        st.success("Rates pushed to OTAs!")

    st.markdown("---")
    st.subheader("System Status")

    # Get real data from database
    conn = get_database_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM inventory')
    total_rooms = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM bookings WHERE checkin = ?', (date.today(),))
    today_bookings = cursor.fetchone()[0]

    current_occupancy = (today_bookings / total_rooms) * 100 if total_rooms > 0 else 0

    st.metric("Total Rooms", f"{total_rooms}")
    st.metric("Target ADR", "319 AED")
    st.metric("Current Occupancy", f"{current_occupancy:.1f}%")

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

        conn = get_database_connection()
        cursor = conn.cursor()

        # Get room types
        cursor.execute('SELECT * FROM room_types ORDER BY type_id')
        room_types = cursor.fetchall()

        for room_type in room_types:
            type_id, name, capacity, base_rate = room_type

            with st.expander(f"{name} - Base Rate: {base_rate} AED"):
                col_a, col_b, col_c = st.columns(3)

                with col_a:
                    floor_price = st.number_input(
                        "Floor Price",
                        min_value=100,
                        max_value=1000,
                        value=int(base_rate * 0.7),
                        key=f"floor_{name}"
                    )

                with col_b:
                    ceiling_price = st.number_input(
                        "Ceiling Price",
                        min_value=200,
                        max_value=2000,
                        value=int(base_rate * 1.5),
                        key=f"ceiling_{name}"
                    )

                with col_c:
                    manual_override = st.number_input(
                        "Manual Override",
                        min_value=0,
                        max_value=2000,
                        value=0,
                        key=f"override_{name}"
                    )

                # Show upcoming pricing (simulated)
                st.markdown("**Next 7 Days Pricing:**")
                price_data = []
                for i in range(7):
                    target_date = date.today() + timedelta(days=i)
                    # Simple pricing simulation
                    demand_factor = random.uniform(0.8, 1.2)
                    weekend_factor = 1.1 if target_date.weekday() >= 5 else 1.0
                    final_price = base_rate * demand_factor * weekend_factor

                    price_data.append({
                        'Date': target_date.strftime('%Y-%m-%d'),
                        'Price (AED)': f"{final_price:.0f}",
                        'Demand': f"{random.uniform(0.6, 0.9):.1%}",
                        'Weekend': "Yes" if target_date.weekday() >= 5 else "No"
                    })

                st.dataframe(pd.DataFrame(price_data), use_container_width=True)

    with col2:
        st.subheader("Pricing Parameters")

        st.markdown("**Adjust sensitivity:**")

        alpha = st.slider("Demand Sensitivity", 0.0, 1.0, 0.3, 0.05)
        beta = st.slider("Competitor Sensitivity", 0.0, 1.0, 0.25, 0.05)
        gamma = st.slider("Time Decay", 0.0, 0.1, 0.02, 0.01)

        if st.button("Update Parameters"):
            st.success("Parameters updated!")

        st.markdown("---")

        st.subheader("Demand Forecast")

        # Simple forecast chart
        forecast_dates = pd.date_range(start=date.today(), periods=14, freq='D')
        forecast_data = []

        for i, forecast_date in enumerate(forecast_dates):
            base_occupancy = 75
            weekend_boost = 5 if forecast_date.weekday() >= 5 else 0
            seasonal_variation = random.uniform(-10, 10)
            final_occupancy = base_occupancy + weekend_boost + seasonal_variation

            forecast_data.append({
                'Date': forecast_date.strftime('%m-%d'),
                'Occupancy %': max(40, min(95, final_occupancy))
            })

        chart_data = pd.DataFrame(forecast_data)
        st.line_chart(chart_data.set_index('Date'))

# Tab 2: Channels
with tab2:
    st.header("Channel Management")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Channel Rules & Commission")

        # Get channel data from database
        cursor.execute('SELECT * FROM channel_rules')
        channels = cursor.fetchall()

        channel_data = []
        for channel in channels:
            channel_id, name, commission_pct, loyalty_discount_pct, is_active = channel
            channel_data.append({
                'Channel': name,
                'Commission %': f"{commission_pct:.1%}",
                'Loyalty Discount %': f"{loyalty_discount_pct:.1%}",
                'Status': "Active" if is_active else "Inactive"
            })

        st.dataframe(pd.DataFrame(channel_data), use_container_width=True)

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
        st.subheader("Channel Performance")

        # Channel performance data
        performance_data = {
            'Channel': ['Direct', 'Booking.com', 'Expedia', 'Agoda', 'Others'],
            'Bookings': [45, 32, 28, 18, 12],
            'Revenue (AED)': [12825, 8320, 7560, 4860, 3240],
            'Avg Rate': [285, 260, 270, 270, 270]
        }

        st.dataframe(pd.DataFrame(performance_data), use_container_width=True)

        st.subheader("Recent Push Log")

        # Simulated push log
        push_data = []
        for i in range(8):
            push_data.append({
                'Time': f"{14 + i}:00",
                'Channel': ['Booking.com', 'Expedia', 'Agoda'][i % 3],
                'Room Type': ['Deluxe', 'Club King'][i % 2],
                'Rate': f"{280 + (i % 3) * 20} AED",
                'Status': '✅ Success' if i % 4 != 0 else '⚠️ Retry'
            })

        st.dataframe(pd.DataFrame(push_data), use_container_width=True)

# Tab 3: Competitors
with tab3:
    st.header("Competitor Analysis")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Current Competitor Rates")

        # Get competitor data from database
        cursor.execute('''
            SELECT competitor_id, AVG(rate) as avg_rate, COUNT(*) as room_count
            FROM competitor_rates
            WHERE date = ?
            GROUP BY competitor_id
        ''', (date.today(),))

        competitors = cursor.fetchall()

        comp_data = []
        for competitor_id, avg_rate, room_count in competitors:
            comp_data.append({
                'Competitor': competitor_id,
                'Avg Rate (AED)': f"{avg_rate:.0f}",
                'Room Types': room_count,
                'Position': '↑' if avg_rate > 319 else '↓'
            })

        if comp_data:
            st.dataframe(pd.DataFrame(comp_data), use_container_width=True)
        else:
            st.info("No competitor data for today. Run data ingestion to populate.")

        st.subheader("Competitive Intelligence")

        intel_data = {
            'Competitor': ['Voco-Dubai', 'Movenpick-BB', 'Hotel Aster', 'Azure Grand', 'Palmview'],
            'Strategy': ['Premium', 'Value', 'Economy', 'Luxury', 'Mid-range'],
            'Market Share': ['18%', '15%', '12%', '8%', '10%'],
            'Recent Activity': ['Rate drop', 'Promotion', 'Stable', 'Rate increase', 'Stable']
        }

        st.dataframe(pd.DataFrame(intel_data), use_container_width=True)

    with col2:
        st.subheader("Rate Positioning")

        # Simple competitor comparison
        our_rate = 319
        comp_names = ['Voco-Dubai', 'Movenpick-BB', 'Hotel Aster', 'Azure Grand', 'Palmview']
        comp_rates = [295, 310, 285, 340, 305]

        positioning_data = pd.DataFrame({
            'Competitor': comp_names + ['Grand Millennium (Us)'],
            'Rate (AED)': comp_rates + [our_rate]
        })

        st.bar_chart(positioning_data.set_index('Competitor'))

        st.subheader("Market Trends")

        st.metric("Market ADR", "308 AED", "+2.1%")
        st.metric("Our Position", "#3 of 6", "↑1")
        st.metric("Rate Variance", "±15 AED", "Normal")

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
            # Get base rate for selected room type
            cursor.execute('SELECT base_rate FROM room_types WHERE name = ?', (room_type_sim,))
            result = cursor.fetchone()
            base_rate = result[0] if result else 300

            normal_price = base_rate
            event_price = base_rate * event_impact

            st.success("Event simulation completed!")

            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Normal Price", f"{normal_price:.0f} AED")
            with col_b:
                st.metric("Event Price", f"{event_price:.0f} AED")
            with col_c:
                price_diff = event_price - normal_price
                st.metric("Price Impact", f"+{price_diff:.0f} AED")

    with col2:
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

            scenario_data = []
            base_prices = [280, 350, 330, 450, 700, 900]  # Room type base rates

            for i, (demand_level, scenario_name) in enumerate([
                (0.6, "Low Demand"),
                (0.75, "Normal Demand"),
                (0.9, "High Demand"),
                (0.95, "Sold Out")
            ]):
                # Simple pricing based on demand
                price_multiplier = 0.8 + (demand_level * 0.4)  # 0.8 to 1.2 range
                avg_price = sum(base_prices) / len(base_prices) * price_multiplier

                scenario_data.append({
                    'Scenario': scenario_name,
                    'Occupancy': f"{demand_level:.0%}",
                    'Avg Price (AED)': f"{avg_price:.0f}",
                    'Revenue Impact': f"{((avg_price / 319) - 1) * 100:+.1f}%"
                })

            st.dataframe(pd.DataFrame(scenario_data), use_container_width=True)

        st.subheader("Real-time Monitoring")

        if st.button("Refresh Market Data"):
            current_time = datetime.now().strftime("%H:%M:%S")
            st.success(f"Market data refreshed at {current_time}")

            metrics_col1, metrics_col2, metrics_col3 = st.columns(3)

            with metrics_col1:
                st.metric("Pickup Rate", f"{random.randint(8, 16)} bookings/hour", f"{random.randint(-2, 5):+d}")

            with metrics_col2:
                st.metric("ADR Trend", f"↗️ {random.uniform(0.5, 4.0):.1f}%", f"{random.randint(3, 12):+d} AED")

            with metrics_col3:
                st.metric("Competitor Activity", f"{random.randint(1, 4)} changes", f"{random.randint(-1, 2):+d}")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 0.9em;'>
    🏨 Grand Millennium Dubai RMS Prototype v1.0 |
    Built with Streamlit |
    339 Rooms | Target ADR: 319 AED |
    Database: {} rooms active
    </div>
    """.format(total_rooms),
    unsafe_allow_html=True
)