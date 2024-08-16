"""
Test script for extract_production.py
"""
import pandas as pd
from pipeline.extract_carbon import CustomDataProcessor
from unittest.mock import patch, MagicMock
from requests.exceptions import RequestException
from tests.mock_data.mock_dataframes import get_dated_mock_dataframe


@patch('pipeline.extract_carbon.requests.get')
def test_fetch_data_success(mock_get, api_client_carbon):
    """
    Test the fetch_data method with a successful API response.
    """

    mock_response = MagicMock()
    mock_response.json.return_value = {'data': 'Battle of Orléans'}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = api_client_carbon.fetch_data()

    mock_get.assert_called_once_with(api_client_carbon.base_url, headers={'Accept': 'application/json'})
    assert result == {'data': 'Battle of Orléans'}

@patch('pipeline.extract_generation.requests.get')
def test_fetch_data_failure(mock_get, api_client_carbon):
    """
    Test the fetch_data method when the API request fails.
    """
    mock_get.side_effect = RequestException("API request failed")

    result = api_client_carbon.fetch_data()

    assert result is None
    api_client_carbon.logger.error.assert_called_once_with("An error occurred: API request failed")

from tests.mock_data.mock_dataframes import get_dated_mock_dataframe

def test_process_data_with_valid_data():
    """
    Test the process_data method with valid data from a dated mock dataframe.
    """
    mock_response = {
        "data": [
            {"from": "1066-09-14T00:00Z", "to": "1066-09-14T00:30Z", "intensity": {"forecast": 0, "index": "very low"}},
            {"from": "1066-09-14T00:30Z", "to": "1066-09-14T01:00Z", "intensity": {"forecast": 1000000, "index": "very high"}}
        ]
    }

    expected_df = pd.DataFrame({
        'from': ["1066-09-14T00:00Z", "1066-09-14T00:30Z"],
        'to': ["1066-09-14T00:30Z", "1066-09-14T01:00Z"],
        'forecast': [0, 1000000],
        'carbon level': ["very low", "very high"]
    })

    processor = CustomDataProcessor()

    df = processor.process_data(mock_response)

    pd.testing.assert_frame_equal(df, expected_df)

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



