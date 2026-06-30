"""Seed realistic mock data for PlaceHolder PropTech platform.
All numbers are illustrative; replace with real APIs/scrapers in Phase 2.
"""
import random
from datetime import datetime, timezone

random.seed(42)

CITIES = [
    {"key": "MMR", "name": "Mumbai (MMR)", "lat": 19.0760, "lng": 72.8777,
     "submarkets": ["Bandra-Kurla Complex", "Lower Parel", "Andheri East", "Powai", "Thane West", "Navi Mumbai"]},
    {"key": "NCR", "name": "Delhi NCR", "lat": 28.6139, "lng": 77.2090,
     "submarkets": ["Connaught Place", "Gurgaon Cyber City", "Noida Sector 62", "Dwarka", "Saket"]},
    {"key": "BLR", "name": "Bengaluru", "lat": 12.9716, "lng": 77.5946,
     "submarkets": ["Whitefield", "Outer Ring Road", "Koramangala", "Indiranagar", "Electronic City", "Hebbal"]},
    {"key": "HYD", "name": "Hyderabad", "lat": 17.3850, "lng": 78.4867,
     "submarkets": ["HITEC City", "Gachibowli", "Banjara Hills", "Kondapur", "Madhapur"]},
    {"key": "CHN", "name": "Chennai", "lat": 13.0827, "lng": 80.2707,
     "submarkets": ["OMR", "Guindy", "T. Nagar", "Anna Nagar", "Porur"]},
    {"key": "PUN", "name": "Pune", "lat": 18.5204, "lng": 73.8567,
     "submarkets": ["Hinjewadi", "Kharadi", "Baner", "Viman Nagar", "Koregaon Park"]},
]

DEV_TYPES = ["Metro", "Highway", "Railway", "Airport", "Residential", "Commercial",
             "Retail", "Industrial", "Hospital", "Land", "Hospitality"]

DEV_STATUSES = ["Announced", "Approved", "Under Construction", "Operational"]

# Curated infrastructure project names (realistic-sounding, illustrative)
INFRA_NAMES = {
    "Metro": ["Aqua Line Extension", "Phase 3 Metro Corridor", "Yellow Line Phase 2",
              "Airport Express Link", "Green Line North", "Purple Line Phase 4"],
    "Highway": ["Mumbai-Delhi Expressway Spur", "Outer Ring Road Widening",
                "Coastal Road Phase 2", "Bangalore-Chennai Expressway", "Samruddhi Mahamarg Link"],
    "Railway": ["Bullet Train Station", "Suburban Rail Corridor", "MTHL Rail Bridge",
                "Goods Bypass Line", "Vande Bharat Hub"],
    "Airport": ["Navi Mumbai Intl Airport T1", "Jewar Airport Cargo Hub",
                "Kempegowda T3 Expansion", "Begumpet GA Terminal"],
}

RE_NAMES = {
    "Residential": ["Oasis Towers", "Skyline Heights", "Palm Meadows", "Aurora Residences",
                    "Riverside Crest", "The Beacon", "Lumen Park", "Vantage One"],
    "Commercial": ["Trinity Square", "Atrium Office Park", "Cypress Plaza", "One Horizon",
                   "World Tech Park", "Embassy Manyata Tech"],
    "Retail": ["Galleria Mall", "Promenade Centre", "Phoenix Marketcity", "Mall of Asia"],
    "Industrial": ["Logistics Park Sector 5", "Cold Chain Hub", "Auto Cluster Phase 2",
                   "Pharma SEZ Block C"],
    "Hospital": ["Apollo Multispecialty", "Fortis Greens", "Manipal Heart Institute"],
    "Land": ["Greenfield Township", "SEZ Land Parcel A", "Mixed-Use Land Block"],
    "Hospitality": ["Hyatt Regency Tower", "Taj Convention Hotel", "Marriott Bay"],
}

OWNERS = ["DLF Ltd", "Godrej Properties", "Prestige Estates", "Brigade Group", "Oberoi Realty",
          "Embassy Group", "K Raheja Corp", "Hiranandani Group", "Lodha Group", "Mahindra Lifespaces",
          "Tata Realty", "Phoenix Mills", "L&T Realty", "Sobha Developers", "Adani Realty"]

