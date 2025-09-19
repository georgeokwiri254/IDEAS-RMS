# Grand Millennium Dubai - Revenue Management System (RMS) Prototype

## 🏨 Project Overview

This is a comprehensive Revenue Management System (RMS) prototype developed for **Grand Millennium Dubai**, featuring 339 rooms with a target ADR of 319 AED. The system demonstrates dynamic pricing, channel management, competitor analysis, and demand forecasting using Python, Streamlit, and SQLite.

## 🎯 Key Features

### 1. **Dynamic Pricing Engine**
- Real-time price optimization using demand, competitor, and event data
- Configurable pricing formula with floor/ceiling constraints
- Multiple pricing coefficients (demand sensitivity, competitor response, time decay)

### 2. **Multi-Channel Management**
- Integration with major OTAs (Booking.com, Expedia, Agoda)
- Commission and loyalty discount management
- Rate parity monitoring and alerts

### 3. **Competitor Intelligence**
- Real-time competitor rate tracking
- Rate positioning analysis
- Market trend monitoring

### 4. **Demand Forecasting**
- ML-based demand prediction
- Booking pace analysis
- Seasonal and event-based adjustments

### 5. **Interactive Dashboard**
- 4 comprehensive tabs: RMS, Channels, Competitors, Simulation
- Real-time metrics and KPI tracking
- Scenario testing and simulation tools

## 🏗️ System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit UI  │────│  Pricing Engine  │────│   SQLite DB     │
│   (4 Tabs)     │    │                  │    │   (9 Tables)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌────────┴─────────┐            │
         │              │                  │            │
         ▼              ▼                  ▼            ▼
┌─────────────────┐ ┌──────────────┐ ┌─────────────┐ ┌────────────────┐
│ Channel Manager │ │ Data Ingest  │ │ Forecasting │ │ Competitor     │
│ (OTA Pushes)    │ │ (PMS/Comp)   │ │ (ML Models) │ │ Intelligence   │
└─────────────────┘ └──────────────┘ └─────────────┘ └────────────────┘
```

## 🏢 Hotel Configuration

### Room Types (339 Total Rooms)
- **Deluxe**: 120 rooms @ 280 AED base rate
- **Club King**: 60 rooms @ 350 AED base rate
- **Club Twin**: 50 rooms @ 330 AED base rate
- **One-Bedroom**: 60 rooms @ 450 AED base rate
- **Two-Bedroom**: 40 rooms @ 700 AED base rate
- **Executive Suite**: 9 rooms @ 900 AED base rate

### Distribution Channels
- **Direct Booking**: 0% commission
- **Booking.com**: 15% commission, 10% loyalty discount
- **Expedia**: 18% commission, 12% loyalty discount
- **Agoda**: 15% commission, 8% loyalty discount
- **Other OTAs**: 20% commission, 5% loyalty discount

## 🚀 Quick Start

### Option 1: Simple Startup (Recommended)
```bash
# Make sure you're in the project directory
cd "IDEAS RMS"

# Run the startup script
./run_rms.sh
```

### Option 2: Manual Setup
```bash
# 1. Set up database
python3 setup_database.py

# 2. Create virtual environment (optional)
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install streamlit pandas numpy sqlalchemy plotly

