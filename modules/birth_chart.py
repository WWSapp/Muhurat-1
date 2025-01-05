import swisseph as swe
from typing import Dict, Any

# Add the birth chart calculation code here
def calculate_rashi(jd: float, planet: int) -> Dict[str, Any]:
    """Calculate Rashi (zodiac sign) for any planet"""
    # Use Lahiri ayanamsa
    position = swe.calc_ut(jd, planet, swe.FLG_SIDEREAL)[0]
    longitude = position[0]
    rashi_num = int(longitude / 30)
    degree = longitude % 30
    
    rashi_names = ["Mesha", "Vrishabha", "Mithuna", "Karka", 
                  "Simha", "Kanya", "Tula", "Vrishchika", 
                  "Dhanu", "Makara", "Kumbha", "Meena"]
    
    return {
        "rashi": rashi_names[rashi_num],
        "degree": degree,
        "longitude": longitude
    }

def calculate_birth_chart(jd: float, lat: float, lon: float) -> Dict[str, Any]:
    """Calculate complete birth chart"""
    planets = {
        "Sun": swe.SUN,
        "Moon": swe.MOON,
        "Mars": swe.MARS,
        "Mercury": swe.MERCURY,
        "Jupiter": swe.JUPITER,
        "Venus": swe.VENUS,
        "Saturn": swe.SATURN,
        "Rahu": swe.MEAN_NODE,  # Using mean nodes for Rahu
        "Ketu": swe.MEAN_NODE   # Ketu is 180° from Rahu
    }
    
    chart = {}
    for planet_name, planet_id in planets.items():
        rashi_info = calculate_rashi(jd, planet_id)
        if planet_name == "Ketu":
            # Adjust longitude for Ketu (180° from Rahu)
            rashi_info["longitude"] = (rashi_info["longitude"] + 180) % 360
            rashi_info["rashi"] = rashi_names[int(rashi_info["longitude"] / 30)]
        
        chart[planet_name] = rashi_info
