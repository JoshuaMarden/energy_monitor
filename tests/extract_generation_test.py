"""
Test script for extract_production.py
"""
import pandas as pd
from pipeline.extract_generation import CustomDataProcessor
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta
from requests.exceptions import RequestException
from tests.mock_data.mock_dataframes import get_dated_mock_dataframe


def test_construct_default_params_manual(api_client):
    """
    Mock the current time to a fixed point and
    use a manually set past time.
    """
    fixed_now = datetime(2000, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    fixed_past = datetime(1999, 12, 31, 12, 0, 0, tzinfo=timezone.utc)  # 12 hours before fixed_now
    
    with patch('pipeline.extract_generation.datetime') as mock_datetime:
        mock_datetime.now.return_value = fixed_now
        
        expected_params = {
            'publishDateTimeFrom': fixed_past.isoformat(),
            'publishDateTimeTo': fixed_now.isoformat(),  # This should match fixed_now exactly
            'format': 'json'
        }
        
        params = api_client.construct_default_params()
        
        assert params == expected_params

def test_construct_default_params_dynamic(api_client):
    """
    Mock the current time to a fixed point and check it can generate
    a time in the past.
    """
    fixed_now = datetime(2000, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    
    with patch('pipeline.extract_generation.datetime') as mock_datetime:
        mock_datetime.now.return_value = fixed_now
        
        expected_params = {
            'publishDateTimeFrom': (fixed_now - timedelta(hours=12)).isoformat(),
            'publishDateTimeTo': (fixed_now).isoformat(),
            'format': 'json'
        }
        
        params = api_client.construct_default_params()
        
        assert params == expected_params

        
@patch('pipeline.extract_generation.APIClient.construct_default_params')
@patch('pipeline.extract_generation.requests.get')
def test_fetch_data_success(mock_get, mock_construct_default_params, api_client):
    """
    Test the fetch_data method with a successful API response, using mocked construct_default_params.
    """
    # Mock the parameters that construct_default_params should return
    mock_params = {
        'publishDateTimeFrom': '1940-01-01T21:17:16.714027+00:00',
        'publishDateTimeTo': '2000-01-01T09:17:16.714028+00:00',
        'format': 'json'
    }
    mock_construct_default_params.return_value = mock_params

    mock_response = MagicMock()
    mock_response.json.return_value = {'data': 'some_data'}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = api_client.fetch_data()

    mock_get.assert_called_once_with(api_client.base_url, params=mock_params)

    # Assert the result returned by fetch_data is as expected
    assert result == {'data': 'some_data'}

@patch('pipeline.extract_generation.requests.get')
def test_fetch_data_failure(mock_get, api_client):
    """
    Test the fetch_data method when the API request fails.
    """
    mock_get.side_effect = RequestException("API request failed")

    result = api_client.fetch_data()

    assert result is None

    api_client.logger.error.assert_called_once_with("An error occurred: API request failed")

def test_process_data_with_valid_data():
    """
    Test the process_data method with valid data from a dated mock dataframe.
    """
    mock_df = get_dated_mock_dataframe()

    sample_data = {"data": mock_df.to_dict(orient='records')}

    expected_time_period = {
        "publishTimeStart": pd.Timestamp("1970-01-01T00:00:00"),
        "publishTimeEnd": pd.Timestamp("2000-01-01T00:00:00")
    }

    processor = CustomDataProcessor()

    df, time_period = processor.process_data(sample_data)

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