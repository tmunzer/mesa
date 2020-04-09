from libs import req
import re
import requests
import json
import time
from datetime import datetime


class Teams:

    def __init__(self, config, configuration_method):
        if config:
            self.enabled = config["enabled"]
            self.url = config["url"]
        if configuration_method:
            self.configuration_method = configuration_method
        else:
            self.enabled = False
        self.threads = {}
        self.color = {
            "green": "#36a64f",
            "blue": "#2196f3",
            "orange": "#F39C12",
            "red": "#E74C3C"

        }

    def do_not_send(self, thread_id):
        self.threads[thread_id]["do_not_send"] = True

    def _clear_data(self, thread_id):
        self.threads[thread_id] = {
            "messages": [], "severity": 7, "do_not_send": False}


    def add_messages(self, message, severity, thread_id):
        if not thread_id in self.threads:
            self.threads[thread_id] = {
                "messages": [], "severity": 7,  "do_not_send": False}
        self.threads[thread_id]["messages"].append(message)
        if severity < self.threads[thread_id]["severity"]:
            self.threads[thread_id]["severity"] = severity

    def _get_color(self, severity):
        if severity >= 6:
            return self.color["green"]
        elif severity >= 5:
            return self.color["blue"]
        elif severity >= 4:
            return self.color["orange"]
        else:
            return self.color["red"]

    def _split_message(self, message):
        part_message = message.split(" | ")
        part_len = len(part_message)
        if part_len == 2:
            return [part_message[0], "Switch Unknown", "Port Unknown", part_message[1]]
        elif part_len == 3:
            return [part_message[0], part_message[1], "Port Unknown", part_message[2]]
        elif part_len == 4:
            return [part_message[0], part_message[1], part_message[2], part_message[3]]
        else:
            return ["Site Unknown", "Switch Unknown", "Port Unknown", message]

    def _generate_message(self, messages):
        color = "#aaaaaa"
        status = "WARNING"
        index_messages = len(messages) - 1
        if "ERROR" in messages[index_messages]:
            status = "ERROR"
            color = self.color["red"]
            facts = self._generate_not_success(status, messages)  
        elif "WARNING" in messages[index_messages]:
            status = "ABORTED"
            color = self.color["orange"]
            facts = self._generate_not_success(status, messages)  
        elif "NOTICE" in messages[index_messages]:
            message = messages[index_messages].replace("*NOTICE*: ", "")
            configuration = messages[index_messages-1].split("\n")[1:]
            status = "SUCCESS"
            color = self.color["green"]
            facts = self._generate_success(status, message, configuration)            
        else:
            facts = self._generate_not_success(status, messages)  
        return [status, facts, color]

    def _generate_not_success(self, status, messages):
        facts = []     
        for mess in messages:
            name, value = mess.split(":", 1)
            facts.append({"name": name.replace("*",""), "value": value})
        return facts


    def _generate_success(self, status, message, configuration):
        site, switch, port, info = self._split_message(message)
        text = "%s > %s > %s configured through %s" % (
            site, switch, port, self.configuration_method.upper())
 
        port_profile = "Unknown"
        lan_segment = "Unknown"
        native_vlan = "Unknown"
        for conf in configuration:
            key, value = conf.split(":") 
            if key.strip() == "Port Profile Name":
                port_profile = value.strip()
            elif key.strip() == "LAN Segments":
                lan_segment = value.strip()
            elif key.strip() == "Native VLAN":
                native_vlan = value.strip()
        
        facts = [
            {"name": status, "value": text},
            {"name": "Port Profile Name","value": port_profile},
            {"name": "LAN Segment","value": lan_segment},
            {"name": "Native VLAN","value": native_vlan}
            ]     

        return facts


    def send_message(self, thread_id):
        if self.enabled and len(self.threads[thread_id]["messages"]) > 0 and self.threads[thread_id]["do_not_send"] == False:
            messages = self.threads[thread_id]["messages"]
            now = datetime.now()
            now.strftime("%d/%m/%Y %H:%M:%S")
            part_message = messages[0].replace("*NOTICE*: ", "").split("|")
            site_name = part_message[0].replace("MIST SITE: ", "")
            title = "%s on site %s" % (part_message[1], site_name)
            status, facts, color = self._generate_message(messages)
            print(color)
            body = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": color,
                "summary": title,
                "sections": [{
                    "activityTitle": title,
                    "activitySubtitle": str(now),
                    "facts": facts,
                    "markdown": True
                }]
            }
            data = json.dumps(body)
            data = data.encode("ascii")
            requests.post(self.url, headers={
                          "Content-type": "application/json"}, data=data)
            self._clear_data(thread_id)
