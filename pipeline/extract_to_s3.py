import os
import logging
import timeit
from extract_generation import main as extract_generation
from extract_demand import main as extract_demand
from extract_price import main as extract_price

from constants import Constants as ct
import config as cg

save_directory = ct.DATA
if not os.path.exists(save_directory):
    os.makedirs(save_directory)

SCRIPT_NAME = (os.path.basename(__file__)).split(".")[0]
LOGGING_LEVEL = logging.DEBUG

logger = cg.setup_logging(SCRIPT_NAME, LOGGING_LEVEL)


def pipeline():
    logger.info("|===============")
    logger.info("==> Running Extract Scripts..")
    logger.info("=======================================")
    logger.info(" ")

    logger.info("===========")
    logger.info("==> Executing extract_production..")
    logger.info("===========")
    extract_time = timeit.timeit(extract_generation, number=1)
    logger.info("Extract script completed in %s seconds", extract_time)

    logger.info("===========")
    logger.info("==> Executing extract_demand..")
    logger.info("===========")
    extract_time = timeit.timeit(extract_demand, number=1)
    logger.info("Extract script completed in %s seconds", extract_time)

    logger.info("===========")
    logger.info("==> Executing extract_price..")
    logger.info("===========")
    extract_time = timeit.timeit(extract_price, number=1)
    logger.info("Extract script completed in %s seconds", extract_time)

    logger.info("===============")
    logger.info("==> Extract Scripts Complete!")
    logger.info("=======================================|")


def main():
    pipeline_time = timeit.timeit(pipeline, number=1)
    logger.info("Pipeline completed in %s seconds", pipeline_time)


if __name__ == "__main__":
    main()
