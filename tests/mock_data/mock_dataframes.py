"""
Mock dataframes for testing
"""
from datetime import datetime
import pandas as pd

def get_simple_mock_dataframe() -> pd.DataFrame:
    data = {
        'column1': [1, 2, 3],
        'column2': ['sherbet', 'liquorice', 'bon-bon']
    }
    return pd.DataFrame(data)


def get_dated_mock_dataframe() -> pd.DataFrame:
    data = {
        'publishTime': [datetime(1970, 1, 1), datetime(1970, 1, 1), datetime(2000, 1, 1)],
        'settlementDate': [datetime(1970, 12, 25), datetime(1970, 12, 25), datetime(1999, 12, 25)],
        'settlementPeriod': [1, 2, 48]
    }
    return pd.DataFrame(data)