# 4. Run the application
streamlit run simple_app.py
```

### Access the Application
Open your browser and navigate to: **http://localhost:8501**

## 📊 Database Schema

The system uses SQLite with 9 core tables:

1. **room_types** - Room type definitions and base rates
2. **inventory** - Individual room inventory (339 rooms)
3. **bookings** - Historical and future bookings
4. **competitor_rates** - Competitor pricing data
5. **price_history** - Historical pricing decisions
6. **channel_rules** - Distribution channel configurations
7. **event_multipliers** - Special events and their impact
8. **forecast_data** - Demand forecasting results
9. **push_log** - Rate distribution history

## 💰 Pricing Formula

The dynamic pricing engine uses the following formula:

```
price = clip(
    base_rate *
    (1 + α * (forecasted_demand - baseline_demand)) *
    (1 + β * (competitor_index - 1)) *
    (1 + δ * event_multiplier) *
    (1 - γ * time_to_arrival_factor),
    floor, ceiling
)
```

**Where:**
- **α (alpha)**: Demand sensitivity coefficient (default: 0.3)
- **β (beta)**: Competitor sensitivity coefficient (default: 0.25)
- **γ (gamma)**: Time decay factor (default: 0.02)
- **δ (delta)**: Event multiplier impact (default: 1.0)

## 🎮 User Interface Tabs

### 1. 🎯 RMS Tab
- Room type pricing controls (floor/ceiling)
- Pricing coefficient adjustments
- 7-day pricing preview
- Demand forecasting charts
- Manual price overrides

### 2. 📺 Channels Tab
- Channel performance metrics
- Commission and discount rules
- Rate parity monitoring
- Push log and status tracking
- Revenue by channel analysis

### 3. 🏨 Competitors Tab
- Current competitor rates
- Rate positioning charts
- Market trend analysis
- Competitive intelligence dashboard
- Rate volatility tracking

### 4. 🎲 Simulation Tab
- Event impact simulation
- Demand scenario testing
- Competitor response modeling
- Real-time market monitoring
- What-if analysis tools

## 📈 Sample Data

The system comes pre-populated with:
- **594 historical bookings** (60 days)
- **930 competitor rate points** (30 days forward)
- **186 forecast data points** (30 days forward)
- **3 special events** (Dubai Shopping Festival, Business Conference, International Expo)
- **5 competitor hotels** (Voco-Dubai, Movenpick-BB, Hotel Aster, Azure Grand, Palmview)

## 🔧 Advanced Features

### Data Ingestion Pipeline
```python
# Simulate PMS data ingestion
from src.services.data_ingestion import DataIngestionPipeline
pipeline = DataIngestionPipeline()
results = pipeline.run_full_ingestion_cycle()
```

### Pricing Engine API
```python
# Calculate dynamic pricing
from src.services.pricing_engine import PricingEngine
engine = PricingEngine()
price_info = engine.calculate_dynamic_price('Deluxe', date.today() + timedelta(days=1))
```

### Channel Management
```python
# Push rates to channels
from src.services.channel_manager import ChannelManagerAdapter
cm = ChannelManagerAdapter()
result = cm.push_rate_to_channel('BOOKING_COM', 'Deluxe', target_date, 285.0)
```

### Forecasting
```python
# Generate demand forecast
from src.services.forecasting import ForecastingEngine
forecaster = ForecastingEngine()
forecast = forecaster.calculate_demand_forecast('Deluxe', target_date)
```

## 🛠️ Technical Requirements

- **Python 3.8+**
- **Streamlit** (web interface)
- **SQLite** (database)
- **Pandas** (data manipulation)
- **NumPy** (numerical computing)
- **Plotly** (charts and graphs)
- **Scikit-learn** (machine learning - optional)

## 🎯 Business Metrics

### Key Performance Indicators
- **Target ADR**: 319 AED
- **Current Occupancy**: Real-time calculation
- **Revenue per Available Room (RevPAR)**
- **Booking Pace**: Lead time analysis
- **Competitor Rate Index**: Market positioning

### Pricing Optimization Goals
- Maximize revenue while maintaining occupancy
- Respond dynamically to market conditions
- Maintain rate parity across channels
- Optimize for seasonal and event demand

## 🔮 Future Enhancements

### Production Readiness
- Replace SQLite with PostgreSQL/MySQL
- Implement real PMS integrations (Opera, Protel)
- Connect to actual OTA APIs
- Add comprehensive monitoring and alerting

### Advanced Features
- Machine learning model optimization
- A/B testing framework for pricing strategies
- Advanced competitor intelligence
- Mobile application interface
- API for third-party integrations

### Business Intelligence
- Executive dashboard with KPIs
- Automated reporting and insights
- Predictive analytics for market trends
- Integration with business intelligence tools

## 📞 Support

For questions or issues with the RMS prototype:

1. Check the database status: `python3 setup_database.py`
2. Verify all dependencies are installed
3. Review the Streamlit logs for error messages
4. Ensure port 8501 is available

## 📄 License

This is a prototype system developed for demonstration purposes. All code and configurations are proprietary to Grand Millennium Dubai.

---

**Built with ❤️ for Grand Millennium Dubai**
*Revenue Management System Prototype v1.0*