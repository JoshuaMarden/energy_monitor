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

import config as cg

load_dotenv()

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
            if "cost" in file:
                formatted_data = self.cost_transform(df)
                if formatted_data:
                    data['cost'] = formatted_data
                self.logger.info("""Transformed cost data""")
            if "carbon" in file:
                formatted_data = self.carbon_transform(df)
                data['carbon'] = formatted_data
                self.logger.info("""Transformed carbon data""")
        diff = list(set(self.period_g) - set(self.period_c))
        for period in diff:
            for values in data['generation']:

                if values[5] == period:
                    if period == 2:
                        yesterday = datetime.date.today() - datetime.timedelta(days=1)
                        data['cost'].append((yesterday, 2, 0, 0))
                    data['cost'].append((values[1], values[5], 0, 0))
                    break

        diff = list(set(self.time_g) - set(self.time_d))
        for time in diff:
            for values in data['generation']:
                if values[0] == time:
                    data['demand'].append((values[0], 0))
                    break

        self.delete_read_files(files)
        return data

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

    def cost_transform(self, df: pd.DataFrame) -> tuple:
        """
        Filters and transforms the cost dataframe passed into it and returns
        a list of tuples
        """
        df = df.get(['settlementDate', 'settlementPeriod',
                     'systemSellPrice', 'systemBuyPrice'])
        self.period_c = df['settlementPeriod'].unique()
        if 2 in self.period_c:
            yesterday = datetime.date.today() - datetime.timedelta(days=1)
            df.loc[len(df.index)] = [str(yesterday), 2, 0, 0]
        if 1 in self.period_c:
            yesterday = datetime.date.today() - datetime.timedelta(days=1)
            df.loc[len(df.index)] = [str(yesterday), 1, 0, 0]
        print(df)
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
        if data.get('cost'):
            sql_query = """INSERT INTO Cost (publish_date, settlement_period, sell_price, buy_price)
                        VALUES %s
                        ON CONFLICT (publish_date, settlement_period) DO UPDATE
                        SET sell_price=EXCLUDED.sell_price,
                        buy_price=EXCLUDED.buy_price"""
            execute_values(curr, sql_query, data['cost'])
            self.logger.info(
                """Loaded cost data into the database""")
        if data.get('demand'):
            sql_query = """INSERT INTO Carbon (publish_time, forecast, carbon_level)
                        VALUES %s
                        ON CONFLICT DO NOTHING"""
            execute_values(curr, sql_query, data['carbon'])
            self.logger.info(
                """Loaded carbon data into the database""")
        if data.get('demand'):
            sql_query = """INSERT INTO Generation (publish_time, publish_date,
                         fuel_type, gain_loss, generated, settlement_period)
                        VALUES %s
                        ON CONFLICT DO NOTHING"""
            execute_values(curr, sql_query, data['generation'])
            self.logger.info(
                """Loaded generation data into the database""")


if __name__ == "__main__":
    db_conn = DatabaseConnection()
    s3_bucket = S3bucket()
    s3_bucket.get_files_from_bucket()
    tf = Transform()
    values = tf.get_data()
    load = Load()
    load.load_values(db_conn.get_connection(), values)
