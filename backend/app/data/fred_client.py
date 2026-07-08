import httpx
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class FredAPIClient:
    BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

    def __init__(self):
        self.api_key = settings.FRED_API_KEY
        if not self.api_key:
            logger.warning("FRED_API_KEY is not set. FRED API calls will fail.")

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError))
    )
    def fetch_series(self, series_id: str, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[Dict[str, Any]]:
        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json"
        }
        
        if start_date:
            params["observation_start"] = start_date.strftime("%Y-%m-%d")
        if end_date:
            params["observation_end"] = end_date.strftime("%Y-%m-%d")

        with httpx.Client(timeout=10.0) as client:
            response = client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            
            data = response.json()
            observations = data.get("observations", [])
            
            records = []
            for obs in observations:
                val = obs.get("value")
                if val == "." or val is None:
                    continue # missing value handling
                
                records.append({
                    "observation_date": datetime.strptime(obs["date"], "%Y-%m-%d").date(),
                    "value": float(val),
                    "series_id": series_id,
                    "source": "FRED"
                })
                
            return records
