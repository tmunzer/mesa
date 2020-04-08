from libs import req
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
            "orange": "warning",
            "red": "danger"

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
            return [part_message[0], "Unknown", "Unknown", part_message[1]]
        elif part_len == 3:
            return [part_message[0], part_message[1], "Unknown", part_message[2]]
        elif part_len == 4:
            return [part_message[0], part_message[1], part_message[2], part_message[3]]
        else:
            return ["Unknown", "Unknown", "Unknown", message]

    def _generate_message(self, messages):
        text = ""
        site = "Unknown"
        switch = "Unknown"
        port = "Unknown"
        info = "Unknown"
        color = "#aaaaaa"
        status = "WARNING"
        index_messages = len(messages) - 1
        if "ERROR" in messages[index_messages]:
            message = messages[index_messages].replace("*ERROR*: ", "")
            site, switch, port, info = self._split_message(message)
            text = "%s > %s > %s configured through %s:\n %s" % (
                site, switch, port, self.configuration_method.upper(), info)
            status = "ERROR"
            color = self.color["red"]
        if "WARNING" in messages[index_messages]:
            message = messages[index_messages].replace("*WARNING*: ", "")
            site, switch, port, info = self._split_message(message)
            text = "%s > %s > %s configured through %s:\n %s" % (
                site, switch, port, self.configuration_method.upper(), info)
            status = "ABORTED"
            color = self.color["orange"]
        elif "NOTICE" in messages[index_messages]:
            message = messages[index_messages].replace("*NOTICE*: ", "")
            site, switch, port, info = self._split_message(message)
            configuration = messages[index_messages-1].split("\n")[1:]
            configuration = ("\n").join(configuration)
            text = "%s > %s > %s configured through %s\n%s" % (
                site, switch, port, self.configuration_method.upper(), configuration)
            status = "SUCCESS"
            color = self.color["green"]
        else:
            text = "\n".join(messages)
        return [status, text, color]


    def _msteams_message(self, message):
        messages = message.split(":")
        port_profile_index = messages.index("Port Profile Name")
        if port_profile_index: port_profile = message[port_profile_index + 1]
        else: port_profile: "Unknow"

        lan_segment_index = messages.index("LAN Segments")
        if lan_segment_index: lan_segment = message[lan_segment_index + 1]
        else: lan_segment: "Unknow"

        native_vlan_index = messages.index("Native VLAN")
        if native_vlan_index: native_vlan = message[native_vlan_index + 1]
        else: native_vlan: "Unknow"

        return [port_profile, lan_segment, native_vlan]


    def send_message(self, thread_id):
        if self.enabled and len(self.threads[thread_id]["messages"]) > 0 and self.threads[thread_id]["do_not_send"] == False:
            messages = self.threads[thread_id]["messages"]
            now = datetime.now()
            now.strftime("%d/%m/%Y %H:%M:%S")
            part_message = messages[0].replace("*NOTICE*: ", "").split("|")
            site_name = part_message[0].replace("MIST SITE: ", "")
            title = "%s on site %s" % (part_message[1], site_name)
            status, message, color = self._generate_message(messages)
            port_profile, lan_segment, native_vlan = self._msteams_message(message)

            body = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": color,
                "summary": title,
                "sections": [{
                    "activityTitle": title,
                    "activitySubtitle": now,
                    "facts": [{
                        "name": status,
                        "value": "CSO SITE: lab > SWITCH: sw-jn-01.lab.THOMAS_MUN > PORT: ge-0/0/0 configured through CSO"
                    }, {
                        "name": "Port Profile Name",
                        "value": port_profile
                    }, {
                        "name": "LAN Segment",
                        "value": lan_segment
                    }, {
                        "name": "Native VLAN",
                        "value": native_vlan
                    }],
                    "markdown": True
                }]
            }
            data = json.dumps(body)
            data = data.encode("ascii")
            requests.post(self.url, headers={
                          "Content-type": "application/json"}, data=data)
            self._clear_data(thread_id)
