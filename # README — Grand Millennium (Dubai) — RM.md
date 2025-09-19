# README — Grand Millennium (Dubai) — RMS Prototype (Python + Streamlit + SQLite)

Below is a concise, **10-point** README arranged by topic (each topic bolded). It describes the prototype, architecture, pipeline, UI, synthetic data, pricing logic, channel rules, and how to run the app. Use this as the high-level README to present to GMs/owners and as a developer quick-start.

1. **Project purpose & scope**
   This prototype simulates a Revenue Management System (RMS) for **Grand Millennium, Dubai** (339 rooms, target ADR ≈ **319 AED** for Sep). It demonstrates: data ingestion (PMS + competitors), SQLite storage with synthetic data, a Streamlit UI with tabs (RMS, Channels, Competitors, Simulation), a dynamic pricing engine (floor/ceiling + automatic re-pricing), and mock rate pushes to OTAs (Booking.com / Agoda / Expedia) via a channel-manager abstraction.

2. **System architecture (high level)**

   * **Clients/UI:** Streamlit web app (tabs for RMS, Channels, Competitors, Simulations).
   * **Business logic:** Python services (ingest, normalization, pricing engine, channel manager connector).
   * **Storage:** SQLite for prototype (tables for inventory, bookings, competitor\_rates, price\_history, channel\_rules).
   * **Integrations:** PMS extractor (simulated), competitor collector (synthetic or scraped/API), Channel Manager Adapter (simulates OTP/XML or REST pushes).
     Diagram (conceptual): Streamlit ↔ Pricing Engine ↔ SQLite ← Ingestors (PMS + Competitors) → Channel Manager → OTAs.

3. **Data pipeline & ingestion (step-by-step)**

   1. **PMS extract** — scheduled job pulls reservations, rates, room inventory (CSV / API simulated).
   2. **Competitor ingest** — scheduled scraper/API to pull competitor rates and availability (synthetic here).
   3. **Normalization** — unify date formats, currency (AED), room type mapping, and fill missing values.
   4. **Load** — write normalized rows to SQLite tables (`bookings`, `inventory`, `competitor_rates`).
   5. **Aggregation** — daily aggregation jobs compute pickup, pace, on-the-books, lead time distributions for model input.
      Automate scheduling with cron / Airflow in production; for prototype, a Python scheduler or Streamlit button triggers jobs.

4. **SQLite schema & synthetic dataset (core tables)**

   * `inventory(room_id, room_type, hotel_id, status)`
   * `room_types(type_id, name, capacity, base_rate)`
   * `bookings(booking_id, room_type, checkin, checkout, rate, channel, created_at)`
   * `competitor_rates(date, competitor_id, room_type, rate, scraped_at)`
   * `price_history(date, room_type, published_rate, channel, floor, ceiling, source)`
   * `channel_rules(channel_id, commission_pct, loyalty_discount_pct, name)`
     Synthetic setup: **339 rooms** broken down (example counts summing to 339): Deluxe 120, Club King 60, Club Twin 50, One-Bedroom 60, Two-Bedroom 40, Executive Suite 9. Example base rates (AED): Deluxe 280, Club King 350, Club Twin 330, 1BR 450, 2BR 700, Exec 900.

5. **Streamlit UI & tabs (what each tab does)**

   * **RMS (main):** set global floor & ceiling per room\_type, view forecasted pickup, manual override, apply mass updates, and trigger reprice.
   * **Channels:** view channel rules (commission, loyalty discounts), per-channel published rates, and simulated push log to OTAs.
   * **Competitors:** show 5 synthetic competitors (e.g., Voco-Dubai, Movenpick-BB, Hotel Aster, Azure Grand, Palmview), their room rates, and volatility graphs.
   * **Simulation:** choose event dates, change occupancy, simulate competitor drops, and watch automatic repricing & parity impacts in real time.
     UI buttons allow: `Run Ingest`, `Compute Forecast`, `Run Reprice`, `Push to Channels (simulate)`.

