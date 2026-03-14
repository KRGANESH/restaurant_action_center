import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DB_PATH = "database/restaurant.db"
CSV_PATH = "data/restaurant_inventory_100days.csv"
COST_RATIO_THRESHOLD = 0.5
MAX_ALERTS_TO_ENRICH = 5