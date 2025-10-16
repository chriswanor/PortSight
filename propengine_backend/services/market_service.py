import requests
import pandas as pd
from sqlalchemy import text
from db.connection import engine

# ==============================
# CONFIGURATION
# ==============================
RENTCAST_API_KEY = "969613c94fec4387bb1879a38204e57d"
FRED_API_KEY = "your_fred_api_key_here"   # get from https://fred.stlouisfed.org/docs/api/api_key.html


# ==============================
# MAIN ENTRY POINT
# ==============================
def update_market_data(property_id: int, zip_code: str):
    """
    Fetches market data from RentCast + FRED for a specific property
    and stores/updates it in the market_data table.
    """

    # ---- 1️⃣ RentCast: Local Market Data ----
    rentcast_data = fetch_rentcast_market(zip_code)

    # ---- 2️⃣ FRED: Macro Data ----
    fred_data = fetch_fred_data()

    # ---- 3️⃣ Risk Score ----
    risk_score = compute_risk_score({
        "rent_growth": rentcast_data.get("rent_growth_yoy"),
        "vacancy": rentcast_data.get("vacancy_rate_market"),
        "interest_rate": fred_data.get("interest_rate_10yr"),
        "employment_growth": fred_data.get("employment_growth"),
    })

    # ---- 4️⃣ Insert or Update in SQL ----
    insert_query = text("""
        INSERT INTO market_data (
            property_id, region_code, rent_growth_yoy,
            vacancy_rate_market, cap_rate_market, interest_rate_10yr,
            employment_growth, population_growth, risk_score
        )
        VALUES (
            :property_id, :region_code, :rent_growth_yoy,
            :vacancy_rate_market, :cap_rate_market, :interest_rate_10yr,
            :employment_growth, :population_growth, :risk_score
        )
        ON DUPLICATE KEY UPDATE
            rent_growth_yoy = VALUES(rent_growth_yoy),
            vacancy_rate_market = VALUES(vacancy_rate_market),
            cap_rate_market = VALUES(cap_rate_market),
            interest_rate_10yr = VALUES(interest_rate_10yr),
            employment_growth = VALUES(employment_growth),
            population_growth = VALUES(population_growth),
            risk_score = VALUES(risk_score),
            updated_at = CURRENT_TIMESTAMP;
    """)

    with engine.begin() as conn:
        conn.execute(insert_query, {
            "property_id": property_id,
            "region_code": zip_code,
            "rent_growth_yoy": rentcast_data.get("rent_growth_yoy"),
            "vacancy_rate_market": rentcast_data.get("vacancy_rate_market"),
            "cap_rate_market": rentcast_data.get("cap_rate_market"),
            "interest_rate_10yr": fred_data.get("interest_rate_10yr"),
            "employment_growth": fred_data.get("employment_growth"),
            "population_growth": fred_data.get("population_growth"),
            "risk_score": risk_score
        })

    print(f"[✅] Market data updated for property {property_id} ({zip_code})")


# ==============================
# RENTCAST
# ==============================
def fetch_rentcast_market(zip_code: str):
    """
    Fetch rent growth, vacancy rate, and cap rate for the given ZIP
    """
    url = f"https://api.rentcast.io/v1/markets/rent-growth?zip={zip_code}"
    headers = {"accept": "application/json", "X-Api-Key": RENTCAST_API_KEY}

    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        data = res.json()

        return {
            "rent_growth_yoy": data.get("rentGrowthYearOverYear"),
            "vacancy_rate_market": data.get("vacancyRate"),
            "cap_rate_market": data.get("capRate"),
            "median_rent": data.get("medianRent"),
            "median_price_per_sf": data.get("medianPricePerSqft")
        }

    except Exception as e:
        print(f"[RentCast Error] Failed to fetch data for {zip_code}: {e}")
        return {
            "rent_growth_yoy": None,
            "vacancy_rate_market": None,
            "cap_rate_market": None
        }


# ==============================
# FRED
# ==============================
def fetch_fred_data():
    """
    Fetch 10-Year Treasury, Employment Growth, and Population Growth
    """
    def get_series(series_id):
        url = "https://api.stlouisfed.org/fred/series/observations"
        params = {"series_id": series_id, "api_key": FRED_API_KEY, "file_type": "json"}
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        df = pd.DataFrame(data["observations"])
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        return df

    try:
        df_10yr = get_series("DGS10")        # 10-Year Treasury
        df_emp = get_series("PAYEMS")        # Nonfarm Employment
        df_pop = get_series("POP")           # Population

        employment_growth = df_emp["value"].pct_change(12).iloc[-1]
        population_growth = df_pop["value"].pct_change(1).iloc[-1]

        return {
            "interest_rate_10yr": round(df_10yr["value"].iloc[-1], 4),
            "employment_growth": round(employment_growth, 4),
            "population_growth": round(population_growth, 4)
        }

    except Exception as e:
        print(f"[FRED Error] Failed to fetch FRED data: {e}")
        return {
            "interest_rate_10yr": None,
            "employment_growth": None,
            "population_growth": None
        }


# ==============================
# RISK SCORE
# ==============================
def compute_risk_score(inputs: dict):
    """
    Compute a composite 0–1 risk score based on market and macro indicators.
    Lower rent growth, higher vacancy, higher rates = higher risk.
    """
    try:
        rent = inputs.get("rent_growth") or 0.02
        vac = inputs.get("vacancy") or 0.05
        rate = inputs.get("interest_rate") or 4
        jobs = inputs.get("employment_growth") or 0.01

        score = (
            (0.05 - rent) * 10 +      # inverse
            vac * 5 +
            (rate / 10) +
            (0.03 - jobs) * 10
        )

        return round(max(0, min(1, score / 10)), 4)

    except Exception as e:
        print(f"[Risk Score Error] {e}")
        return None


# ==============================
# MANUAL TEST
# ==============================
if __name__ == "__main__":
    # Example run: Chicago ZIP 60601
    update_market_data(property_id=1, zip_code="60601")
