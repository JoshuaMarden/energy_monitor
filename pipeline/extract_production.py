import os
import sys
import requests
import pandas as pd
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Dict, Any

import config as cg
from constants import Constants as ct

# Set up logging
SCRIPT_NAME = (os.path.basename(__file__)).split(".")[0]
LOGGING_LEVEL = logging.DEBUG

logger = cg.setup_logging(SCRIPT_NAME, LOGGING_LEVEL)

ENDPOINT = ct.PRODUCTION_ENDPOINT

class APIClient:
    """
    Constructs the default parameters for a request, and makes the request
    returning data over a specific range.
    """
   
    def __init__(self, base_url: str, logger: logging.Logger) -> None:
        """
        Initialize class variables.
        """
        self.base_url = base_url
        self.logger = logger

    def construct_default_params(self) -> Dict[str, str]:
        """
        Get a time range. Currently fetches data from 12 hours ago to present.
        """
        twelve_hours_ago = datetime.now(timezone.utc) - timedelta(hours=12)
        now = datetime.now(timezone.utc)

        return {
            'publishDateTimeFrom': twelve_hours_ago.isoformat(),  # ISO 8601 format, already UTC-aware
            'publishDateTimeTo': now.isoformat(),
            'format': 'json'
        }

    def fetch_data(self) -> Optional[Dict[str, Any]]:
        """
        Uses the above-created time range to make an API request, returning data.
        """
        try:
            response = requests.get(self.base_url, params=self.construct_default_params())
            response.raise_for_status()  
            return response.json()  
        except requests.exceptions.RequestException as e:
            self.logger.error(f"An error occurred: {e}")
            return None

class DataProcessor:
    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger

    def process_data(self, data: Dict[str, Any]) -> Optional[Tuple[pd.DataFrame, Dict[str, datetime]]]:
        if not data or "data" not in data:
            self.logger.warning("No data found in response.")
            return None
        
        df = pd.DataFrame(data["data"])
        
        publish_times = pd.to_datetime(df["publishTime"])
        time_period = {
            "publishTimeStart": publish_times.min(),
            "publishTimeEnd": publish_times.max()
        }
        
        return df, time_period

class Main:
    def __init__(self, api_client: APIClient, data_processor: DataProcessor, logger: logging.Logger) -> None:
        self.api_client = api_client
        self.data_processor = data_processor
        self.logger = logger

    def execute(self) -> Optional[Tuple[pd.DataFrame, Dict[str, datetime]]]:
        data = self.api_client.fetch_data()
        if data:
            result = self.data_processor.process_data(data)
            if result is not None:
                df, time_period = result
                self.logger.info("DataFrame of Fuel Data:")
                self.logger.debug(df.to_string())  # Log the DataFrame as a string
                self.logger.info("\nTime Period of Data:")
                self.logger.info(time_period)
                return df, time_period
            else:
                self.logger.error("Failed to process the data.")
        else:
            self.logger.error("Failed to retrieve data from API.")
        return None
        
if __name__ == "__main__":
    base_url = ENDPOINT
    
    api_client = APIClient(base_url, logger)
    data_processor = DataProcessor(logger)
    main = Main(api_client, data_processor, logger)

    main.execute()