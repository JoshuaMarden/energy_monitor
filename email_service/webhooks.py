"""
Creates the urls for webhooks and also sends them off
telling the server when to turn on or off the Electric cars
"""
import os
import logging
from typing import Any, Dict, Optional
import json
import datetime

import requests
import pandas as pd
from psycopg2.extensions import connection
from psycopg2 import connect
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

from pipeline.common import DataProcessor
import config as cg
from constants import Constants as ct

load_dotenv()

ENDPOINT = "http://user/"
STOP_START_CHARGING = "/charging_status/"
SCRIPT_NAME = (os.path.basename(__file__)).split(".")[0]
LOGGING_LEVEL = logging.DEBUG
global_logger = cg.setup_logging(SCRIPT_NAME, LOGGING_LEVEL)


class Extract:
    """
    Extracts data from a database
    """

    def __init__(self) -> None:
        """
        Initialize class variables.
        """
        self.logger = global_logger

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

    def get_user_data(self, conn: connection):
        """
        Loads the data from the RDS database
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


class APIClient:
    """
    Constructs the default parameters for a request, and makes the request
    returning data over a specific range.
    """

    def __init__(self,
                 logger: logging.Logger = global_logger) -> None:
        """
        Initialise class variables.
        """
        self.logger = logger

    def post_webhook_data(self, user_data, on_off) -> Optional[Dict[str, Any]]:
        """
        Makes an API request, returning data as json.
        """
        headers = {'Content-Type': 'application/json'}
        base_url = ENDPOINT + \
            user_data['user_id'] + STOP_START_CHARGING + on_off

        try:
            response = requests.post(
                base_url, data=json.dumps(user_data), headers=headers, timeout=20)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"An error occurred: {e}")
            return None

    def create_webhook_data(self, user_data: dict) -> dict:
        """
        Creates the data sent to the webhook url
        """
        webhook_data = {}

        return webhook_data

    def check_turn_on(self, time: list) -> bool:
        """
        Checks to see if the current time falls in the range that the 
        Electric car should be charging
        """
        now = datetime.datetime.now()
        start = datetime.datetime.strptime(time[0], "%Y-%m-%dT%H:%M%z")
        end = datetime.datetime.strptime(time[1], "%Y-%m-%dT%H:%M%z")
        if start < now < end:
            return True
        return False


if __name__ == "__main__":
    extract = Extract()
    client = APIClient()
    db_conn = extract.get_connection()
    user_data_db = extract.get_user_data(db_conn)
    for _, user in user_data_db.iterrows():
        print(user)
        if client.check_turn_on(user['hours']):
            users_webhook_data = client.create_webhook_data(user)
            client.post_webhook_data(users_webhook_data, 'on')
        elif user['already_on']:
            users_webhook_data = client.create_webhook_data(user)
            client.post_webhook_data(users_webhook_data, 'off')
