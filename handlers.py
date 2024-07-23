from datetime import datetime
import json
from typing import List
import tornado
import tornado.websocket
from tornado import ioloop


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("WebSocket Server is running")


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