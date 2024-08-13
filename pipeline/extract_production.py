import os
import sys
import requests
import pandas as pd
import logging
from datetime import datetime, timedelta, timezone

import config as cg
from constants import Constants as ct

# Set up logging
SCRIPT_NAME = (os.path.basename(__file__)).split(".")[0]
LOGGING_LEVEL = logging.DEBUG

logger = cg.setup_logging(SCRIPT_NAME, LOGGING_LEVEL)

ENDPOINT = ct.PRODUCTION_ENDPOINT

class APIClient:
    def __init__(self, base_url):
        self.base_url = base_url

    def construct_default_params(self):

        twelve_hours_ago = datetime.now(timezone.utc) - timedelta(hours=12)
        now = datetime.now(timezone.utc)

        return {
            'publishDateTimeFrom': twelve_hours_ago.isoformat(),  # ISO 8601 format, already UTC-aware
            'publishDateTimeTo': now.isoformat(),
            'format': 'json'
        }

    def fetch_data(self):
        try:
            response = requests.get(self.base_url, params=self.construct_default_params())
            response.raise_for_status()  
            return response.json()  
        except requests.exceptions.RequestException as e:
            logger.error(f"An error occurred: {e}")
            return None

class DataProcessor:
    def process_data(self, data):
        if not data or "data" not in data:
            logger.warning("No data found in response.")
            return None
        
        df = pd.DataFrame(data["data"])
        
        publish_times = pd.to_datetime(df["publishTime"])
        time_period = {
            "publishTimeStart": publish_times.min(),
            "publishTimeEnd": publish_times.max()
        }
        
        return df, time_period

class Main:
    def __init__(self, api_client, data_processor):
        self.api_client = api_client
        self.data_processor = data_processor

    def execute(self):
        data = self.api_client.fetch_data()
        if data:
            df, time_period = self.data_processor.process_data(data)
            if df is not None:
                logger.info("DataFrame of Fuel Data:")
                logger.debug(df.to_string())  # Log the DataFrame as a string
                logger.info("\nTime Period of Data:")
                logger.info(time_period)
                return df, time_period
            else:
                logger.error("Failed to process the data.")
        else:
            logger.error("Failed to retrieve data from API.")
        return None, None
        
if __name__ == "__main__":
    base_url = ENDPOINT
    
    api_client = APIClient(base_url)
    data_processor = DataProcessor()
    main = Main(api_client, data_processor)

    main.execute()