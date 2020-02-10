from libs import req
import requests
import json

class Slack:

    def __init__(self, config):
        print(config)
        if config: 
            self.enabled = config["enabled"]
            self.url = config["url"]
        else: 
            self.enabled = False
        self.title = ""
        self.messages = [] 
        self.severity = 7
        
    def _clear_data(self):
        self.title = ""
        self.messages = [] 
        self.severity = 7

    def set_title(self, title):
        self.title = title
    def add_messages(self, message, severity):
        self.messages.append(message) 
        if severity < self.severity: 
            self.severity = severity

    def send_message(self):
        if self.enabled:
            body = {
                "blocks": [
                    {
                        "type": "divider"
                    }                      
                ]
            }
            text = ""
            for message in self.messages:
                text += "%s\n" %(message)

            body["blocks"].append({
                "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": text
                    }
            })
            data = json.dumps(body)
            data = data.encode("ascii")
            requests.post(self.url, headers={"Content-type": "application/json"}, data=data)
            self._clear_data()