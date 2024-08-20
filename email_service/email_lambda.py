"""
Connects to the database, gets the hours to send to users and sends the email
to about when they the best time is to charge their EVs and other electric devices
"""
import os
import logging
import glob

from dotenv import load_dotenv
import boto3
import pandas as pd
from psycopg2.extensions import connection
from psycopg2 import connect
from psycopg2.extras import RealDictCursor, execute_values
import datetime

from pipeline.common import DataProcessor
import config as cg
from constants import Constants as ct


class GetUserData:
    ...


class DatabaseConnection:
    """
    gets database connection
    """

    def get_connection(self) -> connection:
        """Returns a connection to the database movies"""
        connecting = connect(
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASSWORD"),
            host=os.environ.get("DB_HOST"),
            port=os.environ.get("DB_PORT"),
        )
        connecting.autocommit = True
        return connecting
