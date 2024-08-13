import os
import sys
import requests
from datetime import datetime, timedelta, timezone

import config as cg
from constants import Constants as ct

ENDPOINT = ct.PRODUCTION_ENDPOINT

class APIClient:
    def __init__(self, base_url):
        self.base_url = base_url

    def construct_default_params(self):
        
        twelve_hours_ago = datetime.now(timezone.utc) - timedelta(hours=12)
        now = datetime.now(timezone.utc)

        return {
            'start_time': twelve_hours_ago.isoformat(),  # ISO 8601 format, already UTC-aware
            'end_time': now.isoformat(),
        }

    def fetch_data(self):
        
        try:
            response = requests.get(self.base_url, params=self.construct_default_params())
            response.raise_for_status()  
            return response.json()  
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            return None

class DataProcessor:
    def get_last_entry(self, data):
        if not data or "data" not in data:
            print("No data found in response.")
            return None
        
        # Sorting data by publishTime to ensure we get the latest entry
        sorted_data = sorted(data["data"], key=lambda x: datetime.fromisoformat(x["publishTime"][:-1]))
        return sorted_data[-1] if sorted_data else None

class Main:
    def __init__(self, api_client, data_processor):
        self.api_client = api_client
        self.data_processor = data_processor

    def get_latest_data_entry(self):
        data = self.api_client.fetch_data()
        if data:
            last_entry = self.data_processor.get_last_entry(data)
            if last_entry:
                return last_entry
            else:
                print("Failed to find the last entry.")
        else:
            print("Failed to retrieve data from API.")
        
        
if __name__ == "__main__":
    base_url = ENDPOINT
    
    api_client = APIClient(base_url)
    data_processor = DataProcessor()
    main = Main(api_client, data_processor)

    latest_entry = main.get_latest_data_entry()
    if latest_entry:
        print("Last Data Entry:")
        print(latest_entry)