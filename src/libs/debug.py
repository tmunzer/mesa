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

    def __init__(self, level=6, slack_config = None, msteams_conf = None, configuration_method = None):
        self.level = level
        self.slack = Slack(slack_config, configuration_method)
        self.msteams = Slack(slack_config, configuration_method)
        log.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))        

    def get_datetime(self):
            now = datetime.now()
            return now.strftime("%d/%m/%Y %H:%M:%S")

    def emergency(self, message, thread_id=None):
        if self.level >= 0:
            dt = self.get_datetime()
            data = dt + ' - REQ ' + str(thread_id) + ' - ' + magenta(' EMERGENCY: ') + message
            print(data)
            if thread_id: 
                self.slack.add_messages("*EMERGENCY*: " + message, 0, thread_id)
                self.msteams.add_messages("*EMERGENCY*: " + message, 0, thread_id)

    def alert(self, message, thread_id=None):
        if self.level >= 1:
            dt = self.get_datetime()
            data = dt + ' - REQ ' + str(thread_id) + ' - ' + magenta(' ALERT: ') + message
            print(data)
            if thread_id: 
                self.slack.add_messages("*ALERT*: " + message, 1, thread_id)
                self.msteams.add_messages("*ALERT*: " + message, 1, thread_id)

    def critical(self, message, thread_id=None):
        if self.level >= 2:
            dt = self.get_datetime()
            data = dt + ' - REQ ' + str(thread_id) + ' - ' + magenta(' CRITICAL: ') + message
            print(data)
            if thread_id: 
                self.slack.add_messages("*CRITICAL*: " + message, 2, thread_id)
                self.msteams.add_messages("*CRITICAL*: " + message, 2, thread_id)

    def error(self, message, thread_id=None):
        if self.level >= 3:
            dt = self.get_datetime()
            data = dt + ' - REQ ' + str(thread_id) + ' - ' + red(' ERROR: ') + message
            print(data)
            if thread_id: 
                self.slack.add_messages("*ERROR*: " + message, 3, thread_id)
                self.msteams.add_messages("*ERROR*: " + message, 3, thread_id)

    def warning(self, message, thread_id=None):
        if self.level >= 4:
            dt = self.get_datetime()
            data = dt + ' - REQ ' + str(thread_id) + ' - ' + yellow(' WARNING: ') + message
            print(data)
            if thread_id: 
                self.slack.add_messages("*WARNING*: " + message, 4, thread_id)
                self.msteams.add_messages("*WARNING*: " + message, 4, thread_id)

    def notice(self, message, thread_id=None):
        if self.level >= 5:
            dt = self.get_datetime()
            data = dt + ' - REQ ' + str(thread_id) + ' - ' + blue(' NOTICE: ') + message
            print(data)
            if thread_id: 
                self.slack.add_messages("*NOTICE*: " + message, 5, thread_id)
                self.msteams.add_messages("*NOTICE*: " + message, 5, thread_id)

    def info(self, message, thread_id=None):
        if self.level >= 6:
            dt = self.get_datetime()
            data = dt + ' - REQ ' + str(thread_id) + ' - ' + green(' INFO: ') + message
            print(data)
            if thread_id: 
                self.slack.add_messages("*INFO*: " + message, 6, thread_id)
                self.msteams.add_messages("*INFO*: " + message, 6, thread_id)

    def debug(self, message, thread_id=None):
        if self.level >= 7:
            dt = self.get_datetime()
            data = dt + ' - REQ ' + str(thread_id) + ' - ' + white(' DEBUG: ') + message
            print(data)
            if thread_id: 
                self.slack.add_messages("*DEBUG*: " + message, 7, thread_id)
                self.msteams.add_messages("*DEBUG*: " + message, 7, thread_id)
