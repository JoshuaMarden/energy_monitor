import logging
import cProfile
import pstats
from datetime import datetime, timedelta
import os
from io import StringIO
from constants import Constants as ct

LOGS_DIR = ct.LOGS

def obscure(secret: str) -> str:
    """
    Replaces all but the first and last 3 chars in a string
    with asterisks in order to keep it partially private.
    If the length is less than 6, only keeps the first and last chars and obscures the rest.
    If the length is 3 or less, replaces all chars with asterisks.
    """
    length = len(secret)
    
    if length <= 3:
        return '*' * length
    elif length <= 6:
        return secret[0] + '*' * (length - 2) + secret[-1]
    else:
        return secret[:3] + '*' * (length - 6) + secret[-3:]

def setup_logging(log_name: str, logging_level=logging.DEBUG,
                  logs_dir=LOGS_DIR):
    """Setup logging with two logs: one for normal logs, and one for warnings and errors.
    Prints everything to the terminal as well as saving it to files."""

    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
        print(f"Log dir created: `{logs_dir}`")
        if not os.path.exists(logs_dir):
            raise Exception(f"Failed to create logs directory: {logs_dir}")

    logger = logging.getLogger(log_name)
    logger.setLevel(logging_level)

    console_handler = logging.StreamHandler()
    file_handler = logging.FileHandler(f'{logs_dir}/{log_name}.log')
    error_file_handler = logging.FileHandler(f'{logs_dir}/{log_name}_issues.log')

    console_handler.setLevel(logging_level)
    file_handler.setLevel(logging_level)
    error_file_handler.setLevel(logging.WARNING)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    error_file_handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        logger.addHandler(error_file_handler)

    return logger

def setup_subtle_logging(log_name, logging_level=logging.DEBUG, logs_dir=LOGS_DIR):
    """setup logging with only one log file and without printing
    to the terminal - useful for perfomrance logging"""
    logger = logging.getLogger(log_name)
    logger.setLevel(logging_level)

    file_handler = logging.FileHandler(f'{logs_dir}/{log_name}.log')

    file_handler.setLevel(logging.DEBUG)
    logger.propagate = False


    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(file_handler)

    return logger

def start_monitor() -> cProfile.Profile:
    """Launches cProfile so it can log performance"""
    profiler = cProfile.Profile()
    profiler.enable()

    return profiler

def stop_monitor(script_name: str, profiler: cProfile.Profile, logger,
                 logs_dir=LOGS_DIR) -> None:
    """Terminates performance tracking, saves both a .prof files and a
    human readable text file."""
    profiler.disable()

    binary_profile = f"{logs_dir}/{script_name}_performance.prof"

    profiler.dump_stats(binary_profile)

    s = StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats()

    human_readable_stats = s.getvalue()
    text_profile = os.path.join(logs_dir, f"{script_name}_performance.txt")
    with open(text_profile, 'w') as f:
        f.write(human_readable_stats)
 
    logger.info(s.getvalue())


def get_settlement_period(current_time=None, previous_period=False):
    """
    Get the current settlement period for energy providers, where
    2300:2330 is the first period.
    """

    if current_time is None:
        current_time = datetime.now()

    start_of_day = current_time.replace(hour=23, minute=0, second=0, microsecond=0)
    if current_time.hour < 23:
        start_of_day -= timedelta(days=1)

    time_difference = current_time - start_of_day
    minutes_since_start = time_difference.total_seconds() // 60

    settlement_period = int(minutes_since_start // 30) + 1

    if previous_period:
        settlement_period -= 1

    if settlement_period < 1:
        settlement_period = 48
    elif settlement_period > 48:
        settlement_period = 48 

    return settlement_period