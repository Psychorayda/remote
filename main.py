import logging
from handlers import *
from app import Application

handlers = [
    (r"/", MainHandler),
    (r"/ws/", EchoWebSocket),
]

if __name__ == "__main__":
    app = Application(handlers=handlers)
    server = tornado.httpserver.HTTPServer(app)
    server.listen(18888)
    logging.info(f"Tornado server is running at http://localhost:18888")
    tornado.ioloop.IOLoop.current().start()
