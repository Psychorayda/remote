from datetime import datetime
import json
from typing import Any, List
import tornado
import tornado.websocket
from tornado import ioloop


# class BaseHandler(tornado.web.RequestHandler):
#     def set_default_headers(self):
#         self.set_header("Access-Control-Allow-Origin", "*")
#         self.set_header("Access-Control-Allow-Headers", "x-requested-with")
#         self.set_header("Access-Control-Allow-Methods", "*")

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("WebSocket Server is running")

class TelesSetHandler(tornado.web.RequestHandler):
    async def post(self):
        try:
            body: dict = json.loads(self.request.body)
            peer_name = body.get('peer_name')
            prop_name = body.get('prop_name')
            val = body.get('val')
            if not peer_name or not prop_name or val is None:
                self.set_status(400)
                self.write("Invalid request: Missing parameters")
                return
            self.application.setPeerProp(peer_name, prop_name, val)
        except json.JSONDecodeError:
            self.set_status(400)
            self.write("Invalid request: Unable to decode JSON")

class TelesCmdHandler(tornado.web.RequestHandler):
    async def post(self):
        try:
            body: dict = json.loads(self.request.body)
            peer_name = body.get('peer_name')
            command = body.get('command')
            if not peer_name or not command:
                self.set_status(400)
                self.write("Invalid request: Missing parameters")
                return
            self.application.sendPeerCmd(peer_name, command)
        except json.JSONDecodeError:
            self.set_status(400)
            self.write("Invalid request: Unable to decode JSON")

class EchoWebSocket(tornado.websocket.WebSocketHandler):
    def open(self):
        active_connections.append(self)
        print(f"WebSocket opened, there are {len(active_connections)} connections")
        self.count = 0
        self.periodic_ping = ioloop.PeriodicCallback(self.ping_conn, 5 * 1000)
        self.periodic_ping.start()

    def on_close(self):
        if hasattr(self, 'periodic_ping'):
            self.periodic_ping.stop()
        active_connections.remove(self)
        print(f"WebSocket closed, there are {len(active_connections)} connections")

    def ping_conn(self):
        if not self.ws_connection:
            return
        self.count += 1
        message = {
            "route": "PING",
            "data": {
                "deviceName": "",
                "time": str(datetime.now()),
                "count": self.count
            }
        }
        try:
            self.write_message(message)
        except tornado.websocket.WebSocketClosedError:
            print("WebSocket is closed. Stopping periodic ping.")
            self.periodic_ping.stop()

    def on_message(self, message):
        # print("Received message:", message)
        message: dict = json.loads(message)
        if message["route"] == "PING":
            self.write_message({
                "route": "PONG",
                "data": {
                    "deviceName": "",
                    "time": str(datetime.now()),
                    "count": message["data"]["count"]
                }
            })
    

active_connections: List[EchoWebSocket] = []