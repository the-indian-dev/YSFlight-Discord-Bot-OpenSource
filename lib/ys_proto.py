#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Author      : https://theindiandev.in/
Forked from : https://bitbucket.org/vincentweb/ys_proto/src
Indentation : 4 spaces
"""

import time
from struct import pack, unpack
import socket
import threading
import logging

logging.basicConfig(level=logging.INFO)


class ProtoEncoder:
    """
    YS Protocol Encoder Class
    -------------------------
    This Class contains all the functions for preparing packets
    to be sent to the YSFlight Server
    """
    @staticmethod
    def send(buffer: bytes):
        """
        Add to a packet the 'size' information
        """
        return pack("I", len(buffer)) + buffer

    @staticmethod
    def reply(type: int, buffer: bytes):
        """
        - Shortcut to reply the packet you received
        - Can also be used to generate packets for required actions
        type: the type of the received packet
        buffer: the received buffer
        return: the reply
        """
        return ProtoEncoder.send(pack("I", type) + buffer)

    @staticmethod
    def ack(id, info):
        """
        Shortcut to send an acknowledgement packet
        """
        return pack('IIII', 12, 6, id, info)

    @staticmethod
    def login(username: bytes = b"ysProtoBot", version: int = 20150425):
        """
        Returns a packet of type 1: login
        username : username of the bot
        version : YSFlight Net version
        return: The login packet
        """
        username = username[0:15]
        version = int(version)
        return ProtoEncoder.send(pack("I16sI", 1, username, version))

    @staticmethod
    def integer(integer):
        """
        Generate an integer into a packet
        """
        return ProtoEncoder.send(pack("I", integer))

    @staticmethod
    def keep_alive():
        """
        Generate packets for keeping the connection alive
        """
        logging.debug("Keep Alive Packet Sent!")
        return ProtoEncoder.send(pack("I", 17))

    @staticmethod
    def message(msg: str, add_bot_tag: bool = True, bot_tag: str = "[BOT]"):
        """
        Generate packets for sending messages
        """
        if add_bot_tag:
            msg = bot_tag + msg
        decode = "l" + str(len(msg) + 2) + "s"
        msg_buffer = bytes(msg, 'utf-8')
        buffer = pack(decode, 0, msg_buffer)
        return ProtoEncoder.reply(32, buffer)


class ProtoDecoder:
    """
    YSF Protocol Decoder Class
    --------------------------
    This class contains all the functions for decoding
    packets received from the server
    """
    @staticmethod
    def flight_options(buffer: bytes):
        """
        Read packet of type 43
        buffer = bytes for the data
        return: The tuple (unknown, option)
        """
        decode = "I" + str(len(buffer) - 4) + "s"
        return unpack(decode, buffer)

    @staticmethod
    def map(buffer: bytes):
        """
        Read packet of type 4
        buffer : bytes for the data
        return: A tuple containing the name of the map
        """
        try:
            return unpack("60s", buffer)
        except:
            logging.critical("INVALID MAP. TERMINATING...")

    @staticmethod
    def msg(buffer: bytes):
        """
        Read packet of type 32
        buffer : bytes of the data
        @return: The tuple (unknown_long, chat_message)
        """
        decode = "l" + str(len(buffer) - 8) + "s"
        return unpack(decode, buffer)

    @staticmethod
    def integer(buffer):
        """
        Read packet of type 29, 31, 39
        buffer : bytes of the data
        return: (tuple) The YS version of the server,
                 if the missiles are on or off,
                 if the weapons are on or off, ...
        """
        return unpack("I", buffer)

    @staticmethod
    def players(buffer: bytes):
        """
        Read packet of type 37
        buffer : bytes of data
        return: The tuple (action, IFF, ID, unknown, nickname)
        """
        decode = "hhII" + str(len(buffer) - 12) + "s"
        return unpack(decode, buffer)

    @staticmethod
    def weather(buffer: bytes):
        """
        Read packet of type 33
        buffer : bytes of data
        return: The tuple (day, options, windX, windY, windZ, visibility)
        """
        return unpack("IIffff", buffer)


class Server:
    """
    Server class
    ------------
    This class holds the credentials to connect with the YSFlight Server
    It also has all the functions required interact with the server
    """
    def __init__(self, ip: str, port: int = 7915,
                 username: str = "ysProtoBot",
                 version: int = 20150425,
                 timeout: int = 5,
                 bot_tag: str = '[BOT]'):
        self.ip = ip
        self.port = port
        self.username = bytes(username[0:15], 'utf-8')
        self.version = version
        self.status = "offline"
        self.map = b""
        self.missileON = 0
        self.weaponON = 0
        self.blackoutON = 0
        self.collON = 0
        self.landingON = 0
        self.weather = (0, 0, 0.0, 0.0, 0.0, 0.0)
        self.radarAlti = b""
        self.f3view = True
        self.userList = []
        self.users = 0
        self.flyingUsers = 0
        self.timeout = timeout  # Amount of time to wait for server to respond
        self.connector = socket.socket()
        self.connection_status = False
        self.userOption = 0     # Show usernames within 'n' radius distance while flying
        self.tag = bot_tag
        self.log_private_msgs = False   # Ignores messages sent to the bot privately and its own messages
        self.keep_alive_thread = threading.Thread(target=self.keep_alive)
        self.__listeners_on_msg = []   # Listeners for the on message events

    def __eq__(self, other):
        if not isinstance(other, Server):
            return NotImplemented
        return self.ip == other.ip and\
            self.port == other.port and\
            self.version == other.version

    def return_info(self):
        users = []
        for user in self.userList:
            username = user[-1].decode("UTF-8")
            users.append(username)
        return {"status": self.status, "radarAlti": self.radarAlti, "userList": users, "map": self.map.decode('utf-8'),
                "blackout": self.blackoutON,
                "weather": self.weather, "radar": self.radarAlti, "f3": str(self.f3view), "missileON": self.missileON}

    def disconnect(self):
        self.connection_status = False
        try:
            self.connector.close()
        except:
            logging.warning("Failed to disconnect!")

    def send(self, buffer):
        """Send 'buffer' to the server
        return: 1 if success, 0 else
        """
        try:
            self.connector.send(buffer)
            return 1
        except Exception as e:
            logging.warning("Failed to send buffer! %s", e)
            return 0

    def receive(self):
        """Receive data from the server
        @return: the tuple (size, type, buffer)
        size=0 and type=0 in case of failure
        """
        try:
            size = ProtoDecoder.integer(self.connector.recv(4))[0]
            type = ProtoDecoder.integer(self.connector.recv(4))[0]
            logging.debug("size " + str(size) + " type " + str(type))
        except:
            logging.debug("Receive failure 1")
            return 0, 0, ""
        try:
            return size, type, self.connector.recv(size - 4)
        except:
            logging.debug("Receive failure 2")
            return size, 0, ""

    def connect(self):
        self.connector.settimeout(self.timeout)
        try:
            self.connector.connect((self.ip, self.port))
            self.connection_status = True
            logging.info("Connection to %s successful!", self.ip)
        except Exception as e:
            self.status = "offline"
            logging.warning("Connection to %s UNSUCCESSFUL! Error : %s", self.ip, e)
            return
        if not (self.send(ProtoEncoder.login(self.username, self.version))):
            self.status = "locked"
            logging.warning("Server Locked!")
            return
        logging.info("Connected!")
        self.keep_alive_thread.start()
        while self.connection_status:
            (size, type, buffer) = self.receive()
            self.status = "online"
            if not (self.processor(size, type, buffer)):
                self.status = "online"  # should be laggy
                # if there were and error
                #  or if we see an aircraft_list packet, we exit
                # if type == 0:# or type==44:
                logging.info("enough!")
                self.disconnect()

    def send_message(self, msg: str, add_bot_tag: bool = True, tag: str = None):
        """
        msg : The message you want to send
        """
        if tag is None:
            tag = self.tag
        msg_buffer = ProtoEncoder.message(msg, add_bot_tag, tag)
        self.send(msg_buffer)

    def keep_alive(self):
        while True:
            time.sleep(30)
            self.send(ProtoEncoder.keep_alive())
            logging.debug("Sent alive packet")

    def on_message(self, func):
        self.__listeners_on_msg.append(func)
    
    def processor(self, size, type, buffer):
        """
        Takes the decision of what doing when we receive a packet
        of type X
        """
        if type == 0:
            return 1
        elif type == 4:
            self.map = ProtoDecoder.map(buffer)[0]
            end = self.map.find(b'\x00')
            self.map = self.map[:end]
            # logging.info("map " + self.map)
            self.send(ProtoEncoder.reply(4, buffer))
            # ask to get the weather packet:
            self.send(ProtoEncoder.integer(33))
            # ask to get the user-list:
            self.send(ProtoEncoder.integer(37))
        elif type == 16:
            # we finished with the air-list
            self.send(ProtoEncoder.ack(7, 0))
        elif type == 29:
            self.version = ProtoDecoder.integer(buffer)[0]
            logging.debug("version " + str(self.version))
            if self.version != self.version:
                logging.warning("reconnecting with another net-version")
                self.disconnect()
                self.connect()
            else:
                self.send(ProtoEncoder.ack(9, 0))
        elif type == 31:
            self.missileON = bool(ProtoDecoder.integer(buffer)[0])
            logging.debug("missileON " + str(self.missileON))
            self.send(ProtoEncoder.ack(10, 0))
        elif type == 32:
            msg_buffer = ProtoDecoder.msg(buffer)[1]
            msg = msg_buffer.decode().split('\x00', 1)[0]
            if msg == "** Log-on process completed **":
                logging.info("Log-on process completed")
            elif not msg.startswith(self.tag):
                logging.debug(msg)
                for func in self.__listeners_on_msg:
                    func(msg, self)
        elif type == 33:
            self.weather = ProtoDecoder.weather(buffer)
            opts = bin(self.weather[1])
            self.collON = bool(int(opts[5]))
            logging.debug("collON " + str(self.collON))
            self.blackoutON = bool(int(opts[7]))
            logging.debug("blackoutON " + str(self.blackoutON))
            self.landingON = bool(int(opts[3]))
            logging.debug("landevON " + str(self.landingON))
            logging.debug(
                "day " + str(self.weather[0]) +
                " windX " + str(self.weather[2]) +
                " windZ " + str(self.weather[3]) +
                " windY " + str(self.weather[4]) +
                " visib " + str(self.weather[5])
            )
            self.send(ProtoEncoder.ack(4, 0))
        elif type == 37:  # Never received, FIXME
            user = list(ProtoDecoder.players(buffer))
            user[4] = user[4].rstrip(b'\0')  # to remove null at end
            user = tuple(user)
            self.userList.append(user)
            if user[0] == 1 or user[0] == 3:
                self.flyingUsers += 1
            if user[4] != self.username and user[4] != 'Console Server':
                self.users += 1
            logging.debug("user " + str(user))
        elif type == 39:
            self.weaponON = bool(ProtoDecoder.integer(buffer)[0])
            logging.debug("weaponON " + str(self.weaponON))
            self.send(ProtoEncoder.ack(11, 0))
        elif type == 41:
            self.userOption = ProtoDecoder.integer(buffer)[0]
            logging.debug("User option " + str(self.userOption))
        elif type == 43:
            self.send(ProtoEncoder.reply(43, buffer))
            mesg = ProtoDecoder.flight_options(buffer)[1]
            if mesg[:14] == "NOEXAIRVW TRUE":
                logging.info("no F3 view")
                self.f3view = False
            else:
                try:
                    self.radarAlti = float(mesg[10:-2])
                except:
                    self.radarAlti = 0
                logging.debug("radar alti " + str(self.radarAlti))
        elif type == 44:
            self.send(ProtoEncoder.reply(44, buffer))
            # aircraft list
        return 1


class Subscription:
    def __init__(self):
        self.servers = []
        self.__subscribed = []
        self.__subscribed_threads = []

    def subscribe(self, server: Server):
        self.servers.append(server)
        t = threading.Thread(target=server.connect)
        t.start()
        self.__subscribed_threads.append(t)

        @server.on_message
        def e(msg, server_recv):
            self.listen(msg, server_recv)
        return 0

    def unsubscribe(self, server: Server):
        try:
            self.servers.remove(server)
            return 0
        except:
            logging.warning("The following server doesn't exist")
            return -1

    def on_message(self, func):
        self.__subscribed.append(func)

    def interact(self, server: Server, msg:str, tag:str = None):
        for all_server in self.servers:
            if server == all_server:
                all_server.send_message(msg, tag=tag)
                return 0

        logging.warning("Couldn't find the server!")
        return -1

    def listen(self, msg,  server_recv):
        for func in self.__subscribed:
            try:
                func(msg, server_recv)
            except Exception as e:
                print(e)
