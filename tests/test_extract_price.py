"""
Test script for extract_demand.py
"""
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock, call
from tests.mock_data.mock_dataframes import get_dated_mock_dataframe
from pipeline.extract_demand import CustomDataProcessor


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


def test_construct_default_params(api_client_price):
    """
    Check construction of defualt paramteres is done properly
    """
    date = "1970-01-01"
    period = 999

    result = api_client_price.construct_default_params(date=date, period=period)

    expected_result = "mock_url/1970-01-01/999?format=json"
    assert result == expected_result

@patch('pipeline.extract_price.APIClient.construct_default_params')
@patch('pipeline.extract_price.requests.get')
def test_fetch_data_success(mock_get, mock_construct_default_params, api_client_price):
    """
    Test the fetch_data method.
    """
    periods = {
        '2024-08-16': [1, 2],
        '2024-08-17': [48]
    }

    mock_construct_default_params.side_effect = [
        "mock_api/2024-08-16/1?format=json",
        "mock_api2024-08-16/2?format=json",
        "mock_api/2024-08-17/48?format=json"
    ]

    # Mock API responses
    mock_response_1 = MagicMock()
    mock_response_1.json.return_value = {'data': 'Crécy'}
    mock_response_1.raise_for_status.return_value = None

    mock_response_2 = MagicMock()
    mock_response_2.json.return_value = {'data': 'Poitiers'}
    mock_response_2.raise_for_status.return_value = None

    mock_response_3 = MagicMock()
    mock_response_3.json.return_value = {'data': 'Agincourt'}
    mock_response_3.raise_for_status.return_value = None

    mock_get.side_effect = [mock_response_1, mock_response_2, mock_response_3]

    result = api_client_price.fetch_data(periods)

    assert result == [
        {'data': 'Crécy'},
        {'data': 'Poitiers'},
        {'data': 'Agincourt'}
    ]
    assert mock_get.call_count == 3

    mock_construct_default_params.assert_has_calls([
        call("2024-08-16", 1),
        call("2024-08-16", 2),
        call("2024-08-17", 48)
    ])

def test_process_data_with_valid_data():
    """
    Test the process_data method with valid data from a dated mock dataframe.
    """
    mock_df = get_dated_mock_dataframe()
    sample_data = {"data": mock_df.to_dict(orient='records')}

    processor = CustomDataProcessor()

    df, time_period = processor.process_data(sample_data)

    expected_time_period = {
        "From": pd.Timestamp("1969-12-31T23:00:00"),
        "To": pd.Timestamp("1999-12-31T23:00:00")
    }
    pd.testing.assert_frame_equal(df, mock_df)

    assert time_period == expected_time_period

def test_process_data_with_no_data(caplog):
    """
    Test the process_data method when no data is provided.
    """

    processor = CustomDataProcessor()

    result = processor.process_data({})

    assert result is None
    assert "No data found in response." in caplog.text

def test_process_data_with_missing_data_key(caplog):
    """
    Test the process_data method when the data dictionary
    does not contain the "data" key.
    """
    processor = CustomDataProcessor()

    result = processor.process_data({"other_key": "value"})

    assert result is None
    assert "No data found in response." in caplog.text

