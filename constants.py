from typing import Any


class Constants:
    # Constants go here
    DATA = "tmp/data/"
    LOGS = "tmp/logs/"

    PRODUCTION_ENDPOINT = "https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELINST"

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError(f"Can't Reassign Constant {name}")