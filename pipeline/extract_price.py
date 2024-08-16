import logging
import os
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import requests
from dotenv import load_dotenv

from pipeline.common import DataProcessor
import config as cg
from constants import Constants as ct

# Global constants
ENDPOINT = ct.PRICE_ENDPOINT
SAVE_NAME = ct.RAW_PRICE_DATA_NAME
SAVE_LOCATION = ct.RAW_PRICE_DATA_PATH
S3_BUCKET = ct.S3_BUCKET
REFERENCE_DATA = ct.RAW_GENERATION_DATA_PATH

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

    def __init__(self, base_url: str = ENDPOINT, logger: logging.Logger = logger) -> None:
        """
        Initialize class variables.
        """
        self.base_url = base_url
        self.logger = logger
    
    def get_settlement_periods(self,
                               path_to_reference_data: str = REFERENCE_DATA)\
                                                                             -> Dict\
                                                                                [str, List[int]]:
        """
        Gets a local file and looks at what dates/settlement periods are in it.
        Those settlement periods can be used to request the price of fuel
        at those times.
        """
        df = pd.read_feather(path_to_reference_data)
        periods = df.groupby('settlementDate')['settlementPeriod'].unique().to_dict()
        periods = {k: list(v) for k, v in periods.items()}
        logger.info(f"Getting price data for {periods}")
        return periods

    def construct_default_params(self, date: str, period: int) -> str:
        """
        Constructs the request URL using a specific date and period.
        """
        return f"{self.base_url}/{date}/{period}?format=json"

    def fetch_data(self, periods: Dict[str, List[int]]) -> List[Dict[str, Any]]:
        """
        Makes API requests for each date and settlement period.
        """
        response_list = []

        for date, period_list in periods.items():
            for period in period_list:
                url = self.construct_default_params(date, period) 

                try:
                    response = requests.get(url) 
                    response.raise_for_status()  
                    response_list.append(response.json())  
                except requests.exceptions.RequestException as e:
                    self.logger.warning(f"An error occurred when requesting fuel data for {date}, period {period}!")
                    self.logger.warning(f"{e}")
            
        return response_list


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
        super().__init__(save_location, 
                         aws_access_key, 
                         aws_secret_key, 
                         region, 
                         s3_file_name, 
                         bucket, 
                         logger)

    def process_data(self, response_list: List[Dict[str, Any]],
                     logger: logging.Logger = logger) -> Optional[Tuple[pd.DataFrame, int]]:
        """
        Takes a list of responses, merges them into a DataFrame, and returns it.
        """
        logger = logger or self.logger
        
        if not response_list:
            logger.warning("No data found in response.")
            return None
        
        df_list = [pd.DataFrame(response["data"]) for response in response_list]
        if not df_list:
            logger.warning("No valid data found in response list.")
            return None

        df = pd.concat(df_list, ignore_index=True)
        df_length = len(df)

        return df, df_length


class Main:
    """
    Links much of the functionality of the helper classes together.
    """
    def __init__(self, 
                 api_client: APIClient,
                 data_processor: CustomDataProcessor,
                 reference_data_path: str = REFERENCE_DATA, 
                 logger: logging.Logger = logger) -> None:
        """
        Initialize class variables.
        """
        self.api_client = api_client
        self.data_processor = data_processor
        self.reference_data_path = reference_data_path
        self.logger = logger

    def execute(self) -> Optional[Tuple[pd.DataFrame, int]]:
        """
        Executes the full workflow: fetches data from the API, processes it,
        saves it locally, and uploads it to an S3 bucket.
        """
        self.logger.info("Starting the execution of the workflow.")
    
        try:
            periods = self.api_client.get_settlement_periods(self.reference_data_path)
            self.logger.info(f"Retrieved settlement periods: {periods}")

            response_list = self.api_client.fetch_data(periods)
            if response_list:
                self.logger.info("Data successfully fetched from the API.")

                result = self.data_processor.process_data(response_list)
                if result is not None:
                    df, number_of_settlement_periods = result

                    self.logger.debug("DataFrame of Price Data:")
                    self.logger.debug(df.to_string())  # Log the entire DataFrame as a string
                    self.logger.info("Head of the DataFrame:")
                    self.logger.info("\n" + df.head().to_string())
                    self.logger.info("Number of Settlement Periods:")
                    self.logger.info(number_of_settlement_periods)

                    # Saving data locally
                    self.logger.info("Saving data locally.")
                    local_save_path = self.data_processor.save_data_locally(df)
                    self.logger.info(f"Data successfully saved locally at {local_save_path}.")

                    # Uploading data to S3
                    self.logger.info("Preparing to upload data to S3.")
                    s3_client = self.data_processor.get_s3_client()

                    if s3_client:
                        self.logger.info("S3 client initialized successfully.")
                        self.data_processor.save_data_to_s3()
                        self.logger.info(f"Data successfully uploaded to S3 at `{self.data_processor.s3_file_name}`.")
                    else:
                        self.logger.error("Failed to initialize S3 client.")

                    return df, number_of_settlement_periods
                else:
                    self.logger.error("Failed to process the data.")
            else:
                self.logger.error("Failed to retrieve data from the API.")
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

    # Instantiate APIClient and DataProcessor with default arguments
    api_client = APIClient() 
    data_processor = CustomDataProcessor()  

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