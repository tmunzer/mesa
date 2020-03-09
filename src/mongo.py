from pymongo import MongoClient
###########################
### LOGGING SETTINGS
try:
    from config import log_level
except:
    log_level = 6
finally:
    from libs.debug import Console
console = Console(log_level)


class MesaDB():
    
    def __init__(self, server="localhost"):
        try:
            self.client = MongoClient(server)
            if not "mesa" in self.client.list_database_names():
                console.debug("No \"mesa\" database for now...")
        except:
            console.critical("Unable to get access to MongoDB... Exiting...")
            exit(255)
        self.db = self.client["mesa"]
        self.db_devices = self.db["devices_ports"]

    def _add_db_device(self, ap_mac):
        db_device = self.db_devices.insert_one({"ap_mac": ap_mac})
        return self.db_devices.find_one({"_id": db_device.inserted_id})

    def update_db_device(self, ap_mac, org_id, site_id, connected, lldp_system_name=None, lldp_port_desc=None):
        db_device = self.db_devices.find_one({"ap_mac": ap_mac})
        if not db_device:
            db_device = self._add_db_device(ap_mac)
        db_device["org_id"] = org_id
        db_device["site_id"] = site_id
        db_device["connected"] = connected
        db_device["lldp_system_name"] = lldp_system_name
        db_device["lldp_port_desc"] = lldp_port_desc
        self.db_devices.update_one({"ap_mac": ap_mac}, {"$set":db_device})

    def get_db_device(self, ap_mac):
        return self.db_devices.find_one({"ap_mac": ap_mac})

    def get_previous_lldp_info(self, ap_mac):
        db_device = self.get_db_device(ap_mac)
        if db_device and  "lldp_system_name" in db_device and "lldp_port_desc":
            return db_device
        else:
            return None