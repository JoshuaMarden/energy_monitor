"""
Connects to an S3 bucket, downloads, transforms and loads the data into a
database 
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

load_dotenv()

SCRIPT_NAME = (os.path.basename(__file__)).split(".")[0]
LOGGING_LEVEL = logging.DEBUG
logger = cg.setup_logging(SCRIPT_NAME, LOGGING_LEVEL)


class Transform:
    """
   turns all files into a pd.Dataframe with the correct format

    """

    def __init__(self) -> None:
        """
        Initialize class variables.
        """
        self.logger = logger

    def get_data(self) -> dict[tuple]:
        """
        Turns downloaded files into an pandas dataframe, then Transforms the 
        dataframe into a list of tuples
        """
        files = [file for file in glob.glob(
            "*.feather*") if os.path.isfile(file)]
        data = {}
        for file in files:
            df = pd.read_feather(file)
            if "generation" in file:
                formatted_data = self.generation_transform(df)
                data['generation'] = formatted_data
                self.logger.info(
                    """Transformed generation data""")
            if "demand" in file:
                formatted_data = self.demand_transform(df)
                data['demand'] = formatted_data
                self.logger.info("""Transformed demand data""")
            if "carbon" in file:
                formatted_data = self.carbon_transform(df)
                data['carbon'] = formatted_data
                self.logger.info("""Transformed carbon data""")
            if "piechart" in file:
                formatted_data = self.piechart_transform(df)
                data['piechart'] = formatted_data
                self.logger.info("""Transformed piechart data""")

        print(data['piechart'])

        data = self.difference_of_dates(data)
        self.delete_read_files(files)
        return data

    def difference_of_dates(self, data_conflict: dict):
        """
        Works out the difference of dates between the time column of generation
        and the time column of demand, adds the missing dates to demand and
        returns it
        Mainly to fix foreign key errors
        """
        diff = list(set(self.time_g) - set(self.time_d))
        for time in diff:
            for values in data_conflict['generation']:
                if values[0] == time:
                    data_conflict['demand'].append((values[0], 0))
                    break
        return data_conflict

    def generation_transform(self, df: pd.DataFrame) -> tuple:
        """
        Filters and transforms the generation dataframe passed into it and returns
        a list of tuples
        """
        df['publish_date'] = df['publishTime'].apply(lambda x: x.split('T')[0])
        df['gain_loss'] = df['generation'].apply(
            lambda x: '+' if x > 0 else '-')

        self.period_g = df['settlementPeriod'].unique()
        self.time_g = df['publishTime'].unique()
        df = df.get(['publishTime', 'publish_date', 'fuelType', 'gain_loss',
                     'generation', 'settlementPeriod'])
        return list(df.itertuples(index=False, name=None))

    def demand_transform(self, df: pd.DataFrame) -> tuple:
        """
        Filters and transforms the demand dataframe passed into it and returns
        a list of tuples
        """
        df = df.get(['startTime', 'demand'])
        self.time_d = df['startTime'].unique()
        return list(df.itertuples(index=False, name=None))

    def carbon_transform(self, df: pd.DataFrame) -> tuple:
        """
        Filters and transforms the carbon dataframe passed into it and returns
        a list of tuples
        """
        df = df.get(['from', 'forecast', 'carbon level'])
        bins = [0, 34, 109, 189, 270, 1000]
        labels = ["very low", "low", "moderate", "high", "very high"]
        df['carbon level'] = pd.cut(
            df['forecast'], bins=bins, labels=labels, right=True)
        return list(df.itertuples(index=False, name=None))

    def piechart_transform(self, df: pd.DataFrame) -> tuple:
        """
        Filters and transforms the carbon dataframe passed into it and returns
        a list of tuples
        """
        print(df)
        df = df[['fuel_type', 'from', 'percentage']]
        return list(df.itertuples(index=False, name=None))

    def delete_read_files(self, files):
        """
        Removes downloaded files 
        """
        for file in files:
            os.remove(file)


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


class Load:
    """
    Loads data into a database
    """

    def __init__(self) -> None:
        """
        Initialize class variables.
        """
        self.logger = logger

    def load_values(self, conn, data):
        """
        Loads the data into an RDS database
        """
        curr = conn.cursor(cursor_factory=RealDictCursor)
        if data.get('demand'):
            sql_query = """INSERT INTO Demand (publish_time, Demand_amt)
                        VALUES %s
                        ON CONFLICT (publish_time) DO UPDATE
                        SET Demand_amt=EXCLUDED.Demand_amt"""
            execute_values(curr, sql_query, data['demand'])
            self.logger.info(
                """Loaded demand data into the database""")
        if data.get('demand'):
            sql_query = """INSERT INTO Carbon (publish_time, forecast, carbon_level)
                        VALUES %s
                        ON CONFLICT DO NOTHING"""
            execute_values(curr, sql_query, data['carbon'])
            self.logger.info(
                """Loaded carbon data into the database""")
        if data.get('generation'):
            sql_query = """INSERT INTO Generation (publish_time, publish_date,
                         fuel_type, gain_loss, generated, settlement_period)
                        VALUES %s
                        ON CONFLICT DO NOTHING"""
            execute_values(curr, sql_query, data['generation'])
            self.logger.info(
                """Loaded generation data into the database""")
        if data.get('piechart'):
            sql_query = """INSERT INTO generation_percent (fuel_type, date_time,
                         slice_percentage)
                        VALUES %s
                        ON CONFLICT DO NOTHING"""
            execute_values(curr, sql_query, data['piechart'])
            self.logger.info(
                """Loaded piechart data into the database""")
        curr.close()
        conn.close()


if __name__ == "__main__":
    db_conn = DatabaseConnection()
    s3_bucket = DataProcessor(save_location="your_save_location",
                              aws_access_key=os.getenv('AWS_ACCESS_KEY'),
                              aws_secret_key=os.getenv('AWS_SECRET_KEY'),
                              region=os.getenv('AWS_REGION'),
                              s3_file_name="your_s3_file_name",
                              bucket=ct.S3_BUCKET,
                              logger=logger)
    s3_bucket.get_s3_client()
    s3_bucket.get_files_from_bucket()
    tf = Transform()
    values = tf.get_data()
    load = Load()
    load.load_values(db_conn.get_connection(), values)
