### IMPORTS ###
from libs import req
import json

### CONF IMPORT ###
from config import cso_method

###########################
# LOGGING SETTINGS
console = None
###########################
# PARAMETERS
user = cso_method["login"]
password = cso_method["password"]
tenant = cso_method["tenant"]
host = cso_method["host"]
port_profile_default = cso_method["conf_default"]
port_profile_ap = cso_method["conf_ap"]

###########################
# VARIABLES
apitoken = {}
url_prefix = "https://%s" % host

###########################
# FUNCTIONS

# get API token from CSO


def _get_apitoken():
    url = "%s/v3/auth/tokens" % url_prefix
    body = {
        "auth": {
            "identity": {
                "methods": ["password"],
                "password": {
                    "user": {
                        "domain": {"id": "default"},
                        "name": user,
                        "password": password
                    }
                }
            },
            "scope": {
                "project": {
                    "domain": {
                        "id": "default"
                    },
                    "name": tenant
                }
            }
        }
    }
    resp = req.post(url=url, body=body)
    if resp["status_code"] == 200 or resp["status_code"] == 201:
        apitoken["token"] = resp["headers"]["X-Subject-Token"]
        apitoken["data"] = resp["result"]
        console.info("CSO Authentication successful")
    else:
        console.critical(
            "Unable to get access to CSO. Please check your authentication settings!")

# Devices


def _get_devices():
    url = "%s/data-view-central/device" % url_prefix
    headers = {"x-auth-token": apitoken["token"]}
    resp = req.get(url=url, headers=headers)
    return resp["result"]["device"]


def _find_device_uuid(site_name, device_name):
    devices = _get_devices()
    device_uuid = None
    for device in devices:
        if device_name in device["fq_name"]:
            device_uuid = device["uuid"]
    if device_uuid == None:
        console.error(
            "CSO SITE: %s | Unable to find the device %s in your CSO account. The configuration will fail, Stopping the prorcess..." %(site_name, device_name))
    return device_uuid


def _get_device_info(device_uuid):
    url = "%s/data-view-central/device/%s" % (url_prefix, device_uuid)
    headers = {"x-auth-token": apitoken["token"]}
    resp = req.get(url=url, headers=headers)["result"]
    return resp

# Port Profiles


def _get_port_profile():
    url = "%s/tssm/port-profile" % url_prefix
    headers = {"x-auth-token": apitoken["token"]}
    resp = req.get(url=url, headers=headers)
    return resp["result"]["port-profile"]


def __find_port_profile_uuid(site_name, profile_name):
    port_profiles = _get_port_profile()
    port_profile_uuid = None
    for port_profile in port_profiles:
        if profile_name in port_profile["fq_name"]:
            port_profile_uuid = port_profile["uuid"]
    if port_profile_uuid == None:
        console.error(
            "CSO SITE: %s | Unable to find the port profile %s in your CSO account. The configuration will fail, Stopping the prorcess..." % (site_name, profile_name))
    return port_profile_uuid

# Device Ports


def _get_device_port(switch_uuid):
    url = "%s/data-view-central/device-port?parent_id=%s" % (
        url_prefix, switch_uuid)
    headers = {"x-auth-token": apitoken["token"]}
    resp = req.get(url=url, headers=headers)["result"]
    return resp

# LAN segments


def _get_lan_segments(site_uuid):
    url = "%s/topology-service/lan-segment/_filter" % url_prefix
    headers = {"x-auth-token": apitoken["token"],
               "Content-Type": "application/json"}
    body = {
        "query": {
            "bool": {
                "must": [{
                    "term": {"parent_uuid._raw": site_uuid}

                }]
            }
        },
        "detail": True
    }
    resp = req.post(url, headers, body)
    return resp["result"]["lan-segment"]


def _find_lan_segments_uuid(site_name, lan_segments, vlan_id=None):
    lan_segment_uuid = []
    for lan_segment in lan_segments:
        if vlan_id == None or lan_segment["vlan"] == vlan_id:
            lan_segment_uuid.append(lan_segment["uuid"])
    if len(lan_segment_uuid) == 0:
        console.error(
            "CSO SITE: %s | Unable to find the vlan %s. The configuration will fail, Stopping the prorcess..." %(site_name, vlan_id))        
    return lan_segment_uuid