REITS = [
    {"symbol": "EMBASSY", "name": "Embassy Office Parks REIT", "category": "Commercial Office",
     "market_cap_cr": 36500, "dividend_yield": 6.8, "nav": 392.5, "ltv": 32.0,
     "description": "India's first listed REIT — Grade-A office assets across Bengaluru, Mumbai, Pune."},
    {"symbol": "MINDSPACE", "name": "Mindspace Business Parks REIT", "category": "Commercial Office",
     "market_cap_cr": 22100, "dividend_yield": 6.4, "nav": 374.2, "ltv": 28.5,
     "description": "K Raheja-sponsored REIT with assets in MMR, Hyderabad, Pune & Chennai."},
    {"symbol": "BIRET", "name": "Brookfield India REIT", "category": "Commercial Office",
     "market_cap_cr": 14800, "dividend_yield": 7.1, "nav": 282.0, "ltv": 36.0,
     "description": "Brookfield-sponsored Pan-India Grade-A commercial portfolio."},
    {"symbol": "NXST", "name": "Nexus Select Trust", "category": "Retail / Mall",
     "market_cap_cr": 21300, "dividend_yield": 6.2, "nav": 142.1, "ltv": 29.0,
     "description": "India's first retail REIT — urban consumption centres across 14 cities."},
]


def _rand_coord(lat, lng, spread=0.18):
    return lat + random.uniform(-spread, spread), lng + random.uniform(-spread, spread)


async def seed_all(db):
    # Markets
    await db.markets.insert_many([
        {"key": c["key"], "name": c["name"], "lat": c["lat"], "lng": c["lng"],
         "submarkets": c["submarkets"]} for c in CITIES
    ])

    # Developments
    developments = []
    for city in CITIES:
        for _ in range(28):
            t = random.choice(DEV_TYPES)
            if t in INFRA_NAMES:
                base_name = random.choice(INFRA_NAMES[t])
            elif t in RE_NAMES:
                base_name = random.choice(RE_NAMES[t])
            else:
                base_name = f"{t} Project"
            lat, lng = _rand_coord(city["lat"], city["lng"])
            sub = random.choice(city["submarkets"])
            status = random.choice(DEV_STATUSES)
            year = random.randint(2024, 2029)
            inv = round(random.uniform(150, 12000), 1)  # INR crore
            size = round(random.uniform(0.8, 250), 1)   # acres or lakh sqft (depends on type)
            developments.append({
                "name": f"{base_name} — {sub}",
                "type": t,
                "status": status,
                "city": city["name"],
                "city_key": city["key"],
                "submarket": sub,
                "lat": lat,
                "lng": lng,
                "developer": random.choice(OWNERS) if t not in ("Metro", "Highway", "Railway", "Airport") else "Govt / PSU",
                "investment_inr_cr": inv,
                "size": size,
                "completion_year": year,
                "description": f"{t} development in {sub}, {city['name']}. Expected to add capacity and demand uplift to the surrounding micro-market.",
            })
    await db.developments.insert_many(developments)

    # Comps
    comps = []
    PROP_TYPES = ["Apartment", "Villa", "Office", "Retail Shop", "Warehouse", "Plot"]
    for city in CITIES:
        for _ in range(60):
            sub = random.choice(city["submarkets"])
            pt = random.choice(PROP_TYPES)
            tx = random.choice(["Sale", "Sale", "Rent"])  # 2:1 ratio
            sqft = random.choice([550, 720, 950, 1200, 1450, 1800, 2400, 4500, 12000, 50000])
            if tx == "Sale":
                psf = random.uniform(6000, 38000) if pt != "Plot" else random.uniform(2000, 22000)
                asking = round(psf * sqft, 0)
                sold = round(asking * random.uniform(0.92, 1.02), 0)
                rent_pm = None
            else:
                psf = random.uniform(40, 220)
                asking = round(psf * sqft, 0)
                sold = round(asking * random.uniform(0.9, 1.0), 0)
                rent_pm = sold
            comps.append({
                "city": city["name"],
                "city_key": city["key"],
                "submarket": sub,
                "address": f"{random.randint(1,99)}/{random.randint(100,999)}, {sub}",
                "property_type": pt,
                "transaction_type": tx,
                "size_sqft": sqft,
                "building_age_yrs": random.randint(0, 28),
                "land_size_acres": round(random.uniform(0.05, 4.0), 2) if pt in ("Villa", "Plot", "Warehouse") else None,
                "asking_price_inr": asking,
                "sold_price_inr": sold,
                "rent_pm_inr": rent_pm,
                "price_per_sqft": round(sold / sqft, 0) if sqft else 0,
                "owner": random.choice(OWNERS + ["Private Individual", "Corporate Entity"]),
                "transaction_date": f"{random.randint(2023, 2026)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                "source": "MLS Aggregator (mock)",
            })
    await db.comps.insert_many(comps)

    # REITs
    await db.reits.insert_many(REITS)
