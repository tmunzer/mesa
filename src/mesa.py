
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
import time

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
timeout_site_outage = mist_conf["timeout_site_outage"]
wait_site_outage = mist_conf["wait_site_outage"]

###########################
### VARS
server_port = 51360

###########################
### FUNCTIONS

# Function called when an AP is connected/disconnected
def _check_site_outage(level, level_id, ap_mac):
    console.info("Pausing to check possible outage on %s %s" %(level, level_id))
    time.sleep(wait_site_outage)
    url = "https://%s/api/v1/%s/%s/devices" %(mist_cloud, level, level_id)    
    headers = {'Content-Type': "application/json", "Authorization": "Token %s" %apitoken}
    resp = req.get(url, headers=headers)["result"]
    oldest_change_timestamp = -1
    latest_change_timestamp = -1
    ap_change_timestamp = -1
    for device in resp:
        if device["type"] == "ap":
            if oldest_change_timestamp == -1 or oldest_change_timestamp > device["modified_time"]:
                oldest_change_timestamp = device["modified_time"]
            if latest_change_timestamp == -1 or latest_change_timestamp < device["modified_time"]:
                latest_change_timestamp = device["modified_time"]
            if device["mac"] == ap_mac:
                ap_change_timestamp = device["modified_time"]
    if oldest_change_timestamp + timeout_site_outage > ap_change_timestamp or latest_change_timestamp + timeout_site_outage < ap_change_timestamp:
        return True
    else:
        return False

def _get_ap_details(level, level_id, mac):
    url = "https://%s/api/v1/%s/%s/devices/search?mac=%s" %(mist_cloud, level, level_id, mac)    
    headers = {'Content-Type': "application/json", "Authorization": "Token %s" %apitoken}
    return req.get(url, headers=headers)["result"]

def _initiate_conf_change(action, level, level_id, mac):
    resp = _get_ap_details(level, level_id, mac)
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

def ap_event(event):
    mac = event["ap"]
    if "site_id" in event:
        level = "sites"
        level_id = event["site_id"]
    else:
        level = "orgs"
        level_id = ["org_id"]
    action = event["type"]    
    console.info("Received message %s for AP %s" %(action, mac))
    if action == "AP_DISCONNECTED":
        site_out = _check_site_outage(level, level_id, mac)
    else:
        site_out = False
    if site_out == False:
        _initiate_conf_change(action, level, level_id, mac)
    else: 
        console.critical("All APs from %s %s were disconnected in less than %s seconds!!! Aborting configuration change!!!" %(level, level_id, timeout_site_outage * 2))

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











