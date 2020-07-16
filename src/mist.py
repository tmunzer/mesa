### IMPORTS ###
from libs import req
import json

### CONF IMPORT ###
from config import mist_conf, mist_method

###########################
# LOGGING SETTINGS
console = None
###########################
# PARAMETERS
apitoken = mist_conf["apitoken"]
host = mist_conf["mist_cloud"]
port_profile_default = mist_method["profile_default"]
port_profile_ap = mist_method["profile_ap"]
profile_ap = mist_method["conf_ap"]

###########################
# VARIABLES
url_prefix = "https://%s" % host

###########################
# FUNCTIONS

# Devices


def get_switch_conf(site_id, site_name, switch_id, switch_name, thread_id):
    url = "%s/api/v1/sites/%s/devices/%s" %(url_prefix, site_id, switch_id)
    headers = {'Content-Type': "application/json",
            "Authorization": "Token %s" % apitoken}
    switch_conf = req.get(url, headers=headers)["result"]
    if switch_conf:
        return switch_conf
    else:
        console.error("MIST SITE: {0} | SWITCH {1} | Unable to find switch configuration...".format(site_name, switch_name), thread_id)
        return None
 
def update_port_usage(switch_conf):
    port_usage = switch_conf["port_usage"] if "port_usage" in switch_conf else {}    
    port_usage[profile_ap["name"]] =  profile_ap 
    return port_usage

def update_port_config(switch_conf, port_id, port_profile, evap_connectedent):    
    port_config= switch_conf["port_config"] if "port_config" in switch_conf else {}
    if ap_connected:
        port_config[port_id] = {"usage": port_profile}
    else:
        del port_config[port_id]
    return port_config

# Configure swtich port

def _set_switchport_config(site_id, site_name, switch_name, switch_id, port_id, port_profile, thread_id, ap_connected=False):
    url = "%s/api/v1/sites/%s/devices/%s" %(url_prefix, site_id, switch_id)
    headers = {'Content-Type': "application/json",
            "Authorization": "Token %s" % apitoken}

    switch_conf = get_switch_conf(site_id, site_name, switch_id, switch_name, thread_id)
    switch_conf["port_usage"] = update_port_usage(switch_conf)
    switch_conf["port_config"] = update_port_config(switch_conf, port_id, port_profile, ap_connected)
    console.notice("MIST SITE: {0} | SWITCH: {1} | PORT: {2} | Sending request to MIST to apply the profile {3}".format(site_name, switch_name, port_id, port_profile), thread_id)

    resp = req.put(url, headers=headers, body=switch_conf)
    return resp

# Deploy and Commit switch configuration

def _init(site_id, switch_name):
    url = "{0}/api/v1/sites/{1}/devices/search?type=switch{2}".format(url_prefix, site_id, "")
    headers = {'Content-Type': "application/json",
            "Authorization": "Token %s" % apitoken}
    
    resp = req.get(url, headers=headers)["result"]["results"]
    for sw in resp:
        if switch_name in sw["hostname"]:
            return "00000000-0000-0000-1000-{0}".format(sw["mac"])
    return None



def ap_connected(mac, lldp_system_name, lldp_port_desc, o_console, thread_id=None, site_name=None, site_id=None, *args):
    global console 
    console = o_console
    switch_id = _init(site_id, lldp_system_name)
    if switch_id:
        _set_switchport_config(site_id, site_name, lldp_system_name, switch_id, lldp_port_desc, port_profile_ap, thread_id, True)
    else:
        console.error("MIST SITE {0} | unable to find the switch {1}".format(site_name, lldp_system_name), thread_id)


def ap_disconnected(mac, lldp_system_name, lldp_port_desc, o_console, thread_id=None, site_name=None, site_id=None, *args):
    global console 
    console = o_console
    switch_id = _init(site_id, lldp_system_name)
    if switch_id:
        _set_switchport_config(site_id, site_name, lldp_system_name, switch_id, lldp_port_desc, port_profile_default, thread_id)
    else:
        console.error("MIST SITE {0} | unable to find the switch {1}".format(site_name, lldp_system_name), thread_id)
