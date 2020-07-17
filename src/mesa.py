
### WEB SERVER IMPORTS ###
import sys
from mongo import MesaDB
from flask import Flask
from flask import json
from flask import request

from mesa_ctrl import Mesa

from config import mist_conf
server_uri = mist_conf["server_uri"]


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

@app.route("cleasrpass", methods=["POST"])
def postClearpassHandler():
    global active_threads
    global mesa_db
    content = request.get_json()
    event={}
    event["mac"] = content["switch_mac"] if "switch_mac" in content else None
    event["port"] = content["switch_port"] if "switch_port" in content else None
    event["source"] = "clearpass"
    if "type" in event and (event["type"] == "AP_CONNECTED" or event["type"] == "AP_DISCONNECTED" or event["type"] == "AP_RESTARTED"):
        thread_id = active_threads
        if active_threads == 1000:
            active_threads = 1
        else:
            active_threads += 1
        Mesa(event, thread_id, mesa_db).start()

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=server_port)
