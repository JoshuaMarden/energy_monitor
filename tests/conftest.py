"""
Fixtures for pytesting
"""

import pytest
from unittest.mock import MagicMock
import logging
from pipeline.common import DataProcessor
from tests.mock_data.mock_dataframes import get_simple_mock_dataframe


@pytest.fixture
def mock_logger():
    return MagicMock(spec=logging.Logger)

@pytest.fixture
def sample_dataframe():
    return get_simple_mock_dataframe()

@pytest.fixture
def data_processor(mock_logger):
    return DataProcessor(
        save_location="mock_path",
        aws_access_key="mock_key",
        aws_secret_key="mock_secret",
        region="mock_region",
        s3_file_name="mock_file",
        bucket="mock_bucket",
        logger=mock_logger
    )
