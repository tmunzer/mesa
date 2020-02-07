
###########################
### IMPORTS
from libs import req
import time
###########################
### LOADING SETTINGS
from config import site_outage
from config import mist_conf

apitoken = mist_conf["apitoken"]
mist_cloud = mist_conf["mist_cloud"]
timeout_site_outage = site_outage["outage_timeout"]
timeout_ap_removed = site_outage["removed_timeout"]
min_disconnected_percentage = site_outage["min_percentage"] / 100

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
            return True
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
                return False
            # otherwise, no outage detected, processing the message
            else: 
                percentage_outaged_aps = round(percentage_outaged_aps * 100) 
                console.info("No site outage detected. %s%% of APs disconnected in less than %s seconds: Processing the message" %(percentage_outaged_aps, timeout_site_outage))
                return False
    else:
        return True


# Function called when an AP is connected/disconnected
def site_online(level, level_id, ap_mac):
    url = "https://%s/api/v1/%s/%s/stats/devices" %(mist_cloud, level, level_id)    
    headers = {'Content-Type': "application/json", "Authorization": "Token %s" %apitoken}
    resp = req.get(url, headers=headers)
    if "result" in resp:
        return _process_timestamp(resp["result"])
    