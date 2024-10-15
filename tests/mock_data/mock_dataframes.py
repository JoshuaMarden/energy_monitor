"""
Mock dataframes for testing
"""
from datetime import datetime
import pandas as pd


def get_generation_mock_dataframe():
    data = {
        'publishTime': ['2024-08-19T11:40:00Z', '2024-08-18T23:00:00Z', '2024-08-19T11:40:00Z'],
        'fuelType': ['sherbet', 'liquorice', 'bon-bon'],
        'settlementPeriod': [2, 3, 4],
        'generation': [200, 0, -100],
        'do not include': [1, 2, 3]
    }
    return pd.DataFrame(data)


def get_demand_mock_dataframe():
    data = {
        'startTime': ['2024-08-19T11:40:00Z', '2024-08-19T11:40:00Z', '2024-08-19T11:40:00Z'],
        'demand': [100, 200, 300]
    }
    return pd.DataFrame(data)


def get_cost_mock_dataframe():
    data = {
        'settlementDate': ['2024-08-19', '2024-08-19', '2024-08-19'],
        'settlementPeriod': [1, 2, 4],
        'systemSellPrice': [100, 200, 300],
        'systemBuyPrice': [100, 200, 300]
    }
    return pd.DataFrame(data)


def get_carbon_mock_dataframe():
    data = {
        'from': ['2024-08-18T23:00Z', '2024-08-18T23:30Z', '2024-08-19T00:00Z'],
        'to': ['2024-08-18T23:00Z', '2024-08-18T23:30Z', '2024-08-19T00:00Z'],
        'forecast': [20, 70, 200],
        'carbon level': ['low', 'low', 'low']
    }
    return pd.DataFrame(data)


def get_simple_mock_dataframe() -> pd.DataFrame:
    data = {
        'column1': [1, 2, 3],
        'column2': ['sherbet', 'liquorice', 'bon-bon']
    }
    return pd.DataFrame(data)


def get_dated_mock_dataframe() -> pd.DataFrame:
    data = {
        'publishTime': [
            datetime(1970, 1, 1, 0, 0),
            datetime(1970, 1, 1, 12, 0),
            datetime(2000, 1, 1, 0, 0)
        ],
        'settlementDate': [
            datetime(1970, 12, 25, 0, 0),
            datetime(1970, 12, 25, 12, 0),
            datetime(1999, 12, 25, 0, 0)
        ],
        'settlementPeriod': [1, 2, 48],
        'startTime': [
            datetime(1969, 12, 31, 23, 0),
            datetime(1970, 1, 1, 11, 0),
            datetime(1999, 12, 31, 23, 0)
        ]
    }
    return pd.DataFrame(data)
