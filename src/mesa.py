
### WEB SERVER IMPORTS ###
from flask import Flask
from flask import json
from flask import request
### OTHER IMPORTS ###
import json
from libs import req
import os
import time
from threading import Thread

###########################
### LOADING SETTINGS
from config import mist_conf
from config import disconnect_validation
from config import configuration_method
from config import slack_conf

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
    print("Error in the configuration file. Please check the configuration_method variable! Exiting...")
    exit(255)
import outage_detection
import lldp_detection

###########################
### LOGGING SETTINGS
try:
    from config import log_level
except:
    log_level = 6
finally:
    from libs.debug import Console


###########################
### VARS
server_port = 51360

###########################
### FUNCTIONS

def _disconnect_validation(level, level_id, level_name, ap_mac, lldp_system_name, lldp_port_desc, console):
    if disconnect_validation_method == "outage":  
        console.info("Pausing for %s seconds to check possible outage on %s %s" %(disconnect_validation_wait_time, level, level_id))
        time.sleep(disconnect_validation_wait_time)      
        return outage_detection.site_online(level, level_id, level_name, ap_mac)
    elif disconnect_validation_method == "lldp":
        console.info("Pausing for %s seconds to check possible outage on %s %s" %(disconnect_validation_wait_time, level, level_id))
        time.sleep(disconnect_validation_wait_time)
        return lldp_detection.ap_still_connected(level, level_id, level_name, ap_mac, lldp_system_name, lldp_port_desc, disconnect_validation_wait_time, console)
    else:
        return True

def _get_ap_details(level, level_id, mac, console):
    url = "https://%s/api/v1/%s/%s/devices/search?mac=%s" %(mist_cloud, level, level_id, mac)    
    headers = {'Content-Type': "application/json", "Authorization": "Token %s" %apitoken}
    resp = req.get(url, headers=headers)
    if resp and "result" in resp:
        return resp["result"]
    else: return None

def _get_new_site_name(device, level_name, console):
    url = "https://%s/api/v1/sites/%s" %(mist_cloud, device["site_id"])
    headers = {'Content-Type': "application/json", "Authorization": "Token %s" %apitoken}
    resp = req.get(url, headers=headers)
    if resp and "result" in resp:
        return (resp["result"]["name"], resp["result"]["id"])
    else:
        console.error("MIST AP %s | Not on site %s anymore, and unable to find where it is. Aborting..." %(device["mac"], level_name))

def _deep_dive_lookup_for_ap(org_id, action, level, level_id, level_name, ap_mac, retry, console):
    url = "https://%s/api/v1/orgs/%s/inventory" %(mist_cloud, org_id)  
    headers = {'Content-Type': "application/json", "Authorization": "Token %s" %apitoken}
    resp = req.get(url, headers=headers)
    if resp and "result" in resp:
        for device in resp["result"]:
            if device["mac"] == ap_mac:
                site_name, site_id = _get_new_site_name(device, level_name, console)
                console.notice("MIST AP %s | Has been moved from site %s to site %s. Processing with the new site..." %(ap_mac, level_name, site_name))
                _initiate_conf_change(action, org_id, "sites", site_id, site_name, ap_mac, True, console)
                break
    else:
        console.error("MIST AP %s | May have been removed from the Org before I get the message. Unable to retrieve the required informations. Aborting...")

def _initiate_conf_change(action, org_id, level, level_id, level_name, ap_mac, retry, console):
    resp = _get_ap_details(level, level_id, ap_mac, console)
    if resp and "results" in resp and len(resp["results"]) == 1: 
        console.debug("AP %s found in %s %s" %(ap_mac, level, level_id))
        ap_info = resp["results"][0]
        if "lldp_system_name" in ap_info and "lldp_port_desc" in ap_info:
            lldp_system_name = ap_info["lldp_system_name"]
            lldp_port_desc = ap_info["lldp_port_desc"]

            if configuration_method == "cso":
                console.notice("MIST SITE: %s | SWITCH: %s | PORT: %s | Configuration will be done through CSO" %(level_name, lldp_system_name, lldp_port_desc))
                if action == "AP_CONNECTED":
                    cso.ap_connected(ap_mac, lldp_system_name, lldp_port_desc, console)
                elif action == "AP_DISCONNECTED":
                    disconnect_validated = _disconnect_validation(level, level_id, level_name, ap_mac, lldp_system_name, lldp_port_desc, console)
                    if disconnect_validated == True: cso.ap_disconnected(ap_mac, lldp_system_name, lldp_port_desc, console)
            elif configuration_method == "ex":
                console.notice("MIST SITE: %s | SWITCH: %s | PORT: %s | configuration will be done directly on the switch" %(level_name, lldp_system_name, lldp_port_desc))
                if action == "AP_CONNECTED":
                    ex.ap_connected(level_name, ap_mac, lldp_system_name, lldp_port_desc)
                elif action == "AP_DISCONNECTED":
                    disconnect_validated = _disconnect_validation(level, level_id, level_name, ap_mac, lldp_system_name, lldp_port_desc, console)
                    if disconnect_validated == True: ex.ap_disconnected(level_name, ap_mac, lldp_system_name, lldp_port_desc)
        else:
            console.error("MIST SITE: %s | Received %s for AP %s, but I'm unable retrieve the LLDP information" %(level_name, action, ap_mac))    
    elif not retry:
        _deep_dive_lookup_for_ap(org_id, action, level, level_id, level_name, ap_mac, retry, console,)
    else: 
        console.error("MIST SITE: %s | Received %s for AP %s, but I'm unable to find it" %(level_name, action, ap_mac))

def ap_event(event, thread, active_threads):
    console = Console(log_level, slack_conf, configuration_method, thread)
    mac = event["ap"] 
    if "site_id" in event:
        level = "sites"
        level_id = event["site_id"]
        org_id = event["org_id"]
        if "site_name" in event: level_name = event["site_name"]
        else: level_name = "no site name"
    else:
        level = "orgs"
        level_id = event["org_id"]
        org_id = event["org_id"]
        level_name = "ROOT_ORG"
    action = event["type"]    
    if level_id in site_id_ignored:
        console.notice("MIST SITE: %s | RECEIVED message %s for AP %s, but site %s should be ignored. Discarding the message..." %(level_name, action, mac, level_id))
    else:
        console.notice("MIST SITE: %s | RECEIVED message %s for AP %s" %(level_name, action, mac))
        _initiate_conf_change(action, org_id, level, level_id, level_name, mac, False, console)
    console.slack.send_message()
    active_threads -= 1

###########################
### ENTRY POINT

active_threads = 1
app = Flask(__name__)
@app.route(server_uri, methods=["POST"])
def postJsonHandler():
    global active_threads
    content = request.get_json()
    for event in content["events"]:
        if event["type"] == "AP_CONNECTED" or event["type"] == "AP_DISCONNECTED"  or event["type"] == "AP_RESTARTED":  
            this_thread = active_threads 
            active_threads +=1
            process = Thread(target=ap_event, args=(event, this_thread, active_threads))
            process.start()
    return '', 200


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=server_port)


