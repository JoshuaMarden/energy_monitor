import os
import sys
import requests
import pandas as pd
import logging
import pyarrow
import boto3
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Dict, Any

import config as cg
from constants import Constants as ct

ENDPOINT = ct.DEMAND_ENDPOINT
SAVE_NAME = ct.RAW_DEMAND_DATA_NAME
SAVE_LOCATION = ct.RAW_DEMAND_DATA_PATH
S3_BUCKET = ct.S3_BUCKET

load_dotenv('.env')
AWS_ACCESS_KEY=os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_KEY=os.getenv('AWS_SECRET_KEY')
AWS_REGION=os.getenv('AWS_REGION')

# Logging
SCRIPT_NAME = (os.path.basename(__file__)).split(".")[0]
LOGGING_LEVEL = logging.DEBUG
logger = cg.setup_logging(SCRIPT_NAME, LOGGING_LEVEL)

class APIClient:
    """
    Constructs the default parameters for a request, and makes the request
    returning data over a specific range.
    """

    def __init__(self, base_url: str, logger: logging.Logger) -> None:
        """
        Initialise class variables.
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
            'From': twelve_hours_ago.isoformat(),  # ISO 8601 format, already UTC-aware
            'To': now.isoformat(),
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
    """
    Processes the data that is returned from APIClient, putting it in
    a pandas DataFrame.
    """
    def __init__(self, save_location: str, logger: logging.Logger) -> None:
        """
        Initialize class variables.
        """
        self.logger = logger
        self.save_location = save_location

    def process_data(self, data: Dict[str, Any]) -> Optional[Tuple[pd.DataFrame, Dict[str, datetime]]]:
        """
        Takes data, returns it as a tuple. The first element is the data in
        a pd.DataFrame, the second element is a dictionary containing the
        time window over which the data was fetched.
        """
        if not data or "data" not in data:
            self.logger.warning("No data found in response.")
            return None

        df = pd.DataFrame(data["data"])

        start_times = pd.to_datetime(df["startTime"])
        time_period = {
            "From": start_times.min(),
            "To": start_times.max()
        }

        return df, time_period

    def save_data_locally(self, dataframe: pd.DataFrame) -> None:
        """
        Saves the DataFrame to the specified save location in Feather format.
        """
        dataframe.to_feather(self.save_location)
        self.logger.info(f"Raw data saved to `{self.save_location}`")

    def get_s3_client(self, access_key: str, secret_key: str, region: str) -> Optional[boto3.client]:
        """
        Gets the boto3 client so that s3 bucket can be accessed for data storage
        """
        self.logger.info("Fetching boto3 client...")
        self.logger.info("AWS access key: `%s`", cg.obscure(access_key))
        self.logger.info("AWS secret key: `%s`", cg.obscure(secret_key))

        try:
            client = boto3.client(
                's3',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region
            )
            self.logger.info("Retrieved client successfully.")
            self.logger.debug(f"Client: {client}")

        except Exception as e:
            self.logger.error("Failed to get client!")
            self.logger.error(f"{e}")
            return None

        return client

    def save_data_to_s3(self, client: boto3.client, 
                        save_location: str,
                        s3_file_name: str,
                        bucket: str)\
                                    -> None:
        """
        Save data to the S3 bucket.
        """
        try:
            with open(save_location, 'rb') as file_data:
                client.put_object(Bucket=bucket, Key=s3_file_name, Body=file_data)
            self.logger.info(f"Data successfully saved to S3 as `{s3_file_name}`.")
        except Exception as e:
            self.logger.error(f"Error saving data to S3: {e}")


class Main:
    """
    Links much of the functionality of the helper classes together.
    """
    def __init__(self, api_client: APIClient,
                 data_processor: DataProcessor,
                 logger: logging.Logger) -> None:
        """
        Initialize class variables.
        """
        self.api_client = api_client
        self.data_processor = data_processor
        self.logger = logger

    def execute(self, 
                s3_access_key: str, 
                s3_secret_key: str, 
                s3_region: str, 
                s3_bucket: str, 
                s3_file_name: str) -> Optional[Tuple[pd.DataFrame, Dict[str, datetime]]]:
        """
        Executes the full workflow: fetches data from the API, processes it,
        saves it locally, and uploads it to an S3 bucket.
        """
        data = self.api_client.fetch_data()
        if data:
            result = self.data_processor.process_data(data)
            if result is not None:
                df, time_period = result

                self.logger.debug("DataFrame of Fuel Data:")
                self.logger.debug(df.to_string())  # Log the entire DataFrame as a string
                self.logger.info("Head of the DataFrame:")
                self.logger.info("\n" + df.head().to_string())
                self.logger.info("Time Period of Data:")
                self.logger.info(time_period)

                self.data_processor.save_data_locally(df)

                s3_client = self.data_processor.get_s3_client(s3_access_key, s3_secret_key, s3_region)

                if s3_client:
                    self.data_processor.save_data_to_s3(s3_client, self.data_processor.save_location, s3_file_name, s3_bucket)
                return df, time_period
            else:
                self.logger.error("Failed to process the data.")
        else:
            self.logger.error("Failed to retrieve data from API.")
        return None

def main():
    """
    Runs everything
    """
    base_url = ENDPOINT
    save_location = SAVE_LOCATION

    s3_access_key = AWS_ACCESS_KEY
    s3_secret_key = AWS_SECRET_KEY
    s3_region = AWS_REGION
    s3_bucket = S3_BUCKET
    s3_file_name = SAVE_NAME

    # Setup logging and performance tracking
    performance_logger = cg.setup_subtle_logging(SCRIPT_NAME)
    profiler = cg.start_monitor()
    logger.info("---> Logging initiated.")

    api_client = APIClient(base_url, logger)
    data_processor = DataProcessor(save_location, logger)
    main_class = Main(api_client, data_processor, logger)


    # Winds down, stores performance log.
    logger.info("---> Operation completed. Stopping performance monitor.")
    cg.stop_monitor(SCRIPT_NAME, profiler, performance_logger)
    logger.info("---> Data inserted and process completed for %s.", SCRIPT_NAME)

    main_class.execute(s3_access_key, s3_secret_key, s3_region, s3_bucket, s3_file_name)


if __name__ == "__main__":

    main()
