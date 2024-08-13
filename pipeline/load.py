import os
import sys
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Dict, Any

import boto3
import requests
import pandas as pd


import config as cg
from constants import Constants as ct

SCRIPT_NAME = (os.path.basename(__file__)).split(".")[0]
LOGGING_LEVEL = logging.DEBUG
logger = cg.setup_logging(SCRIPT_NAME, LOGGING_LEVEL)


class S3bucket:
    """
    downloads files in an S3 bucket
    """

    def __init__(self) -> None:
        """
        Initialize class variables.
        """
        self.bucket = "c12-energy-tracker"
        self.secret_key = os.environ.get("ACCESS_KEY")
        self.public_key = os.environ.get("ACCESS_KEY")

    def get_client(self) -> boto3.client:
        """Connects to the S3 instance and returns it"""
        s3 = boto3.client('s3',
                          aws_access_key_id=self.public_key,
                          aws_secret_access_key=self.secret_key)
        return s3

    def get_files_from_bucket(self):
        client = self.get_client()
        data = client.list_objects(Bucket=self.bucket)
        print(data['Contents'])


if __name__ == "__main__":
    s3_bucket = S3bucket()
    s3_bucket.get_files_from_bucket()
    print("hello")
