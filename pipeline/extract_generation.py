import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

import pandas as pd
import requests
from dotenv import load_dotenv

from pipeline.common import DataProcessor
import config as cg
from constants import Constants as ct

# Global constants
ENDPOINT = ct.GENERATION_ENDPOINT
SAVE_NAME = ct.RAW_GENERATION_DATA_NAME
SAVE_LOCATION = ct.RAW_GENERATION_DATA_PATH
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
            # ISO 8601 format, already UTC-aware
            'publishDateTimeFrom': twelve_hours_ago.isoformat(),
            'publishDateTimeTo': now.isoformat(),
            'format': 'json'
        }

    def fetch_data(self) -> Optional[Dict[str, Any]]:
        """
        Uses the above-created time range to make an API request, returning data.
        """
        try:
            response = requests.get(
                self.base_url, params=self.construct_default_params())
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

    def process_data(self, data: Dict[str, Any]) -> Optional[Tuple[pd.DataFrame, Dict[str, datetime]]]:
        """
        Takes data, returns it as a tuple. The first element is the data in
        a pd.DataFrame, the second element is a dictionary containing the
        time window over which the data was fetched.
        """

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
        self.s3_access_key = s3_access_key
        self.s3_secret_key = s3_secret_key
        self.s3_region = s3_region
        self.s3_bucket = s3_bucket
        self.s3_file_name = s3_file_name
        self.logger = logger

    def execute(self) -> Optional[Tuple[pd.DataFrame, Dict[str, datetime]]]:
        """
        Executes the full workflow: fetches data from the API, processes it,
        saves it locally, and uploads it to an S3 bucket.
        """
        self.logger.info("Starting the execution of the workflow.")

        try:
            data = self.api_client.fetch_data()
            if data:
                self.logger.info("Data successfully fetched from the API.")

                result = self.data_processor.process_data(data)
                if result is not None:
                    df, time_period = result

                    self.logger.debug("DataFrame of Demand Data:")
                    # Log the entire DataFrame as a string
                    self.logger.debug(df.to_string())
                    self.logger.info("Head of the DataFrame:")
                    self.logger.info("\n" + df.head().to_string())
                    self.logger.info("Time Period of Data:")
                    self.logger.info(time_period)

                    # Saving data locally
                    self.logger.info("Saving data locally.")
                    local_save_path = self.data_processor.save_data_locally(df)
                    self.logger.info(f"Data successfully saved locally at {
                                     local_save_path}.")

                    # Uploading data to S3
                    self.logger.info("Preparing to upload data to S3.")
                    s3_client = self.data_processor.get_s3_client()

                    if s3_client:
                        self.logger.info("S3 client initialized successfully.")
                        self.data_processor.save_data_to_s3()
                        self.logger.info(f"Data successfully uploaded to S3 at `{
                                         self.s3_file_name}`.")
                    else:
                        self.logger.error("Failed to initialize S3 client.")

                    return df, time_period
                else:
                    self.logger.error("Failed to process the data.")
            else:
                self.logger.error("Failed to retrieve data from API.")
        except Exception as e:
            self.logger.error(f"An error occurred during the execution: {e}")

        self.logger.info("Execution of the workflow completed.")
        return None


def main() -> None:
    """
    Runs everything
    """

    # Declare Variables
    script_name = SCRIPT_NAME

    # Setup logging and performance tracking
    performance_logger = cg.setup_subtle_logging(script_name)
    profiler = cg.start_monitor()
    logger.info("---> Logging initiated.")

    # Instantiate APIClient and DataProcessor using their default values
    api_client = APIClient()
    data_processor = CustomDataProcessor()

    # Instantiate the Main class, using default values for S3 credentials and logger
    main_class = Main(api_client, data_processor)

    # Run the main execution workflow
    main_class.execute()

    # Winds down, stores performance log
    logger.info("---> Operation completed. Stopping performance monitor.")
    cg.stop_monitor(script_name, profiler, performance_logger)
    logger.info("---> Data inserted and process completed for %s.", script_name)


if __name__ == "__main__":
    main()
