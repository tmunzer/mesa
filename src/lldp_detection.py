
###########################
### IMPORTS
from libs import req
import time


###########################
### LOADING SETTINGS
from config import mist_conf

apitoken = mist_conf["apitoken"]
mist_cloud = mist_conf["mist_cloud"]
server_uri = mist_conf["server_uri"]

###########################
### FUNCTIONS

def _get_switch_info(level, level_id, level_name, switch_name, console, thread_id):
    url = "https://%s/api/v1/%s/%s/devices/search?type=switch&name=%s" %(mist_cloud, level, level_id, switch_name)     
    headers = {'Content-Type': "application/json", "Authorization": "Token %s" %apitoken}
    resp = req.get(url, headers=headers)
    if "result" in resp and "results" in resp["result"]:
        if len(resp["result"]["results"]) == 1:
            return resp["result"]["results"][0]
    console.error("MIST SITE: %s | SWITCH: %s | Unable to get the switch info" %(level_name, switch_name), thread_id)
    console.send_message(thread_id)
    return resp[0]


def _get_switch_mac(level, level_id, level_name, switch_name, console, thread_id):
    switch_info = _get_switch_info(level, level_id, level_name, switch_name, console, thread_id)
    if not "mac" in switch_info:
        console.error("MIST SITE: %s | SWITCH: %s | Unable to get the MAC Address of the switch" %(level_name, switch_name), thread_id)
        console.send_message(thread_id)
        return False
    else:
        return switch_info["mac"]


def _get_switchport_info(level, level_id, level_name, switch_name, port_name, console, thread_id):
    switch_mac = _get_switch_mac(level, level_id, level_name, switch_name, console, thread_id)
    if switch_mac:
        url = "https://%s/api/v1/%s/%s/stats/switch_ports/search?switch=%s&port_id=%s" %(mist_cloud, level, level_id, switch_mac, port_name)    
        headers = {'Content-Type': "application/json", "Authorization": "Token %s" %apitoken}
        resp = req.get(url, headers=headers)
        if "result" in resp and "results" in resp["result"]:
            if len(resp["result"]["results"]) == 1:
                return resp["result"]["results"][0]
        console.error("MIST SITE: %s | SWITCH: %s | Unable to get the switchport info" %(level_name, switch_name), thread_id)
        console.send_message(thread_id)

def ap_disconnected(level, level_id, level_name, ap_mac, switch_name, port_name, wait_time, console, thread_id):
    swichport_info = _get_switchport_info(level, level_id, level_name, switch_name, port_name, console, thread_id)    
    if swichport_info == None:
        console.error("MIST SITE: %s | SWITCH: %s | PORT: %s | Unable to retrieve information: Discarding the message" %(level_name, switch_name, port_name), thread_id)
        console.send_message(thread_id)
        return False
    # switch port is down
    elif not "up" in swichport_info:
        console.info("MIST SITE: %s | SWITCH: %s | PORT: %s | Switchport down: Processing the message" %(level_name, switch_name, port_name), thread_id)
        return True
    # No device connected to the switch port (but switchport UP???)
    elif not "neighbor_mac" in swichport_info:
        console.warning("MIST SITE: %s | SWITCH: %s | PORT: %s | Switchport UP but no device connected to the switchport: Processing the message" %(level_name, switch_name, port_name), thread_id)
        return True
    # Other device connected to the switchport
    elif not swichport_info["neighbor_mac"].replace(":","") == ap_mac.replace(":",""):
        console.info("MIST SITE: %s | SWITCH: %s | PORT: %s | Device connected to the switchport is not the AP AP (Device MAC %s): Processing the message" %(level_name, switch_name, port_name, swichport_info["neighbor_mac"]), thread_id)
        return True
    # AP still connected to the switchport
    elif wait_time == False:    
        console.warning("MIST SITE: %s | SWITCH: %s | PORT: %s | AP still connected to the switport. Possible outage: Discarding the message" %(level_name, switch_name, port_name), thread_id)
        console.send_message(thread_id)
        return False
    else:
        console.info("MIST SITE: %s | SWITCH: %s | PORT: %s | AP still connected to the switport. Waiting for another %s seconds..." %(level_name, switch_name, port_name, wait_time), thread_id)
        time.sleep(wait_time)
        return ap_disconnected(level, level_id, level_name, ap_mac, switch_name, port_name, False, console, thread_id)

