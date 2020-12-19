import logging

from utils import path_util


def get_logger(
    name: str,
    nameLength=25,
    with_log_file=False,
    log_dir_path=f"{path_util.get_project_root()}/logs",
):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        fmt="{asctime} | "
        + "{levelname: <7} |  "
        + "{name: <"
        + str(nameLength)
        + "}   : "
        + "{message}",
        style="{",
    )
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if with_log_file:
        file_handler = logging.FileHandler(f"{log_dir_path}/{name}.log")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


if __name__ == "__main__":
    logger = get_logger("logger_factory", nameLength=20, with_log_file=True)
    logger.debug("A debug message")
