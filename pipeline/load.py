import os
import sys
import logging
import glob
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
        self.logger = logger
        self.bucket = "c12-energy-tracker"
        self.public_key = os.environ.get("ACCESS_KEY")
        self.secret_key = os.environ.get("SECRET_KEY")

    def get_client(self) -> boto3.client:
        """Connects to the S3 instance and returns it"""
        s3 = boto3.client('s3',
                          aws_access_key_id=self.public_key,
                          aws_secret_access_key=self.secret_key)
        return s3

    def get_files_from_bucket(self):
        """
        Downloads All files in the s3 Bucket
        """
        client = self.get_client()
        data = client.list_objects(Bucket=self.bucket)
        for file in data['Contents']:

            client.download_file(self.bucket, file['Key'], f'''{
                                 file['Key']} {file['LastModified']}''')
            self.logger.info(f"""Downloaded file: '{file['Key']} {
                             file['LastModified']}'""")


class Transform:
    """
   turns all files into a pd.Dataframe with the correct format

    """

    def __init__(self) -> None:
        """
        Initialize class variables.
        """
        ...

    def get_dfs(self):
        files = [file for file in glob.glob(
            f"*.feather*") if os.path.isfile(file)]

        for file in files:
            df = pd.read_feather(file)
            if "production" in file:
                self.production_transform(df)
            if "demand" in file:
                self.demand_transform(df)
            if "cost" in file:
                self.cost_transform(df)

    def production_transform(self, df: pd.DataFrame):

        df['gain_loss'] = df['generation'].apply(
            lambda x: '+' if x > 0 else '-')
        df = df[['publishTime', 'fuelType', 'gain_loss',
                'generation', 'settlementPeriod']]

        values = list(df.itertuples(index=False, name=None))

    def demand_transform(self, df: pd.DataFrame):
        df = df[['startTime', 'demand']]
        values = list(df.itertuples(index=False, name=None))

    def cost_transform(self, df: pd.DataFrame):
        df.to_csv('to.csv')
        df = df[['settlementDate', 'settlementPeriod',
                 'systemSellPrice', 'systemBuyPrice']]
        values = list(df.itertuples(index=False, name=None))


if __name__ == "__main__":
    s3_bucket = S3bucket()
    s3_bucket.get_files_from_bucket()
    tf = Transform()
    tf.get_dfs()

    print("hello")
