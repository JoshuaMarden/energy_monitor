"""
Test script for extract_demand.py
"""
import pandas as pd
import numpy as np
from pipeline.extract_price import CustomDataProcessor, APIClient
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta
from requests.exceptions import RequestException
from tests.mock_data.mock_dataframes import get_dated_mock_dataframe


@patch('pandas.read_feather')
def test_get_settlement_periods(mock_read_feather, api_client_price):
    """
    Checks get_settlement_periods reads a .feather file and then
    extracts the dates and settlement periods from it.
    """
    mock_df = get_dated_mock_dataframe()
    mock_read_feather.return_value = mock_df  

    custom_reference_data_path = "custom/mock/reference_data.feather"

    result = api_client_price.get_settlement_periods(path_to_reference_data=custom_reference_data_path)

    expected_result = {
        '1970-12-25': [np.int64(2)],
        '1999-12-25': [np.int64(48)]}
    
    # Convert the result's keys to strings for a comparison
    result = {k.strftime('%Y-%m-%d'): v for k, v in result.items()}

    assert result == expected_result
    mock_read_feather.assert_called_once_with(custom_reference_data_path)