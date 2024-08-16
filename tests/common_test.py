"""
Test script for common.py
"""

from unittest.mock import MagicMock, patch

def test_save_data_locally(data_processor, simple_mock_dataframe, mock_logger):
    with patch("pandas.DataFrame.to_feather") as mock_to_feather:
        data_processor.save_data_locally(simple_mock_dataframe)
        
        # Check if to_feather was called with the correct path
        mock_to_feather.assert_called_once_with("mock_path")
        
        # Check if logger.info was called correctly
        mock_logger.info.assert_called_with("Raw data saved to `mock_path`")

def test_get_s3_client(data_processor, mock_logger):
    with patch("boto3.client") as mock_boto_client:
        mock_boto_instance = MagicMock()
        mock_boto_client.return_value = mock_boto_instance
        
        s3_client = data_processor.get_s3_client()
        
        # Verify that boto3.client was called with the correct parameters
        mock_boto_client.assert_called_once_with(
            's3',
            aws_access_key_id="mock_key",
            aws_secret_access_key="mock_secret",
            region_name="mock_region"
        )
        
        # Check if the correct instance was returned
        assert s3_client == mock_boto_instance
        
        # Check logger calls
        mock_logger.info.assert_any_call("Fetching boto3 client...")
        mock_logger.info.assert_any_call("Retrieved client successfully.")

def test_save_data_to_s3(data_processor, mock_logger):
    with patch("builtins.open", new_callable=MagicMock) as mock_open, \
         patch.object(data_processor, 's3_client', new_callable=MagicMock) as mock_s3_client:
        
        mock_file_data = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file_data
        
        data_processor.save_data_to_s3()
        
        # Verify that the file was opened with the correct path and mode
        mock_open.assert_called_once_with("mock_path", 'rb')
        
        # Verify that s3_client.put_object was called with the correct parameters
        mock_s3_client.put_object.assert_called_once_with(
            Bucket="mock_bucket",
            Key="mock_file",
            Body=mock_file_data
        )
        
        # Check logger call
        mock_logger.info.assert_called_with("Data successfully saved to S3 as `mock_file`.")