6. **Dynamic pricing engine — formula and intuition (beginner-friendly)**

   * **Inputs:** base\_rate (room type), forecasted\_demand, current\_occupancy, days\_to\_arrival (lead time), competitor\_index (relative price position), event\_multiplier, floor, ceiling.
   * **Core formula (configurable):**

     ```
     price = clip( base_rate
                   * (1 + α * (forecasted_demand - baseline_demand))
                   * (1 + β * (competitor_index - 1))
                   * (1 + δ * event_multiplier)
                   * (1 - γ * time_to_arrival_factor),
                   floor, ceiling )
     ```

     Where α, β, γ, δ are tunable coefficients (e.g., α controls inventory sensitivity; β controls how aggressively you chase/lag competitors). `clip()` enforces floor/ceiling.
   * **Practical example (intuitive):** if bookings are accelerating (high booking pace), the `(1 + α*(...))` increases price; if competitors are cheaper (competitor\_index < 1), the `(1 + β*(...))` pushes price down unless prevented by the floor.

7. **Forecasting & booking pace (how the model feeds pricing)**

   * **Booking pace** = new bookings for a date in the last N days / expected bookings baseline. Use rolling windows (7/14/30 days).
   * **Forecast model(s):** simple exponential smoothing or XGBoost/time-series model that consumes: historical pickup, day\_of\_week, holiday/event flags, lead\_time, competitor\_rate\_stats, and weather/events.
   * **Feedback loop:** after the day-of-stay passes, compare forecast vs actual; store error metrics and retrain/adjust α, β, γ parameters periodically.

8. **Competitor integration & parity handling**

   * **Competitor index** = (median competitor rate for same room\_type / our base\_rate). Compute per date and per room\_type.
   * **Normalization & mapping:** map competitor room type names into your types (Deluxe ↔ competitor Deluxe). Use fuzzy mapping table in DB.
   * **Parity resolution:** the Channel Manager Adapter records any channel-level adjustments applied by OTAs; parity alerts raise flags when an OTA shows a lower net price (after OTA discounts/commission). Prototype simulates these differences and flags parity violations in the UI.

9. **Channels, discounts & push mechanics (practical details)**

   * **Channel Manager abstraction:** implement a `channel_manager.py` class that turns in-memory `published_rate` → OTA payload. In production this maps to: OTA XML (OTA RatePlan & Availability), Booking.com REST or API, Expedia/Agoda APIs or via channel manager providers (SiteMinder, RateTiger). For prototype the method writes simulated API responses to `push_log`.
   * **Why channels show different guest prices:** some OTAs apply **loyalty/marketing discounts** on top of your published rate (e.g., “member price”, promo code, Genius). Also OTAs show **net vs gross** pricing (commission handled differently). In prototype, channel rules include `loyalty_discount_pct` and `commission_pct` so the UI can show `guest_display_price = published_rate * (1 - loyalty_discount_pct)` and `hotel_net = published_rate * (1 - commission_pct)`.
   * **Example behaviors to demonstrate:** Booking.com member discount (configurable 5–15%), Expedia partner deals, Agoda flash sale (temporary -X%), and agency negotiated rates (net rates). These are modeled as configurable rules in `channel_rules`.

10. **Simulations, volatility for event dates, deployment & next steps**

    * **Event volatility:** define event multipliers for specific dates (e.g., International Expo weeks → event\_multiplier = +0.25). Simulation tab should let you toggle events and see price variance and pick-up impact.
    * **How to run prototype locally:**

      1. Clone repo.
      2. `python -m venv venv && source venv/bin/activate` (or Windows equivalent).
      3. `pip install -r requirements.txt` (requirements: streamlit, pandas, numpy, sqlalchemy, sklearn/xgboost optional).
      4. `python generate_synthetic_data.py` (creates SQLite `rms.db` with 339-room inventory, bookings, 5 competitors).
      5. `streamlit run app.py` (open `http://localhost:8501`) — use UI tabs to ingest, forecast, reprice, and push.
    * **Production/next steps:** replace SQLite with Snowflake/BigQuery/Redshift, run ingestors with Airflow, replace simulated channel manager with a real channel manager or OTA integrations (XML/REST), add monitoring, and A/B test pricing coefficients.

---

If you want, I can now:

* Expand any single point into a full README section (e.g., include the exact SQLite `CREATE TABLE` statements and `generate_synthetic_data.py`), or
* Generate `app.py` + `generate_synthetic_data.py` starter files for this prototype (Streamlit UI skeleton + pricing engine).

Which one should I produce next?
