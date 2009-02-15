# -*- coding: utf-8 -*-

import re, socket, string
from SocketServer import BaseRequestHandler
from GaduHandler import *
from threading import *
from Connection import *

class HubHandler(BaseRequestHandler):
	"""Handles incoming hub requests."""

	def mangle_text(self, data, rules):
		"""Mangles text data.

		Arguments:
		- data: Text data
		- rules: List of rules"""

		for rule in rules:
			data = re.sub(rule.match, rule.replace, data)

		return data

	def handle(self):
		self.conn.type = Connection.HTTP
		self.server.app.update_connection(self.conn)

		# Make request to original server or simulate reply

		if self.headers[0].find("/appsvc/appmsg") != -1:
			hub_request = True
		else:
			hub_request = False

		orig_request = "".join(self.headers)
		request = self.mangle_text(orig_request, Config().http_request_rules)
		self.server.app.log_connection(self.conn, Connection.HTTP_REQUEST, request, orig_request)

		if Config().simulation:
			(ip, port) = self.local_address

			if self.headers[0].find("/appsvc/appmsg.asp") != -1:
				reply = "HTTP/1.0 200 OK\r\n\r\n0 0 0 %s:8074 0.0.0.0 0.0.0.0\n" % (ip)
			elif self.headers[0].find("/appsvc/appmsg2.asp") != -1:
				reply = "HTTP/1.0 200 OK\r\n\r\n0 %s:8074 %s\n" % (ip, ip)
			elif self.headers[0].find("/appsvc/appmsg") != -1:
				reply = "HTTP/1.0 200 OK\r\n\r\n0 0 %s:8074 %s\n" % (ip, ip)
			else:
				reply = "HTTP/1.0 404 Not Found\r\nContent-type: text/html\r\n\r\n<H1>Not Found</H1>"

		else:
			reply = self.get_reply(self.address, request, hub_request)

			if not reply:
				reply = "HTTP/1.0 503 Service Unavailable\r\nContent-type: text/html\r\n\r\n<H1>Service Unavailable</H1>"

		# Mangle reply

		orig_reply = reply
		reply = self.mangle_text(reply, Config().http_reply_rules)
		self.server.app.log_connection(self.conn, Connection.HTTP_REPLY, reply, orig_reply)

		# Send the reply to the client

		self.client.write(reply)
		self.client.flush()
		self.client.close()
	
		return

	def get_reply(self, address, request, hub_request = False):
		"""Connects to original server and gets reply.

		Arguments:
		- address: Server address
		- request: Complete request string
		- hub_request: Flag indicating hub request

		Returns complete reply string or False on failure."""

		# Connect to original server

		server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		self.server.app.log_connection(self.conn, Connection.HTTP_CONNECTING, "%s:%d" % address)

		try:
			server.connect(address)
		except socket.error, msg:
			(errno, strerror) = msg
			self.server.app.log_connection(self.conn, Connection.HTTP_FAILED, strerror)
			return False

		self.server.app.log_connection(self.conn, Connection.HTTP_CONNECTED)

		server.send(request)
		server_file = server.makefile("r")
		server.close()

		# Read the reply. First the headers...

		headers = []
		body = []

		while True:
			line = server_file.readline()

			if not line:
				return False

			if line == "\r\n":
				break

			headers.append(line)

		if len(headers) < 1:
			return False

		# ...then the reply body

		while True:
			line = server_file.readline()

			if not line:
				break

			body.append(line)

#		# If this is a hub reply, substitute server addres with our own
#
#		if hub_request and headers[0][:12] == "HTTP/1.0 200":
#			body[0] = self.change_server_address(body[0], self.local_address)

		reply = "".join(headers) + "\r\n" + "".join(body)

		return reply

#	def change_server_address(self, line, address):
#		"""Substitutes server address in hub reply. Stores original
#		address for subsequent connections.
#
#		Arguments:
#		- line: First line of the reply
#		- address: Local address
#
#		Returns modified reply."""
#
#		rule = re.compile("^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(:(\d{1,5}))*")
#
#		fields = string.split(line)
#
#		(ip, port) = address
#		port = 8074
#
#		# Substitute all occurences of IP addresses to our own
#
#		for i in range(len(fields)):
#			match = rule.match(fields[i])
#
#			if not match:
#				continue
#
#			# Substitute but store the original
#
#			if match.lastindex == 1:
#				fields[i] = ip
#				address = (match.group(1), 8074)
#			else:
#				fields[i] = ip + ":" + str(port)
#				address = (match.group(1), int(match.group(3)))
#
#			Config().set_server_address(address)
#
#		# Return result. Note that hub end the line with "\n"
#		# not "\r\n".
#
#		return " ".join(fields) + "\n"
#
