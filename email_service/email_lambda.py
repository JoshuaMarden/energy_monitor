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
from psycopg2.extras import RealDictCursor, execute
import datetime

from pipeline.common import DataProcessor
import config as cg
from constants import Constants as ct

load_dotenv()

SCRIPT_NAME = (os.path.basename(__file__)).split(".")[0]
LOGGING_LEVEL = logging.DEBUG
logger = cg.setup_logging(SCRIPT_NAME, LOGGING_LEVEL)


class Load:
    """
    Loads data into a database
    """

    def __init__(self) -> None:
        """
        Initialize class variables.
        """
        self.logger = logger

    def get_user_data(self, conn, data):
        """
        Loads the data into an RDS database
        """
        curr = conn.cursor(cursor_factory=RealDictCursor)

        sql_query = """SELECT * FROM user_data"""
        curr.execute(sql_query)
        data = curr.fetchall()

        self.logger.info(
            """Loaded user data from the database""")
        curr.close()
        conn.close()
        return pd.DataFrame.from_dict(data)


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
