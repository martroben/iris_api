
from dataclasses import dataclass, field
import logging
import os


def get_logger(name: str, level: str, indicator: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    handler = logging.StreamHandler()                       # Direct logs to stdout
    formatter = logging.Formatter(
        fmt=f"{indicator}{{asctime}} | {{name}} | {{funcName}} | {{levelname}}: {{message}}",
        datefmt="%m/%d/%Y %H:%M:%S",
        style="{")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


@dataclass
class LogString:
    exception: Exception
    logger: logging.Logger = field(init=False)
    exception_type: str = field(init=False)
    short: str = field(init=False)
    full: str = field(init=False)

    def __post_init__(self):
        self.logger = logging.getLogger(os.getenv("LOG_NAME", "root"))

    def __str__(self):
        return self.full

    def record(self, level: str):
        self.logger.log(level=logging.getLevelName(level), msg=self.full)


###################
# app log strings #
###################

@dataclass
class SqlConnectError(LogString):
    database_path: str

    def __post_init__(self):
        self.exception_type = self.exception.__class__.__name__
        self.short = f"While opening database connection, {self.exception_type} occurred."
        self.full = f"{self.short} Database path: {self.database_path}. Error: {self.exception}."


@dataclass
class SqlDeleteError(LogString):
    def __post_init__(self):
        self.exception_type = self.exception.__class__.__name__
        self.short = f"While deleting data from database, {self.exception_type} occurred."
        self.full = f"{self.short} {self.exception}"


@dataclass
class UrlError(LogString):
    url: str

    def __post_init__(self):
        self.exception_type = self.exception.__class__.__name__
        self.short = f"While downloading Iris data, {self.exception_type} occurred."
        self.full = f"{self.short} Url: {self.url}. Error: {self.exception}."


@dataclass(kw_only=True)
class ForbiddenAttributes(LogString):
    class_name: str
    received_attributes: list
    allowed_attributes: dict

    def __post_init__(self):
        self.short = f"Can't assign forbidden attributes to class {self.class_name}."
        self.full = f"{self.short} Problematic attributes: {', '.join(self.received_attributes)}. " \
                    f"Only the following attributes are allowed: " \
                    f"{', '.join(list(self.allowed_attributes.keys()))}."

