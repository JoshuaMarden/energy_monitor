from typing import Any


class Constants:
    # Constants go here
    DATA = "tmp/data/"
    LOGS = "tmp/logs/"

    RAW_PRODUCTION_DATA = DATA + "/raw_production_data.feather"
    RAW_DEMAND_DATA = DATA + "/raw_demand_data.feather"
    RAW_COST_DATA = DATA + "/raw_cost_data.feather"
    RAW_CARBON_DATA = DATA + "/raw_carbon_data.feather"

    PRODUCTION_ENDPOINT = "https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELINST"
    DEMAND_ENDPOINT = "https://bmrs.elexon.co.uk/rolling-system-demand"
    COST_ENDPOINT = "https://bmrs.elexon.co.uk/system-prices"

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError(f"Can't Reassign Constant {name}")