
# standard
from datetime import datetime
import os
import re
import socketserver


def make_dirs(path):
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))


class LogSaver:
    log_indicator = os.environ.get("LOG_INDICATOR", "rabbitofcaerbannog")
    log_name_pattern = re.compile(r"\d{2}/\d{2}/\d{4}\s\d{2}:\d{2}:\d{2}\s\|\s(.+?)\s\|")
    logs_path = os.getenv("LOG_FOLDER_PATH", os.path.join("/", "log"))

    def __init__(self):
        if not os.path.exists(self.logs_path):
            os.makedirs(self.logs_path)

    def save(self, log_data):
        if self.log_indicator in log_data:
            log_parsed = log_data.split(self.log_indicator)[1].strip()
            log_name = self.log_name_pattern.search(log_parsed).group(1)
            file_path = os.path.join(self.logs_path, log_name, f"{datetime.today().strftime('%Y_%m_%d')}")
            make_dirs(file_path)
            with open(file_path, "a") as log_file:
                log_file.write(f"{log_parsed}\n")


class UDPHandler(socketserver.BaseRequestHandler):
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
