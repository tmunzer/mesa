
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

def _get_switch_info(level, level_id, level_name, switch_name):
    url = "https://%s/api/v1/%s/%s/devices/search?type=switch&hostname=%s" %(mist_cloud, level, level_id, switch_name)     
    headers = {'Content-Type': "application/json", "Authorization": "Token %s" %apitoken}
    resp = req.get(url, headers=headers)
    if "result" in resp and "results" in resp["result"]:
        if len(resp["result"]["results"]) == 1:
            return resp["result"]["results"][0]
    console.error("SITE: %s | SWITCH: %s | Unable to get the switch info" %(level_name, switch_name))
    return []
        
    


def _get_switch_mac(level, level_id, level_name, switch_name):
    switch_info = _get_switch_info(level, level_id, level_name, switch_name)
    if not "mac" in switch_info:
        console.error("SITE: %s | SWITCH: %s | Unable to get the MAC Address if the switch" %(level_name, switch_name))
        return False
    else:
        return switch_info["mac"]


def _get_switchport_info(level, level_id, level_name, switch_name, port_name):
    switch_mac = _get_switch_mac(level, level_id, level_name, switch_name)
    if switch_mac:
        url = "https://%s/api/v1/%s/%s/stats/switch_ports/search?switch=%s&port_id=%s" %(mist_cloud, level, level_id, switch_mac, port_name)    
        headers = {'Content-Type': "application/json", "Authorization": "Token %s" %apitoken}
        resp = req.get(url, headers=headers)
        if "result" in resp and "results" in resp["result"]:
            if len(resp["result"]["results"]) == 1:
                return resp["result"]["results"][0]
        console.error("SITE: %s | SWITCH: %s | Unable to get the switchport info" %(level_name, switch_name))

def ap_still_connected(level, level_id, level_name, ap_mac, switch_name, port_name):
    swichport_info = _get_switchport_info(level, level_id, level_name, switch_name, port_name)    
    if swichport_info == None:
        console.error("SITE: %s | SWITCH: %s | PORT: %s | Unable to retrieve information: Discarding the message" %(level_name, switch_name, port_name))
        return False
    # switch port is down
    elif not "up" in swichport_info:
        console.info("SITE: %s | SWITCH: %s | PORT: %s | Switchport down: Processing the message" %(level_name, switch_name, port_name))
        return True
    # No device connected to the switch port (but switchport UP???)
    elif not "neighbor_mac" in swichport_info:
        console.info("SITE: %s | SWITCH: %s | PORT: %s | Switchport UP but no device connected to the switchport: Processing the message" %(level_name, switch_name, port_name))
        return True
    # Other device connected to the switchport
    elif not swichport_info["neighbor_mac"] == ap_mac:
        console.info("SITE: %s | SWITCH: %s | PORT: %s | Device connected to the switchport is not the AP AP: Processing the message" %(level_name, switch_name, port_name))
        return True
    # AP still connected to the switchport
    else:
        console.info("SITE: %s | SWITCH: %s | PORT: %s | AP still connected to the switport. Possible outage: Discarding the message" %(level_name, switch_name, port_name))
        return False

