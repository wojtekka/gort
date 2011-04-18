# -*- coding: utf-8 -*-

import time, struct
from Utils import *
from PacketParser import *

class Event:
	def __init__(self, conn, type, details=None):
		self.timestamp = time.time()
		self.timestamp_str = "%.3f" % (self.timestamp - conn.open_timestamp)
		self.details = details
		self.type = type

		if type == Connection.PROXY_REQUEST:
			self.type_str = "Proxy request"
		elif type == Connection.PROXY_REPLY:
			self.type_str = "Proxy reply"
		elif type == Connection.HTTP_CONNECTING or type == Connection.GADU_CONNECTING:
			self.type_str = "Connecting to %s" % details
			self.details = None
		elif type == Connection.HTTP_CONNECTED or type == Connection.GADU_CONNECTED:
			self.type_str = "Connected"
		elif type == Connection.HTTP_FAILED or type == Connection.GADU_FAILED:
			self.type_str = "Connection failed"
		elif type == Connection.HTTP_REQUEST:
			self.type_str = "HTTP request"
		elif type == Connection.HTTP_REPLY:
			self.type_str = "HTTP reply"
		elif type == Connection.GADU_CLIENT:
			self.type_str = "Client packet"
			self.parse_packet(False)
		elif type == Connection.GADU_SERVER:
			self.type_str = "Server packet"
			self.parse_packet(True)
		elif type == Connection.GADU_SIMULATED_CLIENT:
			self.type_str = "Simulated client packet"
			self.parse_packet(False)
		elif type == Connection.GADU_SIMULATED_SERVER:
			label = "Simulated server packet"
			self.parse_packet(True)
		elif type == Connection.GADU_STATE:
			self.type_str = "Changed state to %s" % details
			self.details = None
		elif type == Connection.GADU_SSL:
			self.type_str = "Detected SSL connection"
		elif type == Connection.GADU_CLIENT_DISCONNECTED:
			self.type_str = "Client disconnected"
		elif type == Connection.GADU_SERVER_DISCONNECTED:
			self.type_str = "Server disconnected"
		elif type == Connection.PROXY_CONNECTED:
			self.type_str = "New connection from %s" % details
			self.details = None
		elif type == Connection.RAW_CLIENT:
			self.type_str = "Client packet"
		elif type == Connection.RAW_SERVER:
			self.type_str = "Server packet"
		else:
			self.type_str = "Unknown event (%d)" % self.type

	def parse_packet(self, from_server):
		type_str = self.type_str

		for i in range(len(self.details)):
			parser = PacketParser(self.details[i], from_server)
			name = parser.get_name()
			if name:
				self.type_str = type_str + " " + name
			self.details[i] = parser.get_data()

class Connection:
	UNKNOWN, GADU, HTTP = range(3)

	PROXY_REQUEST = 0
	PROXY_REPLY = 1
	HTTP_CONNECTING = 2
	HTTP_CONNECTED = 3
	HTTP_FAILED = 4
	HTTP_REQUEST = 5
	HTTP_REPLY = 7
	GADU_CONNECTING = 9
	GADU_CONNECTED = 10
	GADU_FAILED = 11
	GADU_STATE = 12
	GADU_SERVER = 13
	GADU_CLIENT = 14
	GADU_SIMULATED_SERVER = 15
	GADU_SIMULATED_CLIENT = 16
	GADU_SSL = 17
	GADU_CLIENT_DISCONNECTED = 18
	GADU_SERVER_DISCONNECTED = 19
	PROXY_CONNECTED = 20
	RAW_CLIENT = 21
	RAW_SERVER = 22

	def __init__(self, source):
		self.source = source	
		self.open_timestamp = time.time()
		self.active = True
		self.events = []
		self.listener = None
		self.iter = None
		self.type = self.UNKNOWN

	def append(self, type, details=None):
		event = Event(self, type, details)
		self.events.append(event)
		return event

	def close(self):
		self.close_timestamp = time.time()
		self.active = False
