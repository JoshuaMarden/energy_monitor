from typing import Any


class Constants:
    # Constants go here
    DATA = "/tmp/data/"
    LOGS = "/tmp/logs/"

    CARBON_ENDPOINT = "https://api.carbonintensity.org.uk/intensity/date"

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError(f"Can't Reassign Constant {name}")
