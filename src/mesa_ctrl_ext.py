### IMPORTS ###
import lldp_detection
import outage_detection
from config import slack_conf
from config import msteams_conf
from config import configuration_method
from config import disconnect_validation
from config import mist_conf
### OTHER IMPORTS ###
import json
from libs import req
import os
import time
from threading import Thread


###########################
# LOADING SETTINGS

apitoken = mist_conf["apitoken"]
mist_cloud = mist_conf["mist_cloud"]
site_id_ignored = mist_conf["site_id_ignored"]
disconnect_validation_method = disconnect_validation["method"]
disconnect_validation_wait_time = disconnect_validation["wait_time"]
if "wait_for_cloud_update" in mist_conf:
    wait_for_cloud_update = mist_conf["wait_for_cloud_update"]
else:
    wait_for_cloud_update = 60
###########################
# LOGGING SETTINGS
try:
    from config import log_level
except:
    log_level = 6
finally:
    from libs.debug import Console
console = Console(log_level, slack_conf, msteams_conf, configuration_method)

###########################
### METHODS IMPORT ###
if configuration_method == "cso":
    import cso
elif configuration_method == "ex":
    import ex
elif configuration_method == "mist":
    import mist
else:
    print("Error in the configuration file. Please check the configuration_method variable! Exiting...")
    exit(255)

###########################
# CLASS MESA

class MesaExt(Thread):

    def __init__(self, event, thread_id, mesa_db):
        Thread.__init__(self)
        self.event = event
        self.thread_id = thread_id
        self.mesa_db = mesa_db

    def run(self):
        event = self.event
        switch_mac = event["mac"]
        switch_port = event["port"]
        ap_mac = event["ap_mac"] if "ap_mac" in event else None
        url = "https://{0}/api/v1/orgs/{1}/inventory?mac={2}".format(mist_cloud, event["org_id"], switch_mac)
        headers = {'Content-Type': "application/json",
                "Authorization": "Token %s" % apitoken}
        resp = req.get(url, headers=headers)
        if resp and "result" in resp:
            switch = resp["result"][0]

        switch_name = switch["name"]
        if "site_id" in switch:
            level = "sites"
            level_id = switch["site_id"]
            org_id = switch["org_id"]
            if "site_name" in event:
                level_name = event["site_name"]
            else:
                level_name = "no site name"
        else:
            level = "orgs"
            level_id = event["org_id"]
            org_id = event["org_id"]
            level_name = "ROOT_ORG"
        action = event["type"]
        if level_id in site_id_ignored:
            console.info("EXTERNAL | MIST SITE: {0} | RECEIVED message {1} on switch {2} port {3} but this site should be ignored. Discarding the message...".format(level_name, action, switch_name, switch_port), self.thread_id)                
        else:
            console.notice("EXTERNAL | MIST SITE: {0} | RECEIVED message {1} on switch {2} port {3}.".format(level_name, action, switch_name, switch_port), self.thread_id)            
            self._route_request(action, org_id, level, level_id, level_name, ap_mac, switch_name, switch_port, True)   

    def _disconnect_validation(self, level, level_id, level_name, ap_mac, lldp_system_name, lldp_port_desc):
        if disconnect_validation_method == "outage":
            console.info("Pausing for %s seconds to check possible outage on %s %s" % (disconnect_validation_wait_time, level, level_id), self.thread_id)
            time.sleep(disconnect_validation_wait_time)
            return outage_detection.site_online(level, level_id, level_name, ap_mac, console, self.thread_id)
        elif disconnect_validation_method == "lldp":
            console.info("Pausing for %s seconds to check possible outage on %s %s" % (disconnect_validation_wait_time, level, level_id), self.thread_id)
            time.sleep(disconnect_validation_wait_time)
            return lldp_detection.ap_disconnected(level, level_id, level_name, ap_mac, lldp_system_name, lldp_port_desc, disconnect_validation_wait_time, console, self.thread_id)
        else:
            return True


    def _route_request(self, action, org_id, level, level_id, level_name, ap_mac, lldp_system_name, lldp_port_desc, force=False):
        if configuration_method == "cso":
            configuration_route = cso
        elif configuration_method == "ex":
            configuration_route = ex
        elif configuration_method == "mist":
            configuration_route = mist
        else:
            console.critical("Unable to find the switchport configuration method in the configuration file...", self.thread_id)
        
        if action == "AP_CONNECTED":      
            configuration_route.ap_connected(lldp_system_name, lldp_port_desc, console, self.thread_id, level_name, level_id)
            self.mesa_db.update_db_device(ap_mac, org_id, level_id, True, lldp_system_name, lldp_port_desc)
            console.send_message(self.thread_id)

        elif action == "AP_DISCONNECTED":            
            if force:
                disconnect_validated = True
            else:
                disconnect_validated = self._disconnect_validation(level, level_id, level_name, ap_mac, lldp_system_name, lldp_port_desc)
            if disconnect_validated == True:
                configuration_route.ap_disconnected(lldp_system_name, lldp_port_desc, console, self.thread_id, level_name, level_id)
                self.mesa_db.update_db_device(ap_mac, org_id, level_id, False, lldp_system_name, lldp_port_desc)
                console.send_message(self.thread_id)

        elif action == "AP_RESTARTED":
            previous_device_state = self.mesa_db.get_previous_lldp_info(ap_mac)
            if not previous_device_state:
                console.warning("AP %s restarted, but the previous value is not in the DB... Processing the message as a AP_CONNECTED message only..." % (ap_mac), self.thread_id)
                self._route_request("AP_CONNECTED", org_id, level, level_id, level_name, ap_mac, lldp_system_name, lldp_port_desc, True)

            else:
                console.debug("Previous LLDP information: %s | %s" % (previous_device_state["lldp_system_name"], previous_device_state["lldp_port_desc"]), self.thread_id)
                console.debug("Current LLDP information : %s | %s" % (lldp_system_name, lldp_port_desc), self.thread_id)
                if lldp_system_name != previous_device_state["lldp_system_name"] or lldp_port_desc != previous_device_state["lldp_port_desc"]:
                    self._route_request("AP_DISCONNECTED", org_id, level, level_id, level_name, ap_mac, previous_device_state["lldp_system_name"], previous_device_state["lldp_port_desc"], True)                    
                    console.add_message(5, "MIST SITE: %s | RECEIVED message AP_RESTARTED for AP %s" %(level_name, ap_mac), self.thread_id)                    
                    self._route_request("AP_CONNECTED", org_id, level, level_id, level_name, ap_mac, lldp_system_name, lldp_port_desc, True)
                else:
                    console.do_not_send_message(self.thread_id)
                    console.info("AP %s restarted, but switchport didn't change... Discarding the message..." % (ap_mac), self.thread_id)




