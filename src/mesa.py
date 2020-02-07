
### WEB SERVER IMPORTS ###
from flask import Flask
from flask import json
from flask import request
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

###########################
### LOADING SETTINGS
from config import mist_conf
from config import disconnect_validation
from config import configuration_method

apitoken = mist_conf["apitoken"]
mist_cloud = mist_conf["mist_cloud"]
server_uri = mist_conf["server_uri"]
site_id_ignored = mist_conf["site_id_ignored"]
disconnect_validation_method = disconnect_validation["method"]
disconnect_validation_wait_time = disconnect_validation["wait_time"]

###########################
### METHODS IMPORT ###
if configuration_method == "cso":
    import cso
elif configuration_method == "ex":
    import ex
else:
    console.critical("Error in the configuration file. Please check the configuration_method variable! Exiting...")
    exit(255)
import outage_detection
import lldp_detection
###########################
### VARS
server_port = 51360

###########################
### FUNCTIONS

def _disconnect_validation(level, level_id, level_name, ap_mac, lldp_system_name, lldp_port_desc):
    if disconnect_validation_method == "outage":  
        console.info("Pausing to check possible outage on %s %s" %(level, level_id))
        time.sleep(disconnect_validation_wait_time)      
        return outage_detection.site_online(level, level_id, level_name, ap_mac)
    elif disconnect_validation_method == "lldp":
        console.info("Pausing to check possible outage on %s %s" %(level, level_id))
        time.sleep(disconnect_validation_wait_time)
        return lldp_detection.ap_still_connected(level, level_id, level_name, ap_mac, lldp_system_name, lldp_port_desc)
    else:
        return True

def _get_ap_details(level, level_id, mac):
    url = "https://%s/api/v1/%s/%s/devices/search?mac=%s" %(mist_cloud, level, level_id, mac)    
    headers = {'Content-Type': "application/json", "Authorization": "Token %s" %apitoken}
    resp = req.get(url, headers=headers)
    if "result" in resp:
        return resp["result"]

def _initiate_conf_change(action, level, level_id, level_name, ap_mac):
    resp = _get_ap_details(level, level_id, ap_mac)
    if "results" in resp and len(resp["results"]) == 1: 
        console.debug("AP %s found in %s %s" %(ap_mac, level, level_id))
        ap_info = resp["results"][0]
        lldp_system_name = ap_info["lldp_system_name"]
        lldp_port_desc = ap_info["lldp_port_desc"]
        if configuration_method == "cso":
            console.info("SITE: %s | SWITCH: %s | PORT: %s | Configuration will be done through CSO" %(level_name, lldp_system_name, lldp_port_desc))
            if action == "AP_CONNECTED":
                cso.ap_connected(level_name, ap_mac, lldp_system_name, lldp_port_desc)
            elif action == "AP_DISCONNECTED":
                disconnect_validated = _disconnect_validation(level, level_id, level_name, ap_mac, lldp_system_name, lldp_port_desc)
                if disconnect_validated == True: cso.ap_disconnected(level_name, ap_mac, lldp_system_name, lldp_port_desc)
        elif configuration_method == "ex":
            console.info("SITE: %s | SWITCH: %s | PORT: %s | configuration will be done directly on the switch" %(level_name, lldp_system_name, lldp_port_desc))
            if action == "AP_CONNECTED":
                ex.ap_connected(level_name, ap_mac, lldp_system_name, lldp_port_desc)
            elif action == "AP_DISCONNECTED":
                disconnect_validated = _disconnect_validation(level, level_id, level_name, ap_mac, lldp_system_name, lldp_port_desc)
                if disconnect_validated == True: ex.ap_disconnected(level_name, ap_mac, lldp_system_name, lldp_port_desc)
    else:
        console.warning("Received %s for AP %s, but I'm unable to find it in %s %s" %(action, ap_mac, level, level_id))

def ap_event(event):
    mac = event["ap"]
    if "site_id" in event:
        level = "sites"
        level_id = event["site_id"]
        level_name = event["site_name"]
        if level_id in site_id_ignored:
            return False
    else:
        level = "orgs"
        level_id = ["org_id"]
        level_name = "ROOT_ORG"
    action = event["type"]    
    console.info("SITE: %s | RECEIVED message %s for AP %s" %(level_name, action, mac))
    _initiate_conf_change(action, level, level_id, level_name, mac)

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


