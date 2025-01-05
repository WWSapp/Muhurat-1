import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import swisseph as swe
import pytz
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set ephemeris path
ephe_path = os.path.join(os.path.dirname(__file__), 'ephe')
swe.set_ephe_path(ephe_path)

class DateRequest(BaseModel):
    date: Optional[str] = None
    timezone: Optional[str] = "Asia/Kolkata"

@app.get("/")
async def root():
    return {"message": "Panchanga API is running"}

@app.post("/panchanga/")
async def get_panchanga(request: DateRequest):
    try:
        # Parse date or use current date
        if request.date:
            date = datetime.strptime(request.date, "%Y-%m-%d")
        else:
            date = datetime.now(pytz.timezone(request.timezone))
        
        # Convert to Julian Date
        jd = swe.julday(date.year, date.month, date.day, 
                       date.hour + date.minute/60.0)
        
        # Get sunrise, sunset
        sunrise = swe.rise_trans(jd, swe.SUN, rsmi=swe.CALC_RISE)
        sunset = swe.rise_trans(jd, swe.SUN, rsmi=swe.CALC_SET)
        
        # Calculate positions
        sun_pos = swe.calc_ut(jd, swe.SUN)[0]
        moon_pos = swe.calc_ut(jd, swe.MOON)[0]
        
        # Calculate tithi (lunar day)
        moon_sun_diff = moon_pos[0] - sun_pos[0]
        if moon_sun_diff < 0:
            moon_sun_diff += 360
        tithi = int(moon_sun_diff / 12) + 1
        
        return {
            "date": date.strftime("%Y-%m-%d"),
            "sunrise": sunrise,
            "sunset": sunset,
            "tithi": tithi,
            "sun_longitude": sun_pos[0],
            "moon_longitude": moon_pos[0]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
