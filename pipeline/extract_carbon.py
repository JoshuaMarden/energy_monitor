import logging
import os
from typing import Any, Dict, Optional

import boto3
import pandas as pd
import requests
from dotenv import load_dotenv

from common import DataProcessor
import config as cg
from constants import Constants as ct

save_directory = 'tmp/data'
if not os.path.exists(save_directory):
    os.makedirs(save_directory)

# Global constants
ENDPOINT = ct.CARBON_ENDPOINT
SAVE_NAME = ct.RAW_CARBON_DATA_NAME
SAVE_LOCATION = ct.RAW_CARBON_DATA_PATH
S3_BUCKET = ct.S3_BUCKET

load_dotenv('.env')
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
AWS_REGION = os.getenv('AWS_REGION')

# Logging
SCRIPT_NAME = os.path.basename(__file__).split(".")[0]
LOGGING_LEVEL = logging.DEBUG
logger = cg.setup_logging(SCRIPT_NAME, LOGGING_LEVEL)


class APIClient:
    """
    Constructs the default parameters for a request, and makes the request
    returning data over a specific range.
    """

    def __init__(self,
                 base_url: str = ENDPOINT,
                 logger: logging.Logger = logger) -> None:
        """
        Initialise class variables.
        """
        self.base_url = base_url
        self.logger = logger

    def fetch_data(self) -> Optional[Dict[str, Any]]:
        """
        Makes an API request, returning data as json.
        """
        headers = {'Accept': 'application/json'}
        try:
            response = requests.get(self.base_url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"An error occurred: {e}")
            return None


class CustomDataProcessor(DataProcessor):
    """
    Custom DataProcessor that implements a specific process_data method.
    """

    def __init__(self, save_location: str = SAVE_LOCATION,
                 aws_access_key: str = AWS_ACCESS_KEY,
                 aws_secret_key: str = AWS_SECRET_KEY,
                 region: str = AWS_REGION,
                 s3_file_name: str = SAVE_NAME,
                 bucket: str = S3_BUCKET,
                 logger: logging.Logger = logger) -> None:
        """
        Initialize the CustomDataProcessor with the parent class constructor.
        """
        # Call the parent class's __init__ method
        super().__init__(save_location,
                         aws_access_key,
                         aws_secret_key,
                         region,
                         s3_file_name,
                         bucket,
                         logger)

    def process_data(self, data: Dict[str, Any],
                     logger: logging.Logger = logger) -> Optional[pd.DataFrame]:
        """
        Takes data, places it in DataFrame, and reformats it.
        """
        logger = logger or logging.getLogger(__name__)

        if not data or "data" not in data:
            logger.warning("No data found in response.")
            return None

        df = pd.DataFrame(data["data"])

        # Custom processing logic
        df['forecast'] = df['intensity'].apply(lambda x: x['forecast'])
        df['carbon level'] = df['intensity'].apply(lambda x: x['index'])

        return df[['from', 'to', 'forecast', 'carbon level']]


class Main:
    """
    Links much of the functionality of the helper classes together.
    """

    def __init__(self,
                 api_client: APIClient,
                 data_processor: CustomDataProcessor,
                 s3_access_key: str = AWS_ACCESS_KEY,
                 s3_secret_key: str = AWS_SECRET_KEY,
                 s3_region: str = AWS_REGION,
                 s3_bucket: str = S3_BUCKET,
                 s3_file_name: str = SAVE_NAME,
                 logger: logging.Logger = logger) -> None:
        """
        Initialize class variables.
        """
        self.api_client = api_client
        self.data_processor = data_processor
        self.logger = logger
        self.s3_access_key = s3_access_key
        self.s3_secret_key = s3_secret_key
        self.s3_region = s3_region
        self.s3_bucket = s3_bucket
        self.s3_file_name = s3_file_name

    def execute(self) -> Optional[pd.DataFrame]:
        """
        Executes the full workflow: fetches data from the API, processes it,
        saves it locally, and uploads it to an S3 bucket.
        """
        self.logger.info("Starting data fetch from API.")
        data = self.api_client.fetch_data()

        if data:
            self.logger.info("Data fetched successfully from API.")
            self.logger.debug(f"Fetched Data: {data}")

            self.logger.info("Processing the fetched data.")
            df = self.data_processor.process_data(data)

            if df is not None:
                self.logger.info("Data processed successfully into DataFrame.")
                self.logger.debug("DataFrame of Carbon Forecast Data:")
                self.logger.debug(df.to_string())

                self.logger.info("Saving the processed data locally.")
                self.data_processor.save_data_locally(df)
                self.logger.info(f"Data saved locally at `{
                                 self.data_processor.save_location}`.")

                self.logger.info("Attempting to get S3 client.")
                s3_client = self.data_processor.get_s3_client()

                if s3_client:
                    self.logger.info("S3 client retrieved successfully.")
                    self.logger.info("Uploading the data to S3.")
                    self.data_processor.save_data_to_s3()
                    self.logger.info(f"Data successfully uploaded to S3 bucket `{
                                     self.s3_bucket}` as `{self.s3_file_name}`.")
                else:
                    self.logger.error(
                        "Failed to get S3 client. Data was not uploaded to S3.")
                return df
            else:
                self.logger.error(
                    "Failed to process the data into a DataFrame.")
        else:
            self.logger.error("Failed to retrieve data from API.")

        return None


def main() -> None:
    """
    Runs everything
    """

    # Setup Variables
    script_name = SCRIPT_NAME
    save_location = SAVE_LOCATION

    # Setup logging and performance tracking
    performance_logger = cg.setup_subtle_logging(script_name)
    profiler = cg.start_monitor()
    logger.info("---> Logging initiated.")

    # Instantiate APIClient and DataProcessor using their default values
    api_client = APIClient()
    data_processor = CustomDataProcessor(save_location)

    # Instantiate Main class with default arguments
    main_class = Main(api_client, data_processor)

    # Run the main execution workflow
    main_class.execute()

    # Winds down, stores performance log
    logger.info("---> Operation completed. Stopping performance monitor.")
    cg.stop_monitor(script_name, profiler, performance_logger)
    logger.info("---> Data inserted and process completed for %s.", script_name)


if __name__ == "__main__":
    main()
