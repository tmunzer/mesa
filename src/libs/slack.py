from libs import req

class Slack:

    def __init__(self, config):
        print(config)
        if config: 
            self.enabled = config["enabled"]
            self.url = config["url"]
        else: 
            self.enabled = False
        self.ap_mac = ""
        self.action = ""
        self.site = ""
        self.switch = ""
        self.port = ""
        self.conf = ""
        self.status = ""
        self.warning = []
        self.error = []
        
    def _clear_data(self):
        self.ap_mac = ""
        self.action = ""
        self.site = ""
        self.switch = ""
        self.port = ""
        self.conf = ""
        self.status = ""
        self.warning = []
        self.error = []

    def set_ap_mac(self, ap_mac):
        self.ap_mac = ap_mac
    def set_action(self, action):
        self.action = action
    def set_site(self, site):
        self.site = site
    def set_switch(self, switch):
        self.switch = switch
    def set_port(self, port):
        self.port = port
    def set_conf(self, conf):
        self.conf = conf
    def set_status(self, status):
        self.status = status
    def add_warning(self, warning):
        self.warning.append(warning) 
    def add_error(self, error):
        self.error.append(error) 

    def send_message(self):
        if self.enabled:
            body = {
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "plain_text",
                            "text": "Received message: AP %s is now %s" %(self.ap_mac, self.action),
                            "emoji": True
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "plain_text",
                            "text": "SITE: %s" %(self.site),
                            "emoji": True
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "plain_text",
                            "text": "SWITCH/PORT: %s/%s" %(self.site, self.port),
                            "emoji": True
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "plain_text",
                            "text": "NEW CONF: %s" %(self.conf),
                            "emoji": True
                        }
                    }
                ]
            }
            #for message in self.messages:
            #    body.append(message)
            req.post(self.url, {"Content-type": "application/json"}, body)
            self._clear_data()