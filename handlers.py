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

class TelesHandler(tornado.web.RequestHandler):
    def put(self, peer_name: str = None, prop_name: str = None, val: Any = None,):
        print("set got")
        print(f"{peer_name} {prop_name} {val}")
        self.application.setPeerProp(peer_name, prop_name, val)

    def post(self, peer_name: str, command: str):
        print("cmd got")
        self.application.sendPeerCmd(peer_name, command)

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
        print("Received message:", message)
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