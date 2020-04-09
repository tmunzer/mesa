from datetime import datetime
from .slack import Slack
from .msteams import Teams
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
        self.msteams = Teams(msteams_conf, configuration_method)
        log.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))        

    def add_message(self, level, message, thread_id):
        text_level = ["*EMERGENCY*: ", "*ALERT*: ", "*CRITICAL*: ", "*ERROR*: ", "*WARNING*: ", "*NOTICE*: ", "*INFO*: ", "*DEBUG*: " ]
        if thread_id:
            self.slack.add_messages(text_level[level] + message, level, thread_id)
            self.msteams.add_messages(text_level[level] + message, level, thread_id)

    def send_message(self, thread_id):
        if thread_id:
            self.slack.send_message(thread_id)
            self.msteams.send_message(thread_id)

    def do_not_send_message(self, thread_id):
        if thread_id:
            self.slack.do_not_send(thread_id)
            self.msteams.do_not_send(thread_id)

    def _get_datetime(self):
            now = datetime.now()
            return now.strftime("%d/%m/%Y %H:%M:%S")

    def emergency(self, message, thread_id=None):
        if self.level >= 0:
            dt = self._get_datetime()
            data = dt + ' - REQ ' + str(thread_id) + ' - ' + magenta(' EMERGENCY: ') + message
            print(data)
            self.add_message(0, message, thread_id)

    def alert(self, message, thread_id=None):
        if self.level >= 1:
            dt = self._get_datetime()
            data = dt + ' - REQ ' + str(thread_id) + ' - ' + magenta(' ALERT: ') + message
            print(data)
            self.add_message(1, message, thread_id)

    def critical(self, message, thread_id=None):
        if self.level >= 2:
            dt = self._get_datetime()
            data = dt + ' - REQ ' + str(thread_id) + ' - ' + magenta(' CRITICAL: ') + message
            print(data)
            self.add_message(2, message, thread_id)

    def error(self, message, thread_id=None):
        if self.level >= 3:
            dt = self._get_datetime()
            data = dt + ' - REQ ' + str(thread_id) + ' - ' + red(' ERROR: ') + message
            print(data)
            self.add_message(3, message, thread_id)

    def warning(self, message, thread_id=None):
        if self.level >= 4:
            dt = self._get_datetime()
            data = dt + ' - REQ ' + str(thread_id) + ' - ' + yellow(' WARNING: ') + message
            print(data)
            self.add_message(4, message, thread_id)

    def notice(self, message, thread_id=None):
        if self.level >= 5:
            dt = self._get_datetime()
            data = dt + ' - REQ ' + str(thread_id) + ' - ' + blue(' NOTICE: ') + message
            print(data)
            self.add_message(5, message, thread_id)

    def info(self, message, thread_id=None):
        if self.level >= 6:
            dt = self._get_datetime()
            data = dt + ' - REQ ' + str(thread_id) + ' - ' + green(' INFO: ') + message
            print(data)
            self.add_message(6, message, thread_id)

    def debug(self, message, thread_id=None):
        if self.level >= 7:
            dt = self._get_datetime()
            data = dt + ' - REQ ' + str(thread_id) + ' - ' + white(' DEBUG: ') + message
            print(data)
            self.add_message(7, message, thread_id)
