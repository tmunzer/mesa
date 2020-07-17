
### WEB SERVER IMPORTS ###
from flask import Flask
from flask import json
from flask import request

from mesa_ctrl import Mesa
from mesa_ctrl_ext import MesaExt
from config import mist_conf
server_uri = mist_conf["server_uri"]
from config import external_conf

if external_conf["enabled"]:
    external_server_uri = external_conf["server_uri"]
    external_org_id = external_conf["org_id"]
else:
    external_server_uri = "external"

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
    global active_threads
    global mesa_db
    content = request.get_json()
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
    if external_conf["enabled"]:
        global active_threads
        global mesa_db
        content = request.get_json()
        event={}
        event["mac"] = content["switch_mac"] if "switch_mac" in content else None
        event["port"] = content["switch_port"] if "switch_port" in content else None
        event["source"] = "clearpass"
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
    else: return '',404

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=server_port)
