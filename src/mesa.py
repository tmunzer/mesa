
### WEB SERVER IMPORTS ###
from flask import Flask
from flask import json
from flask import request

### JUNOS IMPORTS ###
from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from pprint import pprint

### OTHER IMPORTS ###
import requests
from requests.exceptions import HTTPError
import json
from datetime import datetime
import logging as log
import os

###########################
### PARAMETERS
config = open("./config.json", "r").read()
config = json.loads(config)
apitoken = config["apitoken"]
mist_cloud = config["mist_cloud"]
domain = config["domain"]
server_uri = config["server_uri"]
ex_username = config["ex_username"]
ex_pwd = config["ex_pwd"]
ex_conf_trunk_ap = config["ex_conf_trunk_ap"]
ex_conf_default = config["ex_conf_default"]

###########################
### VARS
server_port = 51360
log.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
###########################
### FUNCTIONS
def get_datetime():
    now = datetime.now()
    return now.strftime("%d/%m/%Y %H:%M:%S")

def print_success(message):
    dt = get_datetime()
    log.info("%s - Success: %s"%(dt,message))

def print_error(message):
    dt = get_datetime()
    log.error("%s - Error: %s"%(dt,message))

# Function called when an AP is connected/disconnected
def ap_event(event):
    mac = event["ap"]
    if "site_id" in event:
        level = "sites"
        level_id = event["site_id"]
    else:
        level = "orgs"
        level_id = ["org_id"]

    url = "https://%s/api/v1/%s/%s/devices/search?ap=%s" %(mist_cloud, level, level_id, mac)    
    resp = mist_request(url)
    resp = json.loads(resp)
    if "results" in resp and len(resp["results"]) == 1: 
        ap_info = resp["results"][0]
        lldp_system_name = ap_info["lldp_system_name"]+"."+domain
        lldp_port_desc = ap_info["lldp_port_desc"]
        action = event["type"]
        if action == "AP_CONNECTED":
            ap_connected(mac, lldp_system_name, lldp_port_desc)
        elif action == "AP_DISCONNECTED":
            ap_disconnected(mac, lldp_system_name, lldp_port_desc)

# establish connection with EX switch
def ex_connect(dev, switch):
    try:
        dev.open()
        cu = Config(dev)
        print_success("connected to switch %s" %switch)
        return cu
    except:
        print_error("unable to connect to switch %s" %switch)
        return None

# lock ex configuration
def ex_lock(cu, switch):
    try:
        cu.lock()
        print_success("configuration locked on device %s" %switch)
        return True
    except:
        print_error("unable to lock configuration on device %s" %switch)
        return False

# commit ex configuration
def ex_commit(cu, switch):
    try:
        cu.commit()
        print_success("configuration commited on device %s" %switch)
        return True
    except:
        print_error("unable to commit configuration on device %s" %switch)
        return False

# unlock ex configuration
def ex_unlock(cu, switch):
    try:
        cu.unlock()
        print_success("configuration unlocked on device %s" %switch)
        return True
    except:
        print_error("unable to unlock configuration on device %s" %switch)
        return False

# function called to change the ex configuration
def change_ex_conf(switch, conf):
    dev = Device(host=switch, user=ex_username, passwd=ex_pwd)
    cu = ex_connect(dev, switch)
    if not cu == None:
        cmd_result = ex_lock(cu, switch)
        if cmd_result == True:
            for setconf in conf:        
                try:
                    cu.load(setconf, format='set')
                    print_success("%s" %setconf)
                except:
                    print_error("%s"%setconf)
            ex_commit(cu, switch)
            ex_unlock(cu, switch)
            dev.close()
    
# generate the API request against Mist Cloud to get switch LLDP information 
def mist_request(url):
    headers = {'Content-Type': "application/json", "Authorization": "Token %s" %apitoken}
    try:
        print("Request > GET %s" % url)
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')  # Python 3.6
        print(f'HTTP error description: {resp.json()}')
    except Exception as err:
        print(f'Other error occurred: {err}')  # Python 3.6
    else:
        return resp.content

def replace_port(conf, port_num):
    new_conf = []
    for line in conf:
        new_conf.append(line.replace("<port>", port_num))
    return new_conf

def ap_connected(mac, lldp_system_name, lldp_port_desc):
    print("AP %s connected on switch %s on port %s" %(mac, lldp_system_name, lldp_port_desc))
    conf = replace_port(ex_conf_trunk_ap, lldp_port_desc)
    change_ex_conf(lldp_system_name, conf)

def ap_disconnected(mac, lldp_system_name, lldp_port_desc):
    log.info("AP %s disconnected from switch %s on port %s" %(mac, lldp_system_name, lldp_port_desc))
    conf = replace_port(ex_conf_default, lldp_port_desc)
    change_ex_conf(lldp_system_name, conf)

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











