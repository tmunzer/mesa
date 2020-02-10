from datetime import datetime
from .slack import Slack
import logging as log
import os

def red(text): return '\033[0;31m' + text + '\033[0m'
def green(text): return '\033[0;32m' + text + '\033[0m'
def yellow(text): return '\033[0;33m' + text + '\033[0m'
def blue(text): return '\033[0;34m' + text + '\033[0m'
def magenta(text): return '\033[0;35m' + text + '\033[0m'
def cyan(text): return '\033[0;36m' + text + '\033[0m'
def white(text): return '\033[0;37m' + text + '\033[0m'


class Console:
    """
    0: emergency
    1: alert
    2: critical
    3: error
    4: warning
    5: notice
    6: info
    7: debug
    """

    def __init__(self, level=6, slack_config = None):
        self.level = level
        self.slack = Slack(slack_config)
        log.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))        

    def get_datetime(self):
            now = datetime.now()
            return now.strftime("%d/%m/%Y %H:%M:%S")

    def emergency(self, message):
        if self.level >= 0:
            dt = self.get_datetime()
            data = dt + magenta(' EMERGENCY: ') + message
            print(data)
            self.slack.add_messages("*EMERGENCY*: " + message, 0)

    def alert(self, message):
        if self.level >= 1:
            dt = self.get_datetime()
            data = dt + magenta(' ALERT: ') + message
            print(data)
            self.slack.add_messages("*ALERT*: " + message, 1)

    def critical(self, message):
        if self.level >= 2:
            dt = self.get_datetime()
            data = dt + magenta(' CRITICAL: ') + message
            print(data)
            self.slack.add_messages("*CRITICAL*: " + message, 2)

    def error(self, message):
        if self.level >= 3:
            dt = self.get_datetime()
            data = dt + red(' ERROR: ') + message
            print(data)
            self.slack.add_messages("*ERROR*: " + message, 3)

    def warning(self, message):
        if self.level >= 4:
            dt = self.get_datetime()
            data = dt + yellow(' WARNING: ') + message
            print(data)
            self.slack.add_messages("*WARNING*: " + message, 4)

    def notice(self, message):
        if self.level >= 5:
            dt = self.get_datetime()
            data = dt + blue(' NOTICE: ') + message
            print(data)
            self.slack.add_messages("*NOTICE*: " + message, 5)

    def info(self, message):
        if self.level >= 6:
            dt = self.get_datetime()
            data = dt + green(' INFO: ') + message
            print(data)
            self.slack.add_messages("*INFO*: " + message, 6)

    def debug(self, message):
        if self.level >= 7:
            dt = self.get_datetime()
            data = dt + white(' DEBUG: ') + message
            print(data)
            self.slack.add_messages("*DEBUG*: " + message, 7)
