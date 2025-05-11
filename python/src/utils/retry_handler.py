from random import random
from time import sleep

from utils import logger_factory

LOGGER = logger_factory.get_logger(__name__)


def run_with_retries(callback, exception_message: str, max_tries=10, **kwargs):
    """
    Runs a function a number of times equal to `max_tries`.

    ### Parameters
    1. `callback`: The function to run.
    3. `exception_message`: The exception message to return if non of the executions
        return successfully
    4. `max_retries`: The number of times to retry. Default: 10.
    5. `kwargs`: An arbitrary number of keyword arguments that will be passed to the
        callback.
    """

    for i in range(max_tries):
        timeout = random() * (i + 1)
        sleep(timeout)
        # print(timeout)
        try:
            LOGGER.debug(f"Retry ({i+1}/{max_tries})")
            computed_value = callback(**kwargs)
            return computed_value

        except Exception as exc:
            LOGGER.error(exc)

    raise Exception(f"{exception_message} after {max_tries} tries.")
