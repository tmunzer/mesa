from libs import req
import requests
import json

class Slack:

    def __init__(self, config):
        if config: 
            self.enabled = config["enabled"]
            self.url = config["url"]
        else: 
            self.enabled = False
        self.title = ""
        self.messages = [] 
        self.severity = 7
        self.color ={
            "green": "#36a64f",
            "blue": "#2196f3",
            "orange": "warning",
            "red": "danger"

        } 
        
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

    def _get_color(self):
        if self.severity >= 6:
            return self.color["green"]
        elif self.severity >= 5:
            return self.color["blue"]
        elif self.severity >= 4:
            return self.color["orange"]
        else:
            return self.color["red"]

    def send_message(self):
        if self.enabled:
            body = {
                "attachments": [
                    {
                        "fallback": "New MESA event",
                        "color": self._get_color(),
                        "pretext": self.messages[0],          
                        "text": "",            
                    }
                ]
            }
            text = ""
            i = 1
            while i < len(self.messages):
            #for message in self.messages:
                text += "%s\n" %(self.messages[i])
                i+=1

            body["attachments"][0]["text"] = text
            data = json.dumps(body)
            data = data.encode("ascii")
            requests.post(self.url, headers={"Content-type": "application/json"}, data=data)
            self._clear_data()

