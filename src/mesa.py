
### WEB SERVER IMPORTS ###
from flask import Flask
from flask import json
from flask import request


### CONF IMPORT ###
from config import mist_conf
from config import configuration_method

### OTHER IMPORTS ###
import json
from libs import req
import os

###########################
### LOGGING SETTINGS
try:
    from config import log_level
except:
    log_level = 6
finally:
    from libs.debug import Console
    console = Console(log_level)

#if os.path.isfile(portal_file_name):
#    f = open("./data.py", w+)
#    f.close()
#from 
###########################
### METHODS IMPORT ###
if configuration_method == "cso":
    import cso
elif configuration_method == "ex":
    import ex
else:
    console.critical("Error in the configuration file. Please check the configuration_method variable! Exiting...")
    exit(255)
###########################
### PARAMETERS

apitoken = mist_conf["apitoken"]
mist_cloud = mist_conf["mist_cloud"]
server_uri = mist_conf["server_uri"]

###########################
### VARS
server_port = 51360

###########################
### FUNCTIONS

# Function called when an AP is connected/disconnected
def ap_event(event):
    mac = event["ap"]
    if "site_id" in event:
        level = "sites"
        level_id = event["site_id"]
    else:
        level = "orgs"
        level_id = ["org_id"]
    action = event["type"]
    url = "https://%s/api/v1/%s/%s/devices/search?mac=%s" %(mist_cloud, level, level_id, mac)    
    headers = {'Content-Type': "application/json", "Authorization": "Token %s" %apitoken}
    resp = req.get(url, headers=headers)["result"]
    if "results" in resp and len(resp["results"]) == 1: 
        console.debug("AP %s found in %s %s" %(mac, level, level_id))
        ap_info = resp["results"][0]
        lldp_system_name = ap_info["lldp_system_name"]
        lldp_port_desc = ap_info["lldp_port_desc"]
        if configuration_method == "cso":
            console.info("Port %s on switch %s will be configured through CSO" %(lldp_port_desc,lldp_system_name))
            if action == "AP_CONNECTED":
                cso.ap_connected(mac, lldp_system_name, lldp_port_desc)
            elif action == "AP_DISCONNECTED":
                cso.ap_disconnected(mac, lldp_system_name, lldp_port_desc)
        elif configuration_method == "ex":
            console.info("Port %s on switch %s will be configured directly on the switch" %(lldp_port_desc,lldp_system_name))
            if action == "AP_CONNECTED":
                ex.ap_connected(mac, lldp_system_name, lldp_port_desc)
            elif action == "AP_DISCONNECTED":
                ex.ap_disconnected(mac, lldp_system_name, lldp_port_desc)
    else:
        console.warning("Received %s for AP %s, but I'm unable to find it in %s %s" %(action, mac, level, level_id))

###########################
### ENTRY POINT
app = Flask(__name__)
@app.route(server_uri, methods=["POST"])
def postJsonHandler():
    content = request.get_json()
    for event in content["events"]:
        if event["type"] == "AP_CONNECTED" or event["type"] == "AP_DISCONNECTED":
            ap_event(event)
    return '', 200


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=server_port)











