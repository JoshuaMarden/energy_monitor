from typing import Any

class Constants:
    """
    Holds constants for use by other modules.
    """

    # Directories
    DATA = "tmp/data/"
    LOGS = "tmp/logs/"

    # Names for data
    RAW_GENERATION_DATA_NAME = "raw_production_data.feather"
    RAW_DEMAND_DATA_NAME = "raw_demand_data.feather"
    RAW_PRICE_DATA_NAME = "raw_cost_data.feather"
    RAW_CARBON_DATA_NAME = "raw_carbon_data.feather"

    # Paths to local storage for data
    RAW_GENERATION_DATA_PATH = DATA + RAW_GENERATION_DATA_NAME
    RAW_DEMAND_DATA_PATH = DATA + RAW_DEMAND_DATA_NAME
    RAW_PRICE_DATA_PATH = DATA + RAW_PRICE_DATA_NAME
    RAW_CARBON_DATA_PATH = DATA + RAW_CARBON_DATA_NAME

    # Endpoints
    GENERATION_ENDPOINT = "https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELINST"
    DEMAND_ENDPOINT = "https://data.elexon.co.uk/bmrs/api/v1/generation/outturn"
    PRICE_ENDPOINT = "https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/system-prices/"
    CARBON_ENDPOINT = "https://api.carbonintensity.org.uk/intensity/date"

    # S3 Data
    S3_BUCKET = "c12-energy-tracker"

    CARBON_ENDPOINT = "https://api.carbonintensity.org.uk/intensity/date"

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError(f"Can't Reassign Constant {name}")