# Configure swtich port


def _set_switchport_config(site_name, switch_uuid, port_name, port_profile_uuid, lan_segment_uuids=[], native_vlan_uuid=None, switch_name="N/A", profile_name="N/A", lan_segments="N/A", native_lan="N/A"):
    url = "%s/tssm/apply-port-config-association" % url_prefix
    headers = {"x-auth-token": apitoken["token"]}
    body = {
        "input": {
            "port_config_association": [
                {
                    "device_uuid": switch_uuid,
                    "port_name": port_name,
                    "port_configuration": port_profile_uuid,
                    "configuration_type": "profile",
                    "lan_segment": lan_segment_uuids,
                    "native_lan": native_vlan_uuid
                }
            ]
        }
    }
    console.notice("""CSO SITE: %s | SWITCH: %s | PORT: %s | Sending request to CSO to apply new configuration:
    Port profile name: %s
    Lan Segments: %s
    Native VLAN: %s """ % (site_name, switch_name, port_name, profile_name, lan_segments, native_lan))

    console.slack.set_conf("Port profile name: %s\r\nLan Segments: %s\r\nNative VLAN: %s" %(profile_name, lan_segments, native_lan))

    resp = req.post(url, headers, body)
    return resp["result"]

# Deploy and Commit switch configuration


def _deploy_switchport_config(site_name, switch_uuid, port_name, switch_name):
    url = "%s/tssm/deploy-port-config-association" % url_prefix
    headers = {"x-auth-token": apitoken["token"]}
    body = {
        "input": {
            "port_config_association": [
                {"device_uuid": switch_uuid, "port_name": port_name}
            ]
        }
    }
    console.notice("CSO SITE: %s | SWITCH: %s | PORT: %s | Sending request to CSO to deploy new configuration" % (
        site_name, switch_name, port_name))

    console.slack.set_status("Success (deployed through CSO)")

    resp = req.post(url, headers, body)
    return resp["result"]


def _init(hostname):
    site_name = hostname.split(".")[1]
    switch_name = hostname.split(".")[0]

    _get_apitoken()
    switch_uuid = _find_device_uuid(site_name, switch_name)    
    if switch_uuid:
        lan_segments = _get_lan_segments(switch_uuid)
        return [site_name, switch_uuid, lan_segments]
    else:
        return [site_name, switch_uuid, None]


def ap_connected(mac, lldp_system_name, lldp_port_desc, o_console):
    global console 
    console = o_console
    site_name, switch_uuid, lan_segments = _init(lldp_system_name)
    if switch_uuid:
        port_profile_uuid = __find_port_profile_uuid(site_name, port_profile_ap["port_profile_name"])
        if port_profile_uuid:
            lan_segment_uuids = _find_lan_segments_uuid(site_name, lan_segments, None)
            native_vlan_uuid = _find_lan_segments_uuid(site_name, lan_segments, port_profile_ap["native_vlan_id"])
            if len(native_vlan_uuid) == 1 :
                _set_switchport_config(site_name, switch_uuid, lldp_port_desc, port_profile_uuid, lan_segment_uuids,
                                native_vlan_uuid[0], lldp_system_name, port_profile_ap["port_profile_name"], "All", port_profile_ap["native_vlan_id"])
                _deploy_switchport_config(site_name, switch_uuid, lldp_port_desc, lldp_system_name)


def ap_disconnected(mac, lldp_system_name, lldp_port_desc, o_console):
    global console 
    console = o_console
    site_name, switch_uuid, lan_segments = _init(lldp_system_name)
    if switch_uuid:
        port_profile_uuid = __find_port_profile_uuid(site_name, port_profile_default["port_profile_name"])
        if port_profile_uuid:
            lan_segment_uuid = _find_lan_segments_uuid(site_name, lan_segments, port_profile_default["vlan_id"])
            if len(lan_segment_uuid) == 1 :
                _set_switchport_config(site_name, switch_uuid, lldp_port_desc, port_profile_uuid,
                                    lan_segment_uuid, None, lldp_system_name, port_profile_default["port_profile_name"],port_profile_default["vlan_id"])
                _deploy_switchport_config(site_name, switch_uuid, lldp_port_desc, lldp_system_name)
