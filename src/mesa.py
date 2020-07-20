
### WEB SERVER IMPORTS ###
from flask import Flask
from flask import json
from flask import request

from mesa_ctrl import Mesa
from mesa_ctrl_ext import MesaExt
from config import mist_conf
server_uri = mist_conf["server_uri"]
mist_secret = mist_conf["mist_secret"]
from config import external_conf

import hmac, hashlib

if external_conf["enabled"]:
    external_server_uri = external_conf["server_uri"]
    external_org_id = external_conf["org_id"]
    external_secret = external_conf["X-ClientApiKey"]
else:
    external_server_uri = "/external"

from mongo import MesaDB
mongo_host = "mist-mongo"
#mongo_host = None
mesa_db = MesaDB(server=mongo_host)


###########################
# VARS
server_port = 51360


###########################
# ENTRY POINT

active_threads = 1
app = Flask(__name__)


@app.route(server_uri, methods=["POST"])
def postJsonHandler():
    signature = request.headers['X-Mist-Signature'] if "X-Mist-Signature" in request.headers else None
    content = request.get_json()    
    key = str.encode(mist_secret)
    message = request.data
    digester = hmac.new(key, message, hashlib.sha1).hexdigest()
    print("sig {0}".format(signature))
    print("dig {0}".format(digester))
    global active_threads
    global mesa_db
    if "events" in content:
        for event in content["events"]:
            if "type" in event and (event["type"] == "AP_CONNECTED" or event["type"] == "AP_DISCONNECTED" or event["type"] == "AP_RESTARTED"):
                thread_id = active_threads
                if active_threads == 1000:
                    active_threads = 1
                else:
                    active_threads += 1
                Mesa(event, thread_id, mesa_db).start()
    return '', 200

@app.route(external_server_uri, methods=["POST"])
def postClearpassHandler():
    secret = request.headers['X-ClientApiKey'] if "X-ClientApiKey" in request.headers else None
    if secret == external_secret or external_secret == None:
        if external_conf["enabled"]:
            global active_threads
            global mesa_db
            content = request.get_json()
            event={}
            if "switch_mac" in content: event["mac"] = content["switch_mac"] 
            else: return "switch_mac missing", 500

            if "switch_port" in content: event["port"] = content["switch_port"].split(".")[0]
            else: return "switch_port missing", 500
            
            event["org_id"] = external_org_id
            if "type" in content :
                event["type"] = content["type"]
                if event["type"] == "AP_CONNECTED" or event["type"] == "AP_DISCONNECTED" or event["type"] == "AP_RESTARTED":
                    thread_id = active_threads
                    if active_threads == 1000:
                        active_threads = 1
                    else:
                        active_threads += 1
                    MesaExt(event, thread_id, mesa_db).start()
            return '', 200
    return '',401

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=server_port)
