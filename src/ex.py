
### JUNOS IMPORTS ###
from jnpr.junos import Device
from jnpr.junos.utils.config import Config

### CONF IMPORT ###
from config import ex_metod

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
### PARAMETERS
ex_username = ex_metod["username"]
ex_pwd = ex_metod["password"]
domain_name = ex_metod["domain_name"]
ex_conf_trunk_ap = ex_metod["conf_trunk_ap"]
ex_conf_default = ex_metod["conf_default"]


###########################
### FUNCTIONS

def _replace_port(conf, port_num):
    new_conf = []
    for line in conf:
        new_conf.append(line.replace("<port>", port_num))
    return new_conf

# establish connection with EX switch
def _ex_connect(dev, switch):
    try:
        dev.open()
        cu = Config(dev)
        console.notice("SWITCH: %s | Connected" %switch)
        return cu
    except:
        console.error("SWITCH: %s | Unable to connect" %switch)
        return None

# lock ex configuration
def _ex_lock(cu, switch):
    try:
        cu.lock()
        console.notice("SWITCH: %s | Configuration locked" %switch)
        return True
    except:
        console.error("SWITCH: %s | Unable to lock configuration" %switch)
        return False

# commit ex configuration
def _ex_commit(cu, switch):
    try:
        cu.commit()
        console.notice("SWITCH: %s | Configuration commited" %switch)
        return True
    except:
        console.error("SWITCH: %s | Unable to commit configuration" %switch)
        return False

# unlock ex configuration
def _ex_unlock(cu, switch):
    try:
        cu.unlock()
        console.notice("SWITCH: %s | Configuration unlocked" %switch)
        return True
    except:
        console.error("SWITCH: %s | Unable to unlock configuration" %switch)
        return False

# function called to change the ex configuration
def _change_ex_conf(switch, conf):
    dev = Device(host=switch, user=ex_username, passwd=ex_pwd)
    cu = _ex_connect(dev, switch)
    if not cu == None:
        cmd_result = _ex_lock(cu, switch)
        if cmd_result == True:
            for setconf in conf:        
                try:
                    cu.load(setconf, format='set')
                    console.notice("%s" %setconf)
                except:
                    console.error("%s"%setconf)
            _ex_commit(cu, switch)
            _ex_unlock(cu, switch)
            dev.close()

def ap_connected(mac, lldp_system_name, lldp_port_desc):
    lldp_system_name = "%s.%s" %(lldp_system_name, domain_name)
    console.info("SWITCH: %s | PORT: %s | AP %s connected" %(lldp_system_name, lldp_port_desc, mac))
    conf = _replace_port(ex_conf_trunk_ap, lldp_port_desc)
    _change_ex_conf(lldp_system_name, conf)

def ap_disconnected(mac, lldp_system_name, lldp_port_desc):
    lldp_system_name = "%s.%s" %(lldp_system_name, domain_name)
    console.info("SWITCH: %s | PORT: %s | AP %s disconnected" %(mac, lldp_system_name, lldp_port_desc, mac))
    conf = _replace_port(ex_conf_default, lldp_port_desc)
    _change_ex_conf(lldp_system_name, conf)
    