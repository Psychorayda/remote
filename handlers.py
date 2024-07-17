from typing import List
import tornado
import tornado.websocket


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("WebSocket Server is running")


class EchoWebSocket(tornado.websocket.WebSocketHandler):
    def open(self):
        active_connections.append(self)
        print(f"WebSocket opened, there are {len(active_connections)} connections")

    def on_message(self, message):
        print("Received message:", message)

    def on_close(self):
        active_connections.remove(self)
        print(f"WebSocket closed, there are {len(active_connections.count())} connections")

active_connections: List[EchoWebSocket] = []