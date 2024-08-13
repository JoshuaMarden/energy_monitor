from typing import Any


class Constants:
    """
    Holds constants for use by other modules.
    """

    # Directories
    DATA = "tmp/data/"
    LOGS = "tmp/logs/"

    # Names for data
    RAW_PRODUCTION_DATA_NAME = "raw_production_data.feather"
    RAW_DEMAND_DATA_NAME = "raw_demand_data.feather"
    RAW_COST_DATA_NAME = "raw_cost_data.feather"
    RAW_CARBON_DATA_NAME = "raw_carbon_data.feather"

    # Paths to local storage for data
    RAW_PRODUCTION_DATA_PATH = DATA + "/" + RAW_PRODUCTION_DATA_NAME
    RAW_DEMAND_DATA_PATH = DATA + "/" + RAW_DEMAND_DATA_NAME
    RAW_COST_DATA_PATH = DATA + "/" + RAW_COST_DATA_NAME
    RAW_CARBON_DATA_PATH = DATA + "/" + RAW_CARBON_DATA_NAME

    # Endpoints
    PRODUCTION_ENDPOINT = "https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELINST"
    DEMAND_ENDPOINT = "https://bmrs.elexon.co.uk/rolling-system-demand"
    COST_ENDPOINT = "https://bmrs.elexon.co.uk/system-prices"

    # S3 Data
    S3_BUCKET = "c12-energy-tracker"

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError(f"Can't Reassign Constant {name}")