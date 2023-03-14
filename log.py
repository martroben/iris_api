
from dataclasses import dataclass, field
import logging
import os


def setup_logger(name: str, level: str, indicator: str) -> logging.Logger:
    """
    Create a logger with custom format, that can be parsed by external log receiver
    :param name: Name for the log messages emitted by the application
    :param level: Level of log messages that the logger sends (DEBUG/INFO/WARNING/ERROR)
    :param indicator: Unique indicator to let external log receiver distinguish which stdout entries came from the app
    :return: a logging.Logger object with assigned handler and formatter
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    handler = logging.StreamHandler()              # Direct logs to stdout
    formatter = logging.Formatter(
        fmt=f"{indicator}{{asctime}} | {{name}} | {{funcName}} | {{levelname}}: {{message}}",
        datefmt="%m/%d/%Y %H:%M:%S",
        style="{")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


@dataclass
class LogString:
    """
    Parent class for log entries. Stores short and full versions of the log message and the logger to use.
    Subclasses have log messages for specific scenarios, that can be easily translated.
    """
    exception: Exception                                    # Exception to be included in log message
    logger: logging.Logger = field(init=False)              # Logger to use for logging the message
    exception_type: str = field(init=False)                 # Exception type name
    short: str = field(init=False)                          # Short log message for http responses
    full: str = field(init=False)                           # Long log message for saved logs

    def __str__(self):
        return self.full

    def set_logger(self, logger: logging.Logger = None) -> None:
        """
        Specify Logger that is to be used for the log string.
        Defaults to the logger set in LOGGER_NAME env variable.
        """
        if logger is None:
            logger = logging.getLogger(os.getenv("LOGGER_NAME", "root"))
        self.logger = logger

    def record(self, level: str) -> None:
        """"Execute" the log message - i.e. send it to the specified handler"""
        self.logger.log(level=logging.getLevelName(level), msg=self.full)


###################
# app log strings #
###################

@dataclass
class SqlConnectError(LogString):
    """Error in creating or connecting to SQL"""
    database_path: str

    def __post_init__(self):
        self.set_logger()
        self.exception_type = self.exception.__class__.__name__
        self.short = f"While opening database connection, {self.exception_type} occurred."
        self.full = f"{self.short} Database path: {self.database_path}. Error: {self.exception}."


@dataclass
class SqlDeleteError(LogString):
    """Error in deleting data from SQL"""
    def __post_init__(self):
        self.set_logger()
        self.exception_type = self.exception.__class__.__name__
        self.short = f"While deleting data from database, {self.exception_type} occurred."
        self.full = f"{self.short} {self.exception}"


@dataclass
class SqlGetError(LogString):
    """Error in getting data from SQL"""
    def __post_init__(self):
        self.set_logger()
        self.exception_type = self.exception.__class__.__name__
        self.short = f"While getting data from database, {self.exception_type} occurred."
        self.full = f"{self.short} {self.exception}"


@dataclass
class UrlError(LogString):
    """Bad url"""
    url: str

    def __post_init__(self):
        self.set_logger()
        self.exception_type = self.exception.__class__.__name__
        self.short = f"While connecting to Iris data url, {self.exception_type} occurred."
        self.full = f"{self.short} Url: {self.url}. Error: {self.exception}."


@dataclass
class DownloadError(LogString):
    """Bad response for request (status >= 400)"""
    def __post_init__(self):
        self.set_logger()
        self.exception_type = self.exception.__class__.__name__
        self.short = f"While downloading Iris data, {self.exception_type} occurred."
        self.full = f"{self.short} Error: {self.exception}."


@dataclass(kw_only=True)
class ForbiddenAttributes(LogString):
    """Warning for trying to assign attributes that are not allowed to object"""
    class_name: str
    received_attributes: list
    allowed_attributes: dict

    def __post_init__(self):
        self.set_logger()
        self.short = f"Can't assign forbidden attributes to class {self.class_name}."
        self.full = f"{self.short} Problematic attributes: {', '.join(self.received_attributes)}. " \
                    f"Only the following attributes are allowed: " \
                    f"{', '.join(list(self.allowed_attributes.keys()))}."
