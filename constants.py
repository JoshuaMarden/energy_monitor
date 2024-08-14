from typing import Any


class Constants:
    # Constants go here
    DATA = "/tmp/data/"
    LOGS = "/tmp/logs/"

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError(f"Can't Reassign Constant {name}")
