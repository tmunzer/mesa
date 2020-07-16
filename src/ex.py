
### JUNOS IMPORTS ###
from jnpr.junos import Device
from jnpr.junos.utils.config import Config

### CONF IMPORT ###
from config import ex_method

###########################
### LOGGING SETTINGS
console = None

###########################
### PARAMETERS
ex_username = ex_method["username"]
ex_pwd = ex_method["password"]
domain_name = ex_method["domain_name"]
ex_conf_trunk_ap = ex_method["conf_trunk_ap"]
ex_conf_default = ex_method["conf_default"]


###########################
### FUNCTIONS

def _replace_port(conf, port_num):
    new_conf = []
    for line in conf:
        new_conf.append(line.replace("<port>", port_num))
    return new_conf

# establish connection with EX switch
def _ex_connect(level_name, dev, switch, thread_id):
    try:
        dev.open()
        cu = Config(dev)
        console.info("SITE: %s | SWITCH: %s | Connected" %(level_name, switch))
        return cu
    except:
        console.error("SITE: %s | SWITCH: %s | Unable to connect" %(level_name, switch))
        return None

# lock ex configuration
def _ex_lock(level_name, cu, switch, thread_id):
    try:
        cu.lock()
        console.info("SITE: %s | SWITCH: %s | Configuration locked" %(level_name, switch))
        return True
    except:
        console.error("SITE: %s | SWITCH: %s | Unable to lock configuration" %(level_name, switch))
        return False

# commit ex configuration
def _ex_commit(level_name, cu, switch, thread_id):
    try:
        cu.commit()
        console.info("SITE: %s | SWITCH: %s | Configuration commited" %(level_name, switch))
        return True
    except:
        console.error("SITE: %s | SWITCH: %s | Unable to commit configuration" %(level_name, switch))
        return False

# unlock ex configuration
def _ex_unlock(level_name, cu, switch, thread_id):
    try:
        cu.unlock()
        console.info("SITE: %s | SWITCH: %s | Configuration unlocked" %(level_name, switch))
        return True
    except:
        console.error("SITE: %s | SWITCH: %s | Unable to unlock configuration" %(level_name, switch))
        return False

# function called to change the ex configuration
def _change_ex_conf(level_name, switch, conf, thread_id):
    dev = Device(host=switch, user=ex_username, passwd=ex_pwd)
    cu = _ex_connect(level_name, dev, switch, thread_id)
    if not cu == None:
        cmd_result = _ex_lock(level_name, cu, switch, thread_id)
        if cmd_result == True:
            for setconf in conf:        
                try:
                    cu.load(setconf, format='set')
                    console.notice("%s" %setconf)
                except:
                    console.error("%s"%setconf)
            _ex_commit(level_name, cu, switch, thread_id)
            _ex_unlock(level_name, cu, switch, thread_id)
            dev.close()

def ap_connected(mac, lldp_system_name, lldp_port_desc, o_console, thread_id=None, level_name=None):
    global console 
    console = o_console
    lldp_system_name = "%s.%s" %(lldp_system_name, domain_name)
    console.info("SITE: %s | SWITCH: %s | PORT: %s | AP %s connected" %(level_name, lldp_system_name, lldp_port_desc, mac), thread_id)
    conf = _replace_port(ex_conf_trunk_ap, lldp_port_desc)
    _change_ex_conf(level_name, lldp_system_name, conf, thread_id)

def ap_disconnected(mac, lldp_system_name, lldp_port_desc, o_console, thread_id=None, level_name=None):
    global console 
    console = o_console
    lldp_system_name = "%s.%s" %(lldp_system_name, domain_name)
    console.info("SITE: %s | SWITCH: %s | PORT: %s | AP %s disconnected" %(level_name, lldp_system_name, lldp_port_desc, mac), thread_id)
    conf = _replace_port(ex_conf_default, lldp_port_desc)
    _change_ex_conf(level_name, lldp_system_name, conf, thread_id)
    