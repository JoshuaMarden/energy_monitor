"""
Holds the classes that are common the the pipelines' extract scripts
"""
import requests
import logging
import pandas as pd
import boto3
from typing import Dict, Any, Optional
        
class DataProcessor:
    """
    Generic data processing class that handles saving and uploading data.
    """

    def __init__(self, save_location: str, 
                 aws_access_key: str, 
                 aws_secret_key: str, 
                 region: str, 
                 s3_file_name: str, 
                 bucket: str, 
                 logger: logging.Logger) -> None:
        """
        Initialize class variables.

        All vars are intitiated here as flexibility is irrelevant,
        readability and convenicne is King.
        """
        self.save_location = save_location
        self.aws_access_key = aws_access_key
        self.aws_secret_key = aws_secret_key
        self.region = region
        self.s3_file_name = s3_file_name
        self.bucket = bucket
        self.logger = logger
        self.s3_client = None

    def save_data_locally(self, dataframe: pd.DataFrame) -> None:
        """
        Saves the DataFrame to the specified save location in Feather format.
        """
        dataframe.to_feather(self.save_location)
        self.logger.info(f"Raw data saved to `{self.save_location}`")

    def get_s3_client(self) -> Optional[boto3.client]:
        """
        Gets the boto3 client so that s3 bucket can be accessed for data storage.
        """
        self.logger.info("Fetching boto3 client...")
        self.logger.info("AWS access key: `%s`", self.aws_access_key)
        self.logger.info("AWS secret key: `%s`", self.aws_secret_key)

        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.region
            )
            self.logger.info("Retrieved client successfully.")
            self.logger.debug(f"Client: {self.s3_client}")

        except Exception as e:
            self.logger.error("Failed to get client!")
            self.logger.error(f"{e}")
            self.s3_client = None

        return self.s3_client

    def save_data_to_s3(self) -> None:
        """
        Save data to the S3 bucket.
        """
        if not self.s3_client:
            self.logger.error("S3 client not initialized!")
            return

        try:
            with open(self.save_location, 'rb') as file_data:
                self.s3_client.put_object(Bucket=self.bucket, Key=self.s3_file_name, Body=file_data)
            self.logger.info(f"Data successfully saved to S3 as `{self.s3_file_name}`.")
        except Exception as e:
            self.logger.error(f"Error saving data to S3: {e}")
