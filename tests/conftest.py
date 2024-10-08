"""
Fixtures for pytesting
"""
import logging
from unittest.mock import MagicMock
import pytest

from pipeline.common import DataProcessor
from pipeline.extract_generation import APIClient as APIClientGeneration
from pipeline.extract_demand import APIClient as APIClientDemand
from pipeline.extract_carbon import APIClient as APIClientCarbon

from mock_data.mock_dataframes import get_simple_mock_dataframe, get_carbon_mock_dataframe, get_cost_mock_dataframe, get_demand_mock_dataframe, get_generation_mock_dataframe


@pytest.fixture
def mock_logger():
    return MagicMock(spec=logging.Logger)


@pytest.fixture
def simple_mock_dataframe():
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


@pytest.fixture
def api_client_generation(mock_logger):
    """
    Fixture for APIClient from extract_generation
    """
    return APIClientGeneration(base_url="mock_url", logger=mock_logger)


@pytest.fixture
def api_client_demand(mock_logger):
    """
    Fixture for APIClient from extract_demand
    """
    return APIClientDemand(base_url="mock_url", logger=mock_logger)


@pytest.fixture
def api_client_price(mock_logger):
    """
    Fixture for APIClient from extract_demand
    """
    return APIClientPrice(base_url="mock_url", logger=mock_logger)


@pytest.fixture
def api_client_carbon(mock_logger):
    """
    Fixture for APIClient from extract_demand
    """
    return APIClientCarbon(base_url="mock_url", logger=mock_logger)


@pytest.fixture
def mock_gen_df():
    return get_generation_mock_dataframe()


@pytest.fixture
def mock_demand_df():
    return get_demand_mock_dataframe()


@pytest.fixture
def mock_cost_df():
    return get_cost_mock_dataframe()


@pytest.fixture
def mock_carbon_df():
    return get_carbon_mock_dataframe()
