from libs import req
import requests
import json
import time
from datetime import datetime
class Slack:

    def __init__(self, config, configuration_method):
        if config: 
            self.enabled = config["enabled"]
            self.url = config["url"]
        if configuration_method:
            self.configuration_method = configuration_method
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
        self._do_not_send = False
        
    def do_not_send(self):
        self._do_not_send = True

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

    def _split_message(self, message):
        part_message =  message.split(" | ")
        part_len = len(part_message)
        if part_len ==2:
            return [part_message[0], "Unknown", "Unknown", part_message[1]]
        elif part_len ==3:
            return [part_message[0], part_message[1], "Unknown", part_message[2]]
        elif part_len ==4:
            return [part_message[0], part_message[1], part_message[2], part_message[3]]
        else:
            return ["Unknown", "Unknown", "Unknown", message]

    def _generate_message(self):
        text = ""
        site = "Unknown"
        switch = "Unknown"
        port = "Unknown"
        info = "Unknown"
        color = "#aaaaaa"
        index_messages = len(self.messages) - 1
        if "ERROR" in self.messages[index_messages]:
            message = self.messages[index_messages].replace("*ERROR*: ", "")
            site, switch, port, info = self._split_message(message)
            text = "ERROR: %s > %s > %s configured through %s:\n %s" %(site, switch, port, self.configuration_method.upper(), info)  
            color = self.color["red"]          
        if "WARNING" in self.messages[index_messages]:
            message = self.messages[index_messages].replace("*WARNING*: ", "")
            site, switch, port, info = self._split_message(message)
            text = "ABORTED: %s > %s > %s configured through %s:\n %s" %(site, switch, port, self.configuration_method.upper(), info)
            color = self.color["orange"]
        elif "NOTICE" in self.messages[index_messages]:
            message = self.messages[index_messages].replace("*NOTICE*: ", "")
            site, switch, port, info = self._split_message(message)
            configuration = self.messages[index_messages-1].split("\n")[1:]
            configuration = ("\n").join(configuration)
            text = "SUCCESS: %s > %s > %s configured through %s\n%s" %(site, switch, port, self.configuration_method.upper(), configuration)
            color = self.color["green"]
        else: 
            text = "\n".join(self.messages)
        return [text, color]


    def send_message(self):
        if self.enabled and len(self.messages) > 0 and self._do_not_send == False:
            now = datetime.now()
            now.strftime("%d/%m/%Y %H:%M:%S")
            part_message = self.messages[0].replace("*NOTICE*: ", "").split("|")
            site_name = part_message[0].replace("MIST SITE: ", "")
            title = "%s - %s on site %s" %(now, part_message[1], site_name)
            message, color = self._generate_message()
           
            body = {
                "attachments": [
                    {
                        "fallback": "New MESA event",
                        "color": color,
                        "pretext": title,          
                        "text": message,            
                    }
                ]
            }
            data = json.dumps(body)
            data = data.encode("ascii")
            requests.post(self.url, headers={"Content-type": "application/json"}, data=data)
            self._clear_data()

