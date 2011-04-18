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

	def handle(self, indirect=False):
		"""indirect - connection using CONNECT instead of GET"""

		self.conn.type = Connection.HTTP

		if self.server.app.config.hide_http:
			self.server.app.remove_connection(self.conn)
		else:
			self.server.app.update_connection(self.conn)

		# Make request to original server or simulate reply

		if self.headers[0].find("/appsvc/appmsg") != -1:
			hub_request = True
		else:
			hub_request = False

		orig_request = "".join(self.headers) + self.body
		request = self.mangle_text(orig_request, self.server.app.config.http_request_rules)

		if self.server.app.config.simulation:
			# When simulating, we always can "connect" to the server.
			self.reply_connected()
			if orig_request != request:
				details = [orig_request, request]
			else:
				details = [request]
			self.server.app.log_connection(self.conn, Connection.HTTP_REQUEST, [details])

			(ip, port) = self.local_address

			if self.headers[0].find("/appsvc/appmsg.asp") != -1:
				reply = "HTTP/1.0 200 OK\r\n\r\n0 0 0 %s:8074 0.0.0.0 0.0.0.0\n" % (ip)
			elif self.headers[0].find("/appsvc/appmsg2.asp") != -1:
				reply = "HTTP/1.0 200 OK\r\n\r\n0 %s:8074 %s\n" % (ip, ip)
			elif self.headers[0].find("/appsvc/appmsg10.asp") != -1:
				reply = "HTTP/1.0 200 OK\r\n\r\n0 1 %s:443 %s\n" % (ip, ip)
			elif self.headers[0].find("/appsvc/appmsg") != -1:
				reply = "HTTP/1.0 200 OK\r\n\r\n0 0 %s:8074 %s\n" % (ip, ip)
			else:
				reply = "HTTP/1.0 404 Not Found\r\nContent-type: text/html\r\n\r\n<H1>Not Found</H1>"

			orig_reply = reply

		else:
			reply = self.get_reply(self.address, orig_request, request)

			if not reply:
				self.reply_error()
				self.client.close()
				return

			orig_reply = reply

			# If this is a hub reply, substitute server addres with our own

			if hub_request:
				# XXX
				# body[0] = self.change_server_address(body[0], self.local_address)
				pass

		# Mangle reply

		reply = self.mangle_text(reply, self.server.app.config.http_reply_rules)
		if orig_reply != reply:
			details = [orig_reply, reply]
		else:
			details = [reply]
		self.server.app.log_connection(self.conn, Connection.HTTP_REPLY, details)

		# Send the reply to the client

		self.client.write(reply)
		self.client.flush()
		self.client.close()
	
		return

	def get_reply(self, address, orig_request, request):
		"""Connects to original server and gets reply.

		Arguments:
		- address: Server address
		- orig_request: Original request string
		- request: Complete request string

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
		if orig_request != request:
			details = [orig_request, request]
		else:
			details = [request]
		self.server.app.log_connection(self.conn, Connection.HTTP_REQUEST, details)

		server.send(request)
		server_file = server.makefile("r")
		server.close()

		# Read the reply. First the headers...

		headers = []
		body = []

		while True:
			try:
				line = server_file.readline()
			except socket.error, msg:
				(errno, strerror) = msg
				self.server.app.log_connection(self.conn, Connection.HTTP_FAILED, strerror)
				return False

			if not line:
				self.server.app.log_connection(self.conn, Connection.HTTP_FAILED, headers.join("\n"))
				return False

			if line == "\r\n":
				break

			headers.append(line)

		if len(headers) < 1:
			return False

		# ...then the reply body

		while True:
			try:
				line = server_file.readline()
			except socket.error, msg:
				(errno, strerror) = msg
				self.server.app.log_connection(self.conn, Connection.HTTP_FAILED, strerror)
				break

			if not line:
				break

			body.append(line)

		reply = "".join(headers) + "\r\n" + "".join(body)

		return reply

	def change_server_address(self, line, address):
		"""Substitutes server address in hub reply. Stores original
		address for subsequent connections.

		Arguments:
		- line: First line of the reply
		- address: Local address

		Returns modified reply."""

		rule = re.compile("^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|ggproxy-\d+\.gadu-gadu\.pl)(?::(\d{1,5}))*")

		fields = string.split(line)

		(ip, port) = address
		port = 8074

		# Substitute all occurences of IP addresses to our own,
		# but store the original.

		for i in range(len(fields)):
			match = rule.match(fields[i])

			if match:
				if match.lastindex == 1:
					fields[i] = ip
					address = (match.group(1), 8074)
				else:
					fields[i] = ip + ":" + str(port)
					address = (match.group(1), int(match.group(2)))

				self.server.app.config.set_server_address(address)

		# Return result. Note that hub end the line with "\n"
		# not "\r\n".

		return " ".join(fields) + "\n"

