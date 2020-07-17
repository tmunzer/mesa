
########################
# mist_conf:
# Configuration to receive webhooks from Mist Cloud and to send API 
# requests to Mist Cloud
# 
# apitoken:             apitoken from Mist Cloud to sent API requests
# mist_cloud:           api.mist.com if you are using US Cloud, or 
#                       api.eu.mist.com if you are using EU Cloud
# server_uri:           uri where you want to receive wehbooks messages
#                       on this server. 
# site_id_ignored:      Array of site ids you want to ignore (MESA will 
#                       not change the port configuration on these sites)
mist_conf={
    "apitoken": "xxxxxxxxxxxxxxx",
    "mist_cloud": "api.mist.com",
    "server_uri": "/mist-webhooks",
    "site_id_ignored": []
}

log_level = 6
########################
# external_conf:
# allow external systems to send trigger to MESA script. The message recieved by 
# the script must be a JSON payload with the switch mac address, the switch
# port to reconfigure and the event:
# {"switch_mac": "2c21311cbeef", "switch_port": "ge-0/0/0", "type":"AP_DISCONNECTED"}
# or 
# {"switch_mac": "2c21311cbeef", "switch_port": "ge-0/0/0", "type":"AP_CONNECTED"}
#
# enabled: wether or not the script access exteral sources
# server_uri: uri wehre you want to received the messages on this server
# org_id: you Mist org_id. Used to retrieve the switch location and information
external_conf = {
    "enabled": False,
    "server_uri": "/external",
    "org_id": "xxxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxxxx"
}

########################
# slack_conf
# if the script has to send logs to slack webhook. To get the Slack 
# Webhook URL, please go to https://api.slack.com/app
# enabled:      if you want to enable Slack reporting
# url:          URL of your slack webhook
slack_conf = {
    "enabled" : False,
    "url": "https://hooks.slack.com/services/XXXXXXXXX/XXXXXXXXX"
}
msteams_conf = {
    "enabled" : False,
    "url": "https://outlook.office.com/webhook/XXXXXXXXX/IncomingWebhook/XXXXXXXXX"
}
########################
# disconnect_validation
# Indicate the script if the AP_DISCONNECT message has to be verified.
# method: Method to use to valide the AP_DISCONNECT. Possible methods are
# - none:   no validation. Will change the switchport confiugration back
#           to the default when the message is received
# - outage: check if the is a site outage by looking at the number of APs
#           disconnected during the last XX.
# - lldp:   retrieve the lldp information on the switchport (trough Mist
#           APIs) to check if it's still UP, and if the MAC address is the
#           MAC address of the AP.
#           WARNING: For lldp method, the EX switch must be assigned to the
#                    same site as the APs connected to it!!!
# wait_time:        Time to wait (in seconds) before start the test to 
#                   detect if it's one AP disconnected or a general outage
#                   on the site(in this case, no modification will be done 
#                   on the sites)
disconnect_validation = {
    "method": "lldp",
    "wait_time": 30
} 

########################
# site_outage_aps
# logic to detect if the message is received because the AP is really
# disconnected from the network or if all the APs from the site are 
# reported as disconnected. This method is looking at the number of APs
# disconnected during the last XX seconds
# In the 1st case, the switchport will be revert back to its default
# configuration.
# In the 2nd case, the switchport will not be revert back.
# enable:           enable or not the outage detection logic
# outage_timeout:   maximum duration (in seconds) between the first and
#                   the last AP disconnection to detect the outage. 
# removed_timeout:  if the device disconnection is older that "removed_timeout"
#                   (seconds), MESA will not count it in the number of devices
#                   present on this site (AP physically removed from the site 
#                   but not from the Mist UI)
# min_percentage:   Percentage (0-100) of devices that have to be disconnected
#                   for less than "outage_timeout" to consider the site as 
#                   outaged and not process the message
site_outage_aps = {    
    "outage_timeout": 30,
    "removed_timeout": 85400,
    "min_percentage": 50
}

########################
# configuration_method: 
# Indicate the switch how the process to configure the switchport
#
# value "mist":     The script will use Mist to configure the switchport.
#                   You'll have to set the "mist_method" settings below
# value "cso":      The script will use CSO to configure the switchport. 
#                   You'll have to set the "cso_method" settings below
# value "ex":       The script will use pyez to configure the switchport 
#                   directly on the switch. The script must be able to 
#                   resolve the switch FQDN (possible to add the domain 
#                   name to the switch hostname) and reach it.
configuration_method= "mist"

########################
# mist_method: 
# Parameters used to configure the switchport through Mist Wired Assurance
#
# profile_default:  Mist port profile to apply when there is no AP connected  
#                   to the switch port
# profile_ap:       Mist port profile to apply when there is an AP connected
#                   to the switch port
# conf_ap:          Mist port profile to deploy to the switch if not alreay
#                   present
mist_method={
    "profile_default":"default_profile",
    "conf_ap":"ap_profile",
    "conf_ap": {
                "name": "profile_name",
                "mode": "trunk",
                "disabled": False,
                "port_network": "vlan_name",
                "stp_edge": False,
                "all_networks": True,
                "networks": [],
                "port_auth": None
            }
}

########################
# ex_method: 
# Parameters used to configure the switchport directly on the switch
#
# domain_name:      domain name to add to the switch name. Used by the 
#                   script to resolve the switch FQDN
# ex_username:      switch username
# ex_pwd:           switch password
# ex_conf_trunk_ap: "set" commands sent by the script to configure the
#                   switchport when an AP is connected to it. Be sure 
#                   to repalce the port name with <port>. 
# ex_conf_default: "set" commands sent by the script to configure the 
#                   switchport when an AP is removed from it. Be sure 
#                   to repalce the port name with <port>. 
ex_metod= {
    "domain_name": "mydomain.corp",
    "ex_username": "root",
    "ex_pwd": "mybadpassword",
    "ex_conf_trunk_ap": [
        "delete protocols dot1x authenticator interface <port>",
        "set interfaces <port> native-vlan-id 42",
        "set interfaces <port> unit 0 family ethernet-switching interface-mode trunk",
        "set interfaces <port> unit 0 family ethernet-switching vlan members all"
    ],
    "ex_conf_default": [
        "set protocols dot1x authenticator interface <port>",
        "set protocols dot1x authenticator interface <port> mac-radius restrict",
        "set protocols dot1x authenticator interface <port> supplicant multiple",
        "set protocols dot1x authenticator interface <port> retries 2",
        "set protocols dot1x authenticator interface <port> quiet-period 3",
        "set protocols dot1x authenticator interface <port> transmit-period 5",
        "set protocols dot1x authenticator interface <port> mac-radius",
        "set protocols dot1x authenticator interface <port> reauthentication 1800",
        "set protocols dot1x authenticator interface <port> supplicant-timeout 5",
        "set protocols dot1x authenticator interface <port> server-timeout 30",
        "set protocols dot1x authenticator interface <port> maximum-requests 2",
        "set protocols dot1x authenticator interface <port> guest-vlan 12",
        "set protocols dot1x authenticator interface <port> server-fail vlan-name 12",
        "delete interfaces <port> native-vlan-id",
        "delete interfaces <port> unit 0 family ethernet-switching interface-mode trunk",
        "delete interfaces <port> unit 0 family ethernet-switching vlan members all"
    ]
}

########################
# cso_method: 
# Parameters used to configure the switchport through CSO
#
# login:        CSO username
# password:     CSO password
# tenant:       CSO TENANT
# host:         CSO hostname
# conf_ap:      Configuration deployed on the switchport when
#               an AP is connected to it. 
#               This must contain the Port Profile Name from 
#               CSO and the vlan_id (for Access port) or the 
#               native_vlan_id (from Trunk port)
# default_ap:   Configuration deployed on the switchport when
#               an AP is disconnected from it. 
#               This must contain the Port Profile Name from 
#               CSO and the vlan_id (for Access port) or the 
#               native_vlan_id (from Trunk port)
cso_method= {
        "login": "user@domain.corp",
        "password": "mybadpassword",
        "tenant": "MY_CROP",
        "host": "contrail-juniper.net",
        "conf_default": {
            "port_profile_name": "generic-access",
            "vlan_id": 12
        },
        "conf_ap": {
            "port_profile_name": "generic-trunk",
            "native_vlan_id": 11
        }
    }
