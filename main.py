from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import swisseph as swe
import pytz
from datetime import datetime

app = FastAPI()
