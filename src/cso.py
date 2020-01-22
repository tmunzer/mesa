from libs import req
from libs import debug
import json

console = debug.Console()

config = open("./config.json").read()
config = json.loads(config)
user = config["cso"]["login"]
password = config["cso"]["password"]
tenant = config["cso"]["tenant"]
host = config["cso"]["host"]
apitoken = {}
url_prefix = "https://%s" %host
port_profile_default = config["cso"]["switchport_conf"]["default"]
port_profile_ap = config["cso"]["switchport_conf"]["ap"]

def _get_apitoken():
    url = "%s/v3/auth/tokens" %url_prefix
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
		        "scope":{
                    "project":{
                        "domain":{
                            "id":"default"
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
        
        console.info("Authentication successful. New api token received (valid until %s)" %apitoken["data"]["token"]["expires_at"])
        print(resp)
        print()
        print(apitoken)

def _get_sites():
    url = "%s/tssm/site" %url_prefix
    headers = {"x-auth-token": apitoken["token"]}
    resp = req.get(url=url, headers=headers)["result"]
    return resp

def _find_site_uuid(site_name):
    sites = _get_sites()
    site_uuid = None
    for site in sites["site"]:
        if site_name in site["fq_name"]:
            site_uuid = site["uuid"]
    print(site_uuid)
    return site_uuid


def _get_devices():
    url = "%s/data-view-central/device" %url_prefix
    headers = {"x-auth-token": apitoken["token"]}
    resp = req.get(url=url, headers=headers)
    return resp["result"]["device"]

def _find_device_uuid(device_name):
    devices = _get_devices()
    device_uuid = None
    for device in devices:
        if device_name in device["fq_name"]:
            device_uuid = device["uuid"]
    print(device_uuid)
    return device_uuid

def _get_device_info(device_uuid):
    url = "%s/data-view-central/device/%s" %(url_prefix, device_uuid)
    headers = {"x-auth-token": apitoken["token"]}
    resp = req.get(url=url, headers=headers)["result"]
    return resp

def _get_port_profile():
    url = "%s/tssm/port-profile" %url_prefix
    headers = {"x-auth-token": apitoken["token"]}
    resp = req.get(url=url, headers=headers)
    return resp["result"]["port-profile"]

def __find_port_profile_uuid(profile_name):
    port_profiles = _get_port_profile()
    port_profile_uuid = None
    for port_profile in port_profiles:
        if profile_name in port_profile["fq_name"]:
            port_profile_uuid = port_profile["uuid"]
    return port_profile_uuid
    

def _get_device_port(switch_uuid):
    url = "%s/data-view-central/device-port?parent_id=%s" %(url_prefix, switch_uuid)
    headers = {"x-auth-token": apitoken["token"]}
    resp = req.get(url=url, headers=headers)["result"]
    return resp

def _get_lan_segments(site_uuid):
    url = "%s/topology-service/lan-segment/_filter" %url_prefix
    headers = {"x-auth-token": apitoken["token"], "Content-Type":"application/json"}
    body = {
        "query":{
            "bool":{
                "must":[{ 
                        "term":{"parent_uuid._raw":"675672e7-7563-4e00-a40d-89154d1ada2f"}
                            
                    }]
                }
            },
            "detail":True
        }
    resp = req.post(url, headers, body)
    print(resp)
    return resp["result"]["lan-segment"]

def _set_switchport_config(switch_uuid, port_name, port_profile_uuid, lan_segment_uuids=[], native_vlan_uuid=None):
    url = "%s/tssm/apply-port-config-association" %url_prefix
    headers = {"x-auth-token": apitoken["token"]}
    body = {
        "input":{
            "port_config_association":[
                {
                    "device_uuid":switch_uuid,
                    "port_name":port_name,
                    "port_configuration":port_profile_uuid,
                    "configuration_type":"profile",
                    "lan_segment":lan_segment_uuids,
                    "native_lan":native_vlan_uuid
                    }
                ]
                }
        }
    resp = req.post(url, headers, body)
    return resp["result"]


def _deploy_switchport_config(switch_uuid, port_name):
    url = "%s/tssm/deploy-port-config-association" %url_prefix
    headers = {"x-auth-token": apitoken["token"]}
    body = {
        "input":{
            "port_config_association":[
                {"device_uuid":switch_uuid,"port_name":port_name}
                ]
            }
        }
    resp = req.post(url, headers, body)
    return resp["result"]

def _find_lan_segments_uuid(vlan_id=None):
    lan_segment_uuid = []
    for lan_segment in lan_segments:
        if vlan_id == None or lan_segment["vlan"] == vlan_id:
            lan_segment_uuid.append(lan_segment["uuid"])
    return lan_segment_uuid


## TESTING ##
hostname = "sw-jn-01.lab.THOMAS_MUN"
action = "connected"
portname="ge-0/0/10"
mysite= hostname.split(".")[1]
myswitch = hostname.split(".")[0]

## ENTRYPOINT ##

_get_apitoken()
site_uuid = _find_site_uuid(mysite)
switch_uuid = _find_device_uuid(myswitch)
lan_segments = _get_lan_segments(site_uuid)

if action == "connected":
    port_profile_uuid = __find_port_profile_uuid(port_profile_ap["port_profile_name"])
    lan_segment_uuids = _find_lan_segments_uuid(None)
    native_vlan_uuid = _find_lan_segments_uuid(port_profile_ap["native_vlan_id"])
    _set_switchport_config(switch_uuid, portname, port_profile_uuid, lan_segment_uuids, native_vlan_uuid[0])
    _deploy_switchport_config(switch_uuid, portname)

elif action == "disconnected":
    port_profile_uuid = __find_port_profile_uuid(port_profile_default["port_profile_name"])
    lan_segment_uuid = _find_lan_segments_uuid(port_profile_default["vlan_id"])
    _set_switchport_config(switch_uuid, portname, port_profile_uuid, lan_segment_uuid)
    _deploy_switchport_config(switch_uuid, portname)

