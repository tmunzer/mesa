from datetime import datetime
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

    def __init__(self, level=6):
        self.level = level
        log.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

    def get_datetime(self):
            now = datetime.now()
            return now.strftime("%d/%m/%Y %H:%M:%S")

    def emergency(self, message):
        if self.level >= 0:
            dt = self.get_datetime()
            print(dt + magenta(' EMERGENCY: ') + message)

    def alert(self, message):
        if self.level >= 1:
            dt = self.get_datetime()
            print(dt + magenta(' ALERT: ') + message)

    def critical(self, message):
        if self.level >= 2:
            dt = self.get_datetime()
            print(dt + magenta(' CRITICAL: ') + message)

    def error(self, message):
        if self.level >= 3:
            dt = self.get_datetime()
            print(dt + red(' ERROR: ') + message)

    def warning(self, message):
        if self.level >= 4:
            dt = self.get_datetime()
            print(dt + yellow(' WARNING: ') + message)

    def notice(self, message):
        if self.level >= 5:
            dt = self.get_datetime()
            print(dt + blue(' NOTICE: ') + message)

    def info(self, message):
        if self.level >= 6:
            dt = self.get_datetime()
            print(dt + green(' INFO: ') + message)

    def debug(self, message):
        if self.level >= 7:
            dt = self.get_datetime()
            print(dt + white(' DEBUG: ') + message)
