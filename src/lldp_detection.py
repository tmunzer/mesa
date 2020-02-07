
###########################
### IMPORTS
from libs import req

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

apitoken = mist_conf["apitoken"]
mist_cloud = mist_conf["mist_cloud"]
server_uri = mist_conf["server_uri"]

###########################
### FUNCTIONS

def _get_switch_info(level, level_id, switch_name):
    url = "https://%s/api/v1/%s/%s/devices/search?type=switch&hostname=%s" %(mist_cloud, level, level_id, switch_name)    
    headers = {'Content-Type': "application/json", "Authorization": "Token %s" %apitoken}
    resp = req.get(url, headers=headers)
    if "result" in resp and "results" in resp["result"]["results"]:
        if len(resp["result"]["results"]) == 1:
            return resp["result"]["results"][0]
    console.error("SWITCH: %s | Unable to get the switch info" %(switch_name))
        
    


def _get_switch_mac(level, level_id, switch_name):
    switch_info = _get_switch_info(level, level_id, switch_name)
    if not "mac" in switch_info:
        console.error("SWITCH: %s | Unable to get the MAC Address if the switch" %(switch_name))
    else:
        return switch_info["mac"]


def _get_switchport_info(level, level_id, switch_name, port_name):
    switch_mac = _get_switch_mac(level, level_id, switch_name)
    url = "https://%s/api/v1/%s/%s/stats/switch_ports/search?mac=%s&port_id=%s" %(mist_cloud, level, level_id, switch_mac, port_name)    
    headers = {'Content-Type': "application/json", "Authorization": "Token %s" %apitoken}
    resp = req.get(url, headers=headers)
    if "result" in resp and "results" in resp["result"]["results"]:
        if len(resp["result"]["results"]) == 1:
            return resp["result"]["results"][0]
    console.error("SWITCH: %s | Unable to get the switch info" %(switch_name))

def ap_still_connected(level, level_id, ap_mac, switch_name, port_name):
    swichport_info = _get_switchport_info(level, level_id, switch_name, port_name)
    # No device connected to the switch port
    if not "neighbor_mac" in swichport_info:
        console.info("SWITCH: %s | PORT: %s | No device connected to the switchport: Processing the message" %(switch_name, port_name))
        return True
    # Other device connected to the switchport
    elif not swichport_info["neighbor_mac"] == ap_mac:
        console.info("SWITCH: %s | PORT: %s | Device connected to the switchport is not the AP AP: Processing the message" %(switch_name, port_name))
        return True
    # AP still connected to the switchport
    else:
        console.info("SWITCH: %s | PORT: %s | AP still connected to the switport. Possible outage: Discarding the message" %(switch_name, port_name))
        return False

