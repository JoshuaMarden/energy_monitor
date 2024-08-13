import os
import sys
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Dict, Any

import requests
import pandas as pd
import pyarrow


# import config as cg
# from constants import Constants as ct

# # Logging
# SCRIPT_NAME = (os.path.basename(__file__)).split(".")[0]
# LOGGING_LEVEL = logging.DEBUG
# logger = cg.setup_logging(SCRIPT_NAME, LOGGING_LEVEL)


class S3Interaction:
    ...
