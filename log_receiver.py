
# standard
from datetime import datetime
import logging
import os
import re
import socketserver


# Helper function to create a logger with correct formatting for the receiver
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


def make_dirs(path):
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))


class LogSaver:
    """
    Class to handle saving logs. Saves the log to a folder designated by the log name in log string.
    Creates a new file for every new calendar day.
    """
    # Unique string that allows stdout records to be recognized as app logs and strip to syslog info
    log_indicator = os.environ.get("LOG_INDICATOR", "rabbitofcaerbannog")
    # 10/02/2023 11:22:33 | log_name_without_whitespaces | other data
    # Regex pattern to get    ^string in this position^
    log_name_pattern = re.compile(r"\d{2}/\d{2}/\d{4}\s\d{2}:\d{2}:\d{2}\s\|\s(\S+?)\s\|")
    # Log folder root
    logs_path = os.getenv("LOG_FOLDER_PATH", os.path.join("/", "log"))

    def __init__(self):
        if not os.path.exists(self.logs_path):
            os.makedirs(self.logs_path)

    def save(self, log_data):
        if self.log_indicator in log_data:
            log_string = log_data.split(self.log_indicator)[1].strip()
            log_name = self.log_name_pattern.search(log_string).group(1)
            file_path = os.path.join(self.logs_path, log_name, f"{datetime.today().strftime('%Y_%m_%d')}")
        else:                           # Use separate folder for stdout without the indicator (i.e. non-app-related)
            log_string = log_data
            file_path = os.path.join(self.logs_path, "other_stdout", f"{datetime.today().strftime('%Y_%m_%d')}")
        make_dirs(file_path)
        with open(file_path, "a") as log_file:
            log_file.write(f"{log_string}\n")


class UDPHandler(socketserver.BaseRequestHandler):
    """Socket server class to handle incoming UDP requests."""
    log_saver = LogSaver()

    def handle(self):
        # request[0] - data
        # request[1] - socket object
        log_data = self.request[0].decode("utf8")
        self.log_saver.save(log_data)


if __name__ == "__main__":
    log_receiver_ip = os.environ.get("LOG_RECEIVER_IP", "188.0.0.4")
    log_receiver_port = int(os.environ.get("LOG_RECEIVER_PORT", 7001))
    with socketserver.UDPServer((log_receiver_ip, log_receiver_port), UDPHandler) as server:
        server.serve_forever()
