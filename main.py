import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import swisseph as swe
import pytz
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import math

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set ephemeris path and Lahiri Ayanamsa
ephe_path = os.path.join(os.path.dirname(__file__), 'ephe')
swe.set_ephe_path(ephe_path)
swe.set_sid_mode(swe.SIDM_LAHIRI)  # Set Lahiri ayanamsa

class DateRequest(BaseModel):
    date: Optional[str] = None
    timezone: Optional[str] = "Asia/Kolkata"
    lat: Optional[float] = 13.0827  # Default to India
    lon: Optional[float] = 80.2707

# Rashi (Zodiac) calculations
def calculate_rashi(jd: float, planet: int) -> Dict[str, Any]:
    """Calculate Rashi for any planet using Lahiri ayanamsa"""
    position = swe.calc_ut(jd, planet, swe.FLG_SIDEREAL)[0]
    longitude = position[0]
    rashi_num = int(longitude / 30)
    degree = longitude % 30
    
    rashi_names = ["Mesha", "Vrishabha", "Mithuna", "Karka", 
                  "Simha", "Kanya", "Tula", "Vrishchika", 
                  "Dhanu", "Makara", "Kumbha", "Meena"]
    
    return {
        "rashi": rashi_names[rashi_num],
        "degree": round(degree, 2),
        "longitude": round(longitude, 2)
    }

def calculate_birth_chart(jd: float, lat: float, lon: float) -> Dict[str, Any]:
    """Calculate complete birth chart with all planets"""
    planets = {
        "Sun": swe.SUN,
        "Moon": swe.MOON,
        "Mars": swe.MARS,
        "Mercury": swe.MERCURY,
        "Jupiter": swe.JUPITER,
        "Venus": swe.VENUS,
        "Saturn": swe.SATURN,
        "Rahu": swe.MEAN_NODE
    }
    
    chart = {}
    for planet_name, planet_id in planets.items():
        chart[planet_name] = calculate_rashi(jd, planet_id)
        
    # Calculate Ketu (180° from Rahu)
    rahu_lon = chart["Rahu"]["longitude"]
    ketu_lon = (rahu_lon + 180) % 360
    ketu_rashi = int(ketu_lon / 30)
    chart["Ketu"] = {
        "rashi": rashi_names[ketu_rashi],
        "degree": round(ketu_lon % 30, 2),
        "longitude": round(ketu_lon, 2)
    }
    
    # Calculate Lagna (Ascendant)
    houses = swe.houses_ex(jd, lat, lon, b'P')[1]
    lagna_lon = houses[0]
    chart["Lagna"] = {
        "rashi": rashi_names[int(lagna_lon / 30)],
        "degree": round(lagna_lon % 30, 2),
        "longitude": round(lagna_lon, 2)
    }
    
    return chart

def calculate_tithi(jd: float) -> Dict[str, Any]:
    """Calculate Tithi (lunar day) details"""
    sun_lon = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)[0][0]
    moon_lon = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
    tithi_deg = (moon_lon - sun_lon) % 360
    tithi_num = math.ceil(tithi_deg / 12)
    
    tithi_names = ["Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
                  "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
                  "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima/Amavasya"]
    
    paksha = "Shukla" if tithi_num <= 15 else "Krishna"
    tithi_name = tithi_names[(tithi_num - 1) % 15]
    
    return {
        "number": tithi_num,
        "name": tithi_name,
        "paksha": paksha,
        "degrees": round(tithi_deg, 2)
    }

def calculate_nakshatra(jd: float) -> Dict[str, Any]:
    """Calculate Nakshatra (lunar mansion) details"""
    moon_lon = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
    nakshatra_num = math.floor(moon_lon * 27 / 360) + 1
    
    nakshatra_names = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira",
                      "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha",
                      "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati",
                      "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
                      "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
                      "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]
    
    nakshatra_lords = ["Ketu", "Venus", "Sun", "Moon", "Mars",
                      "Rahu", "Jupiter", "Saturn", "Mercury", "Ketu",
                      "Venus", "Sun", "Moon", "Mars", "Rahu",
                      "Jupiter", "Saturn", "Mercury", "Ketu", "Venus",
                      "Sun", "Moon", "Mars", "Rahu", "Jupiter",
                      "Saturn", "Mercury"]
    
    return {
        "number": nakshatra_num,
        "name": nakshatra_names[nakshatra_num - 1],
        "lord": nakshatra_lords[nakshatra_num - 1],
        "degree": round((moon_lon * 27 / 360 % 1) * 360 / 27, 2)
    }

def calculate_yoga(jd: float) -> Dict[str, Any]:
    """Calculate Yoga details"""
    sun_lon = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)[0][0]
    moon_lon = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
    yoga_lon = (sun_lon + moon_lon) % 360
    yoga_num = math.floor(yoga_lon * 27 / 360) + 1
    
    yoga_names = ["Vishkumbha", "Priti", "Ayushman", "Saubhagya", "Shobhana",
                 "Atiganda", "Sukarman", "Dhriti", "Shula", "Ganda",
                 "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
                 "Siddhi", "Vyatipata", "Variyan", "Parigha", "Shiva",
                 "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma",
                 "Indra", "Vaidhriti"]
    
    return {
        "number": yoga_num,
        "name": yoga_names[yoga_num - 1],
        "degree": round((yoga_lon * 27 / 360 % 1) * 360 / 27, 2)
    }

