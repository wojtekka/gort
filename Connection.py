# -*- coding: utf-8 -*-

import time

def _hex_dump(data):
	result = ""
	offset = ""
	hex = ""
	chars = ""

	for i in range(len(data)):
		if i % 16 == 0:
			offset = "%04x: " % i
			hex = ""
			chars = ""

		hex = hex + "%02x" % ord(data[i])

		if data[i] < ' ' or data[i] > '~':
			chars = chars + "."
		else:
			chars = chars + data[i]

		if i % 16 == 15:
			result = result + offset + hex + "  " + chars + "\r\n"
			
		if i + 1 != len(data):
			hex = hex + " "

	if hex and chars and offset:
		hex = hex + "   " * (16 - (len(data) % 16))

		result = result + offset + hex + "  " + chars + "\r\n"

	return result

class Event:
	def __init__(self, conn, type, details=None, orig_details=None):
		self.timestamp = time.time()
		self.timestamp_str = "%.3f" % (self.timestamp - conn.open_timestamp)

		self.details = details

		if details != orig_details:
			self.orig_details = orig_details
		else:
			self.orig_details = None

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
			self.details = _hex_dump(self.details).strip()
			if self.orig_details:
				self.orig_details = _hex_dump(self.orig_details).strip()
		elif type == Connection.GADU_SERVER:
			self.type_str = "Server packet"
			self.details = _hex_dump(self.details).strip()
			if self.orig_details:
				self.orig_details = _hex_dump(self.orig_details).strip()
		elif type == Connection.GADU_SIMULATED_CLIENT:
			self.type_str = "Simulated client packet"
			self.details = _hex_dump(self.details).strip()
		elif type == Connection.GADU_SIMULATED_SERVER:
			self.type_str = "Simulated server packet"
			self.details = _hex_dump(self.details).strip()
		elif type == Connection.GADU_STATE:
			self.type_str = "Changed state to %s" % details
			self.details = None
		else:
			self.type_str = "Unknown event (%d)" % self.type

class Connection:
	UNKNOWN = 0
	GADU = 1
	HTTP = 2

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

	def __init__(self, source):
		self.source = source	
		self.open_timestamp = time.time()
		self.active = True
		self.events = []
		self.listener = None
		self.iter = None
		self.type = self.UNKNOWN

	def append(self, type, details=None, orig_details=None):
		event = Event(self, type, details, orig_details)
		self.events.append(event)
		return event

	def close(self):
		self.close_timestamp = time.time()
		self.active = False
