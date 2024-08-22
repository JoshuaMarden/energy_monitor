"""
Connects to the database, gets the hours to send to users and sends the email
to about when they the best time is to charge their EVs and other electric devices
"""
import os
import logging
from typing import Any, Dict, Optional

from dotenv import load_dotenv
import datetime
import boto3
import requests
import pandas as pd
from psycopg2.extensions import connection
from psycopg2 import connect
from psycopg2.extras import RealDictCursor
import datetime

from pipeline.common import DataProcessor
import config as cg
from constants import Constants as ct

load_dotenv()

ENDPOINT_1 = "https://api.carbonintensity.org.uk/regional/intensity/"
ENDPOINT_2 = "/fw24h/postcode/"
SCRIPT_NAME = (os.path.basename(__file__)).split(".")[0]
LOGGING_LEVEL = logging.DEBUG
logger = cg.setup_logging(SCRIPT_NAME, LOGGING_LEVEL)


class APIClient:
    """
    Constructs the default parameters for a request, and makes the request
    returning data over a specific range.
    """

    def __init__(self,
                 logger: logging.Logger = logger) -> None:
        """
        Initialise class variables.
        """
        self.logger = logger

    def fetch_regional_data(self, postcode) -> Optional[Dict[str, Any]]:
        """
        Makes an API request, returning data as json.
        """
        headers = {'Accept': 'application/json'}
        now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M%z")
        base_url = ENDPOINT_1 + str(now) + ENDPOINT_2 + postcode.split(' ')[0]

        try:
            response = requests.get(base_url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"An error occurred: {e}")
            return None


class Extract:
    """
    Extracts data from a database
    """

    def __init__(self) -> None:
        """
        Initialize class variables.
        """
        self.logger = logger

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

    def get_user_data(self, conn):
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


class SendEmail:

    def send_email(self, data):
        print(data)
        ses = boto3.client('ses',
                           aws_access_key_id=os.environ.get("ACCESS_KEY"),
                           aws_secret_access_key=os.environ.get("SECRET_KEY"),
                           region_name='eu-west-2')
        ses.send_email(
            Source='trainee.jonathan.spence@sigmalabs.co.uk',
            Destination={
                'ToAddresses': [
                    'trainee.jonathan.spence@sigmalabs.co.uk'
                ]
            },
            Message={
                'Subject': {
                    'Data': 'Hours you should charge your car based on the lowest carbon levels',
                },
                'Body': {
                    'Html': {
                        'Data': f'Charge your car between {data[0]} and {data[1]}',
                    }
                }
            },
        )


class ChargeHours:

    def get_possible_hours(self, user_data):
        api_conn = APIClient()
        hours_data = []

        for _, user in user_data.iterrows():
            carbon_data = api_conn.fetch_regional_data(user['user_postcode'])
            carbon = []
            for row in carbon_data['data']['data']:

                carbon.append(
                    {'from': row['from'], 'forecast': row['intensity']['forecast']})
            df = pd.DataFrame.from_dict(carbon)
            df_lowest = df.sort_values(
                'forecast').head(1)
            lowest_index = list(df_lowest.index)[0]
            hours = user['hours_to_charge']
            low = lowest_index - hours
            high = lowest_index + hours
            if low <= 0:
                df = df.head(hours*2)
            elif high >= 48:
                df = df.tail(hours*2)

            else:
                df = df[(df.index >= low) & (df.index <= high)]

            hours_data.append({'user_id': user['users_id'], 'hours': [
                              df['from'].head(1).values[0], df['from'].tail(1).values[0]]})
        return hours_data


if __name__ == "__main__":
    extract = Extract()
    charge_hours = ChargeHours()
    conn = extract.get_connection()
    user_datadb = extract.get_user_data(conn)
    data = charge_hours.get_possible_hours(user_datadb)
    email = SendEmail()
    for user in data:
        email.send_email(user['hours'])