def calculate_karana(jd: float) -> Dict[str, Any]:
    """Calculate Karana details"""
    sun_lon = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)[0][0]
    moon_lon = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
    tithi_deg = (moon_lon - sun_lon) % 360
    karana_num = math.ceil(tithi_deg / 6)
    
    karana_names = ["Bava", "Balava", "Kaulava", "Taitila", "Garaja",
                   "Vanija", "Visti", "Sakuni", "Chatushpada", "Naga"]
    
    return {
        "number": karana_num,
        "name": karana_names[karana_num % 10],
        "degree": round(tithi_deg % 6, 2)
    }

def calculate_muhurta(jd: float, lat: float, lon: float) -> Dict[str, Any]:
    """Calculate various Muhurtas and special timings"""
    sunrise = swe.rise_trans(jd, swe.SUN, lon, lat, 0, rsmi=swe.CALC_RISE)[1][0]
    sunset = swe.rise_trans(jd, swe.SUN, lon, lat, 0, rsmi=swe.CALC_SET)[1][0]
    
    day_duration = sunset - sunrise
    muhurta_duration = day_duration / 30  # 30 muhurtas in a day
    
    weekday = int(jd + 0.5) % 7
    
    # Rahu Kaal calculation
    rahu_start = sunrise + (muhurta_duration * weekday * 2)
    rahu_end = rahu_start + (muhurta_duration * 2)
    
    # Gulika Kaal calculation
    gulika_multiplier = [6, 5, 4, 3, 2, 1, 0][weekday]
    gulika_start = sunrise + (muhurta_duration * gulika_multiplier * 2)
    gulika_end = gulika_start + (muhurta_duration * 2)
    
    return {
        "abhijit": {
            "start": sunrise + (muhurta_duration * 15),
            "end": sunrise + (muhurta_duration * 16)
        },
        "rahu_kaal": {
            "start": rahu_start,
            "end": rahu_end
        },
        "gulika_kaal": {
            "start": gulika_start,
            "end": gulika_end
        }
    }

def calculate_disha_shool(jd: float) -> Dict[str, Any]:
    """Calculate Disha Shool (inauspicious directions)"""
    weekday = int(jd + 0.5) % 7
    
    disha_shool_map = {
        0: ("East", "Taking sweet curd"),      # Sunday
        1: ("North", "Taking ghee"),           # Monday
        2: ("South", "Taking red items"),      # Tuesday
        3: ("West", "Taking curd"),            # Wednesday
        4: ("North", "Taking yellow items"),   # Thursday
        5: ("East", "Taking white items"),     # Friday
        6: ("West", "Taking black items")      # Saturday
    }
    
    direction, remedy = disha_shool_map[weekday]
    return {
        "direction": direction,
        "remedy": remedy,
        "duration": "First 3 muhurtas of the day"
    }

@app.get("/")
async def root():
    """Root endpoint - API health check"""
    return {"message": "Panchanga API is running"}

@app.post("/panchanga/")
async def get_panchanga(request: DateRequest):
    """Main endpoint to get complete Panchanga calculations"""
    try:
        # Parse date or use current date
        if request.date:
            date = datetime.strptime(request.date, "%Y-%m-%d")
        else:
            date = datetime.now(pytz.timezone(request.timezone))
        
        # Convert to Julian Date
        jd = swe.julday(date.year, date.month, date.day, 
                       date.hour + date.minute/60.0)
        
        # Calculate all components
        birth_chart = calculate_birth_chart(jd, request.lat, request.lon)
        tithi = calculate_tithi(jd)
        nakshatra = calculate_nakshatra(jd)
        yoga = calculate_yoga(jd)
        karana = calculate_karana(jd)
        muhurta = calculate_muhurta(jd, request.lat, request.lon)
        disha_shool = calculate_disha_shool(jd)
        
        # Calculate sun/moon rise/set
        sunrise = swe.rise_trans(jd, swe.SUN, request.lon, request.lat, 0, rsmi=swe.CALC_RISE)
        sunset = swe.rise_trans(jd, swe.SUN, request.lon, request.lat, 0, rsmi=swe.CALC_SET)
        moonrise = swe.rise_trans(jd, swe.MOON, request.lon, request.lat, 0, rsmi=swe.CALC_RISE)
        moonset = swe.rise_trans(jd, swe.MOON, request.lon, request.lat, 0, rsmi=swe.CALC_SET)
        
        return {
            "date": date.strftime("%Y-%m-%d"),
            "day": date.strftime("%A"),
            "birth_chart": birth_chart,
            "tithi": tithi,
            "nakshatra": nakshatra,
            "yoga": yoga,
            "karana": karana,
            "muhurta": muhurta,
            "disha_shool": disha_shool,
            "sun_timings": {
                "rise": sunrise[1][0] if sunrise[0] >= 0 else None,
                "set": sunset[1][0] if sunset[0] >= 0 else None
            },
            "moon_timings": {
                "rise": moonrise[1][0] if moonrise[0] >= 0 else None,
                "set": moonset[1][0] if moonset[0] >= 0 else None
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __
