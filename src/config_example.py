
########################
# mist_conf:
# Configuration to receive webhooks from Mist Cloud and to send API 
# requests to Mist Cloud
# 
# apitoken:         apitoken from Mist Cloud to sent API requests
# mist_cloud:       api.mist.com if you are using US Cloud, or 
#                   api.eu.mist.com if you are using EU Cloud
# server_uri:       uri where you want to receive wehbooks messages
#                   on this server. 
mist_conf={
    "apitoken": "xxxxxxxxxxxxxxx",
    "mist_cloud": "api.mist.com",
    "server_uri": "/mist-webhooks",
}

########################
# configuration_method: 
# Indicate the switch how the process to configure the switchport
#
# value "cso":      The script will use CSO to configure the switchport. 
#                   You'll have to set the "cso" settings bellow
# value "ex":       The script will use pyez to configure the switchport 
#                   directly on the switch. The script must be able to 
#                   resolve the switch FQDN (possible to add the domain 
#                   name to the switch hostname) and reach it.
configuration_method= "cso"

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
#               This must contains the Port Profile Name from 
#               CSO and the vlan_id (for Access port) or the 
#               native_vlan_id (from Trunk port)
# default_ap:   Configuration deployed on the switchport when
#               an AP is disconnected from it. 
#               This must contains the Port Profile Name from 
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
            "native_vlan_id": 42
        }
    }
