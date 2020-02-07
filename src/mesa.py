
### WEB SERVER IMPORTS ###
from flask import Flask
from flask import json
from flask import request


### CONF IMPORT ###
from config import mist_conf
from config import configuration_method
from config import site_outage
import time
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
site_id_ignored = mist_conf["site_id_ignored"]
site_outage_detection = site_outage["enabled"]
timeout_site_outage = site_outage["outage_timeout"]
timeout_ap_removed = site_outage["removed_timeout"]
wait_site_outage = site_outage["wait_time"]
min_disconnected_percentage = site_outage["min_percentage"] / 100

###########################
### VARS
server_port = 51360

###########################
### FUNCTIONS
def _process_timestamp(list_devices):
    disconnected_device_timestamps = []   
    num_aps = 0
    num_outaged_aps = 0
    percentage_outaged_aps = 0
    now = round(time.time())
    # remove devices disconnected for a long time and gather last seen timestamp for devices disconnected recently
    for device in list_devices:
        if device["type"] == "ap":
            if device["status"] == "connected":
                num_aps += 1
            elif device["status"] == "disconnected" and now - device["last_seen"] < timeout_ap_removed :
                num_aps += 1
                disconnected_device_timestamps.append(device["last_seen"])
    disconnected_device_timestamps.sort()  
    # we should not get "0" devices, but this is a security to not divide by 0
    if num_aps > 0:
        # if small site the result will not be useable, so processing the message
        if num_aps <= 2:
            console.info("Site outage detection ignored. Less than 2 APs were connected during the last %s seconds: Processing the message" %(timeout_ap_removed))
            return False
        else:
            # check if the devices were disconnect before of after the site outage timeout
            for timestamp in disconnected_device_timestamps:            
                if now - timestamp < timeout_site_outage:
                    num_outaged_aps += 1
            percentage_outaged_aps = (num_outaged_aps / num_aps) 
            # if the number of devices is greater than the configured limit, outage detectect, discarding the message
            if percentage_outaged_aps >= min_disconnected_percentage:
                percentage_outaged_aps = round(percentage_outaged_aps * 100) 
                console.info("Site outage detected! %s%% of APs disconnected in less than %s seconds: Discarding the message" %(percentage_outaged_aps, timeout_site_outage))
                return True
            # otherwise, no outage detected, processing the message
            else: 
                percentage_outaged_aps = round(percentage_outaged_aps * 100) 
                console.info("No site outage detected. %s%% of APs disconnected in less than %s seconds: Processing the message" %(percentage_outaged_aps, timeout_site_outage))
                return False
    else:
        return False


# Function called when an AP is connected/disconnected
def _check_site_outage(level, level_id, ap_mac):
    console.info("Pausing to check possible outage on %s %s" %(level, level_id))
    time.sleep(wait_site_outage)
    url = "https://%s/api/v1/%s/%s/stats/devices" %(mist_cloud, level, level_id)    
    headers = {'Content-Type': "application/json", "Authorization": "Token %s" %apitoken}
    resp = req.get(url, headers=headers)
    if "result" in resp:
        return _process_timestamp(resp["result"])
    

def _get_ap_details(level, level_id, mac):
    url = "https://%s/api/v1/%s/%s/devices/search?mac=%s" %(mist_cloud, level, level_id, mac)    
    headers = {'Content-Type': "application/json", "Authorization": "Token %s" %apitoken}
    resp = req.get(url, headers=headers)
    if "result" in resp:
        return resp["result"]

def _initiate_conf_change(action, level, level_id, mac):
    resp = _get_ap_details(level, level_id, mac)
    if "results" in resp and len(resp["results"]) == 1: 
        console.debug("AP %s found in %s %s" %(mac, level, level_id))
        ap_info = resp["results"][0]
        lldp_system_name = ap_info["lldp_system_name"]
        lldp_port_desc = ap_info["lldp_port_desc"]
        if configuration_method == "cso":
            console.info("SWITCH: %s | PORT: %s | Configuration will be done through CSO" %(lldp_system_name, lldp_port_desc))
            if action == "AP_CONNECTED":
                cso.ap_connected(mac, lldp_system_name, lldp_port_desc)
            elif action == "AP_DISCONNECTED":
                cso.ap_disconnected(mac, lldp_system_name, lldp_port_desc)
        elif configuration_method == "ex":
            console.info("SWITCH: %s | PORT: %s | configuration will be done directly on the switch" %(lldp_system_name, lldp_port_desc))
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
        if level_id in site_id_ignored:
            return False
    else:
        level = "orgs"
        level_id = ["org_id"]
    action = event["type"]    
    console.info("RECEIVED message %s for AP %s" %(action, mac))
    if action == "AP_DISCONNECTED" and site_outage_detection == True:
        site_out = _check_site_outage(level, level_id, mac)
    if action == "AP_CONNECTED" or site_out == False:
        _initiate_conf_change(action, level, level_id, mac)

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


