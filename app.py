import copy
from datetime import datetime, timezone
import logging
import pytz
import tornado
import tornado.websocket
from tornado import ioloop
import pyles

from handlers import active_connections


class Prop:
    def __init__(self, name: str, value: str):
        self.name = name
        self.value = value

class Device:
    def __init__(self, name: str):
        self.name = name
        self.props: list[Prop] = []

class Application(tornado.web.Application, 
                  pyles.TelesApp):
    def __init__(self, handlers) -> None:
        tornado.web.Application.__init__(self, handlers=handlers)
        pyles.TelesApp.__init__(self, 
                                name="web", 
                                in_type="server", 
                                is_client=True, 
                                recvlog=True, 
                                recvvalue=True,
                                site="test",
                                interface="")
        self.active_devices: list[Device] = []
        self.changed_props = set()
        self.active_connections = active_connections
        self.start()
        ioloop.PeriodicCallback(self.prop_diff, 1 * 1000).start()

    def prop_diff(self):
        try:
            changed_props_old = copy.deepcopy(self.changed_props)
            self.changed_props.clear()
            for device, prop in changed_props_old:
                device: Device
                prop: Prop
                message = {
                    "route": "PROP",
                    "data": {
                        "deviceName":  device.name,
                        "prop": {
                            prop.name: prop.value
                        }
                    }
                }
                for conn in self.active_connections:
                    conn.write_message(message=message)
        except Exception as e:
            logging.error("Error: {}".format(e))
        return

    def onInfo(self, peer: pyles.Peer) -> None:
        super().onInfo(peer)
        try:
            self.info(peer)
            self.onStatus(peer, peer.status)
            metadata = {}
            for prop_name in peer.properties:
                prop = peer.properties[prop_name]
                metadata[prop_name] = {
                    "value":     prop.valuestr, 
                    "desc":      prop.desc, 
                    "egu":       prop.egu, 
                    "writable":  prop.writable, 
                    "opts":      prop.choices, 
                    "type":      prop.type.name
                }
            self.metadataChange(peer.name, metadata)
            self.commandChange(peer, peer.commands)
        except Exception as e:
            logging.error("Error: {}".format(e))
    
    def onExit(self, peer: pyles.Peer) -> None:
        super().onExit(peer)
        # logging.info(f"Peer {peer.name} exited")
        try:
            device = self.getDeviceByName(peer.name)
            self.active_devices.remove(device)
            message = {
                "route": "CONN",
                "data": {
                    "deviceName": peer.name,
                    "connected":  False
                }
            }
            for conn in self.active_connections:
                conn.write_message(message=message)
        except Exception as e:
            logging.error("Error: {}".format(e))

    def info(self, peer: pyles.Peer) -> None:
        # logging.info(f"Peer {peer.name} entered")
        try:
            self.active_devices.append(Device(peer.name))
            message = {
                "route": "CONN",
                "data": {
                    "deviceName": peer.name,
                    "connected":  True
                }
            }
            for conn in self.active_connections:
                conn.write_message(message=message)
        except Exception as e:
            logging.error("Error: {}".format(e))

    def onStatus(self, peer: pyles.Peer, status: int) -> None:
        # logging.info(f"Peer {peer.name} status changed into {peer.statusStr}")
        try:
            message = {
                "route": "STATUS",
                "data": {
                    "deviceName": peer.name,
                    "statusInt":  status,
                    "statusStr":  peer.statusStr
                }
            }
            for conn in self.active_connections:
                conn.write_message(message=message)
        except Exception as e:
            logging.error("Error: {}".format(e))

    def metadataChange(self, peer_name: str, metadata: dict) -> None:
        try:
            device = self.getDeviceByName(peer_name)
            for prop_name, prop_meta in metadata.items():
                device.props.append(Prop(prop_name, prop_meta["value"]))
            message = {
                "route": "META",
                "data": {
                    "deviceName": peer_name,
                    "metadata":   metadata
                }
            }
            for conn in self.active_connections:
                conn.write_message(message=message)
        except Exception as e:
            logging.error("Error: {}".format(e))

    def onProperty(self, peer: pyles.Peer, prop: pyles.Property) -> None:
        # logging.info(f"Peer {peer.name} prop {prop.name} changed into {prop.valuestr}")
        try:
            device = self.getDeviceByName(peer.name)
            for dev_prop in device.props:
                if dev_prop.name == prop.name:
                    dev_prop.value = prop.valuestr
                    self.changed_props.add((device, dev_prop))
        except Exception as e:
            logging.error("Error: {}".format(e))

    def commandChange(self, peer: pyles.Peer, commands) -> None:
        try:
            cmds = {}
            for cmdname, cmd in commands.items():
                cmds[cmdname] = {}
                cmds[cmdname]['desc'] = cmd.desc
                cmds[cmdname]['args'] = {}
                for arg in cmd.args:
                    cmds[cmdname]['args'][arg.argname] = str(arg.type)[8:]
            message = {
                "route": "CMD",
                "data": {
                    "deviceName": peer.name,
                    "commands":   cmds
                }
            }
            for conn in self.active_connections:
                conn.write_message(message=message)
        except Exception as e:
            logging.error("Error: {}".format(e))
    
    def onLog(self, peer: pyles.Peer, logmsg):
        super().onLog(peer, logmsg)
        try:
            orig_time = datetime.fromtimestamp(logmsg.timesec + logmsg.timensec/1e9).astimezone(timezone.utc)
            message = {
                "route": "LOG",
                "data": {
                    "deviceName": logmsg.name,
                    "level":      logmsg.level.name,
                    "message":    logmsg.message,
                    "time":       orig_time.isoformat(),
                }
            }
            for conn in self.active_connections:
                conn.write_message(message=message)
        except Exception as e:
            logging.error("Error: {}".format(e))

    def getDeviceByName(self, dev_name: str):
        for device in self.active_devices:
            if device.name == dev_name:
                return device
        logging.warn("Device not found: {}".format(dev_name))
        return None
